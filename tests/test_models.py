from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from dcinside_scraper.core.errors import CaptchaDetectedError, ErrorMapper
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.comment import AuthorInfo
from dcinside_scraper.models.enums import CheckpointStatus, JobType, NicknameType, StopReason
from dcinside_scraper.models.job import JobConfig, RangeFilter
from dcinside_scraper.models.post import PostResult, RepostInfo


def minimal_job(source: dict, job_type: JobType | str | None = None) -> JobConfig:
    return JobConfig(
        job_id="job-1",
        job_type=job_type or source["type"],
        source=source,
    )


@pytest.mark.parametrize(
    "source",
    [
        {"type": "direct_post", "urls": ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"]},
        {
            "type": "gallery_search",
            "gallery_type": "minor",
            "gallery_id": "singlebungle1472",
            "s_type": "search_subject_memo",
            "keyword": "test",
        },
        {"type": "integrated_search", "keyword": "test"},
        {
            "type": "deep_search",
            "keyword": "test",
            "range_filter": {"date_from": "2026-01-01"},
        },
        {
            "type": "no_keyword_range",
            "gallery_type": "minor",
            "gallery_id": "singlebungle1472",
            "range_filter": {"min_post_number": 1},
        },
        {
            "type": "realtime_keyword",
            "keyword": "test",
            "termination": {"duration_seconds": 60},
        },
        {
            "type": "realtime_all",
            "gallery_type": "minor",
            "gallery_id": "singlebungle1472",
            "termination": {"end_at": "2026-01-01T00:00:00Z"},
        },
    ],
)
def test_valid_minimal_job_config_per_source(source: dict) -> None:
    assert minimal_job(source).source.type == source["type"]


def test_job_type_must_match_source_type() -> None:
    with pytest.raises(ValidationError):
        minimal_job(
            {
                "type": "gallery_search",
                "gallery_type": "minor",
                "gallery_id": "singlebungle1472",
                "s_type": "search_subject_memo",
                "keyword": "test",
            },
            job_type=JobType.DIRECT_POST,
        )


@pytest.mark.parametrize(
    "source",
    [
        {
            "type": "realtime_keyword",
            "keyword": "test",
            "termination": {"duration_seconds": 60, "end_at": "2026-01-01T00:00:00Z"},
        },
        {"type": "deep_search", "keyword": "test", "range_filter": {}},
        {
            "type": "no_keyword_range",
            "gallery_type": "minor",
            "gallery_id": "singlebungle1472",
            "range_filter": {},
        },
    ],
)
def test_invalid_source_constraints(source: dict) -> None:
    with pytest.raises(ValidationError):
        minimal_job(source)


def test_range_filter_order_validation() -> None:
    with pytest.raises(ValidationError):
        RangeFilter(min_post_number=10, max_post_number=1)


def test_checkpoint_stopped_requires_reason() -> None:
    with pytest.raises(ValidationError):
        Checkpoint(
            job_id="job-1",
            status=CheckpointStatus.STOPPED,
            job_config_snapshot=minimal_job(
                {"type": "direct_post", "urls": ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"]}
            ),
        )


def test_checkpoint_running_rejects_reason() -> None:
    with pytest.raises(ValidationError):
        Checkpoint(
            job_id="job-1",
            status=CheckpointStatus.RUNNING,
            reason=StopReason.ERROR,
            job_config_snapshot=minimal_job(
                {"type": "direct_post", "urls": ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"]}
            ),
        )


def test_repost_consistency_and_title_normalization() -> None:
    author = AuthorInfo(name="writer", nickname_type=NicknameType.FIXED)
    post = PostResult(
        gallery_id="stockus",
        post_id="17025357",
        is_repost=True,
        repost=RepostInfo(gallery_id="origin", post_id="1", author=author),
        title="(펌) original title",
        author=author,
    )
    assert post.title == "original title"


def test_non_repost_rejects_repost_payload() -> None:
    author = AuthorInfo(name="writer")
    with pytest.raises(ValidationError):
        PostResult(
            gallery_id="stockus",
            post_id="17025357",
            is_repost=False,
            repost=RepostInfo(gallery_id="origin", post_id="1", author=author),
            title="title",
            author=author,
        )


def test_error_redaction_drops_secret_details() -> None:
    error = CaptchaDetectedError(
        "captcha detected",
        details={
            "password": "secret",
            "field_path": "proxy.password",
            "reason": "password=secret",
            "stage": "http",
        },
    )
    result = ErrorMapper.map(error)
    assert "password" not in result.details
    assert result.details["reason"] == "[REDACTED]"
    assert result.retryable is True


def test_import_has_no_runtime_side_effects(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
    code = "import dcinside_scraper, pathlib; print(pathlib.Path('.env').exists(), pathlib.Path('user-agents.txt').exists())"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "False False"

