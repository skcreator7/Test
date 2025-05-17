import os
from typing import List

class Config:
    # Required Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    MONGO_URI = os.getenv("MONGO_URI")
    BASE_URL = os.getenv("BASE_URL")
    
    # Optional Configuration with Defaults
    ADMINS: List[int] = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    MONGO_DB = os.getenv("MONGO_DB", "movie_bot")
    WORKERS = int(os.getenv("WORKERS", "4"))
    SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "3600"))  # 1 hour

    @classmethod
    def validate(cls):
        """Validate all required configuration values"""
        required = {
            'BOT_TOKEN': str,
            'API_ID': int,
            'API_HASH': str,
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
