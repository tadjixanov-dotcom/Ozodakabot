from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, utcnow


class UserInterestProfile(Base):
    """Foydalanuvchi qiziqish profili — tavsiya algoritmi uchun asosiy manba.

    JSON maydonlar:
      positive_keywords / negative_keywords: {"keyword": weight}
      preferred_sources / disliked_sources: {"source_id": weight}
      category_weights: {"slug": weight}
    """

    __tablename__ = "user_interest_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    positive_keywords: Mapped[dict] = mapped_column(JSON, default=dict)
    negative_keywords: Mapped[dict] = mapped_column(JSON, default=dict)
    preferred_sources: Mapped[dict] = mapped_column(JSON, default=dict)
    disliked_sources: Mapped[dict] = mapped_column(JSON, default=dict)
    category_weights: Mapped[dict] = mapped_column(JSON, default=dict)
    profile_vector: Mapped[list | None] = mapped_column(JSON, default=None)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
