import os

class Config:
    # Telegram
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WORKERS = int(os.getenv("WORKERS", 4))
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "telegram_monitor")
    
    # Web
    PORT = int(os.getenv("PORT", 8000))
    BASE_URL = os.getenv("BASE_URL", "https://your-app-name.koyeb.app")
    
    # Monitoring
    MONITORED_CHATS = [
        int(chat_id) for chat_id in 
        os.getenv("MONITORED_CHATS", "-1002193268219").split(",")
        if chat_id.strip()
    ]
