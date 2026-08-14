"""Import-safe collection package.

The older ``dcinside_scraper.search`` package remains as a compatibility
entrypoint; new code should import collection components from here.
"""

from dcinside_scraper.collect.models import (
    CollectorFailure,
    CollectorResult,
    CollectorSummary,
    DatePrecision,
    GalleryCandidate,
    ParsedDate,
    ParserResult,
    RangeDecision,
    SubjectHead,
    TraversalDecision,
)
from dcinside_scraper.collect.parsers import GallerySearchParser, IntegratedSearchParser, SubjectHeadParser
from dcinside_scraper.collect.policies import (
    CandidateDeduper,
    DateParser,
    GalleryCandidateDeduper,
    NullLogger,
    RangeFilterEvaluator,
    SafeCollectorEventBuilder,
    TraversalGuard,
)
from dcinside_scraper.collect.service import (
    DeepSearchCollector,
    DirectPostCollector,
    GallerySearchCollector,
    IntegratedSearchCollector,
    LinkCollectorService,
    NoKeywordRangeCollector,
    RealtimeCollectionCycle,
)
from dcinside_scraper.collect.urls import (
    DATE_JUMP_URL,
    GALL_BASE_URL,
    MAX_INTEGRATED_PAGE,
    SEARCH_BASE_URL,
    GallerySearchUrlBuilder,
    IntegratedSearchUrlBuilder,
    ParsedPostUrl,
    SearchDateJumpClient,
    normalize_post_url,
    parse_post_url,
)

__all__ = [
    "CandidateDeduper",
    "CollectorFailure",
    "CollectorResult",
    "CollectorSummary",
    "DATE_JUMP_URL",
    "DateParser",
    "DatePrecision",
    "DeepSearchCollector",
    "DirectPostCollector",
    "GALL_BASE_URL",
    "GalleryCandidate",
    "GalleryCandidateDeduper",
    "GallerySearchCollector",
    "GallerySearchParser",
    "GallerySearchUrlBuilder",
    "IntegratedSearchCollector",
    "IntegratedSearchParser",
    "IntegratedSearchUrlBuilder",
    "LinkCollectorService",
    "MAX_INTEGRATED_PAGE",
    "NoKeywordRangeCollector",
    "NullLogger",
    "ParsedDate",
    "ParsedPostUrl",
    "ParserResult",
    "RangeDecision",
    "RangeFilterEvaluator",
    "RealtimeCollectionCycle",
    "SEARCH_BASE_URL",
    "SafeCollectorEventBuilder",
    "SearchDateJumpClient",
    "SubjectHead",
    "SubjectHeadParser",
    "TraversalDecision",
    "TraversalGuard",
    "normalize_post_url",
    "parse_post_url",
]
