import asyncio
import json

import requests
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from config import ERROR_MESSAGE, TELEGRAM_BOT_TOKEN, ensure_directories
from ollama_client import process_user_message


async def cevap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Telegram mesajını alır ve işleme katmanına iletir. Ayrıca kullanıcı 'detay' istediğinde arka plan follow-up'ları gönderir."""
    if update.message is None or update.message.text is None or update.effective_user is None:
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        # If user asks for pending details, return them and clear
        if text.lower() in {"detay", "detaylar", "/detay", "/detaylar"}:
            from memory_manager import pop_pending_followups

            followups = await asyncio.to_thread(pop_pending_followups, user_id)
            if not followups:
                await update.message.reply_text("Şu anda gönderilecek detay yok.")
            else:
                for f in followups:
                    # send each follow-up as separate message to avoid large blobs
                    await update.message.reply_text(f)
            return

        reply_text = await asyncio.to_thread(process_user_message, user_id, text)
        await update.message.reply_text(reply_text)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, requests.RequestException):
        # Ana dosya sadece köprü görevi görür; kullanıcıya sade hata mesajı döner.
        await update.message.reply_text(ERROR_MESSAGE)


def main() -> None:
    ensure_directories()
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is missing.")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, cevap))
    app.run_polling()


if __name__ == "__main__":
    main()
