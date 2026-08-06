from __future__ import annotations

from hypothesis import given, settings

from dcinside_scraper.models.enums import IntegratedSearchSort
from dcinside_scraper.search import CandidateDeduper, IntegratedSearchUrlBuilder, RangeFilterEvaluator, SafeCollectorEventBuilder
from tests.strategies.search import bounded_range_filters, keywords, pages, post_candidates


@given(keywords, pages)
@settings(max_examples=30)
def test_integrated_url_never_exceeds_page_120(keyword, page) -> None:
    url = IntegratedSearchUrlBuilder.build(keyword=keyword, page=page, sort_mode=IntegratedSearchSort.LATEST)

    assert "/p/121/" not in url
    assert "/p/120/" in url or page == 1 or page < 120


@given(post_candidates())
@settings(max_examples=30)
def test_candidate_deduper_is_idempotent(candidate) -> None:
    deduper = CandidateDeduper()

    assert deduper.add(candidate) is True
    assert deduper.add(candidate) is False


@given(post_candidates(), bounded_range_filters())
@settings(max_examples=30)
def test_range_filter_decision_is_stable(candidate, range_filter) -> None:
    first = RangeFilterEvaluator.evaluate(candidate, range_filter)
    second = RangeFilterEvaluator.evaluate(candidate, range_filter)

    assert first == second


@given(keywords)
@settings(max_examples=30)
def test_safe_collector_event_redacts_query_and_secret_fields(secret) -> None:
    event = SafeCollectorEventBuilder.build(
        "event",
        url=f"https://gall.dcinside.com/board/lists/?id=x&ci_t={secret}",
        ci_t=secret,
        raw_html=secret,
    )

    assert event["url"] == "https://gall.dcinside.com/board/lists/"
    assert "ci_t" not in event
    assert "raw_html" not in event
