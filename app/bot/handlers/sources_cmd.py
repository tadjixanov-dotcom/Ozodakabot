from __future__ import annotations

from html import escape

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DEFAULT_CATEGORIES
from app.database.repositories.categories import get_category_map
from app.database.repositories.sources import get_active_sources

router = Router(name="sources")


@router.message(Command("sources"))
async def cmd_sources(message: Message, session: AsyncSession) -> None:
    sources = await get_active_sources(session)
    cat_map = await get_category_map(session)

    grouped: dict[str, list[str]] = {}
    for s in sources:
        cat = cat_map.get(s.category_id or -1)
        slug = cat.slug if cat else "other"
        grouped.setdefault(slug, []).append(s.name)

    lines = ["📰 <b>Yangilik manbalari</b>\n"]
    for slug, names in grouped.items():
        name, emoji = DEFAULT_CATEGORIES.get(slug, ("Boshqa", "📰"))
        lines.append(f"{emoji} <b>{escape(name)}</b>: {escape(', '.join(names))}")
    lines.append("\nBot maqolalarning to'liq matnini nusxalamaydi — faqat sarlavha, "
                 "qisqa mazmun va original havola yuboriladi.")
    await message.answer("\n".join(lines))
