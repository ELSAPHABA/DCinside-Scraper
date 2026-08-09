from __future__ import annotations

import asyncio
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dcinside_scraper.adapters import cli
from dcinside_scraper.core.errors import ValidationFailure
from dcinside_scraper.models.enums import JobReportStatus
from dcinside_scraper.models.report import JobReport
from dcinside_scraper.retry import ParserFailureRetryRequest, ParserFailureRetryService, select_parser_failure_retries


class FakeRunner:
    def __init__(self) -> None:
        self.config = None

    async def run(self, config):
        self.config = config
        return JobReport(
            job_id=config.job_id,
            status=JobReportStatus.COMPLETED,
            success_count=len(config.source.urls),
            metadata=config.metadata,
        )


def _line(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False) + "\n"


def test_selector_filters_invalid_ineligible_and_dedupes_last_url() -> None:
    lines = [
        "{bad json}\n",
        _line(
            {
                "gallery_id": "g",
                "post_id": "1",
                "url": "https://gall.dcinside.com/board/view/?id=g&no=1",
                "reason": "post title missing",
                "stage": "post",
                "retryable": True,
            }
        ),
        _line(
            {
                "gallery_id": "g",
                "post_id": "1",
                "url": "https://gall.dcinside.com/board/view/?id=g&no=2",
                "reason": "content parse failure",
                "stage": "post",
                "retryable": True,
            }
        ),
        _line(
            {
                "gallery_id": "g",
                "post_id": "3",
                "url": "https://gall.dcinside.com/board/view/?id=g&no=3",
                "reason": "network",
                "stage": "post",
                "retryable": True,
            }
        ),
    ]

    candidates, summary = select_parser_failure_retries({"failures.jsonl": lines})

    assert [candidate.url for candidate in candidates] == ["https://gall.dcinside.com/board/view/?id=g&no=2"]
    assert summary.initial_failure_count == 4
    assert summary.invalid_failure_record_count == 1
    assert summary.ineligible_failure_count == 1
    assert summary.deduped_failure_count == 1
    assert summary.selected_retry_count == 1


def test_service_skips_existing_posts_and_adds_retry_metadata(tmp_path: Path) -> None:
    failures = tmp_path / "failures.jsonl"
    failures.write_text(
        _line(
            {
                "gallery_id": "g",
                "post_id": "1",
                "url": "https://gall.dcinside.com/board/view/?id=g&no=1",
                "reason": "post title missing",
                "stage": "post",
            }
        )
        + _line(
            {
                "gallery_id": "g",
                "post_id": "2",
                "url": "https://gall.dcinside.com/board/view/?id=g&no=2",
                "reason": "metadata parse failure",
                "stage": "post",
            }
        ),
        encoding="utf-8",
    )
    posts = tmp_path / "posts.jsonl"
    posts.write_text(_line({"site_id": "dcinside", "gallery_id": "g", "post_id": "1"}), encoding="utf-8")
    captured = {}

    async def execute(config):
        captured["config"] = config
        return JobReport(job_id=config.job_id, status=JobReportStatus.COMPLETED, success_count=1, metadata=config.metadata)

    report = asyncio.run(
        ParserFailureRetryService().retry(
            ParserFailureRetryRequest(failure_refs=(str(failures),), existing_post_refs=(str(posts),), job_id="retry-1"),
            execute_job=execute,
        )
    )

    assert captured["config"].source.urls == ["https://gall.dcinside.com/board/view/?id=g&no=2"]
    metadata = report.metadata["parser_failure_retry"]
    assert metadata["selected_retry_count"] == 1
    assert metadata["skipped_existing_count"] == 1
    assert metadata["success_count"] == 1
    assert metadata["remaining_failure_count"] == 0


def test_existing_posts_root_is_local_only_convenience(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    nested = root / "job" / "run"
    nested.mkdir(parents=True)
    (nested / "posts.jsonl").write_text(_line({"gallery_id": "g", "post_id": "1"}), encoding="utf-8")

    index = ParserFailureRetryService().build_existing_post_index(roots=(str(root),))

    assert ("dcinside", "g", "1") in index.keys


def test_cli_retry_failures_uses_injected_runner(tmp_path: Path) -> None:
    failures = tmp_path / "failures.jsonl"
    failures.write_text(
        _line(
            {
                "gallery_id": "g",
                "post_id": "1",
                "url": "https://gall.dcinside.com/board/view/?id=g&no=1",
                "reason": "post identity missing",
                "stage": "post",
            }
        ),
        encoding="utf-8",
    )
    runner = FakeRunner()
    output = io.StringIO()

    code = asyncio.run(
        cli.retry_failures_command_async(
            {"subcommand": "retry-failures", "failure_files": [str(failures)], "job_id": "retry-1"},
            runner=runner,
            output=output,
        )
    )

    assert code == cli.EXIT_SUCCESS
    assert runner.config.source.type == "direct_post"
    assert "retry selected=1" in output.getvalue()


def test_retry_restore_sources_are_mutually_exclusive() -> None:
    with pytest.raises(ValidationFailure):
        cli.build_parser_failure_retry_request(
            {
                "subcommand": "retry-failures",
                "failure_files": ["failures.jsonl"],
                "from_report": "report.json",
                "from_checkpoint": "job-1",
            }
        )


def test_retry_modules_import_without_runtime_side_effects(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
    code = "import dcinside_scraper.retry, pathlib; print(pathlib.Path('.env').exists(), pathlib.Path('Checkpoint.json').exists())"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "False False"
