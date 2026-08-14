"""Import-safe post parsing package.

The older ``dcinside_scraper.post_detail`` package remains as a compatibility
entrypoint; new code should import parser components from here.
"""

from dcinside_scraper.parse.comments import (
    CommentAjaxParser,
    CommentCollection,
    CommentHtmlFallbackParser,
    CommentMemoParser,
    CommentPage,
    CommentPaginationGuard,
    CommentService,
    PaginationDecision,
)
from dcinside_scraper.parse.content import ContentBlockParser, RepostClient, RepostParseResult, RepostParser
from dcinside_scraper.parse.media import DcVideoMetadataResolver
from dcinside_scraper.parse.metadata import ParsedMetadata, PostMetadataParser
from dcinside_scraper.parse.models import ParsedContent
from dcinside_scraper.parse.service import PostDetailService
from dcinside_scraper.parse.warnings import DetailFailureRecorder, SafeDetailEventBuilder
from dcinside_scraper.post_detail.normalization import (
    classify_nickname_type,
    make_safe_detail_failure,
    parse_count,
    parse_dcinside_date,
    strip_repost_marker,
    validate_block_orders,
)

__all__ = [
    "CommentAjaxParser",
    "CommentCollection",
    "CommentHtmlFallbackParser",
    "CommentMemoParser",
    "CommentPage",
    "CommentPaginationGuard",
    "CommentService",
    "ContentBlockParser",
    "DcVideoMetadataResolver",
    "DetailFailureRecorder",
    "PaginationDecision",
    "ParsedContent",
    "ParsedMetadata",
    "PostDetailService",
    "PostMetadataParser",
    "RepostClient",
    "RepostParseResult",
    "RepostParser",
    "SafeDetailEventBuilder",
    "classify_nickname_type",
    "make_safe_detail_failure",
    "parse_count",
    "parse_dcinside_date",
    "strip_repost_marker",
    "validate_block_orders",
]
