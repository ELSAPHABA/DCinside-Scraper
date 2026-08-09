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
from dcinside_scraper.http import (
    HttpClient,
    HttpRuntimeConfig,
    ProxyConfig,
    RuntimePolicyService,
    UserAgentConfig,
)
from dcinside_scraper.models.checkpoint import Checkpoint
from dcinside_scraper.models.comment import Comment
from dcinside_scraper.models.error import ErrorResult
from dcinside_scraper.models.job import JobConfig
from dcinside_scraper.models.post import PostResult
from dcinside_scraper.models.report import JobReport
from dcinside_scraper.outputs import (
    LocalCheckpointStore,
    LocalMediaStore,
    LocalOutputStore,
    OutputRunLayout,
    S3ObjectStore,
    S3OutputStore,
)
from dcinside_scraper.post_detail import (
    CommentService,
    ContentBlockParser,
    PostDetailService,
    PostMetadataParser,
)
from dcinside_scraper.retry import ParserFailureRetryService
from dcinside_scraper.runner import CheckpointCoordinator, JobRunner, RunnerEventBuilder, StopController
from dcinside_scraper.search import (
    CandidateDeduper,
    GallerySearchCollector,
    GallerySearchUrlBuilder,
    IntegratedSearchCollector,
    IntegratedSearchUrlBuilder,
    LinkCollectorService,
)

__all__ = [
    "BlockedResponseError",
    "CaptchaDetectedError",
    "CandidateDeduper",
    "Checkpoint",
    "CheckpointFailureError",
    "Comment",
    "CommentService",
    "ContentBlockParser",
    "CheckpointCoordinator",
    "ErrorResult",
    "GallerySearchCollector",
    "GallerySearchUrlBuilder",
    "HttpClient",
    "HttpRuntimeConfig",
    "IntegratedSearchCollector",
    "IntegratedSearchUrlBuilder",
    "JobConfig",
    "JobConfigValidator",
    "JobReport",
    "JobRunner",
    "LinkCollectorService",
    "LocalCheckpointStore",
    "LocalMediaStore",
    "LocalOutputStore",
    "NetworkFailureError",
    "OutputRunLayout",
    "ParseFailureError",
    "PostResult",
    "PostDetailService",
    "PostMetadataParser",
    "ParserFailureRetryService",
    "ProxyConfig",
    "RuntimePolicyService",
    "RunnerEventBuilder",
    "S3ObjectStore",
    "S3OutputStore",
    "ScraperError",
    "StorageFailureError",
    "StopController",
    "UnavailableContentError",
    "UnsupportedSourceError",
    "UserAgentConfig",
    "ValidationFailure",
    "fetch_comments",
    "fetch_post",
    "resume_job",
    "run_job",
    "search_gallery",
    "search_integrated",
]

__version__ = "0.1.0"
