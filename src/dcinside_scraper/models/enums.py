"""Shared enum contracts."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class JobType(StrEnum):
    DIRECT_POST = "direct_post"
    GALLERY_SEARCH = "gallery_search"
    INTEGRATED_SEARCH = "integrated_search"
    DEEP_SEARCH = "deep_search"
    NO_KEYWORD_RANGE = "no_keyword_range"
    REALTIME_KEYWORD = "realtime_keyword"
    REALTIME_ALL = "realtime_all"


class GalleryType(StrEnum):
    MAJOR = "major"
    MINOR = "minor"
    MINI = "mini"


class MediaMode(StrEnum):
    METADATA_ONLY = "metadata_only"
    DOWNLOAD = "download"


class DcconMode(StrEnum):
    SKIP = "skip"
    METADATA = "metadata"
    DOWNLOAD = "download"


class OutputMode(StrEnum):
    LOCAL = "local"
    S3 = "s3"


class CheckpointMode(StrEnum):
    LOCAL = "local"
    POSTGRES = "postgres"


class ContentBlockType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    DC_VIDEO = "dc_video"
    YOUTUBE = "youtube"
    LINK = "link"
    SERIES = "series"
    UNKNOWN_EMBED = "unknown_embed"


class MediaType(StrEnum):
    IMAGE = "image"
    DC_VIDEO = "dc_video"
    YOUTUBE_THUMBNAIL = "youtube_thumbnail"
    DCCON = "dccon"
    OTHER = "other"


class NicknameType(StrEnum):
    FIXED = "fixed"
    SEMI_FIXED = "semi_fixed"
    GUEST = "guest"
    UNKNOWN = "unknown"


class IntegratedSearchSort(StrEnum):
    RELEVANCE = "relevance"
    LATEST = "latest"


class CheckpointStatus(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"


class StopReason(StrEnum):
    CAPTCHA = "captcha"
    MANUAL_STOP = "manual_stop"
    ERROR = "error"
    TIMEOUT = "timeout"
    LEASE_EXPIRED = "lease_expired"


class JobReportStatus(StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"

