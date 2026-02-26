from datetime import datetime

from aiogram import Bot

from config import settings


async def notify_reception(bot: Bot, text: str) -> None:
    if not settings.reception_chat_id:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"{text}\n\n🕒 {timestamp}"
    await bot.send_message(chat_id=settings.reception_chat_id, text=message)

