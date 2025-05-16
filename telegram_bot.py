from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio

class TelegramBot:
    def __init__(self, db):
        self.db = db
        self.app = Client(
            "my_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=1,
            sleep_threshold=30
        )

    async def start(self):
        """Start with connection monitoring"""
        await self.app.start()
        print(f"🤖 Bot started monitoring channel: {Config.SOURCE_CHANNEL_ID}")
        
        # Start connection monitor
        asyncio.create_task(self.connection_monitor())

    async def connection_monitor(self):
        """Periodically check connection status"""
        while True:
            try:
                if not await self.app.is_connected():
                    print("⚠️ Bot disconnected, attempting reconnect...")
                    await self.app.start()
            except Exception as e:
                print(f"Connection monitor error: {e}")
            await asyncio.sleep(60)  # Check every minute

    async def stop(self):
        """Graceful stop with status check"""
        if await self.app.is_connected():
            await self.app.stop()
            print("✅ Bot stopped cleanly")
