"""Post result contract."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from dcinside_scraper.models.base import MetadataModel
from dcinside_scraper.models.comment import AuthorInfo, Comment, RecommendationInfo
from dcinside_scraper.models.content import ContentBlock, ContentLink
from dcinside_scraper.models.enums import NicknameType
from dcinside_scraper.models.job import utc_now
from dcinside_scraper.models.media import MediaItem


class RepostInfo(MetadataModel):
    gallery_id: str = Field(min_length=1, max_length=100)
    gallery_name: str | None = Field(default=None, max_length=200)
    post_id: str = Field(min_length=1, max_length=100)
    post_number: int | None = Field(default=None, ge=0)
    author: AuthorInfo
    nickname_type: NicknameType = NicknameType.UNKNOWN
    views: int | None = Field(default=None, ge=0)
    recommendations: RecommendationInfo = Field(default_factory=RecommendationInfo)


class PostResult(MetadataModel):
    schema_version: Literal["dcinside.post.v1"] = "dcinside.post.v1"
    scrap_timestamp: datetime = Field(default_factory=utc_now)
    site_id: str = Field(default="dcinside", min_length=1, max_length=50)
    gallery_id: str = Field(min_length=1, max_length=100)
    post_id: str = Field(min_length=1, max_length=100)
    post_number: int | None = Field(default=None, ge=0)
    is_repost: bool = False
    repost: RepostInfo | None = None
    title: str = Field(min_length=1, max_length=1000)
    author: AuthorInfo
    nickname_type: NicknameType = NicknameType.UNKNOWN
    date: datetime | str | None = None
    views: int | None = Field(default=None, ge=0)
    recommendations: RecommendationInfo = Field(default_factory=RecommendationInfo)
    comment_count: int | None = Field(default=None, ge=0)
    content: list[ContentBlock] = Field(default_factory=list)
    images: list[MediaItem] = Field(default_factory=list)
    comments: list[Comment] = Field(default_factory=list)
    links: list[ContentLink] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def _strip_repost_marker(cls, value: str) -> str:
        return value.removeprefix("(펌)").strip()

    @model_validator(mode="after")
    def _validate_post(self) -> "PostResult":
        if self.is_repost and self.repost is None:
            raise ValueError("repost is required when is_repost is true")
        if not self.is_repost and self.repost is not None:
            raise ValueError("repost must be null when is_repost is false")
        orders = [block.order for block in self.content]
        if len(orders) != len(set(orders)):
            raise ValueError("content block orders must be unique")
        return self

