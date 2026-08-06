from __future__ import annotations

from hypothesis import strategies as st

titles = (
    st.text(min_size=1, max_size=50)
    .map(str.strip)
    .filter(lambda value: bool(value) and not value.startswith("(펌)"))
)
counts = st.integers(min_value=0, max_value=1_000_000)
count_strings = counts.map(lambda value: f"조회 {value:,}")
orders = st.lists(st.integers(min_value=0, max_value=20), min_size=0, max_size=20)
failure_reasons = st.text(min_size=1, max_size=40)
