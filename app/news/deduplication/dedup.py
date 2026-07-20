"""Dublikat yangiliklarni aniqlash: hash, URL va sarlavha o'xshashligi bo'yicha."""
from __future__ import annotations

import hashlib
from difflib import SequenceMatcher

from app.news.parsers.cleaner import normalize_title


def content_hash(title: str) -> str:
    """Normallashtirilgan sarlavhadan SHA-256. Katta-kichik harf va tinish belgilariga sezgir emas."""
    return hashlib.sha256(normalize_title(title).encode("utf-8")).hexdigest()


def titles_similar(a: str, b: str, threshold: float = 0.85) -> bool:
    """Ikki sarlavha bir voqea haqida ekanini taxmin qiladi."""
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    # SequenceMatcher qimmat — uzunlik farqi katta bo'lsa oldindan chiqamiz
    if min(len(na), len(nb)) / max(len(na), len(nb)) < 0.5:
        return False
    return SequenceMatcher(None, na, nb).ratio() >= threshold


def find_similar_title(title: str, candidates: list[tuple[int, str]], threshold: float = 0.85) -> int | None:
    """candidates: (article_id, title) juftliklari. O'xshash topilsa article_id qaytaradi."""
    for article_id, cand_title in candidates:
        if titles_similar(title, cand_title, threshold):
            return article_id
    return None
