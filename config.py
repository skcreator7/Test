import os

class Config:
    # Telegram
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WORKERS = int(os.getenv("WORKERS", 4))
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "telegram_bot")
    
    # Web
    PORT = int(os.getenv("PORT", 8000))
    BASE_URL = os.getenv("BASE_URL", "https://your-app-name.koyeb.app")
    
    # Monitoring
    MONITORED_CHATS = [int(c) for c in os.getenv("MONITORED_CHATS", "").split(",") if c]
