from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import asyncio
import logging
from urllib.parse import quote
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.start_time = datetime.now()
        self.app = Client(
            "my_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.WORKERS
        )
        
        # Register handlers
        self.register_handlers()

    def register_handlers(self):
        """Register all message handlers"""
        
        @self.app.on_message(filters.chat(Config.MONITORED_CHATS))
        async def channel_handler(client, message):
            await self.handle_channel_message(client, message)
        
        @self.app.on_message(filters.group)
        async def group_handler(client, message):
            await self.handle_group_message(client, message)
        
        @self.app.on_message(filters.private)
        async def private_handler(client, message):
            await self.handle_private_message(client, message)
        
        @self.app.on_message(filters.text)
        async def text_handler(client, message):
            if not message.command:
                await self.handle_search_request(client, message)

    # ... (keep all other methods exactly the same as before)
    # handle_channel_message, handle_group_message, handle_private_message, 
    # handle_search_request, start, stop methods remain unchanged
