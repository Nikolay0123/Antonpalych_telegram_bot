import asyncio
import json
from pathlib import Path
from typing import Any, Dict

import requests
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import settings
from keyboards import main_menu_keyboard
from languages import t


router = Router()

HOTEL_INFO_PATH = Path("data") / "hotel_info.json"


class AIStates(StatesGroup):
    waiting_question = State()


def load_hotel_info() -> Dict[str, Any]:
    with HOTEL_INFO_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


async def ask_gemini(question: str, lang: str) -> str:
    hotel_info = load_hotel_info()
    system_prompt = (
        "You are a helpful hotel assistant for hotel 'Antonpalych'. "
        "Answer in the user's language. Use only the hotel information provided. "
        "If the question is not covered by the data, say that you are not sure and suggest contacting reception.\n\n"
        f"Hotel data:\n{json.dumps(hotel_info, ensure_ascii=False, indent=2)}"
    )
    body = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt},
                    {"text": f"User language: {lang}"},
                    {"text": f"User question: {question}"},
                ]
            }
        ]
    }
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    params = {"key": settings.gemini_api_key}

    def _request() -> str:
        resp = requests.post(url, params=params, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts") or []
        texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
        return "\n".join(texts).strip()

    try:
        return await asyncio.to_thread(_request)
    except Exception:
        return ""


@router.message()
async def ai_entry(message: Message, state: FSMContext, lang: str) -> None:
    if message.text == t(lang, "main_menu.ai_assistant"):
        await state.set_state(AIStates.waiting_question)
        await message.answer(t(lang, "ai.ask"))
        return

    current_state = await state.get_state()
    if current_state == AIStates.waiting_question.state:
        await message.answer(t(lang, "ai.thinking"))
        answer = await ask_gemini(message.text or "", lang)
        if not answer:
            answer = t(lang, "ai.fallback")
        await message.answer(answer, reply_markup=main_menu_keyboard(lang))
        await state.clear()

