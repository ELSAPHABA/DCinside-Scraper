from __future__ import annotations

import json

from hypothesis import given, settings
from hypothesis import strategies as st

from dcinside_scraper.retry import select_parser_failure_retries


def _failure_line(gallery_id: str, post_id: str, reason: str = "post title missing") -> str:
    return json.dumps(
        {
            "gallery_id": gallery_id,
            "post_id": post_id,
            "url": f"https://gall.dcinside.com/board/view/?id={gallery_id}&no={post_id}",
            "reason": reason,
            "stage": "post",
        }
    )


safe_ids = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=1, max_size=8)


@given(st.lists(st.tuples(safe_ids, safe_ids), min_size=1, max_size=30))
@settings(max_examples=30)
def test_dedupe_never_selects_more_than_unique_keys(pairs: list[tuple[str, str]]) -> None:
    lines = [_failure_line(gallery_id, post_id) for gallery_id, post_id in pairs]
    candidates, summary = select_parser_failure_retries({"failures.jsonl": lines})

    assert len(candidates) <= len(set(pairs))
    assert summary.selected_retry_count == len(candidates)


@given(st.lists(st.tuples(safe_ids, safe_ids), min_size=1, max_size=30))
@settings(max_examples=30)
def test_existing_success_skip_never_increases_selection(pairs: list[tuple[str, str]]) -> None:
    lines = [_failure_line(gallery_id, post_id) for gallery_id, post_id in pairs]
    candidates_without_skip, _ = select_parser_failure_retries({"failures.jsonl": lines})
    existing = {candidate.key for candidate in candidates_without_skip[: len(candidates_without_skip) // 2]}

    candidates_with_skip, _ = select_parser_failure_retries({"failures.jsonl": lines}, existing_keys=existing)

    assert len(candidates_with_skip) <= len(candidates_without_skip)
