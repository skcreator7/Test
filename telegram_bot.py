from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import logging
from urllib.parse import quote
import re

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.app = Client(
            "my_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=Config.WORKERS
        )
        
        # Register handlers
        @self.app.on_message(filters.chat(Config.MONITORED_CHATS))
        async def handle_message(client: Client, message: Message):
            await self._handle_message(client, message)
            
        @self.app.on_message(filters.group & ~filters.service)
        async def moderate_group(client: Client, message: Message):
            await self._moderate_group(client, message)
            
        @self.app.on_message(filters.text & ~filters.command)
        async def respond_to_search(client: Client, message: Message):
            await self._respond_to_search(client, message)

    async def _handle_message(self, client: Client, message: Message):
        """Save channel posts to database"""
        try:
            post_data = {
                "chat_id": message.chat.id,
                "message_id": message.id,
                "text": message.text or message.caption or "",
                "date": message.date,
                "chat_title": message.chat.title,
                "media": bool(message.media)
            }
            await self.db.save_post(post_data)
        except Exception as e:
            logger.error(f"Error saving post: {e}")

    async def _moderate_group(self, client: Client, message: Message):
        """Delete messages containing links or mentions"""
        try:
            text = message.text or message.caption or ""
            if re.search(r'https?://|@\w+', text):
                await message.delete()
                await client.send_message(
                    chat_id=message.chat.id,
                    text=f"@{message.from_user.username} Links/mentions not allowed!",
                    reply_to_message_id=message.id
                )
        except Exception as e:
            logger.error(f"Moderation error: {e}")

    async def _respond_to_search(self, client: Client, message: Message):
        """Respond to any text message with search results"""
        try:
            if message.from_user and message.from_user.is_self:
                return
            
            query = message.text.strip()
            if len(query) < 3:
                return
            
            results = await self.db.search_posts(query)
            if not results:
                return
            
            response = "🔍 Search Results:\n\n"
            base_url = f"{Config.BASE_URL}/watch?q={quote(query)}"
            
            for post in results[:5]:
                title = (post.get('text') or 'No text').split('\n')[0][:100]
                response += f"▶️ [{title}]({base_url}#{post['message_id']})\n"
                response += f"   - {post.get('chat_title', 'Unknown')}\n\n"
            
            await message.reply(
                response,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("View All Results", url=base_url)
                ]]),
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Search response error: {e}")

    async def start(self):
        """Start the bot"""
        await self.app.start()
        logger.info("Bot started")

    async def stop(self):
        """Stop the bot"""
        await self.app.stop()
        logger.info("Bot stopped")
