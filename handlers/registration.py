from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from database import upsert_user
from keyboards import (
    registration_phone_keyboard,
    language_inline_keyboard,
    main_menu_keyboard,
    accept_policy_keyboard,
)
from languages import t


router = Router()


class RegistrationStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_room = State()
    waiting_for_policy_accept = State()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(
        t(lang, "registration.welcome"),
        reply_markup=registration_phone_keyboard(lang),
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone(message: Message, state: FSMContext, lang: str) -> None:
    if not message.contact or not message.contact.phone_number:
        return
    await state.update_data(phone=message.contact.phone_number)
    await message.answer(t(lang, "registration.ask_room"))
    await state.set_state(RegistrationStates.waiting_for_room)


@router.message(RegistrationStates.waiting_for_room)
async def process_room(message: Message, state: FSMContext, lang: str) -> None:
    room = message.text.strip() if message.text else ""
    if not room:
        await message.answer(t(lang, "registration.please_enter_room"))
        return
    await state.update_data(room=room)

    # Отправляем сообщение с политикой и кнопкой "Принять"
    policy_text = t(lang, "registration.policy_message").format(
        link="https://karavan-group.com/otel-chekhov"  # ← заменить на реальную ссылку
    )
    await message.answer(
        policy_text,
        reply_markup=accept_policy_keyboard(lang),
        parse_mode='HTML',
        disable_web_page_preview=True,
    )
    await state.set_state(RegistrationStates.waiting_for_policy_accept)


@router.callback_query(RegistrationStates.waiting_for_policy_accept, F.data == "accept_policy")
async def process_policy_accept(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await callback.message.answer(t(lang, "registration.language_prompt"), reply_markup=language_inline_keyboard())
    await state.set_state(None)  # Переводим к выбору языка — дальше работает старый обработчик
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def process_language(callback: CallbackQuery, state: FSMContext) -> None:
    lang_code = callback.data.split(":", 1)[1]
    data = await state.get_data()
    phone = data.get("phone")
    room = data.get("room")
    if not phone or not room:
        await callback.answer()
        return
    await upsert_user(
        user_id=callback.from_user.id,
        phone=phone,
        room_number=room,
        language=lang_code,
    )
    await state.clear()
    await callback.message.answer(
        t(lang_code, "registration.registration_complete"),
        reply_markup=main_menu_keyboard(lang_code),
    )
    await callback.answer()

