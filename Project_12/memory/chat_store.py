import json
import os

from config import CHAT_FILE, MEMORY_DATA_DIR


def _ensure_memory_dir():
    MEMORY_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_chats():

    if not os.path.exists(CHAT_FILE):
        return {}

    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_chats(data):

    _ensure_memory_dir()
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def get_chat_history(
    user_id,
    max_messages=10
):

    chats = _load_chats()

    messages = chats.get(
        user_id,
        []
    )

    return messages[-max_messages:]


def save_message(
    user_id,
    role,
    content
):

    chats = _load_chats()

    if user_id not in chats:
        chats[user_id] = []

    chats[user_id].append({
        "role": role,
        "content": content
    })

    _save_chats(chats)