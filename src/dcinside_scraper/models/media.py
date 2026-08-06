"""Media and DCCon contracts."""

from __future__ import annotations

from pydantic import Field

from dcinside_scraper.models.base import MetadataModel
from dcinside_scraper.models.enums import MediaType


class MediaItem(MetadataModel):
    media_id: str | None = Field(default=None, max_length=200)
    media_type: MediaType
    url: str = Field(min_length=1, max_length=4096)
    source_url: str | None = Field(default=None, max_length=4096)
    file_path: str | None = None
    object_key: str | None = None
    description: str | None = None


class DcconItem(MetadataModel):
    src: str | None = Field(default=None, max_length=4096)
    alt: str | None = Field(default=None, max_length=1000)
    title: str | None = Field(default=None, max_length=1000)
    conalt: str | None = Field(default=None, max_length=1000)
    file_path: str | None = None
    object_key: str | None = None

