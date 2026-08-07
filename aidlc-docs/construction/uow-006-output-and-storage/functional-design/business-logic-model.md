# Business Logic Model - UOW-006 Output And Storage

## Purpose

UOW-006 stores scraper outputs produced by earlier units.

This unit owns Job JSONL output, failure JSONL output, final Job report output, local media writes, S3-compatible object writes, and local checkpoint file persistence. It does not own link collection, post parsing, HTTP media download, retry scheduling, worker orchestration, PostgreSQL checkpoint storage, CLI prompts, container runtime, or MCP hosting.

## Confirmed Decisions

| Area | Decision |
|---|---|
| Output store contract | `OutputStorePort` appends `PostResult`, writes `FailureRecord`, finalizes `JobReport`, and returns `StoredObjectRef` for written objects |
| JSONL naming | local/S3 object layout uses `outputs/<job_id>/<run_id>/posts.jsonl`; resume creates a new `run_id` |
| JSON shape | `PostResult.model_dump(mode="json")` is written as one JSON object per line with nested content/media/comments preserved and nullable fields kept |
| Polars boundary | current JSONL keeps scraper-native nested records; future platform normalization can split posts/comments/media into common Polars tables |
| Media storage | `MediaStorePort` stores already downloaded bytes and updates `MediaItem.file_path` or `MediaItem.object_key`; HTTP download belongs outside UOW-006 |
| Failure/report output | failures go to `outputs/<job_id>/<run_id>/failures.jsonl`; final summary goes to `outputs/<job_id>/<run_id>/report.json` |
| Failure context | failure records may include safe request context such as proxy host and user-agent; proxy ID/PW, cookies, tokens, raw HTML, and raw headers are excluded |
| Local checkpoint | `Checkpoint.json` stores latest checkpoints for multiple `job_id` values and is written by temporary-file replace |
| S3-compatible storage | Garage is the default deployment target through S3-compatible configuration; no Garage-only API is required |
| Idempotency | output stores are append-only; duplicate prevention belongs to UOW-005 checkpoint/completed-key logic |

## Output Flow

1. Caller creates or resumes a Job run and chooses a `run_id`.
2. Caller opens an output store from `StorageConfig`.
3. For each successful `PostResult`, caller invokes `append_post`.
4. Store serializes the post with Pydantic JSON mode.
5. Store appends exactly one newline-delimited JSON object to `posts.jsonl`.
6. Store returns a `StoredObjectRef`.
7. For each failed item, caller invokes `write_failure`.
8. At Job end, caller invokes `finalize` with `JobReport`.

Checkpoint commit ordering is not decided inside UOW-006. UOW-005 must call checkpoint save only after the relevant output call succeeds.

## Local Output Layout

Default local layout:

```text
<base_output_path>/
  outputs/
    <job_id>/
      <run_id>/
        posts.jsonl
        failures.jsonl
        report.json
        media/
          <gallery_id>/
            <post_no>/
              <media_type>/
                <filename>
  Checkpoint.json
```

If `StorageConfig.base_output_path` is missing, the runtime working directory is the base path.

`run_id` must be unique for each run attempt. Resume reuses the same `job_id` but creates a new `run_id`, so old JSONL files are never appended after resume.

## JSONL Serialization Flow

`PostResult` records are serialized by:

1. `model_dump(mode="json")`
2. safe JSON encoding with `ensure_ascii=False`
3. append one object plus `\n`
4. flush after each append or according to the concrete writer's minimal buffering policy

Nested fields are preserved:

- `content`
- `images`
- `comments`
- `links`
- `repost`
- `recommendations`
- `metadata`

Optional values remain `null`. Empty collections remain empty arrays.

## Failure Output Flow

`FailureRecord` writes use the same JSONL rules as posts.

Allowed safe context:

- `gallery_id`
- `post_id`
- `post_number`
- `url`
- `stage`
- `reason`
- `retryable`
- `proxy_host`
- `user_agent`

Forbidden context:

- proxy ID
- proxy password
- cookie values
- token values
- raw request or response headers
- raw HTML/body/content
- credential file contents

If a lower layer supplies unsafe fields, UOW-006 must drop or redact them before writing.

## Media Storage Flow

`MediaStorePort.save_media(item, content)` receives:

- a `MediaItem`
- already downloaded bytes

The media store:

1. derives a safe filename from `media_id`, URL path, or media type fallback
2. writes bytes under `media/<job_id>/<gallery_id>/<post_no>/<media_type>/`
3. returns the updated `MediaItem`

Local mode sets `file_path`. S3-compatible mode sets `object_key`. Metadata-only mode calls `save_metadata_only` and does not write bytes.

## Local Checkpoint Flow

`CheckpointStorePort.save` updates `Checkpoint.json`.

File shape:

```json
{
  "schema_version": "dcinside.local_checkpoint.v1",
  "updated_at": "2026-08-07T00:00:00Z",
  "checkpoints": {
    "<job_id>": {}
  }
}
```

Write flow:

1. load existing checkpoint map if present
2. replace the target `job_id`
3. write the whole document to a temp file in the same directory
4. atomically replace `Checkpoint.json`

`load(job_id)` reads the matching entry. `load_latest()` returns the checkpoint with the newest `updated_at`.

## S3-Compatible Flow

S3-compatible output uses the same object keys as local mode:

```text
<prefix>/outputs/<job_id>/<run_id>/posts.jsonl
<prefix>/outputs/<job_id>/<run_id>/failures.jsonl
<prefix>/outputs/<job_id>/<run_id>/report.json
<prefix>/outputs/<job_id>/<run_id>/media/<gallery_id>/<post_no>/<media_type>/<filename>
```

Garage is configured through standard S3-compatible fields:

- endpoint URL
- bucket
- optional prefix
- optional region
- access key and secret from runtime configuration

SeaweedFS can later replace Garage through the same S3-compatible boundary.

## Testable Properties

- `append_post` writes exactly one JSON line per `PostResult`.
- `write_failure` writes exactly one JSON line per failure and omits forbidden context.
- Resume creates a different `run_id` path under the same `job_id`.
- JSONL records preserve nested comments/content/media structures.
- Local checkpoint save can load the same checkpoint back.
- Local checkpoint `load_latest()` returns the newest updated checkpoint.
- Media save never performs HTTP requests.
- S3 object keys match local relative paths.
