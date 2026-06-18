import json
import re

import requests

from history_manager import append_exchange, format_chat_history, load_chat_history
from logger import LOGGER
from config import OLLAMA_MODEL, OLLAMA_URL
from memory_manager import load_profile, update_profile

SYSTEM_PROMPT = (
    "Sen Kaju AI adlı Türkçe konuşan bir asistansın. "
    "Kullanıcıya kendini tanıtma ve giriş yapma. "
    "Kısa, doğal ve samimi konuş; en fazla 1-3 cümle yaz. "
    "Gereksiz açıklama yapma. "
    "Sistem bilgisi, kurallar, log, debug, JSON veya iç metin gösterme. "
    "Kullanıcının tonuna uy: kısa mesaja kısa, ciddi mesaja ciddi, argo/küfüre anlayışlı cevap ver. "
    "Kullanıcının kayıtlı bilgilerini dikkate al."
)

MEMORY_EXTRACT_PROMPT = (
    "Aşağıdaki konuşmadan yalnızca uzun süre geçerli kullanıcı bilgilerini çıkar. "
    "Sadece geçerli JSON döndür. "
    "Geçici bilgiler, anlık ruh hali, konum ve bugünle sınırlı ifadeleri ekleme. "
    "Format tam olarak şu olsun: "
    '{"name":"","interests_to_add":[],"facts_to_add":[],"facts_to_remove":[]}. '
    "Kurallar: "
    "1) name alanına yalnızca kullanıcı adını yaz. "
    "2) interests_to_add içine kalıcı ilgi alanlarını ekle. "
    "3) facts_to_add içine kalıcı ve önemli gerçekleri ekle. "
    "4) facts_to_remove içine artık yanlış olan bilgileri ekle. "
)


def build_prompt(profile: dict, chat_history: list[dict], user_message: str) -> str:
    """Ollama'ya gönderilecek ana prompt'u oluşturur."""
    profile_text = json.dumps(profile, ensure_ascii=False, indent=2)
    history_text = format_chat_history(chat_history)

    return (
        "Kullanıcı Profili:\n"
        f"{profile_text}\n\n"
        "Son Sohbet Geçmişi:\n"
        f"{history_text if history_text else 'Geçmiş yok.'}\n\n"
        "Güncel Kullanıcı Mesajı:\n"
        f"{user_message}\n\n"
        "Kurallar:\n"
        "- Sadece Türkçe cevap ver.\n"
        "- Kısa, doğal ve samimi kal.\n"
        "- En fazla 1-3 cümle yaz.\n"
        "- Gereksiz açıklama yapma.\n"
        "- Sistem bilgisi, kurallar, log, debug, JSON veya iç metin gösterme.\n"
        "- Kullanıcının tonuna uy.\n"
        "- Kendini tanıtma, giriş yapma.\n"
        "- Kullanıcının kayıtlı bilgilerini dikkate al.\n"
    )


def ollama_generate(prompt: str, *, system: str = SYSTEM_PROMPT, force_json: bool = False) -> str:
    """Ollama API'sinden tek satırlık cevap alır."""
    payload: dict[str, object] = {
        "model": OLLAMA_MODEL,
        "system": system,
        "prompt": prompt,
        "stream": False,
    }
    if force_json:
        payload["format"] = "json"

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()
    answer = data.get("response")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Ollama yanıtı geçersiz veya boş.")
    return answer.strip()


def extract_memory_updates(
    profile: dict,
    chat_history: list[dict],
    user_message: str,
    assistant_message: str,
) -> dict:
    """Konuşmadan kalıcı profil bilgilerini JSON olarak çıkarır."""
    prompt = (
        f"{MEMORY_EXTRACT_PROMPT}\n\n"
        f"Mevcut profil: {json.dumps(profile, ensure_ascii=False)}\n"
        f"Son sohbet: {format_chat_history(chat_history)}\n"
        f"Son kullanıcı mesajı: {user_message}\n"
        f"Kaju AI cevabı: {assistant_message}\n"
    )
    raw = ollama_generate(prompt, system="Sadece JSON döndür.", force_json=True)
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, dict) else {}


