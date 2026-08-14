"""S3-compatible object storage boundary."""

from __future__ import annotations

from typing import Any

import anyio

from dcinside_scraper.core.errors import StorageFailureError
from dcinside_scraper.models.report import StoredObjectRef
from dcinside_scraper.outputs.layout import OutputRunLayout


class S3ObjectStore:
    """Lazy S3 client wrapper for Garage/SeaweedFS-compatible object writes."""

    def __init__(
        self,
        *,
        bucket: str,
        layout: OutputRunLayout,
        client: Any | None = None,
        endpoint_url: str | None = None,
        region_name: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        force_path_style: bool = False,
    ) -> None:
        self.bucket = bucket
        self.layout = layout
        self._client = client
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.force_path_style = force_path_style

    def object_ref(self, key: str) -> StoredObjectRef:
        object_key = self.layout.prefixed_key(key)
        return StoredObjectRef(
            uri=f"s3://{self.bucket}/{object_key}",
            storage_type="s3",
            object_key=object_key,
            local_path=None,
        )

    async def put_bytes(self, key: str, content: bytes, *, content_type: str | None = None) -> StoredObjectRef:
        object_key = self.layout.prefixed_key(key)
        kwargs: dict[str, Any] = {
            "Bucket": self.bucket,
            "Key": object_key,
            "Body": content,
        }
        if content_type:
            kwargs["ContentType"] = content_type
        try:
            await anyio.to_thread.run_sync(lambda: self._get_client().put_object(**kwargs))
        except Exception as exc:
            raise StorageFailureError(
                "s3 object write failed",
                details={"stage": "s3", "reason": exc.__class__.__name__},
            ) from exc
        return self.object_ref(key)

    async def get_bytes(self, object_key: str) -> bytes:
        try:
            response = await anyio.to_thread.run_sync(
                lambda: self._get_client().get_object(Bucket=self.bucket, Key=object_key)
            )
            body = response["Body"]
            raw = await anyio.to_thread.run_sync(body.read) if hasattr(body, "read") else body
            return raw if isinstance(raw, bytes) else str(raw).encode("utf-8")
        except Exception as exc:
            raise StorageFailureError(
                "s3 object read failed",
                details={"stage": "s3", "reason": exc.__class__.__name__},
            ) from exc

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            import boto3
        except ImportError as exc:
            raise StorageFailureError(
                "s3 extra is required",
                details={"stage": "s3", "reason": "missing_s3_dependency"},
            ) from exc
        kwargs: dict[str, Any] = {}
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        if self.region_name:
            kwargs["region_name"] = self.region_name
        if self.access_key_id:
            kwargs["aws_access_key_id"] = self.access_key_id
        if self.secret_access_key:
            kwargs["aws_secret_access_key"] = self.secret_access_key
        if self.force_path_style:
            try:
                from botocore.config import Config
            except ImportError as exc:
                raise StorageFailureError(
                    "s3 extra is required",
                    details={"stage": "s3", "reason": "missing_s3_dependency"},
                ) from exc
            kwargs["config"] = Config(s3={"addressing_style": "path"})
        self._client = boto3.client("s3", **kwargs)
        return self._client
