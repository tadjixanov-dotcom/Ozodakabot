"""Kollektorlar uchun umumiy tur — barcha manba turlari (RSS, API, GDELT) shu shaklda qaytaradi."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RawItem:
    title: str
    summary: str
    url: str
    external_id: str
    published_at: datetime | None
    image_url: str | None = None
