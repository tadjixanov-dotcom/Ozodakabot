from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Article, Delivery, utcnow


async def get_by_hash(session: AsyncSession, content_hash: str) -> Article | None:
    result = await session.execute(
        select(Article).where(Article.content_hash == content_hash).limit(1)
    )
    return result.scalar_one_or_none()


async def get_by_url(session: AsyncSession, url: str) -> Article | None:
    result = await session.execute(select(Article).where(Article.url == url).limit(1))
    return result.scalar_one_or_none()


async def get_recent_articles(session: AsyncSession, hours: int = 72, limit: int = 500) -> list[Article]:
    since = utcnow() - timedelta(hours=hours)
    result = await session.execute(
        select(Article)
        .where(Article.collected_at >= since, Article.is_duplicate.is_(False))
        .order_by(Article.collected_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_undelivered_for_user(
    session: AsyncSession, user_id: int, category_ids: set[int],
    min_importance: float, hours: int = 48, trusted_only: bool = False, limit: int = 100,
) -> list[Article]:
    """Foydalanuvchiga hali yuborilmagan, kategoriyasi yoqilgan yangi maqolalar."""
    if not category_ids:
        return []
    since = utcnow() - timedelta(hours=hours)
    delivered_sq = select(Delivery.article_id).where(Delivery.user_id == user_id)
    stmt = (
        select(Article)
        .where(
            Article.collected_at >= since,
            Article.is_duplicate.is_(False),
            Article.category_id.in_(category_ids),
            Article.importance_score >= min_importance,
            Article.id.not_in(delivered_sq),
        )
        .order_by(Article.importance_score.desc(), Article.collected_at.desc())
        .limit(limit)
    )
    if trusted_only:
        stmt = stmt.where(Article.reliability_score >= 0.85)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_article(session: AsyncSession, article_id: int) -> Article | None:
    return await session.get(Article, article_id)
