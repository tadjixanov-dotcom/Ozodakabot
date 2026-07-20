"""Matn o'xshashligi — kalit so'zlar to'plami ustida Jaccard koeffitsienti."""
from __future__ import annotations

from app.news.parsers.cleaner import STOPWORDS, tokenize


def keyword_set(text: str) -> set[str]:
    return {t for t in tokenize(text) if t not in STOPWORDS}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    if intersection == 0:
        return 0.0
    return intersection / len(a | b)


def max_similarity(target: set[str], others: list[set[str]]) -> float:
    """Maqola kalit so'zlarining boshqa to'plamlar bilan eng yuqori o'xshashligi."""
    if not target or not others:
        return 0.0
    return max((jaccard(target, other) for other in others), default=0.0)
