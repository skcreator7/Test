from aiohttp import web
import logging
from config import Config

logger = logging.getLogger(__name__)

def setup_routes(app, db, bot):
    @app.get('/')
    async def index(request):
        return web.Response(text="Welcome to the Telegram Bot Server")
    
    @app.on_shutdown.append
    async def on_shutdown(app):
        logger.info("🛑 Starting shutdown sequence...")
        try:
            await bot.stop()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
        finally:
            logger.info("✅ Cleanup complete")
