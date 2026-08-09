from __future__ import annotations

import asyncio
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dcinside_scraper.adapters import cli
from dcinside_scraper.core.errors import ValidationFailure
from dcinside_scraper.models.enums import JobReportStatus
from dcinside_scraper.models.report import JobReport


class FakeRunner:
    def __init__(self, status: JobReportStatus = JobReportStatus.COMPLETED) -> None:
        self.status = status
        self.config = None
        self.request = None
        self.stop_requested = False

    def request_stop(self) -> None:
        self.stop_requested = True

    async def run(self, config):
        self.config = config
        return JobReport(job_id=config.job_id, status=self.status, success_count=1)

    async def resume(self, request):
        self.request = request
        return JobReport(job_id=request.job_id or "latest", status=self.status, success_count=1)


def test_parser_accepts_confirmed_subcommands() -> None:
    parser = cli.build_parser()

    assert parser.parse_args(["wizard"]).subcommand == "wizard"
    assert parser.parse_args(["resume"]).subcommand == "resume"
    assert parser.parse_args(["retry-failures", "--failure-file", "failures.jsonl"]).subcommand == "retry-failures"
    assert parser.parse_args(["import-user-agents", "agents.txt"]).subcommand == "import-user-agents"
    assert parser.parse_args(["configure-proxy", "--host", "proxy.local:8080"]).subcommand == "configure-proxy"
    args = parser.parse_args(["run", "--source", "direct-post", "--url", "https://gall.dcinside.com/board/view/?id=dcbest&no=1"])
    assert args.subcommand == "run"


def test_build_job_config_maps_gallery_search() -> None:
    config = cli.build_job_config(
        {
            "subcommand": "run",
            "source": "gallery-search",
            "job_id": "job-1",
            "gallery_type": "minor",
            "gallery_id": "singlebungle1472",
            "keyword": "싱글벙글",
            "output_path": "out",
            "post_worker_count": 3,
        },
        env={},
    )

    assert config.source.type == "gallery_search"
    assert config.source.gallery_id == "singlebungle1472"
    assert config.storage_config.base_output_path == "out"
    assert config.worker_config.post_worker_count == 3


def test_build_resume_request_allows_missing_job_id() -> None:
    assert cli.build_resume_request({"subcommand": "resume"}).job_id is None


def test_realtime_env_validation() -> None:
    config = cli.build_job_config(
        {"subcommand": "run"},
        env={
            "DCINSIDE_REALTIME_ENABLED": "true",
            "DCINSIDE_REALTIME_MODE": "keyword",
            "DCINSIDE_REALTIME_KEYWORD": "싱글벙글",
            "DCINSIDE_REALTIME_DURATION_SECONDS": "60",
        },
    )
    assert config.source.type == "realtime_keyword"

    with pytest.raises(ValidationFailure):
        cli.build_job_config(
            {"subcommand": "run"},
            env={
                "DCINSIDE_REALTIME_ENABLED": "true",
                "DCINSIDE_REALTIME_MODE": "keyword",
                "DCINSIDE_REALTIME_KEYWORD": "싱글벙글",
                "DCINSIDE_REALTIME_DURATION_SECONDS": "60",
                "DCINSIDE_REALTIME_END_AT": "2026-01-01T00:00:00Z",
            },
        )


def test_import_user_agents_rejects_blank_without_overwriting(tmp_path: Path) -> None:
    source = tmp_path / "blank.txt"
    destination = tmp_path / "user-agents.txt"
    source.write_text("\n\n", encoding="utf-8")
    destination.write_text("Mozilla/5.0\n", encoding="utf-8")

    with pytest.raises(ValidationFailure):
        cli.import_user_agents(source, destination)

    assert destination.read_text(encoding="utf-8") == "Mozilla/5.0\n"


def test_update_proxy_env_preserves_unrelated_lines(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("KEEP=1\nDCINSIDE_PROXY_HOST=old\n", encoding="utf-8")

    cli.update_proxy_env(
        env_file,
        {
            "DCINSIDE_PROXY_HOST": "proxy.local:8080",
            "DCINSIDE_PROXY_ID": "user",
            "DCINSIDE_PROXY_PW": "secret",
        },
    )

    text = env_file.read_text(encoding="utf-8")
    assert "KEEP=1" in text
    assert "DCINSIDE_PROXY_HOST=proxy.local:8080" in text
    assert "DCINSIDE_PROXY_ID=user" in text
    assert "DCINSIDE_PROXY_PW=secret" in text


def test_run_command_uses_injected_runner_without_network() -> None:
    output = io.StringIO()
    runner = FakeRunner()

    code = asyncio.run(
        cli.run_scrape_command_async(
            {
                "subcommand": "run",
                "source": "direct-post",
                "job_id": "job-1",
                "urls": ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"],
            },
            env={},
            runner=runner,
            output=output,
        )
    )

    assert code == cli.EXIT_SUCCESS
    assert runner.config.job_id == "job-1"
    assert "resume:" in output.getvalue()


def test_wizard_maps_direct_post_to_run_command() -> None:
    session = cli.WizardSession(
        input_stream=io.StringIO("1\n1\njob-1\n\nhttps://gall.dcinside.com/board/view/?id=dcbest&no=1\n"),
        output_stream=io.StringIO(),
    )

    command = session.collect_command()

    assert command["subcommand"] == "run"
    assert command["source"] == "direct_post"
    assert command["job_id"] == "job-1"
    assert command["urls"] == ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"]


def test_interrupt_controller_first_stop_second_interrupt() -> None:
    runner = FakeRunner()
    output = io.StringIO()

    with pytest.raises(KeyboardInterrupt):
        with cli.InterruptController(runner, output=output) as controller:
            controller._handle(2, None)
            controller._handle(2, None)

    assert runner.stop_requested is True
    assert "Graceful stop requested" in output.getvalue()


def test_print_error_uses_safe_summary() -> None:
    output = io.StringIO()
    cli.print_error(
        ValidationFailure("failed", details={"password": "secret", "reason": "safe"}),
        output=output,
        include_traceback=True,
    )

    text = output.getvalue()
    assert "validation_error" in text
    assert "secret" not in text
    assert "Traceback" in text


def test_cli_import_has_no_runtime_side_effects(tmp_path: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(Path.cwd() / "src")}
    code = "import dcinside_scraper.adapters.cli, pathlib; print(pathlib.Path('.env').exists(), pathlib.Path('user-agents.txt').exists())"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "False False"


def test_root_main_help_runs_from_repo() -> None:
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        check=True,
    )

    assert "dcinside-scraper" in result.stdout
