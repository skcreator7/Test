from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import os  # Add this import

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.app = Client(
            "my_bot",
            api_id=int(os.getenv("API_ID")),  # Convert to int as env vars are strings
            api_hash=os.getenv("API_HASH"),
            bot_token=os.getenv("BOT_TOKEN"),
            workers=1,
            sleep_threshold=30
        )

    async def start(self):
        """Start with connection monitoring"""
        await self.app.start()
        print(f"🤖 Bot started monitoring channel: {os.getenv('SOURCE_CHANNEL_ID')}")
        # ... rest of your code ...
