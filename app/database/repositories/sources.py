from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Source, utcnow


async def get_active_sources(session: AsyncSession) -> list[Source]:
    result = await session.execute(select(Source).where(Source.is_active))
    return list(result.scalars().all())


async def get_all_sources(session: AsyncSession) -> list[Source]:
    result = await session.execute(select(Source).order_by(Source.id))
    return list(result.scalars().all())


async def get_source(session: AsyncSession, source_id: int) -> Source | None:
    return await session.get(Source, source_id)


async def mark_source_checked(
    session: AsyncSession, source: Source, success: bool, error: str | None = None
) -> None:
    source.last_checked_at = utcnow()
    if success:
        source.last_success_at = utcnow()
        source.last_error = None
    else:
        source.last_error = (error or "unknown")[:512]
    await session.commit()


async def toggle_source(session: AsyncSession, source_id: int) -> Source | None:
    source = await session.get(Source, source_id)
    if source is None:
        return None
    source.is_active = not source.is_active
    await session.commit()
    return source


async def add_source(
    session: AsyncSession, name: str, url: str, category_id: int | None,
    language: str = "en", reliability: float = 0.7,
) -> Source:
    source = Source(
        name=name[:128], url=url[:512], source_type="rss",
        category_id=category_id, language=language, reliability_score=reliability,
    )
    session.add(source)
    await session.commit()
    return source


async def get_failing_sources(session: AsyncSession) -> list[Source]:
    result = await session.execute(
        select(Source).where(Source.is_active, Source.last_error.is_not(None))
    )
    return list(result.scalars().all())
