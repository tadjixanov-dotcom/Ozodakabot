"""Telegram xabarlarini formatlash. HTML parse mode, barcha matnlar escape qilinadi."""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

from app.database.models import Article, category_emoji
from app.news.parsers.cleaner import truncate_text

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
    """Tarjima bor bo'lsa: tepada original (inglizcha), tagida 🇺🇿 o'zbekcha tarjima."""
    emoji = category_emoji(category_slug)
    header = "‼️ <b>Muhim global yangilik</b>" if critical else ""
    meta = (
        f"📂 Kategoriya: {escape(category_name)}\n"
        f"📰 Manba: {escape(source_name)}\n"
        f"🕐 E'lon qilingan: {_fmt_time(article.published_at, tz_name)}"
    )
    link = f"🔗 <a href=\"{escape(article.url, quote=True)}\">Batafsil o'qish</a>"
    orig_title = escape(article.original_title)

    def assemble(parts: list[str]) -> str:
        return "\n\n".join(p for p in parts if p)

    if article.translated_title:
        uz_title = escape(article.translated_title)
        uz_summary = escape(article.translated_summary or "")
        # Original mazmunni sig'guncha qisqartirib boramiz: 350 → 150 → butunlay olib tashlash
        for orig_limit in (350, 150, None):
            orig_summary = (
                escape(truncate_text(article.original_summary or "", orig_limit))
                if orig_limit else ""
            )
            parts = [
                header,
                f"{emoji} <b>{orig_title}</b>",
                orig_summary,
                f"🇺🇿 <b>{uz_title}</b>",
                uz_summary,
                meta,
                link,
            ]
            text = assemble(parts)
            if len(text) <= MAX_MESSAGE_LEN:
                return text
        # Shunda ham uzun — o'zbekcha mazmunni qisqartiramiz
        overflow = len(text) - MAX_MESSAGE_LEN
        uz_summary = uz_summary[: max(0, len(uz_summary) - overflow - 3)] + "…"
        return assemble([header, f"{emoji} <b>{orig_title}</b>",
                         f"🇺🇿 <b>{uz_title}</b>", uz_summary, meta, link])

    # Tarjimasiz variant
    summary = escape(article.display_summary)
    parts = [
        header,
        f"{emoji} <b>{orig_title}</b>",
        summary,
        meta,
        "<i>⚠️ Avtomatik tarjimasiz (original til)</i>",
        link,
    ]
    text = assemble(parts)
    if len(text) > MAX_MESSAGE_LEN:
        overflow = len(text) - MAX_MESSAGE_LEN
        summary = summary[: max(0, len(summary) - overflow - 3)] + "…"
        parts[2] = summary
        text = assemble(parts)[:MAX_MESSAGE_LEN]
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
