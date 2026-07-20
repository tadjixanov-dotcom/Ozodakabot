"""Telegram xabarlarini formatlash. HTML parse mode, barcha matnlar escape qilinadi."""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

from app.database.models import Article, category_emoji

MAX_MESSAGE_LEN = 3800  # Telegram limiti 4096 — zaxira bilan


def _fmt_time(dt: datetime | None, tz_name: str) -> str:
    if dt is None:
        return "—"
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Tashkent")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz).strftime("%d.%m.%Y, %H:%M")


def format_article_message(
    article: Article,
    source_name: str,
    category_name: str,
    category_slug: str,
    tz_name: str = "Asia/Tashkent",
    critical: bool = False,
) -> str:
    emoji = category_emoji(category_slug)
    title = escape(article.display_title)
    summary = escape(article.display_summary)

    parts = []
    if critical:
        parts.append("‼️ <b>Muhim global yangilik</b>")
    parts.append(f"{emoji} <b>{title}</b>")
    if summary:
        parts.append(summary)
    parts.append(
        f"📂 Kategoriya: {escape(category_name)}\n"
        f"📰 Manba: {escape(source_name)}\n"
        f"🕐 E'lon qilingan: {_fmt_time(article.published_at, tz_name)}"
    )
    if not article.translated_title:
        parts.append("<i>⚠️ Avtomatik tarjimasiz (original til)</i>")

    text = "\n\n".join(parts)
    if len(text) > MAX_MESSAGE_LEN:
        # Uzun xabar — summary qismini qisqartiramiz
        overflow = len(text) - MAX_MESSAGE_LEN
        short_summary = summary[: max(0, len(summary) - overflow - 3)] + "…"
        parts[2 if critical else 1] = short_summary
        text = "\n\n".join(parts)[:MAX_MESSAGE_LEN]
    return text


def format_digest(
    items: list[tuple[Article, str, str]],  # (article, source_name, category_slug)
    tz_name: str = "Asia/Tashkent",
) -> str:
    """Dayjest: eng muhim yangiliklar ro'yxati havolalar bilan."""
    if not items:
        return "📭 Hozircha yangi muhim yangiliklar yo'q."

    lines = ["🗞 <b>Yangiliklar dayjesti</b>\n"]
    for i, (article, source_name, category_slug) in enumerate(items, 1):
        emoji = category_emoji(category_slug)
        title = escape(article.display_title)
        url = escape(article.url, quote=True)
        lines.append(f"{i}. {emoji} <a href=\"{url}\">{title}</a> — {escape(source_name)}")

    text = "\n".join(lines)
    return text[:MAX_MESSAGE_LEN]
