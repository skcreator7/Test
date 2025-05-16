from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import logging
from urllib.parse import quote

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
        self.app.on_message(filters.chat(Config.MONITORED_CHATS))(self.handle_message)
        self.app.on_message(filters.text & ~filters.command)(self.respond_to_search)

    async def handle_message(self, client: Client, message: Message):
        try:
            post_data = {
                "chat_id": message.chat.id,
                "message_id": message.id,
                "text": message.text or message.caption or "",
                "date": message.date,
                "chat_title": message.chat.title
            }
            await self.db.save_post(post_data)
        except Exception as e:
            logger.error(f"Error saving post: {e}")

    async def respond_to_search(self, client: Client, message: Message):
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
            
            for post in results:
                title = (post.get('text') or 'No text')[:100]
                response += f"▶️ [{title}]({base_url}#{post['message_id']})\n"
                response += f"   - {post.get('chat_title', 'Unknown')}\n\n"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("View All Results", url=base_url)
            ]])
            
            await message.reply(
                response,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Search response error: {e}")

    async def start(self):
        await self.app.start()
        logger.info("Bot started")

    async def stop(self):
        await self.app.stop()
        logger.info("Bot stopped")
