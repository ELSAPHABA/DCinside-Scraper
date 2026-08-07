from __future__ import annotations

from hypothesis import strategies as st

from tests.strategies.job_configs import safe_ids

unsafe_segments = st.text(min_size=0, max_size=80)
run_ids = safe_ids
