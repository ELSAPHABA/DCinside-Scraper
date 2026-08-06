from __future__ import annotations

from hypothesis import given, settings

from dcinside_scraper.post_detail import make_safe_detail_failure, parse_count, strip_repost_marker, validate_block_orders
from tests.strategies.post_detail import count_strings, failure_reasons, orders, titles


@given(titles)
@settings(max_examples=30)
def test_strip_repost_marker_is_idempotent(title: str) -> None:
    marked = f"(펌) {title}"

    assert strip_repost_marker(strip_repost_marker(marked)) == title


@given(count_strings)
@settings(max_examples=30)
def test_parse_count_is_stable(value: str) -> None:
    first = parse_count(value)
    second = parse_count(value)

    assert first == second
    assert first is None or first >= 0


@given(orders)
@settings(max_examples=30)
def test_validate_block_orders_accepts_only_dense_orders(values: list[int]) -> None:
    expected = values == list(range(len(values)))

    assert validate_block_orders(values) is expected


@given(failure_reasons)
@settings(max_examples=30)
def test_safe_detail_failure_drops_unapproved_fields(reason: str) -> None:
    failure = make_safe_detail_failure(stage="comments", reason=reason, raw_html="<html>", cookie="secret")

    assert failure["reason"] == reason
    assert "raw_html" not in failure
    assert "cookie" not in failure
