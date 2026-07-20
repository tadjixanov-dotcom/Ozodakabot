"""Botning kirish nuqtasi: python -m app.main"""
from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from app.bot.handlers import build_root_router
from app.bot.middlewares.db import DbSessionMiddleware
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database.seed import seed_categories, seed_sources
from app.database.session import async_session_factory, init_db
from app.news.translation.service import build_translator
from app.scheduler.jobs import setup_scheduler


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    if not settings.bot_token:
        raise SystemExit(
            "BOT_TOKEN topilmadi. .env faylini yarating (.env.example dan nusxa oling) "
            "va BotFather'dan olingan tokenni kiriting."
        )

    logger.info("Ma'lumotlar bazasi tayyorlanmoqda...")
    await init_db()
    async with async_session_factory() as session:
        await seed_categories(session)
        await seed_sources(session, settings.sources_config_path)

    translator = build_translator(settings)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.update.outer_middleware(DbSessionMiddleware(async_session_factory))
    dp.include_router(build_root_router())

    scheduler = setup_scheduler(bot, async_session_factory, translator)
    scheduler.start()
    logger.info("Scheduler ishga tushdi (yig'ish har {} daqiqada)", settings.fetch_interval_minutes)

    try:
        me = await bot.get_me()
        logger.info("Bot ishga tushdi: @{}", me.username)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
