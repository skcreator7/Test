from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputPeerChannel
from config import Config
import asyncio
import logging
from urllib.parse import quote
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.app = Client(
            "movie_search_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=20
        )
        self._register_handlers()

    def _register_handlers(self):
        @self.app.on_message(filters.text & ~filters.command)
        async def search_handler(client: Client, message: Message):
            await self._handle_search(client, message)

    async def _get_channel_posts(self, channel_id: int, query: str) -> List[Dict]:
        """Get posts from configured channel (public or private)"""
        try:
            if channel_id in Config.PRIVATE_CHANNELS:
                channel = InputPeerChannel(
                    channel_id,
                    int(Config.get_private_hash(channel_id))
                messages = await self.app.search_messages(
                    entity=channel,
                    query=query,
                    limit=50
                )
            else:
                messages = await self.app.search_messages(
                    chat_id=channel_id,
                    query=query,
                    limit=50
                )
            
            return [self._format_message(msg) async for msg in messages]
        except Exception as e:
            logger.error(f"Channel {channel_id} error: {str(e)}")
            return []

    def _format_message(self, msg) -> Dict:
        return {
            "chat_id": msg.chat.id,
            "message_id": msg.id,
            "text": msg.text or msg.caption or "",
            "date": msg.date,
            "chat_title": msg.chat.title,
            "media": bool(msg.media)
        }

    async def _handle_search(self, client: Client, message: Message):
        """Handle movie search requests"""
        try:
            query = message.text.strip()
            if len(query) < 3:
                return await message.reply("🔍 Please enter at least 3 characters")
            
            # Search in primary source channel
            results = await self._get_channel_posts(Config.SOURCE_CHANNEL_ID, query)
            if not results:
                return await message.reply("🎬 No movies found matching your query")
            
            # Prepare response
            response = "🎥 Search Results:\n\n"
            buttons = []
            
            for idx, post in enumerate(results[:5], 1):
                title = post['text'].split('\n')[0][:50]
                post_url = f"{Config.BASE_URL}/watch?post_id={post['message_id']}&chat_id={post['chat_id']}"
                
                response += f"{idx}. {title}\n"
                buttons.append([InlineKeyboardButton(f"View {idx}", url=post_url)])
            
            reply = await message.reply(
                response,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
            
            # Auto-delete after 3 minutes
            await asyncio.sleep(180)
            await reply.delete()
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            await message.reply("⚠️ Search failed. Please try again later.")

    async def start(self):
        await self.app.start()
        logger.info("Bot started successfully")

    async def stop(self):
        await self.app.stop()
        logger.info("Bot stopped successfully")
