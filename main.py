import asyncio
from aiohttp import web
from telegram_bot import TelegramBot
from database import Database
from web import create_app
from config import Config
import logging
import signal
import socket
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Application:
    def __init__(self):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.db: Optional[Database] = None
        self.bot: Optional[TelegramBot] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

    async def initialize(self) -> web.Application:
        """Initialize all application components"""
        self._validate_config()
        self.loop = asyncio.get_event_loop()
        self._setup_signal_handlers()

        try:
            # Initialize database
            self.db = Database(Config.MONGO_URI)
            await self.db.initialize()
            logger.info("Database initialized successfully")

            # Initialize Telegram bot
            self.bot = TelegramBot(self.db)
            await self.bot.start()
            logger.info("Telegram bot started successfully")

            # Create web application
            app = create_app(self.db, self.bot)
            app.on_shutdown.append(self.on_shutdown)
            app['app_instance'] = self
            
            # Add health check endpoint
            app.router.add_get('/health', self.health_check)
            
            return app
        except Exception as e:
            logger.critical(f"Application initialization failed: {e}")
            await self.cleanup()
            raise

    def _validate_config(self):
        """Validate required configuration"""
        required = [
            'BOT_TOKEN', 'API_ID', 'API_HASH',
            'SOURCE_CHANNEL_ID', 'MONGO_URI'
        ]
        missing = [var for var in required if not getattr(Config, var, None)]
        if missing:
            raise ValueError(f"Missing required configuration: {missing}")

    def _setup_signal_handlers(self):
        """Setup OS signal handlers for graceful shutdown"""
        if not self.loop:
            return

        def shutdown_handler():
            logger.info("Received shutdown signal")
            asyncio.create_task(self.cleanup())

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                self.loop.add_signal_handler(sig, shutdown_handler)
            except NotImplementedError:
                logger.warning(f"Signal handling not supported for {sig}")

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        services = {
            'database': await self.db.is_healthy() if self.db else False,
            'bot': self.bot.is_running() if self.bot else False
        }
        status = all(services.values())
        
        return web.json_response({
            'status': 'up' if status else 'degraded',
            'services': services,
            'hostname': socket.gethost
