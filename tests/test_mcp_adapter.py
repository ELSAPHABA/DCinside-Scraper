from __future__ import annotations

import anyio

from dcinside_scraper.adapters.mcp import McpToolHandlers
from dcinside_scraper.adapters.safe_errors import safe_error_payload
from dcinside_scraper.core.errors import ValidationFailure
from dcinside_scraper.models.enums import JobReportStatus, JobType
from dcinside_scraper.models.job import JobConfig
from dcinside_scraper.models.report import JobReport


class FakeRunner:
    async def resume(self, request):
        return JobReport(job_id=request.job_id or "latest", status=JobReportStatus.COMPLETED, success_count=1)


class FakeRetryService:
    def __init__(self) -> None:
        self.request = None

    async def retry(self, request, *, execute_job):
        self.request = request
        return await execute_job(
            JobConfig(
                job_id=request.job_id or "retry",
                job_type=JobType.DIRECT_POST,
                source={"type": "direct_post", "urls": ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"]},
            )
        )


async def call_resume(payload):
    return await McpToolHandlers().resume_job(payload, runner=FakeRunner())


async def execute_retry(config):
    return JobReport(job_id=config.job_id, status=JobReportStatus.COMPLETED, success_count=1)


async def call_retry(payload, service):
    return await McpToolHandlers().retry_parser_failures(payload, retry_service=service, execute_job=execute_retry)


def test_mcp_resume_job_returns_json_serializable_payload() -> None:
    result = anyio.run(call_resume, {"job_id": "job-1"})

    assert result["ok"] is True
    assert result["data"]["job_id"] == "job-1"
    assert result["data"]["status"] == "completed"


def test_mcp_validation_error_is_safe() -> None:
    result = anyio.run(call_resume, {"unexpected": "value"})

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"
    assert "Traceback" not in str(result["error"])
    assert "secret" not in str(result["error"])


def test_mcp_retry_parser_failures_returns_json_serializable_payload() -> None:
    service = FakeRetryService()

    result = anyio.run(call_retry, {"failure_ref": "failures.jsonl", "job_id": "retry-1"}, service)

    assert result["ok"] is True
    assert result["data"]["job_id"] == "retry-1"
    assert service.request.failure_refs == ("failures.jsonl",)


def test_safe_error_payload_redacts_secret_details() -> None:
    payload = safe_error_payload(
        ValidationFailure("failed", details={"reason": "safe", "password": "secret"}),
        stage="mcp",
    )

    assert payload["code"] == "validation_error"
    assert payload["details"] == {"reason": "safe", "stage": "mcp"}
