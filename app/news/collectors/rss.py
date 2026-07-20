"""RSS/Atom manbalardan yangilik yig'uvchi kollektor."""
from __future__ import annotations

import asyncio
import calendar
from datetime import datetime

import feedparser
import httpx
from loguru import logger

from app.news.collectors.base import RawItem

_USER_AGENT = "Mozilla/5.0 (compatible; OzodakaNewsBot/1.0; +https://t.me)"
_MAX_ENTRIES = 30


def _entry_published(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime.utcfromtimestamp(calendar.timegm(parsed))
            except (ValueError, OverflowError):
                continue
    return None


def _entry_image(entry) -> str | None:
    for media in getattr(entry, "media_content", []) or []:
        if media.get("url"):
            return media["url"]
    for link in getattr(entry, "links", []) or []:
        if str(link.get("type", "")).startswith("image/") and link.get("href"):
            return link["href"]
    return None


def _parse_feed(text: str) -> list[RawItem]:
    parsed = feedparser.parse(text)
    items: list[RawItem] = []
    for entry in parsed.entries[:_MAX_ENTRIES]:
        title = (getattr(entry, "title", "") or "").strip()
        url = (getattr(entry, "link", "") or "").strip()
        if not title or not url.startswith(("http://", "https://")):
            continue
        items.append(RawItem(
            title=title,
            summary=(getattr(entry, "summary", "") or getattr(entry, "description", "") or "").strip(),
            url=url,
            external_id=(getattr(entry, "id", "") or url)[:512],
            published_at=_entry_published(entry),
            image_url=_entry_image(entry),
        ))
    return items


async def fetch_rss(url: str, timeout: float = 20.0) -> list[RawItem]:
    """Bitta RSS manbani o'qiydi. Xatolikda istisno ko'taradi — chaqiruvchi ushlaydi."""
    async with httpx.AsyncClient(
        timeout=timeout, follow_redirects=True, headers={"User-Agent": _USER_AGENT}
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
    # feedparser sinxron — event loop'ni bloklamaslik uchun alohida thread'da
    items = await asyncio.to_thread(_parse_feed, response.text)
    logger.debug("RSS {}: {} ta element", url, len(items))
    return items
