"""APScheduler ishlari: davriy yangilik yig'ish va dayjest yuborish."""
from __future__ import annotations

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import get_settings
from app.news.translation.service import BaseTranslator
from app.services.delivery import deliver_digests, deliver_realtime
from app.services.pipeline import collect_and_process


def setup_scheduler(
    bot: Bot, session_factory: async_sessionmaker, translator: BaseTranslator
) -> AsyncIOScheduler:
    settings = get_settings()
    scheduler = AsyncIOScheduler(timezone="UTC")

    async def collect_job() -> None:
        try:
            new_ids = await collect_and_process(session_factory, translator)
            if new_ids:
                await deliver_realtime(bot, session_factory)
        except Exception as exc:
            # Har qanday xato scheduler'ni to'xtatmasligi kerak
            logger.exception("Yig'ish jarayonida xato: {}", exc)

    async def digest_job() -> None:
        try:
            await deliver_digests(bot, session_factory)
        except Exception as exc:
            logger.exception("Dayjest yuborishda xato: {}", exc)

    scheduler.add_job(
        collect_job, "interval",
        minutes=settings.fetch_interval_minutes,
        id="collect_news", max_instances=1, coalesce=True,
    )
    scheduler.add_job(
        digest_job, "interval",
        minutes=settings.digest_check_interval_minutes,
        id="deliver_digests", max_instances=1, coalesce=True,
    )
    return scheduler
