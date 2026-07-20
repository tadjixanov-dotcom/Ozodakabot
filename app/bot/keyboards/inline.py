"""Inline klaviaturalar."""
from __future__ import annotations

from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.database.models import Category, DEFAULT_CATEGORIES, User


def article_keyboard(article_id: int, category_id: int, url: str) -> InlineKeyboardMarkup:
    """Yangilik xabari ostidagi tugmalar: baholash + qo'shimcha amallar.

    Havola tugma sifatida emas, xabar matni oxirida beriladi (formatter.py).
    """
    share_url = f"https://t.me/share/url?url={quote(url, safe='')}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👎", callback_data=f"fb:{article_id}:dislike"),
            InlineKeyboardButton(text="😐", callback_data=f"fb:{article_id}:neutral"),
            InlineKeyboardButton(text="👍", callback_data=f"fb:{article_id}:like"),
            InlineKeyboardButton(text="🔥", callback_data=f"fb:{article_id}:love"),
        ],
        [
            InlineKeyboardButton(text="🚫 Kamroq ko'rsat", callback_data=f"less:{article_id}"),
            InlineKeyboardButton(text="🔕 Kategoriya", callback_data=f"mutecat:{category_id}"),
        ],
        [
            InlineKeyboardButton(text="📌 Saqlash", callback_data=f"save:{article_id}"),
            InlineKeyboardButton(text="📤 Ulashish", url=share_url),
        ],
        [InlineKeyboardButton(text="➡️ Keyingi yangilik", callback_data="next:1")],
    ])


def categories_keyboard(categories: list[Category], enabled_ids: set[int]) -> InlineKeyboardMarkup:
    rows = []
    for cat in categories:
        emoji = DEFAULT_CATEGORIES.get(cat.slug, ("", "📰"))[1]
        mark = "✅" if cat.id in enabled_ids else "☑️"
        rows.append([InlineKeyboardButton(
            text=f"{mark} {emoji} {cat.name}", callback_data=f"cat:{cat.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


_MODE_LABELS = {"realtime": "⚡ Real-time", "digest": "🗞 Dayjest", "mixed": "🔀 Aralash"}
_IMPORTANCE_LABELS = {0.0: "Hammasi", 0.3: "O'rtacha+", 0.5: "Muhim+", 0.7: "Juda muhim"}


def settings_keyboard(user: User) -> InlineKeyboardMarkup:
    mode = _MODE_LABELS.get(user.delivery_mode, user.delivery_mode)
    quiet = "🌙 Yoqilgan" if user.quiet_hours_enabled else "🔔 O'chirilgan"
    imp = _IMPORTANCE_LABELS.get(round(user.minimum_importance, 1), f"{user.minimum_importance:.1f}")
    trusted = "✅" if user.trusted_only else "☑️"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Rejim: {mode}", callback_data="set:mode")],
        [InlineKeyboardButton(text=f"Kunlik limit: {user.daily_limit} ta", callback_data="set:limit")],
        [InlineKeyboardButton(text=f"Dayjest vaqtlari: {user.digest_times}", callback_data="set:times")],
        [InlineKeyboardButton(
            text=f"Jim rejim ({user.quiet_hours_start:02d}:00–{user.quiet_hours_end:02d}:00): {quiet}",
            callback_data="set:quiet",
        )],
        [InlineKeyboardButton(text=f"Minimal muhimlik: {imp}", callback_data="set:importance")],
        [InlineKeyboardButton(text=f"{trusted} Faqat ishonchli manbalar", callback_data="set:trusted")],
    ])


def confirm_reset_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, tozalansin", callback_data="reset:confirm"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="reset:cancel"),
    ]])


def admin_sources_keyboard(sources) -> InlineKeyboardMarkup:
    rows = []
    for s in sources[:50]:
        status = "🟢" if s.is_active else "🔴"
        err = " ⚠️" if s.last_error else ""
        rows.append([InlineKeyboardButton(
            text=f"{status} {s.name}{err}", callback_data=f"src:{s.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows or [[
        InlineKeyboardButton(text="Manbalar yo'q", callback_data="noop")
    ]])


def broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yuborish", callback_data="admin:broadcast_yes"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="admin:broadcast_no"),
    ]])
