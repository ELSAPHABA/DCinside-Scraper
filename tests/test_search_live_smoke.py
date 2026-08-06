from __future__ import annotations

import asyncio
import os

import pytest

from dcinside_scraper.http import HttpClient, HttpRuntimeConfig, RetryPolicy
from dcinside_scraper.models.enums import GalleryType
from dcinside_scraper.models.job import GallerySearchRequest
from dcinside_scraper.search import GallerySearchCollector

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.getenv("DCINSIDE_LIVE_SMOKE_ENABLED") != "true", reason="live smoke is disabled by default"),
]


def test_gallery_search_live_smoke_fetches_one_page() -> None:
    async def scenario() -> None:
        config = HttpRuntimeConfig(request_interval_seconds=0, retry_policy=RetryPolicy(max_attempts=1))
        async with HttpClient(config) as client:
            page = await GallerySearchCollector(client).collect_page(
                GallerySearchRequest(
                    gallery_type=GalleryType.MINOR,
                    gallery_id="singlebungle1472",
                    s_type="search_subject_memo",
                    keyword="싱글벙글",
                )
            )
            assert page.page == 1

    asyncio.run(scenario())
