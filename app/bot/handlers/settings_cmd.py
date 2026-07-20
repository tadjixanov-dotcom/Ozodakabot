from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import settings_keyboard
from app.core.security import parse_callback
from app.database.repositories.users import get_or_create_user

router = Router(name="settings")

_MODES = ["mixed", "realtime", "digest"]
_LIMITS = [5, 10, 20, 30]
_IMPORTANCES = [0.0, 0.3, 0.5, 0.7]
_TIMES = ["08:00", "08:00,20:00", "08:00,13:00,20:00"]

_TEXT = (
    "⚙️ <b>Sozlamalar</b>\n\n"
    "• <b>Rejim</b>: real-time (darhol), dayjest (belgilangan vaqtda) yoki aralash\n"
    "• <b>Kunlik limit</b>: kuniga maksimal yangiliklar soni\n"
    "• <b>Jim rejim</b>: tunda xabar yubormaslik\n"
    "• <b>Minimal muhimlik</b>: faqat shu darajadan muhim yangiliklar\n"
)


@router.message(Command("settings"))
async def cmd_settings(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await message.answer(_TEXT, reply_markup=settings_keyboard(user))


def _cycle(values: list, current) -> object:
    try:
        idx = values.index(current)
    except ValueError:
        return values[0]
    return values[(idx + 1) % len(values)]


@router.callback_query(F.data.startswith("set:"))
async def on_setting_change(query: CallbackQuery, session: AsyncSession) -> None:
    parsed = parse_callback(query.data)
    if not parsed or not parsed[1]:
        await query.answer("Noto'g'ri so'rov")
        return
    action = parsed[1][0]
    user = await get_or_create_user(session, query.from_user.id, query.from_user.username)

    if action == "mode":
        user.delivery_mode = _cycle(_MODES, user.delivery_mode)
    elif action == "limit":
        user.daily_limit = _cycle(_LIMITS, user.daily_limit)
    elif action == "times":
        user.digest_times = _cycle(_TIMES, user.digest_times)
    elif action == "quiet":
        user.quiet_hours_enabled = not user.quiet_hours_enabled
    elif action == "importance":
        user.minimum_importance = _cycle(_IMPORTANCES, round(user.minimum_importance, 1))
    elif action == "trusted":
        user.trusted_only = not user.trusted_only
    else:
        await query.answer("Noma'lum sozlama")
        return

    await session.commit()
    try:
        await query.message.edit_reply_markup(reply_markup=settings_keyboard(user))
    except Exception:
        pass
    await query.answer("Saqlandi ✅")
