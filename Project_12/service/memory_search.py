"""Patient memory search across profiles, concerns, notes, QA logs, and chats."""
import json
import logging
from typing import Any

from config import CHAT_FILE, PROFILE_FILE, QA_FILE
from service.models import MemoryMatch

logger = logging.getLogger(__name__)


def _load_json(path) -> dict:
  if not path.exists():
    return {}
  try:
    with open(path, "r", encoding="utf-8") as f:
      return json.load(f)
  except (json.JSONDecodeError, OSError) as exc:
    logger.warning("Failed to load %s: %s", path, exc)
    return {}


def _score_match(query: str, text: str) -> bool:
  return query.lower() in text.lower()


def search_memory(
  query: str,
  patient_id: str | None = None,
  max_results: int = 10,
) -> list[MemoryMatch]:
  matches: list[MemoryMatch] = []
  profiles = _load_json(PROFILE_FILE)
  chats = _load_json(CHAT_FILE)
  qa_logs = _load_json(QA_FILE)

  patient_ids = [patient_id] if patient_id else list(profiles.keys())

  for pid in patient_ids:
    profile = profiles.get(pid, {})
    if not profile and patient_id:
      continue

    if profile:
      for field_name, match_type in [
        ("name", "profile"),
        ("email", "profile"),
        ("gender", "profile"),
      ]:
        value = str(profile.get(field_name, ""))
        if value and _score_match(query, value):
          matches.append(
            MemoryMatch(
              patient_id=pid,
              match_type=match_type,
              content=value,
              metadata={"field": field_name},
            )
          )

      for concern in profile.get("reported_concerns", []):
        if _score_match(query, concern):
          matches.append(
            MemoryMatch(
              patient_id=pid,
              match_type="concern",
              content=concern,
            )
          )

      for note in profile.get("important_notes", []):
        if _score_match(query, note):
          matches.append(
            MemoryMatch(
              patient_id=pid,
              match_type="note",
              content=note[:500],
            )
          )

    for entry in qa_logs.get(pid, []):
      question = entry.get("question", "")
      answer = entry.get("answer", "")
      if _score_match(query, question):
        matches.append(
          MemoryMatch(
            patient_id=pid,
            match_type="qa",
            content=question,
            metadata={"timestamp": entry.get("timestamp"), "answer_preview": answer[:200]},
          )
        )
      elif _score_match(query, answer):
        matches.append(
          MemoryMatch(
            patient_id=pid,
            match_type="qa",
            content=answer[:500],
            metadata={"timestamp": entry.get("timestamp"), "matched": "answer"},
          )
        )

    for msg in chats.get(pid, []):
      content = msg.get("content", "")
      if _score_match(query, content):
        matches.append(
          MemoryMatch(
            patient_id=pid,
            match_type="chat",
            content=content[:500],
            metadata={"role": msg.get("role")},
          )
        )

  return matches[:max_results]
