import os
from typing import List

class Config:
    # Required
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID"))
    MONGO_URI = os.getenv("MONGO_URI")
    BASE_URL = os.getenv("BASE_URL")
    
    # Optional with defaults
    ADMINS: List[int] = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    MONGO_DB = os.getenv("MONGO_DB", "telegram_bot")
    
    # Private channels (add access hashes as needed)
    PRIVATE_CHANNELS = {
        int(SOURCE_CHANNEL_ID): "your_access_hash_here"  # Add more as needed
    }
    
    @classmethod
    def get_private_hash(cls, channel_id: int) -> str:
        return cls.PRIVATE_CHANNELS.get(channel_id, "")
