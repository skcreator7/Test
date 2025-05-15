import os
from enum import Enum

class Config:
    # Telegram Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    API_ID = os.getenv("API_ID", "")
    API_HASH = os.getenv("API_HASH", "")
    
    # Channel Configuration
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", -1001234567890))  # Private channel to monitor
    
    # Web Configuration
    PORT = int(os.getenv("PORT", 8080))
    HOST = os.getenv("HOST", "0.0.0.0")
    BASE_URL = os.getenv("BASE_URL", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-random-string")
    
    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "telegram_bot")
    
    # Quality patterns for link extraction
    QUALITY_PATTERNS = {
    "720p": r"\b720p\b|\bHD\b|\b480p\b",
    "1080p": r"\b1080p\b|\bFHD\b|\bFullHD\b",
    "4K": r"\b4K\b|\bUHD\b|\b2160p\b",
    "magnet": r"\bmagnet:\?",
    "torrent": r"\.torrent\b"
}
