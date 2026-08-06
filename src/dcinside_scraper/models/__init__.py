"""Pydantic model contracts."""

from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.comment import AuthorInfo, Comment, RecommendationInfo
from dcinside_scraper.models.content import (
    ContentBlock,
    ContentLink,
    DcVideoBlock,
    ImageBlock,
    LinkBlock,
    SeriesBlock,
    TextBlock,
    UnknownEmbedBlock,
    YouTubeBlock,
)
from dcinside_scraper.models.error import ErrorResult
from dcinside_scraper.models.job import JobConfig
from dcinside_scraper.models.media import DcconItem, MediaItem
from dcinside_scraper.models.post import PostResult, RepostInfo
from dcinside_scraper.models.report import FailureRecord, JobReport, StoredObjectRef

__all__ = [
    "AuthorInfo",
    "Checkpoint",
    "Comment",
    "ContentBlock",
    "ContentLink",
    "DcVideoBlock",
    "DcconItem",
    "ErrorResult",
    "FailureRecord",
    "ImageBlock",
    "JobConfig",
    "JobReport",
    "LinkBlock",
    "MediaItem",
    "PostResult",
    "RecommendationInfo",
    "RepostInfo",
    "SeriesBlock",
    "StoredObjectRef",
    "TextBlock",
    "UnknownEmbedBlock",
    "YouTubeBlock",
]
