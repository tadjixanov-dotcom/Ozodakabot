"""Barcha modellar uchun asos. Vaqtlar hamma joyda naive-UTC saqlanadi."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    """Naive UTC datetime — SQLite/PostgreSQL bilan bir xil ishlaydi."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass
