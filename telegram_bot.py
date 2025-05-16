from pyrogram import Client, filters
from pyrogram.types import Message
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.app = Client(
            "movie_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.WORKERS
        )
        self._register_handlers()

    async def initialize(self):
        await self.app.start()
        logger.info("Bot initialized successfully")
        return self

    def _register_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start(client, message: Message):
            await message.reply("Welcome to Movie Bot!")

        @self.app.on_message(filters.text & filters.private)
        async def echo(client, message: Message):
            await message.reply(f"You said: {message.text}")

    async def stop(self):
        logger.info("Stopping bot...")
        await self.app.stop()
        logger.info("Bot stopped")
