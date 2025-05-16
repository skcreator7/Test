import os
from pyrogram import Client

class Config:
    # Required Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID"))
    MONGO_URI = os.getenv("MONGO_URI")
    BASE_URL = os.getenv("BASE_URL")
    
    # Optional Configuration with Defaults
    ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    MONGO_DB = os.getenv("MONGO_DB", "movie_bot")
    WORKERS = int(os.getenv("WORKERS", "10"))

    @classmethod
    async def get_channel_hash(cls):
        """Automatically fetch private channel hash"""
        async with Client(
            "temp_session",
            api_id=cls.API_ID,
            api_hash=cls.API_HASH,
            bot_token=cls.BOT_TOKEN
        ) as app:
            try:
                channel = await app.get_chat(cls.SOURCE_CHANNEL_ID)
                return str(channel.access_hash)
            except Exception as e:
                raise ValueError(f"Failed to get channel hash: {e}")
