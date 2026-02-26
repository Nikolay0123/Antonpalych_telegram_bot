import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    bot_token: str
    gemini_api_key: str
    bnovo_api_key: str
    bnovo_base_url: str
    reception_chat_id: int
    database_path: str
    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        bnovo_api_key=os.getenv("BNOVO_API_KEY", ""),
        bnovo_base_url=os.getenv("BNOVO_BASE_URL", ""),
        reception_chat_id=int(os.getenv("RECEPTION_CHAT_ID", "0")),
        database_path=os.getenv("DATABASE_PATH", "database.sqlite3"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = get_settings()

