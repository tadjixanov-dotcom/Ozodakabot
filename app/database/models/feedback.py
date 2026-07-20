from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base, utcnow

# Baho turlari va ularning signal qiymatlari
RATING_VALUES: dict[str, int] = {
    "dislike": -1,
    "neutral": 0,
    "like": 1,
    "love": 2,
    "less_topic": -3,
}


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_feedback_user_article"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    rating: Mapped[int] = mapped_column(default=0)
    feedback_type: Mapped[str] = mapped_column(String(16))  # dislike|neutral|like|love|less_topic
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)


class SavedArticle(Base):
    __tablename__ = "saved_articles"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_saved_user_article"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
