from urllib.parse import urlencode
from typing import Set

from aiogram import F, Router
from aiogram.types import Message

from config import settings
from database import get_user
from keyboards import get_booking_button
from languages import t, load_language


router = Router()


@router.message(F.text.contains("Забронировать") | F.text.contains("Booking") | F.text.contains("预订"))
async def booking_handler(message: Message, lang: str):
    """Обработчик нажатия на кнопку бронирования"""
    await message.answer(
        "🔗 Нажмите кнопку ниже, чтобы перейти на сайт бронирования:\n\n"
        "💡 *Совет:* Сайт откроется прямо в Telegram, не закрывайте бота!",
        reply_markup=get_booking_button(lang),
        parse_mode="Markdown"
    )



