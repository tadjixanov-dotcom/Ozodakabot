"""Yangilik xabari ostidagi tugmalar uchun callback handlerlar."""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import parse_callback
from app.database.repositories.articles import get_article
from app.database.repositories.feedback import save_article, upsert_feedback
from app.database.repositories.users import get_or_create_user, set_user_category
from app.recommendations.profile_builder import update_profile_on_feedback
from app.services.delivery import send_next_article

router = Router(name="callbacks")

_FEEDBACK_REPLIES = {
    "dislike": "Bahoyingiz saqlandi. Tavsiyalar yangilanadi. 👌",
    "neutral": "Bahoyingiz saqlandi.",
    "like": "Bahoyingiz saqlandi. Shunga o'xshash yangiliklar ko'payadi. 👍",
    "love": "Ajoyib! Bunday yangiliklar ko'proq bo'ladi. 🔥",
}


@router.callback_query(F.data.startswith("fb:"))
async def on_feedback(query: CallbackQuery, session: AsyncSession) -> None:
    parsed = parse_callback(query.data)
    if not parsed or len(parsed[1]) != 2 or not parsed[1][0].isdigit():
        await query.answer("Noto'g'ri so'rov")
        return
    article_id, ftype = int(parsed[1][0]), parsed[1][1]
    if ftype not in _FEEDBACK_REPLIES:
        await query.answer("Noto'g'ri baho turi")
        return

    article = await get_article(session, article_id)
    if article is None:
        await query.answer("Yangilik topilmadi")
        return

    user = await get_or_create_user(session, query.from_user.id, query.from_user.username)
    await upsert_feedback(session, user.id, article_id, ftype)
    await update_profile_on_feedback(session, user.id, article, ftype)
    await query.answer(_FEEDBACK_REPLIES[ftype])


@router.callback_query(F.data.startswith("less:"))
async def on_less_topic(query: CallbackQuery, session: AsyncSession) -> None:
    parsed = parse_callback(query.data)
    if not parsed or not parsed[1] or not parsed[1][0].isdigit():
        await query.answer("Noto'g'ri so'rov")
        return
    article_id = int(parsed[1][0])
    article = await get_article(session, article_id)
    if article is None:
        await query.answer("Yangilik topilmadi")
        return

    user = await get_or_create_user(session, query.from_user.id, query.from_user.username)
    await upsert_feedback(session, user.id, article_id, "less_topic")
    await update_profile_on_feedback(session, user.id, article, "less_topic")
    await query.answer("Bu mavzudagi yangiliklar kamaytiriladi. 🚫")


@router.callback_query(F.data.startswith("save:"))
async def on_save(query: CallbackQuery, session: AsyncSession) -> None:
    parsed = parse_callback(query.data)
    if not parsed or not parsed[1] or not parsed[1][0].isdigit():
        await query.answer("Noto'g'ri so'rov")
        return
    article_id = int(parsed[1][0])
    user = await get_or_create_user(session, query.from_user.id, query.from_user.username)
    created = await save_article(session, user.id, article_id)
    await query.answer("📌 Saqlandi. /saved bilan ko'ring." if created else "Allaqachon saqlangan.")


@router.callback_query(F.data.startswith("mutecat:"))
async def on_mute_category(query: CallbackQuery, session: AsyncSession) -> None:
    parsed = parse_callback(query.data)
    if not parsed or not parsed[1] or not parsed[1][0].isdigit():
        await query.answer("Noto'g'ri so'rov")
        return
    category_id = int(parsed[1][0])
    if category_id <= 0:
        await query.answer("Kategoriya topilmadi")
        return
    user = await get_or_create_user(session, query.from_user.id, query.from_user.username)
    await set_user_category(session, user, category_id, enabled=False)
    await query.answer("🔕 Kategoriya o'chirildi. Qayta yoqish: /categories")


@router.callback_query(F.data.startswith("next:"))
async def on_next_article(query: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """"➡️ Keyingi yangilik" — navbatdagi eng mos yangilikni yuboradi."""
    user = await get_or_create_user(session, query.from_user.id, query.from_user.username)
    sent = await send_next_article(bot, session, user)
    if sent:
        await query.answer()
    else:
        await query.answer(
            "📭 Hozircha boshqa yangi yangilik yo'q. Keyinroq urinib ko'ring.",
            show_alert=False,
        )


@router.callback_query(F.data == "noop")
async def on_noop(query: CallbackQuery) -> None:
    await query.answer()
