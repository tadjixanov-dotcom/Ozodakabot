"""Boshlang'ich ma'lumotlar: kategoriyalar va manbalar (config/sources.json'dan)."""
from __future__ import annotations

import json
from pathlib import Path

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Category, DEFAULT_CATEGORIES, Source


async def seed_categories(session: AsyncSession) -> None:
    existing = {c.slug for c in (await session.execute(select(Category))).scalars()}
    for slug, (name, _emoji) in DEFAULT_CATEGORIES.items():
        if slug not in existing:
            session.add(Category(name=name, slug=slug, is_active=True))
    await session.commit()


async def seed_sources(session: AsyncSession, config_path: str) -> None:
    path = Path(config_path)
    if not path.exists():
        logger.warning("Manbalar konfiguratsiyasi topilmadi: {}", config_path)
        return

    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("sources.json o'qishda xato: {}", exc)
        return

    categories = {c.slug: c.id for c in (await session.execute(select(Category))).scalars()}
    existing_urls = {s.url for s in (await session.execute(select(Source))).scalars()}

    added = 0
    for entry in entries:
        url = entry.get("url", "").strip()
        if not url or url in existing_urls:
            continue
        session.add(Source(
            name=entry.get("name", url)[:128],
            url=url,
            source_type=entry.get("source_type", "rss"),
            category_id=categories.get(entry.get("category")),
            language=entry.get("language", "en"),
            reliability_score=float(entry.get("reliability_score", 0.7)),
            is_active=bool(entry.get("is_active", True)),
        ))
        added += 1
    await session.commit()
    if added:
        logger.info("{} ta yangi manba qo'shildi", added)
