"""Comment and author contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from dcinside_scraper.models.base import MetadataModel
from dcinside_scraper.models.enums import NicknameType
from dcinside_scraper.models.media import DcconItem


class AuthorInfo(MetadataModel):
    name: str | None = Field(default=None, max_length=200)
    user_id: str | None = Field(default=None, max_length=200)
    ip: str | None = Field(default=None, max_length=100)
    nickname_type: NicknameType = NicknameType.UNKNOWN


class RecommendationInfo(MetadataModel):
    upvotes: int | None = Field(default=None, ge=0)
    downvotes: int | None = Field(default=None, ge=0)


class Comment(MetadataModel):
    comment_id: str = Field(min_length=1, max_length=100)
    comment_number: int | None = Field(default=None, ge=0)
    parent_comment_id: str | None = Field(default=None, max_length=100)
    parent_comment_number: int | None = Field(default=None, ge=0)
    depth: int = Field(default=0, ge=0)
    author: AuthorInfo
    memo_text: str | None = None
    dccons: list[DcconItem] = Field(default_factory=list)
    created_at: datetime | str | None = None

