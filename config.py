import os
from typing import List

class Config:
    # Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", 0))
    BOT_USERNAME = os.getenv("BOT_USERNAME")  # Without @
    ADMINS = [int(admin) for admin in os.getenv("ADMINS", "").split(",") if admin]
    
    # Web
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    BASE_URL = os.getenv("BASE_URL")  # Your Koyeb app URL
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "telegram_bot")
    
    # Auto-delete timings (seconds)
    AUTO_DELETE = {
        "search_results": 60,
        "help_messages": 30,
        "not_found": 20
    }
    
    @classmethod
    def validate(cls):
        required = ["BOT_TOKEN", "API_ID", "API_HASH", "SOURCE_CHANNEL_ID", "MONGO_URI", "BASE_URL", "BOT_USERNAME"]
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing config: {missing}")
