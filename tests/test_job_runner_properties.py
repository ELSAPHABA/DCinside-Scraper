from __future__ import annotations

from hypothesis import given, settings

from dcinside_scraper.core.errors import CaptchaDetectedError, ParseFailureError
from dcinside_scraper.models.enums import CheckpointStatus, JobReportStatus, StopReason
from dcinside_scraper.runner import (
    candidate_post_key,
    post_key_identity,
    report_status_for_checkpoint,
    should_skip_candidate,
    stop_reason_for_error,
)
from tests.strategies.job_runner import checkpoint_statuses, completed_key_sets, post_candidates


@given(post_candidates())
@settings(max_examples=30)
def test_candidate_key_identity_matches_candidate(candidate) -> None:
    key = candidate_post_key(candidate)
    assert post_key_identity(key) == ("dcinside", candidate.gallery_id, candidate.post_id)


@given(post_candidates(), completed_key_sets())
@settings(max_examples=30)
def test_completed_key_skip_matches_identity(candidate, completed) -> None:
    expected = post_key_identity(candidate_post_key(candidate)) in {post_key_identity(key) for key in completed}
    assert should_skip_candidate(candidate, completed) is expected


@given(checkpoint_statuses)
@settings(max_examples=20)
def test_report_status_mapping_is_total(status) -> None:
    mapped = report_status_for_checkpoint(status)
    assert isinstance(mapped, JobReportStatus)
    if status == CheckpointStatus.COMPLETED:
        assert mapped == JobReportStatus.COMPLETED
    elif status == CheckpointStatus.STOPPED:
        assert mapped == JobReportStatus.STOPPED


def test_stop_reason_mapping_distinguishes_captcha() -> None:
    assert stop_reason_for_error(CaptchaDetectedError("captcha")) == StopReason.CAPTCHA
    assert stop_reason_for_error(ParseFailureError("parse")) == StopReason.ERROR
