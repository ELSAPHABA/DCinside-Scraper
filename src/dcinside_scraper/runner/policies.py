"""Pure runner policies."""

from dcinside_scraper.runner.core import (
    RunnerEventBuilder,
    candidate_post_key,
    post_key_identity,
    report_status_for_checkpoint,
    should_skip_candidate,
    stop_reason_for_error,
)

__all__ = [
    "RunnerEventBuilder",
    "candidate_post_key",
    "post_key_identity",
    "report_status_for_checkpoint",
    "should_skip_candidate",
    "stop_reason_for_error",
]
