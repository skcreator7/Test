from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import Config
import logging
from typing import List, Optional

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
        self._register_handlers()

    async def initialize(self):
        await self.app.start()
        me = await self.app.get_me()
        logger.info(f"Bot started as @{me.username}")
        return self

    def _register_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client, message: Message):
            await message.reply(
                "🎬 Welcome to Movie Search Bot!\n\n"
                "Simply type any movie name to search\n"
                "Example: `Avengers Endgame`",
                parse_mode="markdown"
            )

        @self.app.on_message(filters.text & filters.private & ~filters.command)
        async def search_handler(client, message: Message):
            query = message.text.strip()
            if len(query) < 3:
                await message.reply("Please enter at least 3 characters to search")
                return
            
            try:
                results = await self._search_movies(query)
                if not results:
                    await message.reply("No results found. Try different keywords")
                    return
                
                # Send first result with more options button
                first_result = results[0]
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("More Results", callback_data=f"more:{query}")]
                ])
                
                await message.reply(
                    f"🎥 *{first_result['title']}*\n"
                    f"📅 {first_result.get('year', 'N/A')}\n"
                    f"⭐ Rating: {first_result.get('rating', 'N/A')}\n"
                    f"🔗 [More Info]({first_result['url']})",
                    reply_markup=keyboard,
                    parse_mode="markdown"
                )
                
            except Exception as e:
                logger.error(f"Search error: {e}")
                await message.reply("Error searching. Please try again later")

        @self.app.on_callback_query(filters.regex("^more:"))
        async def more_results_handler(client, callback_query):
            query = callback_query.data.split(":")[1]
            results = await self._search_movies(query)
            
            response = ["🔍 Search Results:"]
            for idx, result in enumerate(results[:5], 1):
                response.append(
                    f"{idx}. [{result['title']}]({result['url']}) "
                    f"({result.get('year', 'N/A')})"
                )
            
            await callback_query.message.edit_text(
                "\n".join(response),
                parse_mode="markdown"
            )
            await callback_query.answer()

    async def _search_movies(self, query: str) -> List[dict]:
        """Search movies in database or API"""
        # This should be replaced with your actual search logic
        # Example mock data - replace with real database/API calls
        return [
            {
                "title": f"Movie about {query}",
                "year": "2023",
                "rating": "7.5",
                "url": "https://example.com/movie1"
            },
            {
                "title": f"Another {query} movie",
                "year": "2021",
                "rating": "8.0",
                "url": "https://example.com/movie2"
            }
        ]

    async def stop(self):
        await self.app.stop()
        logger.info("Bot stopped")
