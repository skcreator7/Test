from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import logging

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
        async def start(client, message: Message):
            await message.reply("Hello! I'm your movie bot.")

    async def stop(self):
        await self.app.stop()
        logger.info("Bot stopped")
