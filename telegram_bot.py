from pyrogram import Client, filters, types
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
        async def start_command(client, message: types.Message):
            await message.reply("🔍 इस बॉट का उपयोग करने के लिए कोई कीवर्ड भेजें, हम चैनल पोस्ट खोज देंगे!")

        @self.app.on_message(filters.text & filters.private)
        async def handle_search(client, message: types.Message):
            query = message.text.strip()
            if not query:
                return await message.reply("कृपया एक मान्य खोज क्वेरी भेजें।")

            results = await self.db.search_posts(query)
            if not results:
                return await message.reply("कोई मिलती-जुलती पोस्ट नहीं मिली।")

            first_result = results[0]
            url = f"{Config.BASE_URL}/watch/{str(first_result['_id'])}"

            await message.reply(url, disable_web_page_preview=True)

        @self.app.on_message(filters.channel)
        async def save_channel_post(client, message: types.Message):
            if message.chat.id == Config.SOURCE_CHANNEL_ID and message.text:
                await self.db.save_post(message)
