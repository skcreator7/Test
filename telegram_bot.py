from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
import logging
from database import Database
from typing import List, Dict

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, db: Database):
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
        logger.info("Bot initialized successfully")
        return self

    def _register_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client, message: Message):
            await message.reply(
                "🎬 Welcome to Movie Bot!\n\n"
                "Use /search <query> to find movies\n"
                "Use /latest to get recent updates"
            )

        @self.app.on_message(filters.command("search") & filters.private)
        async def search_handler(client, message: Message):
            query = " ".join(message.command[1:])
            if not query:
                await message.reply("Please provide a search term")
                return
            
            results = await self._search_movies(query)
            if results:
                response = "🔍 Results:\n\n" + "\n".join(
                    f"{i+1}. {res['title']}" for i, res in enumerate(results))
                await message.reply(response)
            else:
                await message.reply("No results found")

        @self.app.on_message(filters.group & filters.text)
        async def group_handler(client, message: Message):
            if message.text.startswith("!"):
                await self._handle_group_command(message)

    async def _search_movies(self, query: str) -> List[Dict]:
        return await self.db.search_posts(query)

    async def _handle_group_command(self, message: Message):
        cmd = message.text[1:].lower()
        if cmd == "help":
            await message.reply(
                "📌 Group Commands:\n"
                "!help - Show this help\n"
                "!latest - Show recent movies"
            )

    async def stop(self):
        await self.app.stop()