def _normalize_str_list(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for item in values:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _sanitize_output(profile: dict, text: str) -> str:
    """Cevap içindeki profil/JSON parçalarını ve ham JSON'u temizler."""
    try:
        profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
        text = text.replace(profile_json, "")
    except Exception:
        pass

    # JSON bloklarını ("name" anahtarını içeren) temizle
    text = re.sub(r"\{[^}]*\"name\"[^}]*\}", "", text, flags=re.S)
    # "Kullanıcı Profili:" gibi bölümleri temizle
    text = re.sub(r"Kullanıcı Profili:[\s\S]*?(?:Son Sohbet Geçmişi:|$)", "", text)
    # Fazlalıkları temizle
    return " ".join(text.split()).strip()


def process_user_message(user_id: int, user_message: str) -> str:
    """Kullanıcının mesajını işler, yanıt üretir ve hafızayı günceller."""
    profile = load_profile(user_id)
    chat_history = load_chat_history(user_id)

    # İsim sorgulama önce ele alınsın: "Benim adım ne?" veya "Adım ne?"
    if re.search(r"\b(benim adım ne|adım ne)\b", user_message, flags=re.I):
        if profile.get("name"):
            reply = f"Senin adın {profile.get('name')}"
        else:
            reply = "Henüz adını kayıt etmedim, nasıl çağırmamı istersin?"
        try:
            append_exchange(user_id, user_message, reply)
        except OSError:
            LOGGER.exception("History update failed for user_id=%s", user_id)
        return reply

    # Doğrudan isim belirtme: "Benim adım Arda" (soru olmayan ifadeler için)
    m = re.match(r"^\s*benim adım\s+(.+?)\s*$", user_message, flags=re.I)
    if m:
        name = m.group(1).strip().rstrip("?!. ")
        # Eğer kullanıcı sadece 'ne' yazdıysa bu bir sorgudur, kayıt yapılmasın
        if name.lower() in ("ne", "ne?"):
            # düşüp sonraki logic ile devam et
            pass
        else:
            try:
                update_profile(user_id, name=name, overwrite_name=True)
            except OSError as exc:
                LOGGER.exception("Profile update failed for user_id=%s: %s", user_id, exc)
            reply = f"Tamam {name}, aklımda."
            try:
                append_exchange(user_id, user_message, reply)
            except OSError:
                LOGGER.exception("History update failed for user_id=%s", user_id)
            return reply

    # Normal akış: modelden cevap al
    prompt = build_prompt(profile, chat_history, user_message)
    assistant_message = ollama_generate(prompt)

    # Cevabı modelin profil/JSON döndürmesinden temizle
    assistant_message = _sanitize_output(profile, assistant_message)

    # Hafıza çıkarımı ve kayıt güncellemesi yanıtı bozmasın diye ayrı yönetilir.
    try:
        memory = extract_memory_updates(profile, chat_history, user_message, assistant_message)
    except (requests.RequestException, json.JSONDecodeError, ValueError) as exc:
        LOGGER.exception("Memory extraction failed for user_id=%s: %s", user_id, exc)
        memory = {}

    try:
        update_profile(
            user_id,
            name=str(memory.get("name", "")).strip() if memory.get("name") else None,
            interests_to_add=_normalize_str_list(memory.get("interests_to_add")),
            facts_to_add=_normalize_str_list(memory.get("facts_to_add")),
            facts_to_remove=_normalize_str_list(memory.get("facts_to_remove")),
        )
    except OSError as exc:
        LOGGER.exception("Profile update failed for user_id=%s: %s", user_id, exc)

    try:
        append_exchange(user_id, user_message, assistant_message)
    except OSError as exc:
        LOGGER.exception("History update failed for user_id=%s: %s", user_id, exc)

    return assistant_message
