"""Pure normalization helpers for post detail parsing."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from dcinside_scraper.models.enums import NicknameType


def strip_repost_marker(title: str) -> str:
    return title.strip().removeprefix("(펌)").strip()


def parse_count(value: str | int | None) -> int | None:
    if isinstance(value, int):
        return value
    digits = re.sub(r"[^0-9]", "", value or "")
    return int(digits) if digits else None


def parse_dcinside_date(value: str | None, *, current_year: int | None = None) -> datetime | str | None:
    raw = (value or "").strip()
    if not raw:
        return None
    for pattern in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, pattern)
        except ValueError:
            pass
    if re.fullmatch(r"\d{1,2}\.\d{1,2}\s+\d{1,2}:\d{2}:\d{2}", raw):
        year = current_year or datetime.now().year
        try:
            return datetime.strptime(f"{year}.{raw}", "%Y.%m.%d %H:%M:%S")
        except ValueError:
            return raw
    return raw


def classify_nickname_type(
    *,
    user_id: str | None = None,
    ip: str | None = None,
    classes: list[str] | tuple[str, ...] | set[str] | None = None,
) -> NicknameType:
    class_text = " ".join(classes or ()).lower()
    if user_id:
        if any(token in class_text for token in ("semi", "half", "nonmember", "minor")):
            return NicknameType.SEMI_FIXED
        return NicknameType.FIXED
    if ip:
        return NicknameType.GUEST
    return NicknameType.UNKNOWN


def validate_block_orders(orders: list[int]) -> bool:
    return orders == list(range(len(orders)))


def make_safe_detail_failure(
    *,
    stage: str,
    reason: str,
    retryable: bool = False,
    field_path: str | None = None,
    failed_fields: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "reason": reason,
        "retryable": retryable,
        "field_path": field_path,
        "failed_fields": failed_fields or [],
    }
