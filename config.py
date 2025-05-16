import os
from typing import List

class Config:
    # Required Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", 0))
    MONGO_URI = os.getenv("MONGO_URI")
    BASE_URL = os.getenv("BASE_URL")
    
    # Optional Configuration
    ADMINS: List[int] = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    WORKERS = int(os.getenv("WORKERS", "10"))
    MONGO_DB = os.getenv("MONGO_DB", "movie_bot")

    @classmethod
    def validate_config(cls):
        """Validate all required configuration values"""
        required = {
            'BOT_TOKEN': str,
            'API_ID': int,
            'API_HASH': str,
            'SOURCE_CHANNEL_ID': int,
            'MONGO_URI': str,
            'BASE_URL': str
        }
        
        errors = []
        for name, expected_type in required.items():
            value = getattr(cls, name)
            if not value:
                errors.append(f"{name} is not set")
            elif not isinstance(value, expected_type):
                errors.append(f"{name} should be {expected_type.__name__}, got {type(value).__name__}")
        
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))
