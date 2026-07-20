from app.database.models import Article, UserInterestProfile
from app.recommendations.scoring import score_article
from app.recommendations.similarity import jaccard, keyword_set


class _NoExplorationRng:
    """Exploration hech qachon ishlamaydi — deterministik test uchun."""

    def random(self) -> float:
        return 0.999


def _article(keywords: list[str], importance: float = 0.5) -> Article:
    return Article(
        id=1, source_id=1, original_title="t", url="https://x.test/a",
        content_hash="h", keywords=keywords, importance_score=importance,
        reliability_score=0.8,
    )


def _profile(**kwargs) -> UserInterestProfile:
    defaults = dict(
        user_id=1, positive_keywords={}, negative_keywords={},
        preferred_sources={}, disliked_sources={}, category_weights={},
    )
    defaults.update(kwargs)
    return UserInterestProfile(**defaults)


def test_jaccard_basics():
    assert jaccard({"a", "b"}, {"a", "b"}) == 1.0
    assert jaccard({"a"}, {"b"}) == 0.0
    assert 0 < jaccard({"a", "b", "c"}, {"b", "c", "d"}) < 1


def test_disliked_similar_article_scores_lower():
    article = _article(["crypto", "bitcoin", "price", "market"])
    disliked = [keyword_set("crypto bitcoin price falls market crash")]
    rng = _NoExplorationRng()

    with_penalty = score_article(article, _profile(), disliked, rng=rng)
    without_penalty = score_article(article, _profile(), [], rng=rng)
    assert with_penalty.score < without_penalty.score


def test_very_similar_disliked_suppressed():
    article = _article(["crypto", "bitcoin", "price"], importance=0.3)
    disliked = [{"crypto", "bitcoin", "price"}]  # to'liq mos — jaccard 1.0
    result = score_article(article, _profile(), disliked, rng=_NoExplorationRng())
    assert result.suppressed is True


def test_critical_news_overrides_dislike():
    article = _article(["war", "nuclear", "strike"], importance=0.95)
    disliked = [{"war", "nuclear", "strike"}]
    result = score_article(article, _profile(), disliked, rng=_NoExplorationRng())
    assert result.suppressed is False
    assert result.critical_override is True


def test_positive_keywords_raise_score():
    article = _article(["robotics", "boston", "dynamics"])
    liked_profile = _profile(positive_keywords={"robotics": 3.0, "boston": 2.0})
    neutral = score_article(article, _profile(), [], rng=_NoExplorationRng())
    boosted = score_article(article, liked_profile, [], rng=_NoExplorationRng())
    assert boosted.score > neutral.score
