from urllib.parse import urlencode

from aiogram import F, Router
from aiogram.types import Message

from config import settings
from database import get_user
from keyboards import bnovo_keyboard
from languages import t


router = Router()


@router.message()
async def open_bnovo(message: Message, lang: str) -> None:
    if message.text != t(lang, "main_menu.booking"):
        return
    user = await get_user(message.from_user.id)
    base_url = settings.bnovo_base_url.rstrip("/")
    params = {}
    if user:
        params["phone"] = user["phone"]
        params["room"] = user["room_number"]
    query = f"?{urlencode(params)}" if params else ""
    url = f"{base_url}{query}"
    await message.answer(
        t(lang, "booking.description"),
        reply_markup=bnovo_keyboard(lang, url),
    )

