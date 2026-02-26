import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Set

import requests
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import settings
from keyboards import main_menu_keyboard
from languages import t, load_language


router = Router()

HOTEL_INFO_PATH = Path("data") / "hotel_info.json"


class AIStates(StatesGroup):
    waiting_question = State()


def load_hotel_info() -> Dict[str, Any]:
    with HOTEL_INFO_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _ai_button_texts() -> Set[str]:
    texts: Set[str] = set()
    for code in ("ru", "en", "zh"):
        data = load_language(code)
        text = data.get("main_menu", {}).get("ai_assistant")
        if isinstance(text, str):
            texts.add(text)
    return texts


AI_BUTTON_TEXTS = _ai_button_texts()


async def ask_gemini(question: str, lang: str) -> str:
    """
    Вопрос к ИИ через OpenRouter (чат-completions).
    """
    api_key = settings.openrouter_api_key
    if not api_key:
        return ""

    hotel_info = load_hotel_info()
    system_prompt = (
        "You are a helpful hotel assistant for smart hotel 'Antonpalych'. "
        "Answer concisely in the user's language. Use only the hotel information provided. "
        "If the question is not covered by the data, say that you are not sure and suggest contacting reception.\n\n"
        f"Hotel data:\n{json.dumps(hotel_info, ensure_ascii=False, indent=2)}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"User language: {lang}\nUser question: {question}",
        },
    ]

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "HTTP-Referer": "https://t.me/Antonpalych_bot",
        "X-Title": "Antonpalych Hotel Bot",
    }
    payload = {
        "model": settings.openrouter_model or "google/gemini-2.0-flash-001",
        "messages": messages,
    }

    def _request() -> str:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message", {}) or {}
        content = message.get("content") or ""
        return str(content).strip()

    try:
        return await asyncio.to_thread(_request)
    except Exception:
        return ""


@router.message(F.text.in_(AI_BUTTON_TEXTS))
async def ai_start(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(AIStates.waiting_question)
    await message.answer(t(lang, "ai.ask"))


@router.message(AIStates.waiting_question, F.text)
async def ai_process_question(message: Message, state: FSMContext, lang: str) -> None:
    await message.answer(t(lang, "ai.thinking"))
    answer = await ask_gemini(message.text or "", lang)
    if not answer:
        answer = t(lang, "ai.fallback")
    await message.answer(answer, reply_markup=main_menu_keyboard(lang))
    await state.clear()

