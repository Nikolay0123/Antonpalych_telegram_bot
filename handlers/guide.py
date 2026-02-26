from typing import Set

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user
from keyboards import main_menu_keyboard
from languages import t, load_language
from utils.notifications import notify_reception


router = Router()


class GuideStates(StatesGroup):
    selecting_language = State()
    selecting_duration = State()
    selecting_type = State()
    entering_places = State()


def guide_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Русский", callback_data="guide_lang:ru"
                )
            ],
            [
                InlineKeyboardButton(
                    text="English", callback_data="guide_lang:en"
                )
            ],
            [
                InlineKeyboardButton(
                    text="中文", callback_data="guide_lang:zh"
                )
            ],
        ]
    )


def guide_duration_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="2 часа", callback_data="guide_dur:2"
                ),
                InlineKeyboardButton(
                    text="4 часа", callback_data="guide_dur:4"
                ),
                InlineKeyboardButton(
                    text="6 часов", callback_data="guide_dur:6"
                ),
            ]
        ]
    )


def guide_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Индивидуальная", callback_data="guide_type:individual"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Групповая", callback_data="guide_type:group"
                )
            ],
        ]
    )


def _guide_button_texts() -> Set[str]:
    texts: Set[str] = set()
    for code in ("ru", "en", "zh"):
        data = load_language(code)
        text = data.get("main_menu", {}).get("guide")
        if isinstance(text, str):
            texts.add(text)
    return texts


GUIDE_BUTTON_TEXTS = _guide_button_texts()


@router.message(F.text.in_(GUIDE_BUTTON_TEXTS))
async def guide_entry(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(GuideStates.selecting_language)
    await message.answer(
        t(lang, "guide.select_language"),
        reply_markup=guide_language_keyboard(),
    )


@router.callback_query(GuideStates.selecting_language, F.data.startswith("guide_lang:"))
async def select_language(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    guide_lang = callback.data.split(":", 1)[1]
    await state.update_data(guide_language=guide_lang)
    await state.set_state(GuideStates.selecting_duration)
    await callback.message.edit_text(
        t(lang, "guide.select_duration"), reply_markup=guide_duration_keyboard()
    )
    await callback.answer()


@router.callback_query(GuideStates.selecting_duration, F.data.startswith("guide_dur:"))
async def select_duration(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    duration = callback.data.split(":", 1)[1]
    await state.update_data(duration=duration)
    await state.set_state(GuideStates.selecting_type)
    await callback.message.edit_text(
        t(lang, "guide.select_type"), reply_markup=guide_type_keyboard()
    )
    await callback.answer()


@router.callback_query(GuideStates.selecting_type, F.data.startswith("guide_type:"))
async def select_type(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    type_ = callback.data.split(":", 1)[1]
    await state.update_data(type=type_)
    await state.set_state(GuideStates.entering_places)
    await callback.message.edit_text(t(lang, "guide.ask_places"))
    await callback.answer()


@router.message(GuideStates.entering_places)
async def enter_places(message: Message, state: FSMContext, lang: str) -> None:
    places = message.text or ""
    data = await state.get_data()
    user = await get_user(message.from_user.id)
    phone = user["phone"] if user else "-"
    room = user["room_number"] if user else "-"
    notify_text = (
        "🚶 ЗАЯВКА НА ГОРОДСКОГО ГИДА\n"
        f"Комната: {room}\n"
        f"Гость: {phone}\n"
        f"Язык гида: {data.get('guide_language')}\n"
        f"Длительность: {data.get('duration')} часов\n"
        f"Тип: {data.get('type')}\n"
        f"Предпочтительные места: {places}"
    )
    await notify_reception(message.bot, notify_text)
    await message.answer(
        t(lang, "guide.sent"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.clear()

