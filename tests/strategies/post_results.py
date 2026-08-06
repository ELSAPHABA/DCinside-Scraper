from __future__ import annotations

from hypothesis import strategies as st

from dcinside_scraper.models.comment import AuthorInfo
from dcinside_scraper.models.post import PostResult, RepostInfo
from tests.strategies.content_blocks import content_block_lists, safe_text
from tests.strategies.job_configs import safe_ids


@st.composite
def post_results(draw):
    author = AuthorInfo(name=draw(safe_text))
    is_repost = draw(st.booleans())
    repost = None
    if is_repost:
        repost = RepostInfo(gallery_id=draw(safe_ids), post_id=draw(safe_ids), author=author)
    return PostResult(
        gallery_id=draw(safe_ids),
        post_id=draw(safe_ids),
        is_repost=is_repost,
        repost=repost,
        title=draw(safe_text.filter(lambda value: bool(value.strip()))),
        author=author,
        content=draw(content_block_lists()),
    )

