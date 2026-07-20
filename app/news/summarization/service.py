"""Qisqartirish yordamchilari. AI qisqartirish translation.service ichida birga bajariladi
(bitta so'rovda tarjima + qisqartirish — arzon va tez); bu modul AIsiz qisqartirish uchun.
"""
from __future__ import annotations

import re

from app.news.parsers.cleaner import truncate_text

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def summarize_plain(text: str, max_sentences: int = 4, max_chars: int = 450) -> str:
    """Matnning birinchi 2-4 gapini oladi (AIsiz rejim uchun)."""
    if not text:
        return ""
    sentences = _SENTENCE_RE.split(text.strip())
    summary = " ".join(sentences[:max_sentences]).strip()
    return truncate_text(summary, max_chars)
