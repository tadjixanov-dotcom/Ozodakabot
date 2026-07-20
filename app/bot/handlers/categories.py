from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import categories_keyboard
from app.core.security import parse_callback
from app.database.repositories.categories import get_all_categories
from app.database.repositories.users import (
    get_enabled_category_ids, get_or_create_user, toggle_user_category,
)

router = Router(name="categories")


@router.message(Command("categories"))
async def cmd_categories(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    categories = await get_all_categories(session)
    enabled = await get_enabled_category_ids(session, user)
    await message.answer(
        "📂 <b>Kategoriyalar</b>\n\nYoqish/o'chirish uchun bosing:",
        reply_markup=categories_keyboard(categories, enabled),
    )


@router.callback_query(F.data.startswith("cat:"))
async def on_category_toggle(query: CallbackQuery, session: AsyncSession) -> None:
    parsed = parse_callback(query.data)
    if not parsed or not parsed[1] or not parsed[1][0].isdigit():
        await query.answer("Noto'g'ri so'rov")
        return
    category_id = int(parsed[1][0])
    user = await get_or_create_user(session, query.from_user.id, query.from_user.username)
    enabled = await toggle_user_category(session, user, category_id)

    categories = await get_all_categories(session)
    enabled_ids = await get_enabled_category_ids(session, user)
    try:
        await query.message.edit_reply_markup(
            reply_markup=categories_keyboard(categories, enabled_ids)
        )
    except Exception:
        pass  # xabar o'zgarmagan bo'lishi mumkin
    await query.answer("✅ Yoqildi" if enabled else "🔕 O'chirildi")
