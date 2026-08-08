from __future__ import annotations

from hypothesis import strategies as st

job_ids = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=30)
post_numbers = st.integers(min_value=1, max_value=10_000_000)


@st.composite
def direct_post_commands(draw):
    post_number = draw(post_numbers)
    job_id = draw(job_ids)
    return {
        "subcommand": "run",
        "source": "direct-post",
        "job_id": job_id,
        "urls": [f"https://gall.dcinside.com/board/view/?id=dcbest&no={post_number}"],
    }


@st.composite
def realtime_keyword_envs(draw):
    duration = draw(st.integers(min_value=1, max_value=86_400))
    keyword = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=30))
    return {
        "DCINSIDE_REALTIME_ENABLED": "true",
        "DCINSIDE_REALTIME_MODE": "keyword",
        "DCINSIDE_REALTIME_KEYWORD": keyword,
        "DCINSIDE_REALTIME_DURATION_SECONDS": str(duration),
    }
