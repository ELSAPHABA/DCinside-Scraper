from __future__ import annotations

from datetime import date

from hypothesis import strategies as st

from dcinside_scraper.models.job import PostCandidate, RangeFilter

keywords = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="/?#"),
    min_size=1,
    max_size=20,
)

pages = st.integers(min_value=1, max_value=300)
gallery_ids = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=20)
post_numbers = st.integers(min_value=1, max_value=1_000_000)


@st.composite
def post_candidates(draw):
    gallery_id = draw(gallery_ids)
    post_number = draw(post_numbers)
    return PostCandidate(
        url=f"https://gall.dcinside.com/board/view/?id={gallery_id}&no={post_number}",
        gallery_id=gallery_id,
        post_id=str(post_number),
        post_number=post_number,
    )


@st.composite
def bounded_range_filters(draw):
    lower = draw(st.integers(min_value=1, max_value=500))
    upper = draw(st.integers(min_value=lower, max_value=lower + 500))
    return RangeFilter(min_post_number=lower, max_post_number=upper)


absolute_dates = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))
