"""Yig'ish jarayonini qo'lda bir marta ishga tushirish (test/diagnostika uchun).

Ishlatish: python -m scripts.collect_once
"""
from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database.seed import seed_categories, seed_sources
from app.database.session import async_session_factory, init_db
from app.news.translation.service import build_translator
from app.services.pipeline import collect_and_process


async def main() -> None:
    settings = get_settings()
    setup_logging("DEBUG")
    await init_db()
    async with async_session_factory() as session:
        await seed_categories(session)
        await seed_sources(session, settings.sources_config_path)
    new_ids = await collect_and_process(async_session_factory, build_translator(settings))
    print(f"Yangi maqolalar: {len(new_ids)} ta")


if __name__ == "__main__":
    asyncio.run(main())
