from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import logging
import asyncio

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
        logger.info("Bot client initialized")

    async def initialize(self):
        try:
            await self.app.start()
            me = await self.app.get_me()
            logger.info(f"Bot started successfully as @{me.username}")
            return self
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

    def _register_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client, message: Message):
            logger.info(f"Received start command from {message.from_user.id}")
            await message.reply("🚀 Welcome to Movie Bot!\n\n"
                              "Send me /search <query> to find movies")

        @self.app.on_message(filters.command("search") & filters.private)
        async def search_handler(client, message: Message):
            query = " ".join(message.command[1:])
            if not query:
                await message.reply("Please provide a search term")
                return
            
            logger.info(f"Search request: {query}")
            await message.reply(f"🔍 Searching for: {query}...")

        @self.app.on_message(filters.text & filters.private)
        async def text_handler(client, message: Message):
            logger.info(f"Received text: {message.text}")
            await message.reply("I'm a movie bot. Use /search to find movies")

    async def stop(self):
        try:
            await self.app.stop()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
