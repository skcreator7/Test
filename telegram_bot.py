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
        logger.info("Bot client initialized")  # Debug log
        self._register_handlers()

    async def initialize(self):
        try:
            await self.app.start()
            me = await self.app.get_me()
            logger.info(f"Bot started successfully as @{me.username} (ID: {me.id})")
            return self
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise

    def _register_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_handler(client, message: Message):
            logger.info(f"Received start from {message.from_user.id}")
            await message.reply("🤖 Hello! I'm your Movie Bot\n\n"
                              "Try sending:\n"
                              "/search <movie name>\n"
                              "/latest")

        @self.app.on_message(filters.command("ping") & filters.private)
        async def ping_handler(client, message: Message):
            await message.reply("🏓 Pong!")
            logger.info("Responded to ping")

        @self.app.on_message(filters.text & filters.private)
        async def echo_handler(client, message: Message):
            logger.info(f"Received text: {message.text}")
            await message.reply("I'm a movie bot. Try /start for help")

    async def stop(self):
        try:
            await self.app.stop()
            logger.info("Bot stopped cleanly")
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")
