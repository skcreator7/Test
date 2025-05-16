import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from database import Database
from web import create_app
from config import Config
import logging
import signal
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def on_shutdown(app: web.Application) -> None:
    """Handle graceful shutdown of application components"""
    logger.info("Starting shutdown sequence...")
    
    shutdown_errors = False
    try:
        if 'bot' in app:
            logger.info("Stopping Telegram bot...")
            await app['bot'].stop()
    except Exception as e:
        logger.error(f"Bot shutdown error: {e}")
        shutdown_errors = True
    
    try:
        if 'db' in app:
            logger.info("Closing database connections...")
            await app['db'].close()
    except Exception as e:
        logger.error(f"Database shutdown error: {e}")
        shutdown_errors = True
    
    logger.info("Shutdown complete" + (" with errors" if shutdown_errors else ""))

def validate_config() -> None:
    """Validate required configuration before starting"""
    required_config = {
        'BOT_TOKEN': str,
        'API_ID': int,
        'API_HASH': str,
        'SOURCE_CHANNEL_ID': int,
        'MONGO_URI': str,
        'BASE_URL': str
    }
    
    errors = []
    for var, var_type in required_config.items():
        value = getattr(Config, var, None)
        if value is None:
            errors.append(f"{var} is not set")
        elif not isinstance(value, var_type):
            errors.append(f"{var} should be {var_type.__name__}, got {type(value).__name__}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))

async def start_app() -> web.Application:
    """Initialize and configure the application"""
    logger.info("Starting application initialization...")
    
    # Initialize database
    logger.info("Connecting to database...")
    db = Database(Config.MONGO_URI, db_name=Config.MONGO_DB)
    await db.initialize()
    
    # Initialize bot
    logger.info("Starting Telegram bot...")
    bot = TelegramBot(db)
    await bot.initialize()  # Changed from start() to be more explicit
    
    # Create web application
    logger.info("Creating web application...")
    app = create_app(db, bot)
    app['db'] = db
    app['bot'] = bot
    
    # Add shutdown handler
    app.on_shutdown.append(on_shutdown)
    
    # Add health check route if not already present
    if 'health' not in app.router:
        app.router.add_get('/health', lambda r: web.json_response({'status': 'ok'}))
    
    logger.info("Application initialization complete")
    return app

def setup_signals(loop: asyncio.AbstractEventLoop) -> None:
    """Configure OS signal handlers"""
    def shutdown_signal():
        logger.info("Received shutdown signal")
        loop.stop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, shutdown_signal)
        except NotImplementedError:
            logger.warning(f"Signal handling not supported for {sig}")

async def shutdown_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel all running tasks during shutdown"""
    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
    if pending:
        logger.info(f"Cancelling {len(pending)} pending tasks...")
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

def main() -> None:
    """Main application entry point"""
    try:
        # Validate configuration first
        validate_config()
        
        # Set up event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Configure signal handlers
        setup_signals(loop)
        
        # Initialize application
        app = loop.run_until_complete(start_app())
        
        # Set up web runner
        runner = web.AppRunner(app)
        loop.run_until_complete(runner.setup())
        
        # Start web server
        site = web.TCPSite(runner, Config.HOST, Config.PORT)
        loop.run_until_complete(site.start())
        
        logger.info(f"Server running on http://{Config.HOST}:{Config.PORT}")
        
        # Run event loop
        loop.run_forever()
        
    except Exception as e:
        logger.critical(f"Application failed to start: {e}", exc_info=True)
        raise
    finally:
        try:
            logger.info("Beginning cleanup...")
            loop.run_until_complete(shutdown_tasks(loop))
            
            # Ensure all transports are closed
            asyncio.set_event_loop(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
            
            if hasattr(loop, 'close'):
                loop.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        finally:
            logger.info("Application stopped")

if __name__ == "__main__":
    main()
