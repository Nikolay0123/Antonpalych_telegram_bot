from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from database import get_user
from languages import t


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: Optional[int] = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        lang = "ru"
        if user_id is not None:
            user = await get_user(user_id)
            if user and user.get("language"):
                lang = user["language"]
        data["lang"] = lang
        return await handler(event, data)


class RegistrationRequiredMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._allowed_commands = {"/start"}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            text = event.text or ""
            if any(text.startswith(cmd) for cmd in self._allowed_commands):
                return await handler(event, data)

            user = await get_user(event.from_user.id)
            if not user:
                lang = data.get("lang", "ru")
                await event.answer(t(lang, "errors.registration_required"))
                return
        if isinstance(event, CallbackQuery):
            user = await get_user(event.from_user.id)
            if not user and not (event.data or "").startswith("lang:"):
                lang = data.get("lang", "ru")
                await event.message.answer(t(lang, "errors.registration_required"))
                return
        return await handler(event, data)

