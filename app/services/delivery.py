"""Yangiliklarni foydalanuvchilarga yetkazish: real-time, dayjest, limitlar, retry."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.bot.keyboards.inline import article_keyboard
from app.database.models import Article, User, utcnow
from app.database.repositories.articles import get_undelivered_for_user
from app.database.repositories.categories import get_category_map
from app.database.repositories.deliveries import count_deliveries_since, record_delivery, was_delivered
from app.database.repositories.feedback import get_feedback_articles, get_or_create_profile
from app.database.repositories.sources import get_source
from app.database.repositories.users import get_active_users, get_enabled_category_ids
from app.recommendations.scoring import ScoredArticle, rank_articles
from app.services.formatter import format_article_message


def _user_local_now(user: User) -> datetime:
    try:
        tz = ZoneInfo(user.timezone)
    except Exception:
        tz = ZoneInfo("Asia/Tashkent")
    return datetime.now(timezone.utc).astimezone(tz)


def in_quiet_hours(user: User, now_local: datetime | None = None) -> bool:
    """Tungi jim rejim tekshiruvi (masalan 23:00 – 07:00)."""
    if not user.quiet_hours_enabled:
        return False
    now_local = now_local or _user_local_now(user)
    hour = now_local.hour
    start, end = user.quiet_hours_start, user.quiet_hours_end
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end  # yarim tundan oshib o'tadigan oraliq


async def _limits_ok(session: AsyncSession, user: User) -> bool:
    settings = get_settings()
    hourly = await count_deliveries_since(session, user.id, hours=1)
    if hourly >= settings.max_messages_per_hour:
        return False
    daily = await count_deliveries_since(session, user.id, hours=24)
    return daily < user.daily_limit


async def _disliked_keyword_sets(session: AsyncSession, user: User) -> list[set[str]]:
    disliked = await get_feedback_articles(session, user.id, ["dislike", "less_topic"])
    return [set(a.keywords or []) for a in disliked if a.keywords]


async def pick_articles_for_user(
    session: AsyncSession, user: User, limit: int
) -> list[ScoredArticle]:
    """Foydalanuvchi uchun eng mos yangiliklarni tanlaydi (tavsiya algoritmi bilan)."""
    category_ids = await get_enabled_category_ids(session, user)
    candidates = await get_undelivered_for_user(
        session, user.id, category_ids,
        min_importance=user.minimum_importance,
        trusted_only=user.trusted_only,
    )
    if not candidates:
        return []
    profile = await get_or_create_profile(session, user.id)
    disliked_sets = await _disliked_keyword_sets(session, user)
    cat_map = await get_category_map(session)
    slugs = {cid: c.slug for cid, c in cat_map.items()}
    return rank_articles(candidates, profile, disliked_sets, slugs, limit)


async def send_article_to_user(
    bot: Bot, session: AsyncSession, user: User, scored: ScoredArticle
) -> bool:
    """Bitta maqolani yuboradi: format, tugmalar, retry/backoff, delivery yozuvi."""
    article = scored.article
    if await was_delivered(session, user.id, article.id):
        return False

    source = await get_source(session, article.source_id)
    cat_map = await get_category_map(session)
    category = cat_map.get(article.category_id or -1)

    text = format_article_message(
        article,
        source_name=source.name if source else "Noma'lum",
        category_name=category.name if category else "Boshqa",
        category_slug=category.slug if category else "",
        tz_name=user.timezone,
        critical=scored.critical_override,
    )
    keyboard = article_keyboard(article.id, article.category_id or 0, article.url)

    for attempt in range(3):
        try:
            msg = await bot.send_message(
                chat_id=user.telegram_id, text=text,
                reply_markup=keyboard, disable_web_page_preview=False,
            )
            await record_delivery(session, user.id, article.id, msg.message_id)
            return True
        except TelegramRetryAfter as exc:
            # Telegram rate limit — kutib qayta urinamiz (exponential backoff bilan)
            await asyncio.sleep(exc.retry_after + 2 ** attempt)
        except TelegramForbiddenError:
            # Foydalanuvchi botni blokladi
            user.is_active = False
            await session.commit()
            logger.info("Foydalanuvchi {} botni bloklagan — deaktiv", user.telegram_id)
            return False
        except TelegramBadRequest as exc:
            logger.error("Xabar yuborilmadi (user={}): {}", user.telegram_id, exc)
            await record_delivery(session, user.id, article.id, None, status="failed")
            return False
    return False


async def deliver_realtime(bot: Bot, session_factory: async_sessionmaker) -> None:
    """Favqulodda muhim yangiliklarni realtime/mixed rejimdagilarga yuboradi.

    Har siklda foydalanuvchiga ko'pi bilan BITTA xabar — qolganlarini
    "➡️ Keyingi yangilik" tugmasi orqali o'zi so'rab oladi.
    """
    settings = get_settings()
    async with session_factory() as session:
        users = await get_active_users(session)
        for user in users:
            if user.delivery_mode not in ("realtime", "mixed"):
                continue
            if in_quiet_hours(user) or not await _limits_ok(session, user):
                continue
            picked = await pick_articles_for_user(session, user, limit=3)
            urgent = [
                s for s in picked
                if s.article.importance_score >= settings.realtime_importance_threshold
                or s.critical_override
            ]
            # realtime rejimda oddiy yangiliklar ham boradi, mixed'da faqat favqulodda
            to_send = picked if user.delivery_mode == "realtime" else urgent
            if to_send:
                await send_article_to_user(bot, session, user, to_send[0])
                await asyncio.sleep(0.1)  # global rate limitga hurmat


def _digest_due(user: User, interval_minutes: int) -> bool:
    """Foydalanuvchining dayjest vaqti kelganmi (oxirgi tekshiruv oynasida)."""
    now_local = _user_local_now(user)
    for slot in (s.strip() for s in (user.digest_times or "").split(",")):
        if not slot or ":" not in slot:
            continue
        try:
            h, m = int(slot.split(":")[0]), int(slot.split(":")[1])
        except ValueError:
            continue
        slot_dt = now_local.replace(hour=h, minute=m, second=0, microsecond=0)
        delta = (now_local - slot_dt).total_seconds() / 60
        if 0 <= delta < interval_minutes:
            # Shu slot uchun allaqachon yuborilganmi
            if user.last_digest_at is not None:
                slot_utc = slot_dt.astimezone(timezone.utc).replace(tzinfo=None)
                if user.last_digest_at >= slot_utc:
                    return False
            return True
    return False


async def deliver_digests(bot: Bot, session_factory: async_sessionmaker) -> None:
    """Rejalashtirilgan dayjestlarni tekshiradi va yuboradi."""
    settings = get_settings()
    async with session_factory() as session:
        users = await get_active_users(session)
        for user in users:
            if user.delivery_mode not in ("digest", "mixed"):
                continue
            if not _digest_due(user, settings.digest_check_interval_minutes):
                continue
            if in_quiet_hours(user):
                continue
            sent = await send_digest_now(bot, session, user)
            if sent:
                user.last_digest_at = utcnow()
                await session.commit()


async def send_digest_now(bot: Bot, session: AsyncSession, user: User) -> int:
    """Foydalanuvchiga eng mos BITTA yangilikni yuboradi (qolganini
    "➡️ Keyingi yangilik" tugmasi bilan o'zi oladi). Yuborilgan sonni qaytaradi."""
    remaining = max(0, user.daily_limit - await count_deliveries_since(session, user.id, 24))
    if remaining == 0:
        return 0
    picked = await pick_articles_for_user(session, user, limit=1)
    if picked and await send_article_to_user(bot, session, user, picked[0]):
        return 1
    return 0


async def send_next_article(bot: Bot, session: AsyncSession, user: User) -> bool:
    """"➡️ Keyingi yangilik" tugmasi uchun: navbatdagi eng mos yangilikni yuboradi.

    Foydalanuvchi o'zi so'ragani uchun jim rejim va limitlar tekshirilmaydi.
    """
    picked = await pick_articles_for_user(session, user, limit=1)
    if not picked:
        return False
    return await send_article_to_user(bot, session, user, picked[0])
