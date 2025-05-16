import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from database import Database
from web import create_app
from config import Config
import logging
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_shutdown(app):
    """Handle application shutdown"""
    try:
        bot = app['bot']
        await bot.stop()
        logger.info("Bot stopped successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        logger.info("Application shutdown complete")

async def start_app():
    """Initialize and return the web application"""
    try:
        # Initialize database
        db = Database(Config.MONGO_URI)
        await db.initialize()
        logger.info("Database initialized successfully")

        # Initialize and start bot
        bot = TelegramBot(db)
        await bot.start()  # This now uses the properly implemented start() method
        logger.info("Telegram bot started successfully")

        # Create web application
        app = create_app(db, bot)
        app['db'] = db
        app['bot'] = bot
        app.on_shutdown.append(on_shutdown)

        return app
    except Exception as e:
        logger.error(f"Application initialization failed: {e}")
        raise

def main():
    """Main application entry point"""
    try:
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Set up signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, loop.stop)

        # Start application
        app = loop.run_until_complete(start_app())

        # Run web server
        web.run_app(
            app,
            port=Config.PORT,
            handle_signals=True,
            shutdown_timeout=60.0
        )
    except Exception as e:
        logger.error(f"Application failed: {e}")
        raise
    finally:
        logger.info("Application stopped")

if __name__ == "__main__":
    main()
