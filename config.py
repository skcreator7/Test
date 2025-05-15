import os

class Config:
    # Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", 0))
    
    # Web
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "telegram_bot")
    
    @classmethod
    def validate(cls):
        required = ["BOT_TOKEN", "API_ID", "API_HASH", "SOURCE_CHANNEL_ID"]
        missing = [var for var in required if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing config: {missing}")
