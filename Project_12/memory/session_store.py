import json
import os
from datetime import datetime

from config import SESSION_FILE, MEMORY_DATA_DIR


def _ensure_memory_dir():
    MEMORY_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_sessions():

    if not os.path.exists(
        SESSION_FILE
    ):
        return {}

    with open(
        SESSION_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def _save_sessions(data):

    _ensure_memory_dir()
    with open(
        SESSION_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def create_session(
    patient_id
):

    data = _load_sessions()

    if patient_id not in data:
        data[patient_id] = []

    session = {

        "start_time":
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "messages": []
    }

    data[patient_id].append(
        session
    )

    _save_sessions(data)

    return len(
        data[patient_id]
    ) - 1


def add_message(
    patient_id,
    session_index,
    role,
    content
):

    data = _load_sessions()

    data[patient_id][
        session_index
    ]["messages"].append({

        "role": role,

        "content": content

    })

    _save_sessions(data)