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

    async def handle_channel_message(self, client: Client, message: Message):
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

    async def handle_group_message(self, client: Client, message: Message):
        """Delete links/mentions immediately in groups"""
        try:
            text = message.text or message.caption or ""
            if re.search(r'https?://|@\w+', text):
                await message.delete()
                reply = await message.reply(
                    f"@{message.from_user.username} Links/mentions not allowed!",
                    reply_to_message_id=message.id
                )
                await asyncio.sleep(180)
                await reply.delete()
        except Exception as e:
            logger.error(f"Group moderation error: {e}")

    async def handle_private_message(self, client: Client, message: Message):
        """Auto-delete all private messages after 3 minutes"""
        try:
            reply = await message.reply("This message will self-destruct in 3 minutes ⏳")
            await asyncio.sleep(180)
            await message.delete()
            await reply.delete()
        except Exception as e:
            logger.error(f"Private message error: {e}")

    async def handle_search_request(self, client: Client, message: Message):
        """Handle search requests"""
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
            
            sent_msg = await message.reply(
                response,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("View All Results", url=base_url)
                ]]),
                disable_web_page_preview=True
            )
            await asyncio.sleep(180)
            await sent_msg.delete()
        except Exception as e:
            logger.error(f"Search response error: {e}")

    async def start(self):
        """Start the Telegram bot client"""
        await self.app.start()
        logger.info("Bot started successfully")
        return self

    async def stop(self):
        """Stop the Telegram bot client"""
        await self.app.stop()
        logger.info("Bot stopped successfully")
