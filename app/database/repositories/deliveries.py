from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Delivery, utcnow


async def record_delivery(
    session: AsyncSession, user_id: int, article_id: int,
    telegram_message_id: int | None, status: str = "sent",
) -> Delivery:
    delivery = Delivery(
        user_id=user_id, article_id=article_id,
        telegram_message_id=telegram_message_id, status=status,
    )
    session.add(delivery)
    await session.commit()
    return delivery


async def was_delivered(session: AsyncSession, user_id: int, article_id: int) -> bool:
    result = await session.execute(
        select(Delivery.id).where(
            Delivery.user_id == user_id, Delivery.article_id == article_id
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def count_deliveries_since(session: AsyncSession, user_id: int, hours: float) -> int:
    since = utcnow() - timedelta(hours=hours)
    result = await session.execute(
        select(func.count(Delivery.id)).where(
            Delivery.user_id == user_id,
            Delivery.delivered_at >= since,
            Delivery.status == "sent",
        )
    )
    return result.scalar_one()


async def count_deliveries_today(session: AsyncSession) -> int:
    """Admin statistikasi uchun: bugungi barcha yuborilgan xabarlar."""
    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count(Delivery.id)).where(
            Delivery.delivered_at >= today, Delivery.status == "sent"
        )
    )
    return result.scalar_one()
