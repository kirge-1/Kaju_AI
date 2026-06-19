import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
USERS_DIR = BASE_DIR / "users"
LOGS_DIR = BASE_DIR / "logs"


load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TOKEN", "")).strip()
TOKEN = TELEGRAM_BOT_TOKEN
ERROR_MESSAGE = os.getenv("ERROR_MESSAGE", "Şu anda cevap oluşturamıyorum, lütfen tekrar dene.").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3").strip()
# FAST_MODEL: birinci seviyede hızlı, hafif model id'si (opsiyonel)
FAST_MODEL = os.getenv("FAST_MODEL", "").strip()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip()
MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "20"))
# Cache TTL saniye olarak (local LRU cache için)
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
# Streaming mekanizmasını etkinleştir (altyapı gerekli)
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "false").lower() in ("1","true","yes")


def ensure_directories() -> None:
    """Gerekli proje klasörlerini oluşturur."""
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


ensure_directories()
