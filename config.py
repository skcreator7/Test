import os
from enum import Enum

class Config:
    # Telegram Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    API_ID = os.getenv("API_ID", "")
    API_HASH = os.getenv("API_HASH", "")
    
    # Web Configuration
    PORT = int(os.getenv("PORT", 8080))
    HOST = os.getenv("HOST", "0.0.0.0")
    BASE_URL = os.getenv("BASE_URL", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-random-string")
    
    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "telegram_bot")
    
    # Moderation Settings
    DELETE_USER_MESSAGES = os.getenv("DELETE_USER_MESSAGES", "true").lower() == "true"
    DELETE_LINKS = os.getenv("DELETE_LINKS", "true").lower() == "true"
    DELETE_USERNAMES = os.getenv("DELETE_USERNAMES", "true").lower() == "true"
    MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", 3))
    WARNING_EXPIRE_HOURS = int(os.getenv("WARNING_EXPIRE_HOURS", 24))
    DELETE_BOT_REPLIES_AFTER = int(os.getenv("DELETE_BOT_REPLIES_AFTER", 60))
    ALLOWED_COMMANDS = ["start", "search", "help", "settings"]
    PROTECTED_CONTENT_TYPES = ["text", "photo", "video", "document"]
    
    # Quality patterns for link extraction
    QUALITY_PATTERNS = {
        "720p": r"720p|HD",
        "1080p": r"1080p|FHD", 
        "4K": r"4K|UHD"
    }

class WarningLevel(Enum):
    INFO = 1
    WARNING = 2 
    SEVERE = 3
