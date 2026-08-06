from __future__ import annotations

from hypothesis import strategies as st

from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.enums import CheckpointStatus, StopReason
from tests.strategies.job_configs import job_configs, safe_ids


@st.composite
def checkpoints(draw):
    status = draw(st.sampled_from(list(CheckpointStatus)))
    reason = draw(st.sampled_from(list(StopReason))) if status == CheckpointStatus.STOPPED else None
    return Checkpoint(
        job_id=draw(safe_ids),
        status=status,
        reason=reason,
        job_config_snapshot=draw(job_configs()),
    )

