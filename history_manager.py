from memory_manager import ensure_user_data, save_user_data
from config import MAX_CHAT_HISTORY

def trim_chat_history(chat_history: list[dict]) -> list[dict]:
    """Yalnızca son 20 kaydı tutar."""
    if len(chat_history) <= MAX_CHAT_HISTORY:
        return chat_history
    return chat_history[-MAX_CHAT_HISTORY:]


def load_chat_history(user_id: int) -> list[dict]:
    """Kullanıcının kayıtlı sohbet geçmişini döndürür."""
    data = ensure_user_data(user_id)
    chat_history = data.get("chat_history", [])
    return chat_history if isinstance(chat_history, list) else []


def append_exchange(user_id: int, user_message: str, assistant_message: str) -> list[dict]:
    """Kullanıcı ve bot mesajını geçmişe ekler ve dosyayı günceller."""
    data = ensure_user_data(user_id)
    chat_history = data.get("chat_history", [])
    if not isinstance(chat_history, list):
        chat_history = []

    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": assistant_message})
    data["chat_history"] = trim_chat_history(chat_history)
    save_user_data(user_id, data)
    return data["chat_history"]


def format_chat_history(chat_history: list[dict]) -> str:
    """Ollama prompt'u için okunabilir sohbet geçmişi üretir."""
    lines: list[str] = []
    for item in chat_history[-MAX_CHAT_HISTORY:]:
        role = item.get("role", "")
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        if role == "user":
            lines.append(f"Kullanıcı: {content}")
        elif role == "assistant":
            lines.append(f"Kaju AI: {content}")
    return "\n".join(lines)
