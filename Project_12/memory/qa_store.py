import json
import os
from datetime import datetime

from config import QA_FILE, MEMORY_DATA_DIR


def _ensure_memory_dir():
    MEMORY_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_qa():

    if not os.path.exists(QA_FILE):
        return {}

    with open(QA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_qa(data):

    _ensure_memory_dir()
    with open(QA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def save_qa(
    patient_id,
    question,
    answer
):

    data = _load_qa()

    if patient_id not in data:
        data[patient_id] = []

    data[patient_id].append({

        "timestamp":
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "question": question,

        "answer": answer

    })

    _save_qa(data)


def get_patient_qa(
    patient_id
):

    data = _load_qa()

    return data.get(
        patient_id,
        []
    )