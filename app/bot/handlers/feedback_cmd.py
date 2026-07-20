from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import confirm_reset_keyboard
from app.database.repositories.feedback import (
    feedback_stats, get_or_create_profile, reset_preferences,
)
from app.database.repositories.users import get_or_create_user

router = Router(name="feedback_cmd")

_TYPE_LABELS = {
    "dislike": "👎 Yoqmadi", "neutral": "😐 Oddiy", "like": "👍 Yoqdi",
    "love": "🔥 Juda qiziq", "less_topic": "🚫 Kamroq ko'rsat",
}


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    stats = await feedback_stats(session, user.id)
    profile = await get_or_create_profile(session, user.id)

    lines = ["📊 <b>Sizning baholaringiz</b>\n"]
    if stats:
        for ftype, label in _TYPE_LABELS.items():
            if ftype in stats:
                lines.append(f"{label}: {stats[ftype]} ta")
    else:
        lines.append("Hali baho bermagansiz.")

    top_pos = sorted((profile.positive_keywords or {}).items(), key=lambda x: -x[1])[:7]
    top_neg = sorted((profile.negative_keywords or {}).items(), key=lambda x: -x[1])[:7]
    if top_pos:
        lines.append("\n✅ <b>Sizga yoqadigan mavzular:</b>")
        lines.append(", ".join(escape(k) for k, _ in top_pos))
    if top_neg:
        lines.append("\n🚫 <b>Kamroq ko'rsatiladigan mavzular:</b>")
        lines.append(", ".join(escape(k) for k, _ in top_neg))

    lines.append("\nTarixni tozalash: /reset_preferences")
    await message.answer("\n".join(lines))


@router.message(Command("reset_preferences"))
async def cmd_reset(message: Message) -> None:
    await message.answer(
        "⚠️ Barcha baholaringiz va tavsiya tarixi o'chiriladi. Tasdiqlaysizmi?",
        reply_markup=confirm_reset_keyboard(),
    )


@router.callback_query(F.data == "reset:confirm")
async def on_reset_confirm(query: CallbackQuery, session: AsyncSession) -> None:
    user = await get_or_create_user(session, query.from_user.id, query.from_user.username)
    await reset_preferences(session, user.id)
    await query.message.edit_text("🧹 Tavsiya tarixi tozalandi. Yangi baholar asosida qayta o'rganaman.")
    await query.answer()


@router.callback_query(F.data == "reset:cancel")
async def on_reset_cancel(query: CallbackQuery) -> None:
    await query.message.edit_text("Bekor qilindi. Baholaringiz saqlanib qoldi. ✅")
    await query.answer()
