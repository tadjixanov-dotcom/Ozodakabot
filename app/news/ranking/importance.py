"""Yangilikning muhimlik darajasini hisoblash (0.0 – 1.0)."""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone

# Global ahamiyatga ega hodisalarni bildiruvchi atamalar (en/ru/uz)
HIGH_IMPACT_TERMS: frozenset[str] = frozenset({
    "war", "invasion", "attack", "missile", "strike", "nuclear", "ceasefire",
    "sanctions", "coup", "assassination", "earthquake", "explosion", "conflict",
    "mobilization", "offensive", "treaty", "summit", "election", "crisis",
    "breakthrough", "casualties", "escalation", "airstrike", "drone",
    "война", "вторжение", "атака", "ракета", "удар", "ядерный", "санкции",
    "переворот", "взрыв", "кризис", "саммит", "перемирие", "наступление",
    "urush", "hujum", "raketa", "yadroviy", "sanksiya", "inqiroz", "portlash",
    "tinchlik", "kelishuv", "prezident",
})

_CLICKBAIT_PATTERNS = [
    re.compile(r"you won'?t believe", re.I),
    re.compile(r"shocking|shocked", re.I),
    re.compile(r"\bthis is why\b", re.I),
    re.compile(r"top \d+ ", re.I),
    re.compile(r"[!?]{2,}"),
    re.compile(r"вы не поверите|шок", re.I),
    re.compile(r"hayron qolasiz|shok", re.I),
]


def is_clickbait(title: str) -> bool:
    return any(p.search(title) for p in _CLICKBAIT_PATTERNS)


def freshness_score(published_at: datetime | None, now: datetime | None = None) -> float:
    """Eksponensial pasayish: yangi = 1.0, 24 soatdan keyin ~0.37."""
    if published_at is None:
        return 0.5
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    if published_at.tzinfo is not None:
        published_at = published_at.astimezone(timezone.utc).replace(tzinfo=None)
    age_hours = max(0.0, (now - published_at).total_seconds() / 3600)
    return math.exp(-age_hours / 24)


def compute_importance(
    title: str,
    summary: str,
    source_reliability: float,
    published_at: datetime | None,
    confirmations: int = 1,
) -> float:
    """Muhimlik = kontent signali + manba ishonchliligi + yangilik + tasdiqlar."""
    text = f"{title} {summary}".lower()
    words = set(re.findall(r"[a-zа-яё']+", text))
    impact_hits = len(words & HIGH_IMPACT_TERMS)
    impact = min(1.0, impact_hits / 3)  # 3+ ta atama = maksimal signal

    # Bir nechta mustaqil manbada tasdiqlangan yangilik muhimroq
    confirmation_boost = min(0.2, 0.07 * (confirmations - 1))

    score = (
        0.45 * impact
        + 0.25 * max(0.0, min(1.0, source_reliability))
        + 0.20 * freshness_score(published_at)
        + confirmation_boost
    )

    if is_clickbait(title):
        score *= 0.6  # clickbait sarlavhalar pastroq baholanadi
    if len(title) < 15 or not summary:
        score *= 0.85  # mazmuni tushunarsiz/qisqa xabarlar

    return round(max(0.0, min(1.0, score)), 4)
