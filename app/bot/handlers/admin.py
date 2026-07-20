"""Admin komandalar: statistika, manbalar boshqaruvi, broadcast."""
from __future__ import annotations

import asyncio
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.filters.admin import IsAdmin
from app.bot.keyboards.inline import admin_sources_keyboard, broadcast_confirm_keyboard
from app.core.security import parse_callback
from app.database.models import DEFAULT_CATEGORIES
from app.database.repositories.categories import get_category_map
from app.database.repositories.deliveries import count_deliveries_today
from app.database.repositories.feedback import top_rated_categories
from app.database.repositories.sources import (
    add_source, get_all_sources, get_failing_sources, toggle_source,
)
from app.database.repositories.users import count_active_users, count_users, get_active_users

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Broadcast tasdiqlanishini kutayotgan matnlar: {admin_telegram_id: text}
_pending_broadcasts: dict[int, str] = {}


@router.message(Command("admin"))
async def cmd_admin(message: Message, session: AsyncSession) -> None:
    total = await count_users(session)
    active = await count_active_users(session)
    today = await count_deliveries_today(session)
    cat_map = await get_category_map(session)

    def _cat_names(rows) -> str:
        names = []
        for cat_id, cnt in rows:
            cat = cat_map.get(cat_id)
            if cat:
                names.append(f"{cat.name} ({cnt})")
        return ", ".join(names) or "—"

    liked = await top_rated_categories(session, positive=True)
    disliked = await top_rated_categories(session, positive=False)
    failing = await get_failing_sources(session)

    lines = [
        "🛠 <b>Admin panel</b>\n",
        f"👥 Foydalanuvchilar: {total} (faol: {active})",
        f"📨 Bugun yuborilgan: {today} ta",
        f"👍 Eng yoqqan: {_cat_names(liked)}",
        f"👎 Eng yoqmagan: {_cat_names(disliked)}",
    ]
    if failing:
        lines.append("\n⚠️ <b>Ishlamayotgan manbalar:</b>")
        for s in failing[:10]:
            lines.append(f"• {escape(s.name)}: {escape((s.last_error or '')[:80])}")
    lines.append(
        "\nKomandalar:\n"
        "/admin_sources — manbalarni yoqish/o'chirish\n"
        "/add_source nom | url | kategoriya — yangi RSS qo'shish\n"
        "/broadcast matn — barchaga xabar yuborish"
    )
    await message.answer("\n".join(lines))


@router.message(Command("admin_sources"))
async def cmd_admin_sources(message: Message, session: AsyncSession) -> None:
    sources = await get_all_sources(session)
    await message.answer(
        "📡 <b>Manbalar</b> (bosish — yoqish/o'chirish):",
        reply_markup=admin_sources_keyboard(sources),
    )


@router.callback_query(F.data.startswith("src:"))
async def on_source_toggle(query: CallbackQuery, session: AsyncSession) -> None:
    parsed = parse_callback(query.data)
    if not parsed or not parsed[1] or not parsed[1][0].isdigit():
        await query.answer("Noto'g'ri so'rov")
        return
    source = await toggle_source(session, int(parsed[1][0]))
    if source is None:
        await query.answer("Manba topilmadi")
        return
    sources = await get_all_sources(session)
    try:
        await query.message.edit_reply_markup(reply_markup=admin_sources_keyboard(sources))
    except Exception:
        pass
    await query.answer(f"{source.name}: {'🟢 yoqildi' if source.is_active else '🔴 o‘chirildi'}")


@router.message(Command("add_source"))
async def cmd_add_source(message: Message, command: CommandObject, session: AsyncSession) -> None:
    """Format: /add_source Nom | https://example.com/rss | ai"""
    if not command.args or command.args.count("|") < 2:
        slugs = ", ".join(DEFAULT_CATEGORIES)
        await message.answer(
            "Format: <code>/add_source Nom | URL | kategoriya</code>\n"
            f"Kategoriyalar: {slugs}"
        )
        return
    name, url, cat_slug = (p.strip() for p in command.args.split("|", 2))
    if not url.startswith(("http://", "https://")):
        await message.answer("URL http(s):// bilan boshlanishi kerak.")
        return
    cat_map = await get_category_map(session)
    category_id = next((c.id for c in cat_map.values() if c.slug == cat_slug), None)
    if category_id is None:
        await message.answer(f"Kategoriya topilmadi: {escape(cat_slug)}")
        return
    source = await add_source(session, name, url, category_id)
    await message.answer(f"✅ Manba qo'shildi: {escape(source.name)}")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("Format: <code>/broadcast xabar matni</code>")
        return
    _pending_broadcasts[message.from_user.id] = command.args
    await message.answer(
        f"📢 Quyidagi xabar <b>barcha faol foydalanuvchilarga</b> yuboriladi:\n\n"
        f"{escape(command.args)}\n\nTasdiqlaysizmi?",
        reply_markup=broadcast_confirm_keyboard(),
    )


@router.callback_query(F.data == "admin:broadcast_yes")
async def on_broadcast_confirm(query: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    text = _pending_broadcasts.pop(query.from_user.id, None)
    if not text:
        await query.answer("Kutilayotgan xabar yo'q")
        return
    await query.message.edit_text("📤 Yuborilmoqda...")
    users = await get_active_users(session)
    sent = failed = 0
    for user in users:
        try:
            await bot.send_message(user.telegram_id, f"📢 {escape(text)}")
            sent += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            failed += 1
        except TelegramForbiddenError:
            user.is_active = False
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await session.commit()
    await query.message.edit_text(f"✅ Yuborildi: {sent} ta, xato: {failed} ta")
    await query.answer()


@router.callback_query(F.data == "admin:broadcast_no")
async def on_broadcast_cancel(query: CallbackQuery) -> None:
    _pending_broadcasts.pop(query.from_user.id, None)
    await query.message.edit_text("Broadcast bekor qilindi.")
    await query.answer()
