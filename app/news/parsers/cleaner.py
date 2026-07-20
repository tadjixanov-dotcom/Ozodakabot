"""HTML tozalash, sarlavha normallashtirish va kalit so'zlarni ajratish."""
from __future__ import annotations

import html
import re
from collections import Counter

from bs4 import BeautifulSoup

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁўЎқҚғҒҳҲ'ʼ\-]{3,}", re.UNICODE)

# Ingliz, rus va o'zbek tillari uchun minimal stop-so'zlar
STOPWORDS: frozenset[str] = frozenset({
    # en
    "the", "and", "for", "that", "with", "this", "from", "have", "has", "was", "were",
    "are", "will", "would", "could", "should", "been", "after", "before", "over", "into",
    "about", "their", "there", "when", "what", "which", "while", "than", "then", "them",
    "they", "its", "his", "her", "who", "how", "why", "can", "may", "more", "most", "new",
    "not", "but", "all", "also", "one", "two", "out", "you", "your", "says", "said", "amid",
    # ru
    "это", "как", "что", "или", "для", "при", "его", "она", "они", "оно", "все", "уже",
    "был", "быть", "если", "чем", "так", "также", "после", "перед", "между", "из-за",
    "года", "году", "лет", "может", "стал", "стала", "более", "менее", "новый", "новая",
    # uz
    "uchun", "bilan", "ham", "va", "yoki", "lekin", "ammo", "bo'ldi", "bo'lgan", "qildi",
    "qilgan", "etdi", "etilgan", "haqida", "yangi", "katta", "kichik", "yil", "yilda",
    "deb", "dedi", "edi", "emas", "bor", "yo'q", "keyin", "oldin", "orqali",
})


def clean_html(text: str | None) -> str:
    """HTML teglar, entitilar va ortiqcha bo'shliqlarni olib tashlaydi."""
    if not text:
        return ""
    soup = BeautifulSoup(html.unescape(text), "html.parser")
    cleaned = soup.get_text(separator=" ")
    return _WS_RE.sub(" ", cleaned).strip()


def normalize_title(title: str) -> str:
    """Dublikat aniqlash uchun sarlavhani kanonik shaklga keltiradi."""
    lowered = _PUNCT_RE.sub(" ", title.lower())
    return _WS_RE.sub(" ", lowered).strip()


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def extract_keywords(text: str, top_n: int = 12) -> list[str]:
    """Oddiy chastota asosidagi kalit so'z ajratish (stop-so'zlarsiz)."""
    tokens = [t for t in tokenize(text) if t not in STOPWORDS]
    if not tokens:
        return []
    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_n)]


def truncate_text(text: str, max_chars: int = 400) -> str:
    """Matnni gap chegarasida qisqartiradi."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    for sep in (". ", "! ", "? "):
        idx = cut.rfind(sep)
        if idx > max_chars // 2:
            return cut[: idx + 1].strip()
    return cut.rsplit(" ", 1)[0].strip() + "…"
