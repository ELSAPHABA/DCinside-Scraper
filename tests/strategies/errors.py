from __future__ import annotations

from hypothesis import strategies as st

from dcinside_scraper.models.error import ErrorResult
from tests.strategies.content_blocks import safe_text


def error_results():
    return st.builds(
        ErrorResult,
        code=st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=50),
        message=safe_text.filter(lambda value: bool(value.strip())),
        details=st.dictionaries(
            keys=st.sampled_from(["field_path", "reason", "stage"]),
            values=safe_text,
            max_size=3,
        ),
        retryable=st.booleans(),
        safe_to_log=st.booleans(),
    )

