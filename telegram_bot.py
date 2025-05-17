from telethon import TelegramClient
from config import Config

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.client = TelegramClient(
            "bot",
            Config.API_ID,
            Config.API_HASH
        )

    async def start(self):
        await self.client.start(bot_token=Config.BOT_TOKEN)

    async def stop(self):
        await self.client.disconnect()
