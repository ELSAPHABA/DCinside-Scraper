from __future__ import annotations

from hypothesis import strategies as st

from dcinside_scraper.models.job import JobConfig, RangeFilter

safe_ids = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=20)


@st.composite
def range_filters(draw):
    lower = draw(st.integers(min_value=0, max_value=1000))
    upper = draw(st.integers(min_value=lower, max_value=lower + 1000))
    return RangeFilter(min_post_number=lower, max_post_number=upper)


@st.composite
def job_configs(draw):
    job_id = draw(safe_ids)
    source = draw(
        st.sampled_from(
            [
                {"type": "direct_post", "urls": ["https://gall.dcinside.com/board/view/?id=dcbest&no=1"]},
                {
                    "type": "gallery_search",
                    "gallery_type": "minor",
                    "gallery_id": "singlebungle1472",
                    "s_type": "search_subject_memo",
                    "keyword": "test",
                },
                {"type": "integrated_search", "keyword": "test"},
            ]
        )
    )
    return JobConfig(job_id=job_id, job_type=source["type"], source=source)

