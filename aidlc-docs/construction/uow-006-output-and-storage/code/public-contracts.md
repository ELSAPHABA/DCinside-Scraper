# Public Contracts - UOW-006 Output And Storage

## Package Exports

UOW-006 adds import-safe storage components under:

```python
dcinside_scraper.outputs
```

Root package exports were also updated for common storage classes:

- `LocalOutputStore`
- `LocalMediaStore`
- `LocalCheckpointStore`
- `OutputRunLayout`
- `S3ObjectStore`

## Local Output Store

```python
from dcinside_scraper.outputs import LocalOutputStore, OutputRunLayout

layout = OutputRunLayout.create(job_id="job-1", run_id="run-1", base_path=".")
store = LocalOutputStore(layout)

post_ref = await store.append_post(post_result)
failure_ref = await store.write_failure(failure_record)
await store.finalize(job_report)
```

Contract:

- writes `outputs/<job_id>/<run_id>/posts.jsonl`
- writes `outputs/<job_id>/<run_id>/failures.jsonl`
- writes `outputs/<job_id>/<run_id>/report.json`
- returns local `StoredObjectRef` values for JSONL append targets
- redacts failure metadata through allow-list rules

## Local Media Store

```python
from dcinside_scraper.outputs import LocalMediaStore

saved_item = await LocalMediaStore(layout).save_media(media_item, content_bytes)
metadata_only_item = await LocalMediaStore(layout).save_metadata_only(media_item)
```

Contract:

- receives already downloaded bytes
- does not perform HTTP requests
- writes under `outputs/<job_id>/<run_id>/media/...`
- returns `MediaItem` with `file_path` in local mode

## Local Checkpoint Store

```python
from dcinside_scraper.outputs import LocalCheckpointStore

store = LocalCheckpointStore(base_path=".")
await store.save(checkpoint)
loaded = await store.load("job-1")
latest = await store.load_latest()
```

Contract:

- stores multiple latest checkpoints in `Checkpoint.json`
- uses process-local locking
- writes through temp-file replace
- targets single-process local execution

## Layout And Pathing

```python
from dcinside_scraper.outputs import OutputRunLayout, sanitize_path_segment, ensure_under_base

layout = OutputRunLayout.create(job_id="job-1", run_id="run-1", prefix="prod")
layout.posts_key
layout.posts_path
layout.prefixed_key(layout.posts_key)
```

Contract:

- sanitizes `job_id`, `run_id`, gallery IDs, post IDs, media type, and filenames
- verifies resolved local paths stay under the configured base directory
- mirrors local relative keys for S3-compatible object keys

## JSON Helpers

```python
from dcinside_scraper.outputs import JsonlWriter, AtomicJsonWriter, to_json_line
```

Contract:

- `JsonlWriter` writes one JSON object plus newline and flushes per record
- `AtomicJsonWriter` writes small JSON documents through temp-file replace
- `to_json_line` serializes Pydantic models with `model_dump(mode="json")`

## Safe Failure Context

```python
from dcinside_scraper.outputs import SafeFailureRecordBuilder, sanitize_failure_context
```

Allowed metadata keys:

- `site_id`
- `gallery_id`
- `post_id`
- `post_number`
- `url`
- `stage`
- `reason`
- `retryable`
- `http_status`
- `proxy_host`
- `user_agent`

Unknown fields are dropped. Proxy credentials, cookies, tokens, raw headers, and raw HTML/body/content are not written.

## S3-Compatible Boundary

```python
from dcinside_scraper.outputs import S3ObjectStore

store = S3ObjectStore(bucket="bucket", layout=layout, endpoint_url="http://garage:3900")
ref = store.object_ref(layout.posts_key)
await store.put_bytes(layout.report_key, b"{}", content_type="application/json")
```

Contract:

- lazy imports `boto3`
- root package import works without S3 extra installed
- object keys mirror local relative layout
- Garage-specific APIs are not used
- S3 write failures surface as `StorageFailureError`

## Boundaries

UOW-006 does not:

- collect links
- fetch posts
- download media from URLs
- deduplicate posts
- decide checkpoint commit timing
- read `.env`
- parse docker environment variables
- provision Garage/PostgreSQL/container resources
