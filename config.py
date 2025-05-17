import os
from typing import List

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", 0))
    MONGO_URI = os.getenv("MONGO_URI", "")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    ADMINS: List[int] = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    MONGO_DB = os.getenv("MONGO_DB", "movie_bot")
    WORKERS = int(os.getenv("WORKERS", "4"))
    TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "https://t.me/Sk4film")
    WHATSAPP_CHANNEL = os.getenv("WHATSAPP_CHANNEL", "https://whatsapp.com/channel/0029Va69Ts2C6ZvmEWsHNo3c")

    @classmethod
    def validate(cls):
        required = {
            'BOT_TOKEN': str,
            'API_ID': int,
            'API_HASH': str,
            'SOURCE_CHANNEL_ID': int,
            'MONGO_URI': str
        }
        errors = []
        for name, expected_type in required.items():
            value = getattr(cls, name)
            if not value:
                errors.append(f"{name} is required")
            elif not isinstance(value, expected_type):
                errors.append(f"{name} should be {expected_type.__name__}")
        if errors:
            raise ValueError("\n".join(errors))
