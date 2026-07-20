"""Gibrid tavsiya ballari.

final_score = importance + interest + freshness + source_score
              - dislike_similarity_penalty
(dublikatlar pipeline bosqichida filtrlangani uchun duplicate_penalty bu yerda 0)
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from app.core.config import get_settings
from app.database.models import Article, UserInterestProfile
from app.news.ranking.importance import freshness_score
from app.recommendations.similarity import max_similarity


@dataclass(slots=True)
class ScoredArticle:
    article: Article
    score: float
    suppressed: bool = False          # umuman yuborilmasin
    critical_override: bool = False   # yoqmasa ham favqulodda muhim — "Muhim global yangilik"


def _article_keywords(article: Article) -> set[str]:
    return set(article.keywords or [])


def _interest_score(article: Article, profile: UserInterestProfile | None, category_slug: str | None) -> float:
    """Foydalanuvchi profilidagi kalit so'z va kategoriya og'irliklaridan qiziqish balli."""
    if profile is None:
        return 0.0
    keywords = _article_keywords(article)
    positive = profile.positive_keywords or {}
    negative = profile.negative_keywords or {}

    score = 0.0
    for kw in keywords:
        score += float(positive.get(kw, 0.0)) * 0.08
        score -= float(negative.get(kw, 0.0)) * 0.08

    if category_slug:
        score += float((profile.category_weights or {}).get(category_slug, 0.0)) * 0.1

    return max(-1.0, min(1.0, score))


def _source_score(article: Article, profile: UserInterestProfile | None) -> float:
    base = max(0.0, min(1.0, article.reliability_score))
    if profile is None:
        return base
    sid = str(article.source_id)
    pref = float((profile.preferred_sources or {}).get(sid, 0.0))
    dislike = float((profile.disliked_sources or {}).get(sid, 0.0))
    return max(0.0, min(1.0, base + 0.1 * pref - 0.1 * dislike))


def score_article(
    article: Article,
    profile: UserInterestProfile | None,
    disliked_keyword_sets: list[set[str]],
    category_slug: str | None = None,
    rng: random.Random | None = None,
) -> ScoredArticle:
    """Bitta maqola uchun foydalanuvchiga moslik balli.

    disliked_keyword_sets — foydalanuvchi "Yoqmadi"/"Kamroq ko'rsat" degan
    maqolalarning kalit so'z to'plamlari.
    """
    settings = get_settings()
    rng = rng or random

    importance = article.importance_score
    freshness = freshness_score(article.published_at or article.collected_at)
    interest = _interest_score(article, profile, category_slug)
    source = _source_score(article, profile)

    dislike_sim = max_similarity(_article_keywords(article), disliked_keyword_sets)
    penalty = dislike_sim * 1.2

    score = 0.40 * importance + 0.18 * freshness + 0.27 * interest + 0.15 * source - penalty

    suppressed = False
    critical_override = False

    if dislike_sim >= settings.dislike_block_threshold:
        if importance >= settings.critical_importance_threshold:
            # Global ahamiyatga ega favqulodda yangilik — baribir yuboriladi, belgilanadi
            critical_override = True
        else:
            suppressed = True
    elif dislike_sim >= settings.dislike_similarity_threshold:
        score -= 0.3  # kuchli pasaytirish, lekin yuborilishi mumkin

    # Exploration: filter pufagiga tushib qolmaslik uchun ba'zida penalti e'tiborsiz qoldiriladi
    if suppressed and not critical_override and rng.random() < settings.exploration_rate:
        suppressed = False
        score = 0.30 * importance + 0.18 * freshness  # neytral ball bilan sinab ko'riladi

    return ScoredArticle(
        article=article,
        score=round(score, 4),
        suppressed=suppressed,
        critical_override=critical_override,
    )


def rank_articles(
    articles: list[Article],
    profile: UserInterestProfile | None,
    disliked_keyword_sets: list[set[str]],
    category_slugs: dict[int, str],
    limit: int,
) -> list[ScoredArticle]:
    """Maqolalarni baholab, eng moslarini tanlaydi (suppressed'lar chiqarib tashlanadi)."""
    scored = [
        score_article(
            a, profile, disliked_keyword_sets,
            category_slugs.get(a.category_id or -1),
        )
        for a in articles
    ]
    visible = [s for s in scored if not s.suppressed]
    visible.sort(key=lambda s: s.score, reverse=True)
    return visible[:limit]
