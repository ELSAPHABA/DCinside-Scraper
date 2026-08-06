"""Import-safe public contracts for the DCinside scraper."""

from dcinside_scraper.core.api import (
    fetch_comments,
    fetch_post,
    resume_job,
    run_job,
    search_gallery,
    search_integrated,
)
from dcinside_scraper.core.errors import (
    BlockedResponseError,
    CaptchaDetectedError,
    CheckpointFailureError,
    NetworkFailureError,
    ParseFailureError,
    ScraperError,
    StorageFailureError,
    UnavailableContentError,
    UnsupportedSourceError,
    ValidationFailure,
)
from dcinside_scraper.core.validation import JobConfigValidator
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.comment import Comment
from dcinside_scraper.models.error import ErrorResult
from dcinside_scraper.models.job import JobConfig
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import JobReport

__all__ = [
    "BlockedResponseError",
    "CaptchaDetectedError",
    "Checkpoint",
    "CheckpointFailureError",
    "Comment",
    "ErrorResult",
    "JobConfig",
    "JobConfigValidator",
    "JobReport",
    "NetworkFailureError",
    "ParseFailureError",
    "PostResult",
    "ScraperError",
    "StorageFailureError",
    "UnavailableContentError",
    "UnsupportedSourceError",
    "ValidationFailure",
    "fetch_comments",
    "fetch_post",
    "resume_job",
    "run_job",
    "search_gallery",
    "search_integrated",
]

__version__ = "0.1.0"
