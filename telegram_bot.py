from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import asyncio
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self._running = False
        self._tasks = set()
        
        self.app = Client(
            "movie_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=10
        )
        
        @self.app.on_message(filters.text & ~filters.command)
        async def search_handler(client, message):
            task = asyncio.create_task(self._handle_search(client, message))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    async def _handle_search(self, client: Client, message: Message):
        """Handle search requests with proper error handling"""
        try:
            query = message.text.strip()
            if len(query) < 3:
                return await message.reply("Minimum 3 characters required")
            
            results = await self.db.search_posts(query)
            if not results:
                return await message.reply("No results found")
            
            response = "🎬 Search Results:\n\n"
            buttons = []
            
            for idx, post in enumerate(results[:5], 1):
                title = post['text'].split('\n')[0][:50] if post['text'] else 'No title'
                post_url = f"{Config.BASE_URL}/watch?post_id={post['message_id']}&chat_id={post['chat_id']}"
                
                response += f"{idx}. {title}\n"
                buttons.append([InlineKeyboardButton(f"View {idx}", url=post_url)])
            
            reply = await message.reply(
                response,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
            
            await asyncio.sleep(180)
            await reply.delete()
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await message.reply("Search failed. Please try again.")

    async def start(self):
        """Start bot with proper task management"""
        self._running = True
        await self.app.start()
        logger.info("Bot started successfully")

    async def stop(self):
        """Stop bot with proper cleanup"""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await self.app.stop()
        logger.info("Bot stopped successfully")
