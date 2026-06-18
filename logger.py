import logging
from pathlib import Path

from config import LOGS_DIR

LOGGER_NAME = "kaju_bot"
LOG_FILE = LOGS_DIR / "bot.log"
ERROR_FILE = LOGS_DIR / "error.log"


def get_logger() -> logging.Logger:
    """Uygulama için ortak logger kurar."""
    Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
    LOG_FILE.touch(exist_ok=True)
    ERROR_FILE.touch(exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    info_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(ERROR_FILE, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    return logger


LOGGER = get_logger()
