from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputPeerChannel
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
        """Initialize bot with channel hash"""
        await self.app.start()
        try:
            channel = await self.app.get_chat(Config.SOURCE_CHANNEL_ID)
            self.channel_hash = channel.access_hash
            logger.info("Successfully fetched channel access hash")
        except Exception as e:
            logger.error(f"Failed to get channel hash: {e}")
            raise
        return self

    def _register_handlers(self):
        @self.app.on_message(filters.group & ~filters.service)
        async def group_handler(client, message):
            await self._handle_group_message(client, message)
        
        @self.app.on_message(filters.private & filters.text & ~filters.command)
        async def private_handler(client, message):
            await self._handle_private_message(client, message)

    async def _get_channel_peer(self):
        """Get InputPeerChannel with current hash"""
        if not self.channel_hash:
            channel = await self.app.get_chat(Config.SOURCE_CHANNEL_ID)
            self.channel_hash = channel.access_hash
        return InputPeerChannel(Config.SOURCE_CHANNEL_ID, self.channel_hash)

    async def _search_channel(self, query: str) -> list:
        """Search in private channel"""
        try:
            channel = await self._get_channel_peer()
            
            messages = []
            async for msg in self.app.search_messages(
                entity=channel,
                query=query,
                limit=10
            ):
                post_data = {
                    "chat_id": msg.chat.id,
                    "message_id": msg.id,
                    "text": msg.text or msg.caption or "",
                    "date": msg.date,
                    "chat_title": msg.chat.title
                }
                await self.db.save_post(post_data)
                messages.append(post_data)
            
            return messages
        except Exception as e:
            logger.error(f"Channel search error: {e}")
            return []

    # ... (rest of the methods remain same as previous implementation)
