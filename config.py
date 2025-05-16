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
    
    # Optional
    ADMINS: List[int] = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    MONGO_DB = os.getenv("MONGO_DB", "movie_bot")

    @classmethod
    def validate(cls):
        """Validate required config"""
        required = {
            'BOT_TOKEN': str,
            'API_ID': int,
            'API_HASH': str,
            'SOURCE_CHANNEL_ID': int,
            'MONGO_URI': str,
            'BASE_URL': str
        }
        
        errors = []
        for name, typ in required.items():
            value = getattr(cls, name)
            if not value:
                errors.append(f"{name} is required")
            elif not isinstance(value, typ):
                errors.append(f"{name} must be {typ.__name__}")
        
        if errors:
            raise ValueError("Config errors:\n" + "\n".join(errors))
