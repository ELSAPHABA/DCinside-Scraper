"""Storage factory from configured DCinside job storage settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dcinside_scraper.core.errors import StorageFailureError
from dcinside_scraper.models.enums import CheckpointMode, OutputMode
from dcinside_scraper.models.job import StorageConfig
from dcinside_scraper.outputs.local import LocalCheckpointStore, LocalMediaStore, LocalOutputStore, OutputRunLayout
from dcinside_scraper.outputs.postgres_checkpoint import PostgresCheckpointStore
from dcinside_scraper.outputs.s3 import S3ObjectStore
from dcinside_scraper.outputs.s3_output import S3OutputStore


@dataclass(frozen=True)
class StorageBundle:
    output_store: Any
    failure_store: Any
    media_store: Any
    checkpoint_store: Any
    layout: OutputRunLayout


class StorageFactory:
    @classmethod
    def create(
        cls,
        config: StorageConfig,
        *,
        job_id: str,
        run_id: str,
        s3_client: Any | None = None,
        postgres_connection_factory: Any | None = None,
        s3_access_key_id: str | None = None,
        s3_secret_access_key: str | None = None,
        s3_force_path_style: bool = False,
    ) -> StorageBundle:
        layout = OutputRunLayout.from_storage_config(config, job_id=job_id, run_id=run_id)
        checkpoint_store = cls._checkpoint_store(config, postgres_connection_factory=postgres_connection_factory)
        if config.output_mode == OutputMode.LOCAL:
            output_store = LocalOutputStore(layout)
            return StorageBundle(output_store, output_store, LocalMediaStore(layout), checkpoint_store, layout)
        if config.output_mode == OutputMode.S3:
            if config.s3 is None:
                raise StorageFailureError("s3 config is required when output_mode is s3", details={"stage": "storage_config"})
            output_store = S3OutputStore(
                layout,
                S3ObjectStore(
                    bucket=config.s3.bucket,
                    layout=layout,
                    client=s3_client,
                    endpoint_url=config.s3.endpoint_url,
                    region_name=config.s3.region,
                    access_key_id=s3_access_key_id,
                    secret_access_key=s3_secret_access_key,
                    force_path_style=s3_force_path_style,
                ),
            )
            return StorageBundle(output_store, output_store, output_store, checkpoint_store, layout)
        raise StorageFailureError("unsupported output mode", details={"stage": "storage_config", "output_mode": str(config.output_mode)})

    @staticmethod
    def _checkpoint_store(config: StorageConfig, *, postgres_connection_factory: Any | None = None) -> Any:
        if config.checkpoint_mode == CheckpointMode.LOCAL:
            return LocalCheckpointStore(config.base_output_path)
        if config.checkpoint_mode == CheckpointMode.POSTGRES:
            if config.postgres is None:
                raise StorageFailureError(
                    "postgres config is required when checkpoint_mode is postgres",
                    details={"stage": "storage_config"},
                )
            return PostgresCheckpointStore(config.postgres.dsn, connection_factory=postgres_connection_factory)
        raise StorageFailureError("unsupported checkpoint mode", details={"stage": "storage_config", "checkpoint_mode": str(config.checkpoint_mode)})


__all__ = ["StorageBundle", "StorageFactory"]
