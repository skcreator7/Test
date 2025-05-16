from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
from database import Database
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db: Database):
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
        self.app.on_message(filters.group & ~filters.service)(self.moderate_group)
        self.app.on_message(filters.text & ~filters.command)(self.respond_to_search)

    async def respond_to_search(self, client: Client, message: Message):
        """Respond to any text message with search results"""
        try:
            # Don't respond to own messages or in channels
            if message.from_user and message.from_user.is_self:
                return
            
            search_query = message.text.strip()
            if len(search_query) < 3:  # Minimum query length
                return
            
            results = await self.db.search_posts(search_query, limit=5)
            if not results:
                return
            
            # Prepare response with markdown links
            response = "🔍 Search Results:\n\n"
            base_url = f"{Config.BASE_URL}/watch?q={quote(search_query)}"
            
            for i, post in enumerate(results[:5], 1):
                title = post.get('text', 'No title').split('\n')[0][:50]  # First line, max 50 chars
                chat_title = post.get('chat_title', 'Unknown')
                response += f"▶️ [{title}]({base_url}#{post['message_id']})\n"
                response += f"   - {chat_title}\n\n"
            
            # Add view all button
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

    # ... (keep other existing methods)
