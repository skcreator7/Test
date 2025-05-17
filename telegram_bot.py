import logging
import os
import re
from typing import List, Dict, Optional
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.api_id = Config.API_ID
        self.api_hash = Config.API_HASH
        self.bot_token = Config.BOT_TOKEN
        self.user_session = os.getenv("USER_SESSION_STRING")
        
        if not self.user_session and not self.bot_token:
            raise ValueError("Either USER_SESSION_STRING or BOT_TOKEN must be provided")
            
        self.mode = "user" if self.user_session else "bot"
        self.client = None
        self._validate_credentials()

    def _validate_credentials(self):
        """Validate the provided credentials"""
        if not isinstance(self.api_id, int) or self.api_id <= 0:
            raise ValueError("Invalid API_ID")
        if not isinstance(self.api_hash, str) or len(self.api_hash) < 10:
            raise ValueError("Invalid API_HASH")
        if self.mode == "bot" and (not isinstance(self.bot_token, str) or ":" not in self.bot_token):
            raise ValueError("Invalid BOT_TOKEN format")
        if self.mode == "user" and not re.match(r"^[0-9a-zA-Z]+$", self.user_session):
            raise ValueError("Invalid USER_SESSION_STRING format")

    async def initialize(self) -> bool:
        """Initialize the Telegram client"""
        try:
            client_config = {
                "api_id": self.api_id,
                "api_hash": self.api_hash,
                "workers": Config.WORKERS
            }

            if self.mode == "user":
                logger.info("Initializing in USER mode")
                self.client = Client(
                    name="user_session",
                    session_string=self.user_session,
                    **client_config
                )
            else:
                logger.info("Initializing in BOT mode")
                self.client = Client(
                    name="bot",
                    bot_token=self.bot_token,
                    **client_config
                )

            await self.client.start()
            me = await self.client.get_me()
            logger.info(f"Successfully started as @{me.username} ({self.mode} mode)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop the Telegram client"""
        if self.client and await self.client.is_initialized:
            try:
                await self.client.stop()
                logger.info("Telegram client stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping client: {e}", exc_info=True)

    async def fetch_channel_messages(self, channel_id: int, query: str = "", limit: int = 10) -> List[Dict]:
        """
        Fetch messages from a channel with optional search query
        
        Args:
            channel_id: Channel ID (with -100 prefix for supergroups)
            query: Search query string
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries with id, title, link, and extracted links
        """
        if not self.client or not await self.client.is_initialized:
            raise RuntimeError("Client not initialized")

        results = []
        try:
            async with self.client:
                async for msg in self.client.search_messages(
                    chat_id=channel_id,
                    query=query,
                    limit=min(limit, 100)  # Telegram API limit
                ):
                    if not msg:
                        continue
                        
                    text = msg.text or msg.caption or ""
                    links = self._extract_links(text)
                    
                    results.append({
                        "id": msg.id,
                        "date": msg.date,
                        "title": self._generate_title(text, msg),
                        "link": self._generate_message_link(channel_id, msg.id),
                        "links": links,
                        "views": getattr(msg, 'views', 0)
                    })
                    
                    if len(results) >= limit:
                        break
                        
        except Exception as e:
            logger.error(f"Error fetching messages from channel {channel_id}: {e}")
            raise
            
        return results

    def _extract_links(self, text: str) -> List[str]:
        """Extract all HTTP/HTTPS links from text"""
        if not text:
            return []
        return re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)

    def _generate_title(self, text: str, msg: Message) -> str:
        """Generate a title from message text"""
        if not text:
            return "No title"
        first_line = text.split('\n')[0]
        return (first_line[:40] + '...') if len(first_line) > 40 else first_line

    def _generate_message_link(self, channel_id: int, message_id: int) -> str:
        """Generate a direct link to the message"""
        if str(channel_id).startswith('-100'):
            channel_id = int(str(channel_id)[4:])
        return f"https://t.me/c/{channel_id}/{message_id}"

    async def is_member_of_channel(self, channel_id: int) -> bool:
        """Check if the user/bot is a member of the specified channel"""
        if not self.client or not await self.client.is_initialized:
            return False
            
        try:
            chat = await self.client.get_chat(channel_id)
            return chat is not None
        except Exception:
            return False
