from pyrogram import Client, filters, types
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

        @self.app.on_message(filters.text & filters.private)
        async def search_handler(client, message: types.Message):
            query = message.text.strip()
            if not query:
                return await message.reply("कृपया कोई वैध सर्च क्वेरी भेजें।")
            
            results = await self.db.search_posts(query)
            if not results:
                return await message.reply("कोई भी मिलती-जुलती पोस्ट नहीं मिली।")
            
            first_result = results[0]
            web_url = f"{Config.BASE_URL}/watch/{str(first_result['_id'])}"
            await message.reply(web_url, disable_web_page_preview=True)

        @self.app.on_message(filters.channel)
        async def channel_handler(client, message: types.Message):
            if message.chat.id == Config.SOURCE_CHANNEL_ID and message.text:
                await self.db.save_post(message)
