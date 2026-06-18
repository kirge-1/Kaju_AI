import asyncio
import json

import requests
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from config import ERROR_MESSAGE, TOKEN, ensure_directories
from ollama_client import process_user_message


async def cevap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Telegram mesajını alır ve işleme katmanına iletir."""
    if update.message is None or update.message.text is None or update.effective_user is None:
        return

    user_id = update.effective_user.id

    try:
        reply_text = await asyncio.to_thread(process_user_message, user_id, update.message.text)
        await update.message.reply_text(reply_text)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, requests.RequestException):
        # Ana dosya sadece köprü görevi görür; kullanıcıya sade hata mesajı döner.
        await update.message.reply_text(ERROR_MESSAGE)


def main() -> None:
    ensure_directories()
    if not TOKEN:
        raise RuntimeError("TOKEN environment variable is missing.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, cevap))
    app.run_polling()


if __name__ == "__main__":
    main()
