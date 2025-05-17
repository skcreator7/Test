import asyncio
from aiohttp import web
from web import create_app
from telegram_bot import TelegramBot
from database import Database
from config import Config
import logging
import signal
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint for monitoring"""
    return web.json_response({"status": "ok", "service": "movie_bot"})

async def shutdown(sig, loop, app):
    """Graceful shutdown handler"""
    logger.info(f"Received {sig.name}, initiating shutdown...")
    
    # Cancel all running tasks
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    for task in tasks:
        task.cancel()
    
    # Wait for tasks to complete
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Stop components
    if 'bot' in app:
        logger.info("Stopping Telegram bot...")
        await app['bot'].stop()
    
    if 'db' in app:
        logger.info("Closing database connection...")
        await app['db'].close()
    
    loop.stop()
    logger.info("Shutdown complete")

async def init_app():
    """Initialize application components"""
    try:
        logger.info("Validating configuration...")
        Config.validate()
        
        logger.info("Initializing database...")
        db = Database(Config.MONGO_URI, Config.MONGO_DB)
        await db.initialize()
        
        logger.info("Starting Telegram bot...")
        bot = TelegramBot(db)
        await bot.initialize()
        
        logger.info("Creating web application...")
        app = create_app(db, bot)
        
        # Add health check endpoint
        app.router.add_get('/health', health_check)
        
        # Store dependencies
        app['db'] = db
        app['bot'] = bot
        
        return app
    
    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}", exc_info=True)
        sys.exit(1)

def handle_exception(loop, context):
    """Handle uncaught exceptions"""
    exc = context.get('exception')
    if exc:
        logger.critical(f"Unhandled exception: {exc}", exc_info=exc)
    else:
        logger.error(f"Unhandled context: {context}")
    sys.exit(1)

def main():
    """Main application entry point"""
    # Configure event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(handle_exception)
    
    try:
        logger.info("Starting application initialization...")
        app = loop.run_until_complete(init_app())
        
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(s, loop, app))
            )
        
        # Start web server
        logger.info(f"Starting web server on {Config.HOST}:{Config.PORT}")
        web.run_app(
            app,
            host=Config.HOST,
            port=Config.PORT,
            access_log=logger,
            shutdown_timeout=5.0
        )
    except Exception as e:
        logger.critical(f"Application failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        loop.close()
        logger.info("Application fully stopped")

if __name__ == "__main__":
    main()
