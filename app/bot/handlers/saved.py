from __future__ import annotations

from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.feedback import get_saved_articles
from app.database.repositories.users import get_or_create_user

router = Router(name="saved")


@router.message(Command("saved"))
async def cmd_saved(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
    articles = await get_saved_articles(session, user.id)
    if not articles:
        await message.answer("📌 Saqlangan yangiliklar yo'q. Xabar ostidagi 📌 tugmasi bilan saqlang.")
        return
    lines = ["📌 <b>Saqlangan yangiliklar</b>\n"]
    for i, a in enumerate(articles, 1):
        url = escape(a.url, quote=True)
        lines.append(f"{i}. <a href=\"{url}\">{escape(a.display_title)}</a>")
    await message.answer("\n".join(lines), disable_web_page_preview=True)
