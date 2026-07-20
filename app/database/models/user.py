from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(128))
    language: Mapped[str] = mapped_column(String(8), default="uz")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")
    # realtime | digest | mixed
    delivery_mode: Mapped[str] = mapped_column(String(16), default="mixed")
    daily_limit: Mapped[int] = mapped_column(default=10)
    digest_times: Mapped[str] = mapped_column(String(64), default="08:00,20:00")
    quiet_hours_start: Mapped[int] = mapped_column(default=23)
    quiet_hours_end: Mapped[int] = mapped_column(default=7)
    quiet_hours_enabled: Mapped[bool] = mapped_column(default=True)
    minimum_importance: Mapped[float] = mapped_column(Float, default=0.3)
    trusted_only: Mapped[bool] = mapped_column(default=False)
    last_digest_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)

    categories: Mapped[list["UserCategory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )


class UserCategory(Base):
    __tablename__ = "user_categories"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    user: Mapped["User"] = relationship(back_populates="categories")
