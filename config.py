import os

class Config:
    # Telegram Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")

    # Source Channel ID (must be provided via Koyeb env vars)
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID"))

    # Web App Configuration
    HOST = os.getenv("HOST", "0.0.0.0")  # Accept requests from all IPs (good for deployment)
    PORT = int(os.getenv("PORT", 8000))  # Default to 8000, can be overridden by Koyeb

    # Base URL of the deployed site (used for generating shareable watch links)
    BASE_URL = os.getenv("BASE_URL", f"http://localhost:{PORT}")

    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "telegram_bot")

    # Secret Key (optional)
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
