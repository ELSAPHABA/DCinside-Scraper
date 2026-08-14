"""Comment parsers and service."""

from dcinside_scraper.post_detail.detail import (
    CommentAjaxParser,
    CommentCollection,
    CommentHtmlFallbackParser,
    CommentMemoParser,
    CommentPage,
    CommentPaginationGuard,
    CommentService,
    PaginationDecision,
)

__all__ = [
    "CommentAjaxParser",
    "CommentCollection",
    "CommentHtmlFallbackParser",
    "CommentMemoParser",
    "CommentPage",
    "CommentPaginationGuard",
    "CommentService",
    "PaginationDecision",
]
