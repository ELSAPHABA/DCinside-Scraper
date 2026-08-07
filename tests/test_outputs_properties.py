from __future__ import annotations

import json

from hypothesis import given, settings

from dcinside_scraper.models.report import FailureRecord
from dcinside_scraper.outputs import (
    OutputRunLayout,
    SafeFailureRecordBuilder,
    sanitize_path_segment,
    to_json_line,
)
from tests.strategies.outputs import run_ids, unsafe_segments
from tests.strategies.post_results import post_results


@given(unsafe_segments)
@settings(max_examples=50)
def test_sanitize_path_segment_produces_single_safe_segment(value: str) -> None:
    segment = sanitize_path_segment(value, "fallback")
    assert segment
    assert "/" not in segment
    assert "\\" not in segment
    assert segment not in {".", ".."}


@given(run_ids, run_ids)
@settings(max_examples=30)
def test_output_layout_keys_are_posix_relative(job_id: str, run_id: str) -> None:
    layout = OutputRunLayout.create(job_id=job_id, run_id=run_id)
    assert layout.posts_key.startswith("outputs/")
    assert "\\" not in layout.posts_key
    assert ".." not in layout.posts_key.split("/")


@given(post_results())
@settings(max_examples=30)
def test_jsonl_line_round_trips_post_result(post) -> None:
    loaded = json.loads(to_json_line(post))
    assert loaded["schema_version"] == "dcinside.post.v1"
    assert loaded["gallery_id"] == post.gallery_id


@given(unsafe_segments)
@settings(max_examples=30)
def test_failure_redaction_is_idempotent(secret: str) -> None:
    failure = FailureRecord(
        reason="failed",
        stage="stage",
        metadata={
            "proxy_host": "127.0.0.1:8080",
            "user_agent": "ua",
            "proxy_password": secret,
            "raw_html": secret,
            "cookie": secret,
        },
    )
    once = SafeFailureRecordBuilder.sanitize(failure)
    twice = SafeFailureRecordBuilder.sanitize(once)
    assert twice.model_dump(mode="json") == once.model_dump(mode="json")
    assert once.metadata == {"proxy_host": "127.0.0.1:8080", "user_agent": "ua"}
