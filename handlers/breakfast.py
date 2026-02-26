import json
from pathlib import Path
from typing import List, Set

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import add_breakfast_order, get_breakfast_orders, get_user, set_breakfast_rating
from keyboards import (
    dates_inline_keyboard,
    time_inline_keyboard,
    breakfast_menu_keyboard,
    main_menu_keyboard,
    rating_keyboard,
)
from languages import t, load_language
from utils.notifications import notify_reception
from utils.validators import validate_quantity


router = Router()

MENU_PATH = Path("data") / "menu_breakfast.json"


class BreakfastStates(StatesGroup):
    selecting_date = State()
    selecting_time = State()
    selecting_dishes = State()
    entering_quantity = State()


def load_menu() -> List[dict]:
    with MENU_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _breakfast_button_texts() -> Set[str]:
    texts: Set[str] = set()
    for code in ("ru", "en", "zh"):
        data = load_language(code)
        text = data.get("main_menu", {}).get("breakfast")
        if isinstance(text, str):
            texts.add(text)
    return texts


BREAKFAST_BUTTON_TEXTS = _breakfast_button_texts()


@router.message(F.text.in_(BREAKFAST_BUTTON_TEXTS))
async def breakfast_entry(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(BreakfastStates.selecting_date)
    await message.answer(
        t(lang, "breakfast.select_date"),
        reply_markup=dates_inline_keyboard(),
    )


@router.callback_query(BreakfastStates.selecting_date, F.data.startswith("date:"))
async def select_date(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    date_iso = callback.data.split(":", 1)[1]
    await state.update_data(date=date_iso)
    await state.set_state(BreakfastStates.selecting_time)
    await callback.message.edit_text(
        t(lang, "breakfast.select_time"),
        reply_markup=time_inline_keyboard(),
    )
    await callback.answer()


@router.callback_query(BreakfastStates.selecting_time, F.data.startswith("time:"))
async def select_time(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    time_str = callback.data.split(":", 1)[1]
    await state.update_data(time=time_str)
    await state.set_state(BreakfastStates.selecting_dishes)
    menu = load_menu()
    await callback.message.edit_text(
        t(lang, "breakfast.select_dish"),
        reply_markup=breakfast_menu_keyboard(lang, menu),
    )
    await callback.answer()


@router.callback_query(BreakfastStates.selecting_dishes, F.data.startswith("dish:"))
async def select_dish(callback: CallbackQuery, state: FSMContext) -> None:
    dish_id = callback.data.split(":", 1)[1]
    data = await state.get_data()
    dishes: List[str] = data.get("dishes", [])
    if dish_id not in dishes:
        dishes.append(dish_id)
    await state.update_data(dishes=dishes)
    await callback.answer()


@router.callback_query(BreakfastStates.selecting_dishes, F.data.startswith("dish_done:"))
async def done_dishes(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    dishes: List[str] = data.get("dishes", [])
    if not dishes:
        await callback.answer()
        return
    await state.set_state(BreakfastStates.entering_quantity)
    await callback.message.edit_text(t(lang, "breakfast.quantity"))
    await callback.answer()


@router.message(BreakfastStates.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext, lang: str) -> None:
    if not message.text or not validate_quantity(message.text):
        await message.answer(t(lang, "breakfast.invalid_quantity"))
        return
    quantity = int(message.text)
    data = await state.get_data()
    date_iso = data["date"]
    time_str = data["time"]
    dishes = data.get("dishes", [])
    order_id = await add_breakfast_order(
        user_id=message.from_user.id,
        date=date_iso,
        time=time_str,
        dishes=",".join(dishes),
        quantity=quantity,
    )
    user = await get_user(message.from_user.id)
    phone = user["phone"] if user else "-"
    room = user["room_number"] if user else "-"
    menu = load_menu()
    id_to_title = {item["id"]: item["name_ru"] for item in menu}
    dishes_titles = ", ".join(id_to_title.get(d, d) for d in dishes)
    notify_text = (
        "🍳 НОВЫЙ ЗАКАЗ ЗАВТРАКА\n"
        f"Комната: {room}\n"
        f"Гость: {phone}\n"
        f"Дата: {date_iso}\n"
        f"Время: {time_str}\n"
        f"Блюда: {dishes_titles}\n"
        f"Количество порций: {quantity}\n"
        f"ID заказа: {order_id}"
    )
    await notify_reception(message.bot, notify_text)
    await message.answer(
        t(lang, "breakfast.order_sent", time=time_str),
        reply_markup=main_menu_keyboard(lang),
    )
    await message.answer(t(lang, "rating.ask"), reply_markup=rating_keyboard())
    await state.clear()


@router.callback_query(F.data.startswith("rating:"))
async def set_rating(callback: CallbackQuery, lang: str) -> None:
    rating = int(callback.data.split(":", 1)[1])
    # В реальном проекте сюда лучше передавать конкретный объект (последний заказ),
    # здесь для простоты считаем, что оценивается последний заказ пользователя.
    orders = await get_breakfast_orders(callback.from_user.id)
    if orders:
        last_order_id = orders[0]["id"]
        await set_breakfast_rating(last_order_id, rating)
    await callback.message.answer(t(lang, "rating.thanks"))
    await callback.answer()

