from __future__ import annotations

import anyio

from dcinside_scraper.adapters.mcp import McpToolHandlers
from dcinside_scraper.adapters.safe_errors import safe_error_payload
from dcinside_scraper.core.errors import ValidationFailure
from dcinside_scraper.models.enums import JobReportStatus
from dcinside_scraper.models.report import JobReport


class FakeRunner:
    async def resume(self, request):
        return JobReport(job_id=request.job_id or "latest", status=JobReportStatus.COMPLETED, success_count=1)


async def call_resume(payload):
    return await McpToolHandlers().resume_job(payload, runner=FakeRunner())


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


def test_safe_error_payload_redacts_secret_details() -> None:
    payload = safe_error_payload(
        ValidationFailure("failed", details={"reason": "safe", "password": "secret"}),
        stage="mcp",
    )

    assert payload["code"] == "validation_error"
    assert payload["details"] == {"reason": "safe", "stage": "mcp"}
