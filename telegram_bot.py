import logging
import os
from pyrogram import Client
from config import Config

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.api_id = Config.API_ID
        self.api_hash = Config.API_HASH
        self.bot_token = Config.BOT_TOKEN
        self.user_session = os.getenv("USER_SESSION_STRING")
        self.mode = "user" if self.user_session else "bot"
        self.client = None

    async def initialize(self):
        if self.mode == "user":
            logger.info("Initializing Telegram in USER mode")
            self.client = Client(
                self.user_session,  # बस इसी तरह दें
                api_id=self.api_id,
                api_hash=self.api_hash,
                in_memory=True      # in_memory optional है
            )
        else:
            logger.info("Initializing Telegram in BOT mode")
            self.client = Client(
                "bot",
                api_id=self.api_id,
                api_hash=self.api_hash,
                bot_token=self.bot_token
            )
        await self.client.start()
        logger.info(f"Telegram client started in {self.mode} mode.")

    async def stop(self):
        if self.client:
            await self.client.stop()
            logger.info("Telegram client stopped.")

    async def fetch_channel_messages(self, channel_id, query, limit=10):
        results = []
        async with self.client:
            async for msg in self.client.search_messages(channel_id, query=query, limit=limit):
                text = msg.text or msg.caption or ""
                links = [word for word in text.split() if word.startswith("http")]
                results.append({
                    "id": msg.message_id,
                    "title": text[:40] + "...",
                    "link": f"https://t.me/c/{str(channel_id)[4:]}/{msg.message_id}",
                    "links": links,
                })
        return results
