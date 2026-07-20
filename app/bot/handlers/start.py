from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import categories_keyboard
from app.database.repositories.categories import get_all_categories
from app.database.repositories.users import get_enabled_category_ids, get_or_create_user

router = Router(name="start")

_WELCOME = (
    "👋 <b>Assalomu alaykum!</b>\n\n"
    "Men dunyo yangiliklarini siz uchun yig'ib, tahlil qilib, o'zbek tilida "
    "yetkazib beruvchi botman.\n\n"
    "📌 Kuzatadigan mavzularim:\n"
    "🪖 Urushlar va geosiyosat\n"
    "🌏 Markaziy Osiyo\n"
    "🤖 Robototexnika\n"
    "🛡 Mudofaa sanoati\n"
    "🧠 Sun'iy intellekt\n"
    "🌍 Global siyosat va iqtisod\n\n"
    "Har bir yangilik ostida baholash tugmalari bor — baholaringiz asosida "
    "men sizga mos yangiliklarni tanlab beraman.\n\n"
    "Quyida qiziqtirgan kategoriyalarni tanlang (barchasi yoqilgan holda boshlanadi). "
    "Boshqa sozlamalar uchun /settings, yordam uchun /help."
)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(
        session, message.from_user.id, message.from_user.username
    )
    categories = await get_all_categories(session)
    enabled = await get_enabled_category_ids(session, user)
    await message.answer(_WELCOME, reply_markup=categories_keyboard(categories, enabled))
