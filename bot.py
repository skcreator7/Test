from pyrogram import Client, filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import Database

class TelegramBot:
    def __init__(self, db: Database):
        self.db = db
        self.app = Client(
            "telegram_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.setup_handlers()

    def setup_handlers(self):
        @self.app.on_message(filters.command("start") & filters.private)
        async def start(client, message: types.Message):
            await message.reply("🔍 यह बॉट प्राइवेट चैनल की पोस्ट सर्च करता है और लिंक वेब पर दिखाता है।")

        @self.app.on_message(filters.text & (filters.private | filters.group))
        async def search_handler(client, message: types.Message):
            query = message.text.strip()
            if not query:
                return

            results = await self.db.search_posts(query)
            if not results:
                return await message.reply("कोई रिज़ल्ट नहीं मिला।")

            first_result = results[0]
            web_url = f"{Config.BASE_URL}/watch/{str(first_result['_id'])}"

            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("वेब पर देखें", url=web_url)]
            ])

            await message.reply(" ", reply_markup=buttons)

        @self.app.on_message(filters.channel)
        async def channel_handler(client, message: types.Message):
            if message.chat.id == Config.SOURCE_CHANNEL_ID and message.text:
                await self.db.save_post(message)
