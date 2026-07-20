from datetime import datetime, timedelta, timezone

from app.news.ranking.importance import compute_importance, freshness_score, is_clickbait


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_high_impact_scores_higher():
    high = compute_importance(
        "War escalation: missile strike hits city, ceasefire collapses",
        "Nuclear talks failed amid new sanctions and offensive operations.",
        source_reliability=0.9, published_at=_now(),
    )
    low = compute_importance(
        "Local bakery wins pastry award",
        "A small bakery received recognition for its croissants this weekend.",
        source_reliability=0.9, published_at=_now(),
    )
    assert high > low


def test_confirmations_boost_score():
    base = compute_importance("Missile strike reported", "Attack on the border area.", 0.8, _now(), 1)
    confirmed = compute_importance("Missile strike reported", "Attack on the border area.", 0.8, _now(), 4)
    assert confirmed > base


def test_clickbait_detected_and_penalized():
    assert is_clickbait("You won't believe what happened next!!")
    clickbait = compute_importance(
        "You won't believe this shocking war update!!",
        "War escalation and missile strikes continue.", 0.9, _now(),
    )
    normal = compute_importance(
        "War update: missile strikes continue in the region",
        "War escalation and missile strikes continue.", 0.9, _now(),
    )
    assert clickbait < normal


def test_freshness_decays():
    fresh = freshness_score(_now())
    old = freshness_score(_now() - timedelta(hours=36))
    assert fresh > old > 0
