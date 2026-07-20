"""Yangilik pipeline'i: yig'ish → tozalash → dedup → baholash → tarjima → saqlash.

Bitta manba ishlamay qolsa boshqalari davom etadi — xatolik butun jarayonni to'xtatmaydi.
"""
from __future__ import annotations

from datetime import timedelta

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.database.models import Article, Source, utcnow
from app.database.repositories.articles import get_by_hash, get_by_url, get_recent_articles
from app.database.repositories.sources import get_active_sources, mark_source_checked
from app.news.collectors.base import RawItem
from app.news.collectors.rss import fetch_rss
from app.news.deduplication.dedup import content_hash, find_similar_title
from app.news.parsers.cleaner import clean_html, extract_keywords
from app.news.ranking.importance import compute_importance
from app.news.summarization.service import summarize_plain
from app.news.translation.service import BaseTranslator


async def _process_item(
    session: AsyncSession,
    source: Source,
    item: RawItem,
    translator: BaseTranslator,
    recent_titles: list[tuple[int, str]],
) -> Article | None:
    """Bitta xom elementni qayta ishlaydi. Yangi maqola yoki None (dublikat/eski) qaytaradi."""
    settings = get_settings()

    # Juda eski yangiliklar tashlab yuboriladi
    if item.published_at is not None:
        age_limit = utcnow() - timedelta(hours=settings.max_article_age_hours)
        if item.published_at < age_limit:
            return None

    title = clean_html(item.title)[:500]
    summary = clean_html(item.summary)
    if not title:
        return None

    # 1) URL bo'yicha dublikat
    if await get_by_url(session, item.url):
        return None

    # 2) Hash bo'yicha dublikat — boshqa manbada ham chiqqan: tasdiq sifatida hisoblanadi
    item_hash = content_hash(title)
    existing = await get_by_hash(session, item_hash)
    if existing:
        existing.confirmations += 1
        existing.importance_score = compute_importance(
            existing.original_title, existing.original_summary or "",
            existing.reliability_score, existing.published_at, existing.confirmations,
        )
        await session.commit()
        return None

    # 3) Sarlavha o'xshashligi bo'yicha dublikat
    similar_id = find_similar_title(title, recent_titles, settings.dedup_title_threshold)
    if similar_id is not None:
        original = await session.get(Article, similar_id)
        if original:
            original.confirmations += 1
            original.importance_score = compute_importance(
                original.original_title, original.original_summary or "",
                original.reliability_score, original.published_at, original.confirmations,
            )
        session.add(Article(
            source_id=source.id, external_id=item.external_id,
            original_title=title, original_summary=summary, url=item.url[:1024],
            published_at=item.published_at, category_id=source.category_id,
            content_hash=item_hash, reliability_score=source.reliability_score,
            is_duplicate=True, duplicate_of_id=similar_id, keywords=[],
        ))
        await session.commit()
        return None

    # 4) Yangi maqola: kalit so'zlar, muhimlik, tarjima
    keywords = extract_keywords(f"{title} {summary}")
    importance = compute_importance(
        title, summary, source.reliability_score, item.published_at, confirmations=1
    )

    translation = await translator.translate(title, summarize_plain(summary))

    article = Article(
        source_id=source.id,
        external_id=item.external_id,
        original_title=title,
        translated_title=translation.title if translation.translated else None,
        original_summary=summary,
        translated_summary=translation.summary if translation.translated else summarize_plain(summary),
        url=item.url[:1024],
        image_url=(item.image_url or "")[:1024] or None,
        published_at=item.published_at,
        category_id=source.category_id,
        keywords=keywords,
        content_hash=item_hash,
        importance_score=importance,
        reliability_score=source.reliability_score,
    )
    session.add(article)
    await session.commit()
    recent_titles.append((article.id, title))
    return article


async def collect_and_process(
    session_factory: async_sessionmaker, translator: BaseTranslator
) -> list[int]:
    """Barcha faol manbalarni tekshiradi. Yangi maqola ID'larini qaytaradi."""
    settings = get_settings()
    new_ids: list[int] = []

    async with session_factory() as session:
        sources = await get_active_sources(session)
        recent = await get_recent_articles(session, hours=72)
        recent_titles = [(a.id, a.original_title) for a in recent]

        for source in sources:
            try:
                items = await fetch_rss(source.url, settings.request_timeout_seconds)
            except Exception as exc:
                logger.warning("Manba ishlamadi [{}]: {}", source.name, exc)
                await mark_source_checked(session, source, success=False, error=str(exc))
                continue

            await mark_source_checked(session, source, success=True)

            for item in items:
                try:
                    article = await _process_item(session, source, item, translator, recent_titles)
                    if article:
                        new_ids.append(article.id)
                except Exception as exc:
                    logger.error("Element qayta ishlashda xato [{}]: {}", source.name, exc)
                    await session.rollback()

    if new_ids:
        logger.info("Yig'ish yakunlandi: {} ta yangi maqola", len(new_ids))
    return new_ids
