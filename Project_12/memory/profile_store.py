import json
import os
import secrets
from datetime import datetime
import hashlib

from config import PROFILE_FILE, MEMORY_DATA_DIR


def _ensure_memory_dir():
    MEMORY_DATA_DIR.mkdir(parents=True, exist_ok=True)

def _load_profiles():

    if not os.path.exists(PROFILE_FILE):
        return {}

    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_profiles(data):

    _ensure_memory_dir()
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# =========================
# Generate Unique Patient ID
# =========================

def generate_patient_id():

    profiles = _load_profiles()

    while True:

        patient_id = (
            f"PSY-{secrets.token_hex(4).upper()}"
        )

        if patient_id not in profiles:
            return patient_id

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def email_exists(email):

    profiles = _load_profiles()

    for patient in profiles.values():

        if patient.get("email") == email:
            return True

    return False

# =========================
# Create New Patient
# =========================

def create_patient(
    name,
    age,
    gender,
    email,
    password
):

    profiles = _load_profiles()

    patient_id = generate_patient_id()

    profiles[patient_id] = {

        "patient_id": patient_id,

        "name": name,

        "age": age,

        "gender": gender,

        "email": email,

        "password": hash_password(password),

        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "reported_concerns": [],

        "important_notes": []
    }

    _save_profiles(profiles)

    return patient_id


# =========================
# Get Profile
# =========================

def get_profile(patient_id):

    profiles = _load_profiles()

    return profiles.get(patient_id)

def login_with_email(
    email,
    password
):

    profiles = _load_profiles()

    hashed = hash_password(password)

    for patient_id, patient in profiles.items():

        if (
            patient.get("email") == email
            and
            patient.get("password") == hashed
        ):

            return patient_id

    return None
# =========================
# Update Profile
# =========================

def update_profile(
    patient_id,
    concern=None,
    note=None
):

    profiles = _load_profiles()

    if patient_id not in profiles:
        return

    if concern:

        if concern not in profiles[patient_id]["reported_concerns"]:

            profiles[patient_id][
                "reported_concerns"
            ].append(concern)

    if note:

        if note not in profiles[patient_id]["important_notes"]:

            profiles[patient_id][
                "important_notes"
            ].append(note)

    _save_profiles(profiles)