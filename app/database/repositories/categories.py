from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Category


async def get_all_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(select(Category).where(Category.is_active).order_by(Category.id))
    return list(result.scalars().all())


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    return await session.get(Category, category_id)


async def get_category_map(session: AsyncSession) -> dict[int, Category]:
    return {c.id: c for c in await get_all_categories(session)}
