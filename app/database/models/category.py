from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    slug: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)


# Standart kategoriyalar: slug -> (nom, emoji)
DEFAULT_CATEGORIES: dict[str, tuple[str, str]] = {
    "wars": ("Urushlar va geosiyosat", "🪖"),
    "region": ("Markaziy Osiyo", "🌏"),
    "robotics": ("Robototexnika", "🤖"),
    "defense": ("Mudofaa sanoati", "🛡"),
    "ai": ("Sun'iy intellekt", "🧠"),
    "global": ("Global siyosat va iqtisod", "🌍"),
}


def category_emoji(slug: str) -> str:
    return DEFAULT_CATEGORIES.get(slug, ("", "📰"))[1]
