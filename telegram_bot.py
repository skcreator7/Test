from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import Database
from datetime import datetime

class TelegramBot:
    def __init__(self, db: Database):
        self.db = db
        self.app = Client(
            "my_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.setup_handlers()

    async def start(self):
        await self.app.start()
        print(f"Bot started at {datetime.now()}")

    async def stop(self):
        await self.app.stop()

    def setup_handlers(self):
        # New: /stats command for admins
        @self.app.on_message(filters.command("stats") & filters.user(Config.ADMINS))
        async def stats_command(_, message: Message):
            count = await self.db.get_post_count()
            await message.reply(f"📊 Total posts: {count}")

        # Rest of your existing handlers...
        @self.app.on_message(filters.channel)
        async def save_channel_post(client, message: Message):
            if message.chat.id == Config.SOURCE_CHANNEL_ID:
                await self.db.save_post(message)
