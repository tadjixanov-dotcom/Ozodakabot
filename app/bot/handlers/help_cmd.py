from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

_HELP = (
    "ℹ️ <b>Yordam</b>\n\n"
    "<b>Komandalar:</b>\n"
    "/start — botni ishga tushirish\n"
    "/categories — kategoriyalarni yoqish/o'chirish\n"
    "/settings — rejim, limit, vaqt sozlamalari\n"
    "/digest — hozir dayjest olish\n"
    "/saved — saqlangan yangiliklar\n"
    "/feedback — baholaringiz va qiziqishlaringiz\n"
    "/reset_preferences — tavsiya tarixini tozalash\n"
    "/sources — yangilik manbalari\n"
    "/help — shu yordam\n\n"
    "<b>Baholash tugmalari:</b>\n"
    "👎 Yoqmadi — shunga o'xshash yangiliklar kamayadi\n"
    "😐 Oddiy — neytral\n"
    "👍 Yoqdi — shunga o'xshashlar ko'payadi\n"
    "🔥 Juda qiziq — kuchli ijobiy signal\n"
    "🚫 Kamroq ko'rsat — mavzu deyarli ko'rinmaydi\n"
    "🔕 Kategoriya — butun kategoriyani o'chiradi\n"
    "📌 Saqlash — keyinroq o'qish uchun\n\n"
    "<b>Rejimlar:</b>\n"
    "⚡ Real-time — yangiliklar topilishi bilan darhol\n"
    "🗞 Dayjest — belgilangan vaqtlarda to'plam\n"
    "🔀 Aralash — favqulodda muhimlari darhol, qolgani dayjestda"
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(_HELP)
