from pyrogram import Client, filters
from pyrogram.types import Message
from typing import List, Dict, Optional, Any
from config import Config
import asyncio
import logging

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
        """Initialize bot"""
        await self.app.start()
        logger.info("Bot initialized successfully")
        return self

    def _register_handlers(self):
        # Fixed filter syntax - removed problematic ~ operator
        @self.app.on_message(filters.group & filters.text)
        async def group_handler(client, message: Message):
            await self._handle_group_message(client, message)
        
        @self.app.on_message(filters.private & filters.text)
        async def private_handler(client, message: Message):
            await self._handle_private_message(client, message)

    async def _handle_group_message(self, client, message: Message):
        """Handle group messages"""
        try:
            logger.info(f"Group message from {message.chat.id}: {message.text}")
            # Your group message handling logic here
        except Exception as e:
            logger.error(f"Error handling group message: {e}")

    async def _handle_private_message(self, client, message: Message):
        """Handle private messages"""
        try:
            logger.info(f"Private message from {message.from_user.id}: {message.text}")
            # Your private message handling logic here
        except Exception as e:
            logger.error(f"Error handling private message: {e}")

    async def stop(self):
        """Stop the bot client"""
        await self.app.stop()
