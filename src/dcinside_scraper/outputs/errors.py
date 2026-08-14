"""Storage error aliases."""

from dcinside_scraper.core.errors import CheckpointFailureError, StorageFailureError

StorageConfigurationError = StorageFailureError
StorageReadError = StorageFailureError
StorageWriteError = StorageFailureError

__all__ = [
    "CheckpointFailureError",
    "StorageConfigurationError",
    "StorageFailureError",
    "StorageReadError",
    "StorageWriteError",
]
