"""Abuse protection: duplicate-request flood detection."""
import hashlib
import threading
import time
from collections import defaultdict

from config import ABUSE_DEDUP_WINDOW_SECONDS, ABUSE_MAX_IDENTICAL_REQUESTS

_lock = threading.Lock()
_recent: dict[str, list[tuple[float, str]]] = defaultdict(list)


def _fingerprint(path: str, client_ip: str, body: bytes) -> str:
  digest = hashlib.sha256(body).hexdigest()[:16]
  return f"{client_ip}:{path}:{digest}"


def check_abuse(path: str, client_ip: str, body: bytes) -> tuple[bool, str]:
  """
  Detect rapid identical requests (prompt flooding / retry abuse).
  Returns (allowed, reason).
  """
  if not body:
    return True, "ok"

  now = time.monotonic()
  fp = _fingerprint(path, client_ip, body)
  window = ABUSE_DEDUP_WINDOW_SECONDS

  with _lock:
    entries = [(t, h) for t, h in _recent[fp] if now - t < window]
    identical_count = len(entries)

    if identical_count >= ABUSE_MAX_IDENTICAL_REQUESTS:
      _recent[fp] = entries
      return False, "duplicate_flood"

    entries.append((now, fp))
    _recent[fp] = entries

  return True, "ok"
