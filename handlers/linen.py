from typing import Set

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import add_linen_request, get_user, set_linen_rating
from keyboards import linen_type_keyboard, main_menu_keyboard, rating_keyboard
from languages import t, load_language
from utils.notifications import notify_reception
from utils.validators import validate_quantity


router = Router()


class LinenStates(StatesGroup):
    selecting_type = State()
    entering_quantity = State()
    entering_time = State()


def _linen_button_texts() -> Set[str]:
    texts: Set[str] = set()
    for code in ("ru", "en", "zh"):
        data = load_language(code)
        text = data.get("main_menu", {}).get("linen")
        if isinstance(text, str):
            texts.add(text)
    return texts


LINEN_BUTTON_TEXTS = _linen_button_texts()


@router.message(F.text.in_(LINEN_BUTTON_TEXTS))
async def linen_entry(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(LinenStates.selecting_type)
    await message.answer(
        t(lang, "linen.type"),
        reply_markup=linen_type_keyboard(lang),
    )


@router.callback_query(LinenStates.selecting_type, F.data.startswith("linen:"))
async def linen_type(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    type_code = callback.data.split(":", 1)[1]
    await state.update_data(type=type_code)
    await state.set_state(LinenStates.entering_quantity)
    await callback.message.edit_text(t(lang, "linen.quantity"))
    await callback.answer()


@router.message(LinenStates.entering_quantity)
async def linen_quantity(message: Message, state: FSMContext, lang: str) -> None:
    if not message.text or not validate_quantity(message.text):
        await message.answer(t(lang, "errors.invalid_input"))
        return
    await state.update_data(quantity=int(message.text))
    await state.set_state(LinenStates.entering_time)
    await message.answer(t(lang, "linen.time"))


@router.message(LinenStates.entering_time)
async def linen_time(message: Message, state: FSMContext, lang: str) -> None:
    preferred_time = message.text or ""
    data = await state.get_data()
    user = await get_user(message.from_user.id)
    phone = user["phone"] if user else "-"
    room = user["room_number"] if user else "-"
    request_id = await add_linen_request(
        user_id=message.from_user.id,
        type_=data["type"],
        quantity=data["quantity"],
        preferred_time=preferred_time,
    )
    type_map = {
        "towels": t(lang, "linen.towels"),
        "bedding": t(lang, "linen.bedding"),
        "both": t(lang, "linen.both"),
    }
    type_text = type_map.get(data["type"], data["type"])
    notify_text = (
        "🧺 ЗАЯВКА НА СМЕНУ БЕЛЬЯ\n"
        f"Комната: {room}\n"
        f"Гость: {phone}\n"
        f"Тип: {type_text}\n"
        f"Количество комплектов: {data['quantity']}\n"
        f"Время: {preferred_time}\n"
        f"ID заявки: {request_id}"
    )
    await notify_reception(message.bot, notify_text)
    await message.answer(
        t(lang, "linen.sent"),
        reply_markup=main_menu_keyboard(lang),
    )
    await message.answer(t(lang, "rating.ask"), reply_markup=rating_keyboard())
    await state.clear()


@router.callback_query(F.data.startswith("rating:"))
async def linen_rating(callback: CallbackQuery, lang: str) -> None:
    rating = int(callback.data.split(":", 1)[1])
    from aiosqlite import connect
    from config import settings

    async with connect(settings.database_path) as db:
        db.row_factory = lambda c, r: {"id": r[0]}
        async with db.execute(
            "SELECT id FROM linen_requests WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (callback.from_user.id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                await set_linen_rating(row["id"], rating)
    await callback.message.answer(t(lang, "rating.thanks"))
    await callback.answer()

