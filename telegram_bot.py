from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database import Database

class TelegramBot:
    def __init__(self, db: Database):
        self.db = db
        self.app = Client(
            "my_telegram_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.setup_handlers()

    async def start(self):
        await self.app.start()
        print("Telegram Bot Started!")

    async def stop(self):
        await self.app.stop()

    def setup_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start_command(client, message: Message):
            await message.reply("🔍 Send any text to search posts.")

        @self.app.on_message(filters.text & (filters.private | filters.group | filters.channel))
        async def handle_search(client, message: Message):
            if message.text.startswith("/"):
                return

            query = message.text
            results = await self.db.search_posts(query)

            if not results:
                await message.reply("No matching posts found.")
                return

            buttons = []
            from utils import make_watch_url
            for result in results:
                url = make_watch_url(result)
                buttons.append([{"text": result.get("channel_name", "Watch"), "url": url}])

            await message.reply(
                "Search results:",
                reply_markup={"inline_keyboard": buttons}
            )

        @self.app.on_message(filters.channel)
        async def save_channel_post(client, message: Message):
            await self.db.save_post(message)

        @self.app.on_message(filters.group)
        async def save_group_post(client, message: Message):
            await self.db.save_post(message)
