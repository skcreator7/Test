import os

class Config:
    # Telegram API
    API_ID = int(os.getenv("API_ID", 12345))  # Default fallback value
    API_HASH = os.getenv("API_HASH", "your_api_hash")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", -1001234567890))
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    
    # Web Server
    PORT = int(os.getenv("PORT", 8000))
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
