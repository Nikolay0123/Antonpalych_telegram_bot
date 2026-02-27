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
    """Получаем описание проблемы и сразу отправляем без выбора срочности"""
    issue = message.text or ""

    # Получаем данные пользователя
    user = await get_user(message.from_user.id)
    phone = user["phone"] if user else "-"
    room = user["room_number"] if user else "-"

    # Создаем заявку (без срочности или со стандартной)
    ticket_id = await add_support_ticket(
        user_id=message.from_user.id,
        issue=issue,
        urgency="normal"  # Ставим срочность "обычная" по умолчанию
    )

    # Отправляем уведомление персоналу
    notify_text = (
        "🆘 НОВАЯ ПРОБЛЕМА\n"
        f"Комната: {room}\n"
        f"Гость: {phone}\n"
        f"Проблема: {issue}\n"
        f"ID заявки: {ticket_id}"
    )
    await notify_reception(message.bot, notify_text)

    await message.answer(
        "✨ Спасибо за обращение! Мы уже работаем над Вашей заявкой!\n\n"
        "Сотрудник отеля свяжется с вами в ближайшее время.",
        reply_markup=main_menu_keyboard(lang),
    )



    # Спрашиваем оценку
    await message.answer(t(lang, "rating.ask"), reply_markup=rating_keyboard())

    await state.clear()


@router.callback_query(F.data.startswith("rating:"))
async def support_rating(callback: CallbackQuery, lang: str) -> None:
    """Обработка оценки поддержки"""
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


