from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(String(512), unique=True)
    source_type: Mapped[str] = mapped_column(String(16), default="rss")  # rss | api | gdelt
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    language: Mapped[str] = mapped_column(String(8), default="en")
    reliability_score: Mapped[float] = mapped_column(Float, default=0.7)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(default=None)
    last_success_at: Mapped[datetime | None] = mapped_column(default=None)
    last_error: Mapped[str | None] = mapped_column(String(512), default=None)
