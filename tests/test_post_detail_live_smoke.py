from __future__ import annotations

import os

import pytest

from dcinside_scraper.models.job import PostRequest, ScrapeOptions

pytestmark = pytest.mark.live


@pytest.mark.skipif(os.getenv("DCINSIDE_LIVE_SMOKE_ENABLED") != "true", reason="live smoke disabled")
def test_post_detail_live_smoke_is_opt_in_only() -> None:
    request = PostRequest(
        url=os.environ.get("DCINSIDE_LIVE_POST_URL", "https://gall.dcinside.com/board/view/?id=dcbest&no=442937"),
        scrape_options=ScrapeOptions(include_comments=False),
    )

    assert request.url.startswith("https://gall.dcinside.com/")
