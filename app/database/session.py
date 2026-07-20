"""Async SQLAlchemy sessiya fabrikasi. SQLite ham, PostgreSQL ham qo'llab-quvvatlanadi."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.database.models import Base

_settings = get_settings()

engine = create_async_engine(_settings.database_url, echo=False, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Jadvallarni yaratadi (MVP uchun; production'da Alembic migratsiyasi ishlatiladi)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
