import json
from pathlib import Path

from config import USERS_DIR


def default_user_data() -> dict:
    return {
        "profile": {
            "name": "",
            "interests": [],
            "facts": [],
        },
        "chat_history": [],
        "pending_memory": [],
    }


def user_file_path(user_id: int) -> Path:
    return USERS_DIR / f"{user_id}.json"


def normalize_user_data(data: object) -> dict:
    """Eksik veya bozuk veriyi güvenli varsayılan yapıya çevir."""
    if not isinstance(data, dict):
        return default_user_data()

    profile = data.get("profile")
    if not isinstance(profile, dict):
        profile = {}

    interests = profile.get("interests")
    facts = profile.get("facts")
    chat_history = data.get("chat_history")
    pending = data.get("pending_memory")

    return {
        "profile": {
            "name": str(profile.get("name", "") or ""),
            "interests": [str(item) for item in interests if item is not None]
            if isinstance(interests, list)
            else [],
            "facts": [str(item) for item in facts if item is not None]
            if isinstance(facts, list)
            else [],
        },
        "chat_history": chat_history if isinstance(chat_history, list) else [],
        "pending_memory": [str(item) for item in pending if item is not None]
        if isinstance(pending, list)
        else [],
    }


def ensure_user_data(user_id: int) -> dict:
    """Kullanıcı dosyasını yoksa oluşturur, varsa güvenli biçimde yükler."""
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    path = user_file_path(user_id)

    if not path.exists():
        data = default_user_data()
        save_user_data(user_id, data)
        return data

    try:
        with path.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
    except (OSError, json.JSONDecodeError):
        loaded = default_user_data()

    data = normalize_user_data(loaded)
    save_user_data(user_id, data)
    return data


def save_user_data(user_id: int, data: dict) -> None:
    """Kullanıcı verisini JSON olarak kaydeder."""
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    path = user_file_path(user_id)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_profile(user_id: int) -> dict:
    """Kullanıcının profil bölümünü döndürür."""
    return ensure_user_data(user_id)["profile"]


def merge_unique(existing: list[str], additions: list[str]) -> list[str]:
    """Tekrarlayan değerleri eklemeden birleştirir."""
    result = list(existing)
    seen = {item for item in result}
    for item in additions:
        cleaned = item.strip()
        if cleaned and cleaned not in seen:
            result.append(cleaned)
            seen.add(cleaned)
    return result


def remove_matching_entries(existing: list[str], removals: list[str]) -> list[str]:
    """Listeden silinmesi istenen kalıcı bilgileri çıkarır."""
    removal_set = {item.strip() for item in removals if item.strip()}
    return [item for item in existing if item not in removal_set]


def update_profile(
    user_id: int,
    *,
    name: str | None = None,
    interests_to_add: list[str] | None = None,
    facts_to_add: list[str] | None = None,
    facts_to_remove: list[str] | None = None,
    overwrite_name: bool = False,
) -> dict:
    """Kullanıcının kalıcı profil bilgilerini günceller.

    overwrite_name: Eğer True ise verilen name değeri varsa mevcut ismin üzerine yazar.
    """
    data = ensure_user_data(user_id)
    profile = data["profile"]

    if name and (overwrite_name or not profile.get("name")):
        profile["name"] = name.strip()

    if interests_to_add:
        profile["interests"] = merge_unique(profile["interests"], interests_to_add)

    if facts_to_add:
        profile["facts"] = merge_unique(profile["facts"], facts_to_add)

    if facts_to_remove:
        profile["facts"] = remove_matching_entries(profile["facts"], facts_to_remove)

    save_user_data(user_id, data)
    return profile


def add_pending_memory(user_id: int, item: str) -> None:
    """Kullanıcının onay bekleyen hafıza girdisini ekler."""
    data = ensure_user_data(user_id)
    pending = data.get("pending_memory", [])
    pending.append(str(item))
    data["pending_memory"] = pending
    save_user_data(user_id, data)


def get_pending_memory(user_id: int) -> list:
    data = ensure_user_data(user_id)
    return data.get("pending_memory", [])


def confirm_pending_memory(user_id: int, index: int | None = None) -> dict:
    """Bekleyen girdileri kalıcı "facts" listesine taşır. index verilmezse tümünü onaylar."""
    data = ensure_user_data(user_id)
    pending = data.get("pending_memory", [])
    if not pending:
        return data["profile"]
    to_confirm = pending if index is None else [pending[index]]
    profile = data["profile"]
    facts = profile.get("facts", [])
    for itm in to_confirm:
        if itm not in facts:
            facts.append(itm)
    profile["facts"] = facts
    if index is None:
        data["pending_memory"] = []
    else:
        # remove the confirmed item
        del data["pending_memory"][index]
    save_user_data(user_id, data)
    return profile
