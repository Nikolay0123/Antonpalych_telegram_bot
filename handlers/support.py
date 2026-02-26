from typing import Set

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from database import add_support_ticket, get_user, set_support_rating
from keyboards import main_menu_keyboard, urgency_keyboard, rating_keyboard
from languages import t, load_language
from utils.notifications import notify_reception


router = Router()


class SupportStates(StatesGroup):
    waiting_issue = State()
    waiting_urgency = State()


def _support_button_texts() -> Set[str]:
    texts: Set[str] = set()
    for code in ("ru", "en", "zh"):
        data = load_language(code)
        text = data.get("main_menu", {}).get("support")
        if isinstance(text, str):
            texts.add(text)
    return texts


SUPPORT_BUTTON_TEXTS = _support_button_texts()


@router.message(F.text.in_(SUPPORT_BUTTON_TEXTS))
async def support_entry(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(SupportStates.waiting_issue)
    await message.answer(t(lang, "support.describe"))


@router.message(SupportStates.waiting_issue)
async def support_issue(message: Message, state: FSMContext, lang: str) -> None:
    issue = message.text or ""
    await state.update_data(issue=issue)
    await state.set_state(SupportStates.waiting_urgency)
    await message.answer(
        t(lang, "support.urgency"), reply_markup=urgency_keyboard(lang)
    )


@router.callback_query(SupportStates.waiting_urgency, F.data.startswith("urgency:"))
async def support_urgency(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    urgency_code = callback.data.split(":", 1)[1]
    data = await state.get_data()
    issue = data["issue"]
    user = await get_user(callback.from_user.id)
    phone = user["phone"] if user else "-"
    room = user["room_number"] if user else "-"
    ticket_id = await add_support_ticket(
        user_id=callback.from_user.id, issue=issue, urgency=urgency_code
    )
    urgency_text_map = {
        "urgent": t(lang, "support.urgent"),
        "normal": t(lang, "support.normal"),
        "low": t(lang, "support.low"),
    }
    urgency_text = urgency_text_map.get(urgency_code, urgency_code)
    notify_text = (
        "🆘 НОВАЯ ПРОБЛЕМА\n"
        f"Комната: {room}\n"
        f"Гость: {phone}\n"
        f"Проблема: {issue}\n"
        f"Срочность: {urgency_text}\n"
        f"ID заявки: {ticket_id}"
    )
    await notify_reception(callback.bot, notify_text)
    await callback.message.edit_text(
        t(lang, "support.sent"),
        reply_markup=main_menu_keyboard(lang),
    )
    await callback.message.answer(t(lang, "rating.ask"), reply_markup=rating_keyboard())
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("rating:"))
async def support_rating(callback: CallbackQuery, lang: str) -> None:
    rating = int(callback.data.split(":", 1)[1])
    # Оцениваем последнюю заявку пользователя
    from aiosqlite import connect
    from config import settings

    async with connect(settings.database_path) as db:
        db.row_factory = lambda c, r: {"id": r[0]}
        async with db.execute(
            "SELECT id FROM support_tickets WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (callback.from_user.id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                await set_support_rating(row["id"], rating)
    await callback.message.answer(t(lang, "rating.thanks"))
    await callback.answer()

