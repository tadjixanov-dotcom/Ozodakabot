from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.users import get_or_create_user
from app.services.delivery import send_digest_now

router = Router(name="digest")


@router.message(Command("digest"))
async def cmd_digest(message: Message, session: AsyncSession, bot: Bot) -> None:
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await message.answer("🔎 Siz uchun eng muhim yangiliklarni tanlayapman...")
    sent = await send_digest_now(bot, session, user)
    if sent == 0:
        await message.answer(
            "📭 Hozircha sizga mos yangi yangiliklar yo'q yoki kunlik limitingiz tugagan.\n"
            "Keyinroq qayta urinib ko'ring yoki /settings orqali limitni oshiring."
        )
