from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
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
            workers=Config.WORKERS  # Now using the Config.WORKERS value
        )
        self._register_handlers()

    async def initialize(self):
        """Initialize bot"""
        await self.app.start()
        logger.info("Bot initialized successfully")
        return self

    def _register_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client, message: Message):
            await message.reply("Welcome to Movie Bot!")

        @self.app.on_message(filters.command("search") & filters.private)
        async def search_handler(client, message: Message):
            query = " ".join(message.command[1:])
            if query:
                await message.reply(f"Searching for: {query}")
            else:
                await message.reply("Please provide a search term")

    async def stop(self):
        """Stop the bot client"""
        await self.app.stop()
