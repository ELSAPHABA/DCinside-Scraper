from __future__ import annotations

from hypothesis import strategies as st

from dcinside_scraper.models.content import TextBlock

safe_text = st.text(alphabet=st.characters(blacklist_categories=("Cs",)), max_size=100)


def content_blocks():
    return st.builds(TextBlock, order=st.integers(min_value=0, max_value=100), text=safe_text)


def content_block_lists():
    return st.lists(st.integers(min_value=0, max_value=100), max_size=10, unique=True).flatmap(
        lambda orders: st.tuples(*(safe_text for _ in orders)).map(
            lambda texts: [TextBlock(order=order, text=text) for order, text in zip(orders, texts)]
        )
    )

