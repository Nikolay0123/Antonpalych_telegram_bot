import json
from pathlib import Path
from typing import Set

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import get_user
from keyboards import (
    excursions_keyboard,
    dates_inline_keyboard,
    time_inline_keyboard,
    main_menu_keyboard,
)
from languages import t, load_language
from utils.notifications import notify_reception
from utils.validators import validate_quantity


router = Router()

EXC_PATH = Path("data") / "excursions.json"


class ExcursionStates(StatesGroup):
    selecting_excursion = State()
    selecting_date = State()
    selecting_time = State()
    entering_people = State()


def load_excursions():
    with EXC_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _excursions_button_texts() -> Set[str]:
    texts: Set[str] = set()
    for code in ("ru", "en", "zh"):
        data = load_language(code)
        text = data.get("main_menu", {}).get("excursions")
        if isinstance(text, str):
            texts.add(text)
    return texts


EXCURSIONS_BUTTON_TEXTS = _excursions_button_texts()


@router.message(F.text.in_(EXCURSIONS_BUTTON_TEXTS))
async def excursions_entry(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(ExcursionStates.selecting_excursion)
    excursions = load_excursions()
    await message.answer(
        t(lang, "excursions.select_excursion"),
        reply_markup=excursions_keyboard(lang, excursions),
    )


@router.callback_query(ExcursionStates.selecting_excursion, F.data.startswith("exc:"))
async def select_excursion(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    exc_id = callback.data.split(":", 1)[1]
    await state.update_data(excursion_id=exc_id)
    await state.set_state(ExcursionStates.selecting_date)
    await callback.message.edit_text(
        t(lang, "excursions.select_date"), reply_markup=dates_inline_keyboard()
    )
    await callback.answer()


@router.callback_query(ExcursionStates.selecting_date, F.data.startswith("date:"))
async def select_date(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    date_iso = callback.data.split(":", 1)[1]
    await state.update_data(date=date_iso)
    await state.set_state(ExcursionStates.selecting_time)
    await callback.message.edit_text(
        t(lang, "excursions.select_time"), reply_markup=time_inline_keyboard()
    )
    await callback.answer()


@router.callback_query(ExcursionStates.selecting_time, F.data.startswith("time:"))
async def select_time(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    time_str = callback.data.split(":", 1)[1]
    await state.update_data(time=time_str)
    await state.set_state(ExcursionStates.entering_people)
    await callback.message.edit_text(t(lang, "excursions.select_people"))
    await callback.answer()


@router.message(ExcursionStates.entering_people)
async def enter_people(message: Message, state: FSMContext, lang: str) -> None:
    if not message.text or not validate_quantity(message.text):
        await message.answer(t(lang, "errors.invalid_input"))
        return
    people = int(message.text)
    data = await state.get_data()
    user = await get_user(message.from_user.id)
    phone = user["phone"] if user else "-"
    room = user["room_number"] if user else "-"
    excursions = load_excursions()
    exc_map = {e["id"]: e for e in excursions}
    exc = exc_map.get(data["excursion_id"])
    if exc:
        title = exc["title_ru"]
    else:
        title = data["excursion_id"]
    notify_text = (
        "🏛️ НОВАЯ ЗАЯВКА НА ЭКСКУРСИЮ\n"
        f"Комната: {room}\n"
        f"Гость: {phone}\n"
        f"Экскурсия: {title}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Количество человек: {people}"
    )
    await notify_reception(message.bot, notify_text)
    await message.answer(
        t(lang, "excursions.sent"),
        reply_markup=main_menu_keyboard(lang),
    )
    await state.clear()

