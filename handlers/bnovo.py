from urllib.parse import urlencode
from typing import Set

from aiogram import F, Router
from aiogram.types import Message

from config import settings
from database import get_user
from keyboards import bnovo_keyboard
from languages import t, load_language


router = Router()


def _booking_button_texts() -> Set[str]:
    texts: Set[str] = set()
    for code in ("ru", "en", "zh"):
        data = load_language(code)
        text = data.get("main_menu", {}).get("booking")
        if isinstance(text, str):
            texts.add(text)
    return texts


BOOKING_BUTTON_TEXTS = _booking_button_texts()


@router.message(F.text.in_(BOOKING_BUTTON_TEXTS))
async def open_bnovo(message: Message, lang: str) -> None:
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

