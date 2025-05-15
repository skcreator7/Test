import os
from typing import List

class Config:
    # Telegram (Required)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", 0))
    
    # Admins (Optional)
    try:
        ADMINS = [int(admin) for admin in os.getenv("ADMINS", "").split(",") if admin]
    except:
        ADMINS = []
        print("⚠️ ADMINS not configured or invalid format")

    # Web (Required)
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    BASE_URL = os.getenv("BASE_URL", "")
    
    # MongoDB (Required)
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB = os.getenv("MONGO_DB", "telegram_bot")

    # Bot username (Optional)
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")

    @classmethod
    def validate(cls):
        required = {
            "BOT_TOKEN": cls.BOT_TOKEN,
            "API_ID": cls.API_ID,
            "API_HASH": cls.API_HASH,
            "SOURCE_CHANNEL_ID": cls.SOURCE_CHANNEL_ID,
            "MONGO_URI": cls.MONGO_URI,
            "BASE_URL": cls.BASE_URL
        }
        
        missing = [name for name, val in required.items() if not val]
        if missing:
            raise ValueError(f"🚨 Missing required configs: {missing}")
