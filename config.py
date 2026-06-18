import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
USERS_DIR = BASE_DIR / "users"
LOGS_DIR = BASE_DIR / "logs"


def _load_env_file(path: Path) -> None:
    """Yerel .env dosyasını ek bağımlılık olmadan yükler."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ[key] = value


_load_env_file(BASE_DIR / ".env")

TOKEN = os.getenv("TOKEN", "").strip()
ERROR_MESSAGE = os.getenv("ERROR_MESSAGE", "Şu anda cevap oluşturamıyorum, lütfen tekrar dene.")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral").strip()
MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "20"))


def ensure_directories() -> None:
    """Gerekli proje klasörlerini oluşturur."""
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


ensure_directories()
