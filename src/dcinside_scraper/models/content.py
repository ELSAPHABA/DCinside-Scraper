"""Ordered post body content block contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from dcinside_scraper.models.base import MetadataModel


class ContentLink(MetadataModel):
    url: str = Field(min_length=1, max_length=4096)
    text: str | None = Field(default=None, max_length=1000)
    title: str | None = Field(default=None, max_length=1000)


class TextBlock(MetadataModel):
    type: Literal["text"] = "text"
    order: int = Field(ge=0)
    text: str


class ImageBlock(MetadataModel):
    type: Literal["image"] = "image"
    order: int = Field(ge=0)
    url: str = Field(min_length=1, max_length=4096)
    source_url: str | None = Field(default=None, max_length=4096)
    alt: str | None = Field(default=None, max_length=1000)
    file_path: str | None = None
    object_key: str | None = None


class DcVideoBlock(MetadataModel):
    type: Literal["dc_video"] = "dc_video"
    order: int = Field(ge=0)
    url: str | None = Field(default=None, max_length=4096)
    thumbnail_url: str | None = Field(default=None, max_length=4096)
    description: str | None = None
    duration: float | None = Field(default=None, ge=0)
    file_path: str | None = None
    object_key: str | None = None


class YouTubeBlock(MetadataModel):
    type: Literal["youtube"] = "youtube"
    order: int = Field(ge=0)
    url: str = Field(min_length=1, max_length=4096)
    video_id: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, max_length=1000)


class LinkBlock(MetadataModel):
    type: Literal["link"] = "link"
    order: int = Field(ge=0)
    url: str = Field(min_length=1, max_length=4096)
    text: str | None = Field(default=None, max_length=1000)
    title: str | None = Field(default=None, max_length=1000)


class SeriesBlock(MetadataModel):
    type: Literal["series"] = "series"
    order: int = Field(ge=0)
    title: str | None = Field(default=None, max_length=1000)
    url: str | None = Field(default=None, max_length=4096)
    post_count: int | None = Field(default=None, ge=0)


class UnknownEmbedBlock(MetadataModel):
    type: Literal["unknown_embed"] = "unknown_embed"
    order: int = Field(ge=0)
    kind: str | None = Field(default=None, max_length=200)
    reason: str | None = Field(default=None, max_length=1000)


ContentBlock = Annotated[
    TextBlock
    | ImageBlock
    | DcVideoBlock
    | YouTubeBlock
    | LinkBlock
    | SeriesBlock
    | UnknownEmbedBlock,
    Field(discriminator="type"),
]

