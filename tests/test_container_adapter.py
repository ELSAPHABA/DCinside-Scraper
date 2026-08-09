from __future__ import annotations

import anyio
import io

from dcinside_scraper.adapters.container import (
    EXIT_SUCCESS,
    EXIT_VALIDATION_ERROR,
    ContainerEnvConfig,
    run_container_async,
)
from dcinside_scraper.models.enums import CheckpointMode, JobReportStatus, OutputMode
from dcinside_scraper.models.report import JobReport


BASE_ENV = {
    "DATABASE_URL": "postgresql://user:secret@db/app",
    "S3_ENDPOINT_URL": "http://garage:3900",
    "S3_BUCKET": "dcinside",
    "S3_ACCESS_KEY_ID": "access",
    "S3_SECRET_ACCESS_KEY": "secret",
}


class FakeRunner:
    def __init__(self) -> None:
        self.config = None
        self.request = None
        self.stop_requested = False

    def request_stop(self) -> None:
        self.stop_requested = True

    async def run(self, config):
        self.config = config
        return JobReport(job_id=config.job_id, status=JobReportStatus.COMPLETED, success_count=1)

    async def resume(self, request):
        self.request = request
        return JobReport(job_id=request.job_id or "latest", status=JobReportStatus.COMPLETED, success_count=1)


async def call_container(argv, env, runner, output=None, error_output=None):
    return await run_container_async(argv, env=env, runner=runner, output=output, error_output=error_output)


def test_container_env_config_requires_storage_and_redacts_repr() -> None:
    config = ContainerEnvConfig.from_env(BASE_ENV)

    assert config.storage_config().output_mode == OutputMode.S3
    assert config.storage_config().checkpoint_mode == CheckpointMode.POSTGRES
    assert "secret" not in repr(config)


def test_container_missing_required_env_returns_validation_error() -> None:
    error_output = io.StringIO()

    code = anyio.run(
        call_container,
        ["run", "--source", "direct-post", "--url", "https://gall.dcinside.com/board/view/?id=dcbest&no=1"],
        {},
        FakeRunner(),
        None,
        error_output,
    )

    assert code == EXIT_VALIDATION_ERROR
    assert "secret" not in error_output.getvalue()
    assert "validation_error" in error_output.getvalue()


def test_container_run_uses_s3_and_postgres_storage_modes_without_network() -> None:
    output = io.StringIO()
    runner = FakeRunner()

    code = anyio.run(
        call_container,
        ["run", "--source", "direct-post", "--job-id", "job-1", "--url", "https://gall.dcinside.com/board/view/?id=dcbest&no=1"],
        BASE_ENV,
        runner,
        output,
    )

    assert code == EXIT_SUCCESS
    assert runner.config.storage_config.output_mode == OutputMode.S3
    assert runner.config.storage_config.checkpoint_mode == CheckpointMode.POSTGRES
    assert '"ok": true' in output.getvalue()


def test_container_resume_uses_env_job_id_without_cli_args() -> None:
    runner = FakeRunner()

    code = anyio.run(call_container, [], {**BASE_ENV, "RESUME": "true", "JOB_ID": "job-1"}, runner)

    assert code == EXIT_SUCCESS
    assert runner.request.job_id == "job-1"
