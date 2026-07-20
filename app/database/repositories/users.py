"""Foydalanuvchilar bilan ishlash repository'si."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.models import Category, User, UserCategory


async def get_user_by_tg(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None) -> User:
    user = await get_user_by_tg(session, telegram_id)
    if user:
        if username and user.username != username:
            user.username = username
            await session.commit()
        return user

    settings = get_settings()
    user = User(
        telegram_id=telegram_id,
        username=username,
        language=settings.default_language,
        timezone=settings.default_timezone,
        daily_limit=settings.default_daily_limit,
    )
    session.add(user)
    await session.flush()

    # Yangi foydalanuvchi uchun barcha kategoriyalar yoqilgan holda boshlanadi
    categories = (await session.execute(select(Category).where(Category.is_active))).scalars().all()
    for cat in categories:
        session.add(UserCategory(user_id=user.id, category_id=cat.id, enabled=True))
    await session.commit()
    await session.refresh(user)
    return user


async def get_active_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).where(User.is_active))
    return list(result.scalars().all())


async def count_users(session: AsyncSession) -> int:
    return (await session.execute(select(func.count(User.id)))).scalar_one()


async def count_active_users(session: AsyncSession) -> int:
    return (await session.execute(select(func.count(User.id)).where(User.is_active))).scalar_one()


async def get_enabled_category_ids(session: AsyncSession, user: User) -> set[int]:
    result = await session.execute(
        select(UserCategory.category_id).where(
            UserCategory.user_id == user.id, UserCategory.enabled
        )
    )
    return set(result.scalars().all())


async def toggle_user_category(session: AsyncSession, user: User, category_id: int) -> bool:
    """Kategoriyani yoqadi/o'chiradi. Yangi holatni qaytaradi."""
    result = await session.execute(
        select(UserCategory).where(
            UserCategory.user_id == user.id, UserCategory.category_id == category_id
        )
    )
    uc = result.scalar_one_or_none()
    if uc is None:
        uc = UserCategory(user_id=user.id, category_id=category_id, enabled=True)
        session.add(uc)
    else:
        uc.enabled = not uc.enabled
    await session.commit()
    return uc.enabled


async def set_user_category(session: AsyncSession, user: User, category_id: int, enabled: bool) -> None:
    result = await session.execute(
        select(UserCategory).where(
            UserCategory.user_id == user.id, UserCategory.category_id == category_id
        )
    )
    uc = result.scalar_one_or_none()
    if uc is None:
        session.add(UserCategory(user_id=user.id, category_id=category_id, enabled=enabled))
    else:
        uc.enabled = enabled
    await session.commit()
