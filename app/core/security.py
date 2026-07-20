"""Xavfsizlik yordamchilari: admin tekshiruvi va callback ma'lumotlarini validatsiya qilish."""
from __future__ import annotations

import re

from app.core.config import get_settings

# callback_data faqat shu shaklda qabul qilinadi: prefix:arg1:arg2 (harf/raqam/pastki chiziq)
_CALLBACK_RE = re.compile(r"^[a-z_]+(:[A-Za-z0-9_.\-]+){0,3}$")

# Ruxsat etilgan callback prefikslari
ALLOWED_PREFIXES = {
    "fb", "less", "save", "mutecat", "cat", "set", "reset", "admin", "src", "noop",
}


def is_admin(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_id_list


def parse_callback(data: str | None) -> tuple[str, list[str]] | None:
    """Callback ma'lumotini xavfsiz ajratadi. Noto'g'ri format — None."""
    if not data or len(data) > 64 or not _CALLBACK_RE.match(data):
        return None
    parts = data.split(":")
    prefix, args = parts[0], parts[1:]
    if prefix not in ALLOWED_PREFIXES:
        return None
    return prefix, args
