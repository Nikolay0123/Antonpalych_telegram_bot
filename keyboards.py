from datetime import date, timedelta
from typing import List

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from languages import t


def registration_phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=t(lang, "registration.phone_button"),
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "main_menu.breakfast"))],
            [KeyboardButton(text=t(lang, "main_menu.excursions"))],
            [KeyboardButton(text=t(lang, "main_menu.guide"))],
            [KeyboardButton(text=t(lang, "main_menu.booking"))],
            [KeyboardButton(text=t(lang, "main_menu.support"))],
            [KeyboardButton(text=t(lang, "main_menu.linen"))],
            [KeyboardButton(text=t(lang, "main_menu.ai_assistant"))],
        ],
        resize_keyboard=True,
    )


def language_inline_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            InlineKeyboardButton(text="🇨🇳 中文", callback_data="lang:zh"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def dates_inline_keyboard(days: int = 7) -> InlineKeyboardMarkup:
    today = date.today()
    rows: List[List[InlineKeyboardButton]] = []
    for i in range(days):
        d = today + timedelta(days=i)
        rows.append(
            [
                InlineKeyboardButton(
                    text=d.strftime("%d.%m"),
                    callback_data=f"date:{d.isoformat()}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def time_inline_keyboard() -> InlineKeyboardMarkup:
    times = ["07:00", "08:00", "09:00", "10:00"]
    rows = [
        [InlineKeyboardButton(text=t_, callback_data=f"time:{t_}")] for t_ in times
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def breakfast_menu_keyboard(lang: str, items: List[dict]) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for item in items:
        if lang == "ru":
            title = item["name_ru"]
        elif lang == "zh":
            title = item["name_zh"]
        else:
            title = item["name_en"]
        rows.append(
            [
                InlineKeyboardButton(
                    text=title, callback_data=f"dish:{item['id']}"
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="✅ OK", callback_data="dish_done:1")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def excursions_keyboard(lang: str, excursions: List[dict]) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []
    for ex in excursions:
        if lang == "ru":
            title = ex["title_ru"]
        elif lang == "zh":
            title = ex["title_zh"]
        else:
            title = ex["title_en"]
        rows.append(
            [InlineKeyboardButton(text=title, callback_data=f"exc:{ex['id']}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def urgency_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "support.urgent"), callback_data="urgency:urgent"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "support.normal"), callback_data="urgency:normal"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "support.low"), callback_data="urgency:low"
                )
            ],
        ]
    )


def linen_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "linen.towels"), callback_data="linen:towels"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "linen.bedding"), callback_data="linen:bedding"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "linen.both"), callback_data="linen:both"
                )
            ],
        ]
    )


def rating_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=str(i), callback_data=f"rating:{i}")
            for i in range(1, 6)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bnovo_keyboard(lang: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "booking.open_bnovo"),
                    url=url,
                )
            ]
        ]
    )

