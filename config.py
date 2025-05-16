import os
from typing import List

class Config:
    # Required
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", 0))
    MONGO_URI = os.getenv("MONGO_URI")
    BASE_URL = os.getenv("BASE_URL")
    
    # Optional with defaults
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    WORKERS = int(os.getenv("WORKERS", "4"))
    MONGO_DB = os.getenv("MONGO_DB", "movie_bot")

    @classmethod
    def validate(cls):
        required = ['BOT_TOKEN', 'API_ID', 'API_HASH', 'SOURCE_CHANNEL_ID', 'MONGO_URI', 'BASE_URL']
        missing = [name for name in required if not getattr(cls, name)]
        if missing:
            raise ValueError(f"Missing config: {', '.join(missing)}")
