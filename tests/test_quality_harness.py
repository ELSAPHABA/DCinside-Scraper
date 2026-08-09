from __future__ import annotations

import json
from pathlib import Path

import pytest

QUALITY_DIR = Path(__file__).parent / "fixtures" / "quality"


def test_quality_post_jsonl_fixture_has_expected_shape() -> None:
    posts = [json.loads(line) for line in (QUALITY_DIR / "posts.jsonl").read_text(encoding="utf-8").splitlines()]

    assert posts
    for post in posts:
        assert post["schema_version"] == "dcinside.post.v1"
        assert post["site_id"] == "dcinside"
        assert post["gallery_id"]
        assert post["post_id"]
        assert "(펌)" not in post["title"]
        if post["is_repost"]:
            assert post["repost"]["gallery_id"]
            assert "comment_count" not in post["repost"]


def test_quality_failure_and_report_fixtures_are_safe() -> None:
    failures = [json.loads(line) for line in (QUALITY_DIR / "failures.jsonl").read_text(encoding="utf-8").splitlines()]
    report = json.loads((QUALITY_DIR / "report.json").read_text(encoding="utf-8"))

    forbidden = {"password", "cookie", "token", "raw_html", "raw_headers", "raw_env"}
    assert report["success_count"] == 1
    assert report["failure_count"] == len(failures)
    for failure in failures:
        assert forbidden.isdisjoint(failure.get("metadata", {}))


def test_quality_post_jsonl_can_be_read_by_polars_when_installed() -> None:
    pl = pytest.importorskip("polars")

    frame = pl.read_ndjson(QUALITY_DIR / "posts.jsonl")

    assert frame.height == 1
    assert "title" in frame.columns
