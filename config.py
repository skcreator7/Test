import os

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    STRING_SESSION = os.getenv("STRING_SESSION", "")
    SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", 0))
    BASE_URL = os.getenv("BASE_URL", "https://your-koyeb-app-url.com")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "movie_bot")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8080))

    @staticmethod
    def validate():
        assert Config.API_ID and Config.API_HASH and Config.STRING_SESSION and Config.SOURCE_CHANNEL_ID, "Missing Telegram config"
        assert Config.MONGO_URI and Config.MONGO_DB, "Missing Mongo config"
