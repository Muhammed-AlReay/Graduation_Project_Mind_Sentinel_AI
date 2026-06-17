#!/usr/bin/env python3
"""Generate realistic mock data for doctor dashboard testing."""
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

EMOTIONS = ["calm", "anxiety", "stress", "sadness", "hope", "anger", "fear"]
ACTIVITIES = ["breathing", "cbt_flow", "journaling", "mindfulness", "video"]
GENDERS = ["male", "female"]
NOTIFICATION_TYPES = ["registration", "login", "google_login", "new_activity", "crisis_alert", "safety_alert"]


def gen_users(n=20):
  users = []
  for i in range(n):
    age = random.randint(18, 55)
    users.append({
      "id": str(uuid.uuid4()),
      "nickname": f"Patient_{i + 1}",
      "age": age,
      "gender": random.choice(GENDERS),
      "email": f"patient{i + 1}@mock.test",
      "created_at": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
    })
  return users


def gen_doctors(n=3):
  return [{
    "id": str(uuid.uuid4()),
    "name": f"Dr. {name}",
    "email": f"dr.{name.lower()}@mock.test",
    "specialty": "Psychiatry",
  } for name in ["Sentinel", "Rahman", "Chen"][:n]]


def gen_sessions(users, per_user=5):
  sessions = []
  for u in users:
    for _ in range(random.randint(1, per_user)):
      sessions.append({
        "id": str(uuid.uuid4()),
        "user_id": u["id"],
        "started_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
        "summary_emotion": random.choice(EMOTIONS),
        "summary_intensity": round(random.uniform(0.2, 0.9), 2),
        "message_count": random.randint(4, 40),
      })
  return sessions


def gen_crisis_flags(users):
  flags = []
  for u in random.sample(users, min(3, len(users))):
    flags.append({
      "id": str(uuid.uuid4()),
      "user_id": u["id"],
      "severity": random.choice(["acute", "elevated"]),
      "category": random.choice(["SUICIDE_RISK", "SELF_HARM", "CRISIS_DISTRESS"]),
      "message": "Mock crisis message for testing",
      "status": random.choice(["open", "resolved"]),
      "created_at": datetime.now().isoformat(),
    })
  return flags


def gen_notifications(users):
  notifs = []
  for u in users[:10]:
    for nt in random.sample(NOTIFICATION_TYPES, 2):
      notifs.append({
        "id": str(uuid.uuid4()),
        "user_id": u["id"],
        "type": nt,
        "title": f"Mock {nt}",
        "read": random.choice([True, False]),
        "created_at": datetime.now().isoformat(),
      })
  return notifs


def gen_recommendations(users):
  recs = []
  for u in users:
    recs.append({
      "user_id": u["id"],
      "anxiety_score": round(random.uniform(0, 1), 2),
      "stress_score": round(random.uniform(0, 1), 2),
      "depression_indicators": round(random.uniform(0, 1), 2),
      "activities": random.sample(ACTIVITIES, 2),
      "coping_strategies": ["deep breathing", "grounding exercise", "journaling"],
      "videos": ["intro-to-cbt", "mindfulness-101"],
    })
  return recs


def main():
  users = gen_users(25)
  data = {
    "generated_at": datetime.now().isoformat(),
    "users": users,
    "doctors": gen_doctors(),
    "sessions": gen_sessions(users),
    "crisis_flags": gen_crisis_flags(users),
    "notifications": gen_notifications(users),
    "recommendations": gen_recommendations(users),
    "analytics": {
      "total_patients": len(users),
      "male": sum(1 for u in users if u["gender"] == "male"),
      "female": sum(1 for u in users if u["gender"] == "female"),
      "under_30": sum(1 for u in users if u["age"] < 30),
      "over_30": sum(1 for u in users if u["age"] >= 30),
    },
  }

  out = Path(__file__).parent.parent / "mock_data" / "mock_dataset.json"
  out.parent.mkdir(exist_ok=True)
  out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
  print(f"Generated mock data: {out}")
  print(f"  Users: {len(data['users'])}, Sessions: {len(data['sessions'])}")


if __name__ == "__main__":
  main()
