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
            await message.reply("🔍 Use /search <query> to find posts!")
        
        @self.app.on_message(filters.text & filters.private)
        async def handle_search(client, message: types.Message):
            # ... (पिछला कोड) ...
