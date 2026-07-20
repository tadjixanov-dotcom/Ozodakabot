from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Article, Feedback, RATING_VALUES, SavedArticle, UserInterestProfile, utcnow,
)


async def upsert_feedback(
    session: AsyncSession, user_id: int, article_id: int, feedback_type: str
) -> Feedback:
    """Bahoni saqlaydi. Qayta bosilsa eski baho yangilanadi — dublikat yozilmaydi."""
    rating = RATING_VALUES.get(feedback_type, 0)
    result = await session.execute(
        select(Feedback).where(Feedback.user_id == user_id, Feedback.article_id == article_id)
    )
    fb = result.scalar_one_or_none()
    if fb is None:
        fb = Feedback(user_id=user_id, article_id=article_id,
                      rating=rating, feedback_type=feedback_type)
        session.add(fb)
    else:
        fb.rating = rating
        fb.feedback_type = feedback_type
        fb.updated_at = utcnow()
    await session.commit()
    return fb


async def get_feedback_articles(
    session: AsyncSession, user_id: int, feedback_types: list[str], limit: int = 60
) -> list[Article]:
    """Foydalanuvchi ma'lum baho bergan maqolalar (tavsiya algoritmi uchun)."""
    result = await session.execute(
        select(Article)
        .join(Feedback, Feedback.article_id == Article.id)
        .where(Feedback.user_id == user_id, Feedback.feedback_type.in_(feedback_types))
        .order_by(Feedback.updated_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def save_article(session: AsyncSession, user_id: int, article_id: int) -> bool:
    """Maqolani saqlash. Allaqachon saqlangan bo'lsa False qaytaradi."""
    result = await session.execute(
        select(SavedArticle).where(
            SavedArticle.user_id == user_id, SavedArticle.article_id == article_id
        )
    )
    if result.scalar_one_or_none():
        return False
    session.add(SavedArticle(user_id=user_id, article_id=article_id))
    await session.commit()
    return True


async def get_saved_articles(session: AsyncSession, user_id: int, limit: int = 20) -> list[Article]:
    result = await session.execute(
        select(Article)
        .join(SavedArticle, SavedArticle.article_id == Article.id)
        .where(SavedArticle.user_id == user_id)
        .order_by(SavedArticle.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_or_create_profile(session: AsyncSession, user_id: int) -> UserInterestProfile:
    result = await session.execute(
        select(UserInterestProfile).where(UserInterestProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = UserInterestProfile(
            user_id=user_id, positive_keywords={}, negative_keywords={},
            preferred_sources={}, disliked_sources={}, category_weights={},
        )
        session.add(profile)
        await session.commit()
    return profile


async def reset_preferences(session: AsyncSession, user_id: int) -> None:
    """Barcha baholar va qiziqish profilini tozalaydi."""
    from sqlalchemy import delete
    await session.execute(delete(Feedback).where(Feedback.user_id == user_id))
    await session.execute(
        delete(UserInterestProfile).where(UserInterestProfile.user_id == user_id)
    )
    await session.commit()


async def feedback_stats(session: AsyncSession, user_id: int) -> dict[str, int]:
    result = await session.execute(
        select(Feedback.feedback_type, func.count(Feedback.id))
        .where(Feedback.user_id == user_id)
        .group_by(Feedback.feedback_type)
    )
    return dict(result.all())


async def top_rated_categories(session: AsyncSession, positive: bool = True, limit: int = 5):
    """Admin statistikasi: eng ko'p yoqtirilgan/yoqtirilmagan kategoriyalar."""
    cond = Feedback.rating > 0 if positive else Feedback.rating < 0
    result = await session.execute(
        select(Article.category_id, func.count(Feedback.id).label("cnt"))
        .join(Article, Article.id == Feedback.article_id)
        .where(cond)
        .group_by(Article.category_id)
        .order_by(func.count(Feedback.id).desc())
        .limit(limit)
    )
    return result.all()
