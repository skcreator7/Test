from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.raw.types import InputPeerChannel
from typing import List, Dict, Optional, Any  # Added type imports
from config import Config
import asyncio
import logging
from urllib.parse import quote
import re

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
        self.channel_hash = None
        self._register_handlers()

    async def initialize(self):
        """Initialize bot with channel info"""
        await self.app.start()
        try:
            channel = await self.app.get_chat(Config.SOURCE_CHANNEL_ID)
            self.channel_hash = channel.access_hash
            logger.info("Bot initialized successfully")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise
        return self

    def _register_handlers(self):
        @self.app.on_message(filters.group & ~filters.service)
        async def group_handler(client, message):
            await self._handle_group_message(client, message)
        
        @self.app.on_message(filters.private & filters.text & ~filters.command)
        async def private_handler(client, message):
            await self._handle_private_message(client, message)

    async def stop(self):
        """Stop the bot client"""
        await self.app.stop()
