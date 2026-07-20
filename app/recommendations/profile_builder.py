"""Foydalanuvchi bahosi asosida qiziqish profilini yangilash."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.database.models import Article, RATING_VALUES, utcnow
from app.database.repositories.categories import get_category
from app.database.repositories.feedback import get_or_create_profile

_KEYWORD_STEP = 0.5
_MAX_WEIGHT = 3.0


def _bump(weights: dict, key: str, delta: float) -> None:
    new = float(weights.get(key, 0.0)) + delta
    weights[key] = max(-_MAX_WEIGHT, min(_MAX_WEIGHT, round(new, 3)))
    if abs(weights[key]) < 0.05:
        weights.pop(key, None)


async def update_profile_on_feedback(
    session: AsyncSession, user_id: int, article: Article, feedback_type: str
) -> None:
    """Har bir baho profil og'irliklarini yangilaydi:
    ijobiy baho → kalit so'zlar positive'ga, salbiy → negative'ga.
    """
    value = RATING_VALUES.get(feedback_type, 0)
    if value == 0:
        return  # neytral baho profilni o'zgartirmaydi

    profile = await get_or_create_profile(session, user_id)
    positive = dict(profile.positive_keywords or {})
    negative = dict(profile.negative_keywords or {})
    cat_weights = dict(profile.category_weights or {})
    pref_sources = dict(profile.preferred_sources or {})
    disliked_sources = dict(profile.disliked_sources or {})

    step = _KEYWORD_STEP * abs(value)
    keywords = list(article.keywords or [])[:10]

    if value > 0:
        for kw in keywords:
            _bump(positive, kw, step)
            _bump(negative, kw, -step * 0.5)  # qarama-qarshi signalni yumshatish
        _bump(pref_sources, str(article.source_id), 0.3 * value)
    else:
        for kw in keywords:
            _bump(negative, kw, step)
            _bump(positive, kw, -step * 0.5)
        _bump(disliked_sources, str(article.source_id), 0.3 * abs(value))

    if article.category_id:
        category = await get_category(session, article.category_id)
        if category:
            _bump(cat_weights, category.slug, 0.2 * value)

    profile.positive_keywords = positive
    profile.negative_keywords = negative
    profile.category_weights = cat_weights
    profile.preferred_sources = pref_sources
    profile.disliked_sources = disliked_sources
    profile.updated_at = utcnow()
    # JSON ustunlar o'zgarganini SQLAlchemy'ga bildirish shart
    for field in ("positive_keywords", "negative_keywords", "category_weights",
                  "preferred_sources", "disliked_sources"):
        flag_modified(profile, field)
    await session.commit()
