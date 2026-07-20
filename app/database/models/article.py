from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, utcnow


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(512))
    original_title: Mapped[str] = mapped_column(String(512))
    translated_title: Mapped[str | None] = mapped_column(String(512))
    original_summary: Mapped[str | None] = mapped_column(Text)
    translated_summary: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1024), index=True)
    image_url: Mapped[str | None] = mapped_column(String(1024))
    published_at: Mapped[datetime | None] = mapped_column(index=True)
    collected_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    keywords: Mapped[list | None] = mapped_column(JSON, default=list)
    entities: Mapped[dict | None] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    importance_score: Mapped[float] = mapped_column(Float, default=0.0)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.7)
    embedding: Mapped[list | None] = mapped_column(JSON, default=None)
    confirmations: Mapped[int] = mapped_column(default=1)
    is_duplicate: Mapped[bool] = mapped_column(default=False)
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id"))

    @property
    def display_title(self) -> str:
        return self.translated_title or self.original_title

    @property
    def display_summary(self) -> str:
        return self.translated_summary or self.original_summary or ""
