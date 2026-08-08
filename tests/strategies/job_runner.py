from __future__ import annotations

from hypothesis import strategies as st

from dcinside_scraper.models.enums import CheckpointStatus, StopReason
from dcinside_scraper.models.job import PostCandidate, PostKey
from tests.strategies.job_configs import safe_ids


@st.composite
def post_candidates(draw):
    gallery_id = draw(safe_ids)
    post_id = draw(safe_ids)
    post_number = draw(st.integers(min_value=1, max_value=1_000_000))
    return PostCandidate(
        url=f"https://gall.dcinside.com/board/view/?id={gallery_id}&no={post_number}",
        gallery_id=gallery_id,
        post_id=post_id,
        post_number=post_number,
    )


@st.composite
def completed_key_sets(draw):
    candidates = draw(st.lists(post_candidates(), min_size=0, max_size=20, unique_by=lambda item: (item.gallery_id, item.post_id)))
    return [PostKey(board_id=candidate.gallery_id, post_id=candidate.post_id) for candidate in candidates]


checkpoint_statuses = st.sampled_from(list(CheckpointStatus))
stop_reasons = st.sampled_from(list(StopReason))
