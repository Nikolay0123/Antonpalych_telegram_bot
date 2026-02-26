import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database import init_db
from handlers import setup_routers
from middlewares import LanguageMiddleware, RegistrationRequiredMiddleware
from utils.logger import setup_logger


async def main() -> None:
    setup_logger()
    await init_db()

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(LanguageMiddleware())
    dp.update.middleware(RegistrationRequiredMiddleware())

    dp.include_router(setup_routers())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

