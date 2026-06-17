"""Per-IP sliding-window rate limiter."""
import threading
import time
from collections import defaultdict
from typing import Optional

from config import (
  RATE_LIMIT_CHAT,
  RATE_LIMIT_CRISIS,
  RATE_LIMIT_MEMORY,
  RATE_LIMIT_WINDOW_SECONDS,
)

_lock = threading.Lock()
_buckets: dict[str, list[float]] = defaultdict(list)

_RATE_LIMITED_PATHS = {
  "/chat": RATE_LIMIT_CHAT,
  "/crisis-detection": RATE_LIMIT_CRISIS,
  "/memory-search": RATE_LIMIT_MEMORY,
}


def _client_key(ip: str, path: str) -> str:
  return f"{ip}:{path}"


def _prune(timestamps: list[float], now: float, window: float) -> list[float]:
  cutoff = now - window
  return [t for t in timestamps if t > cutoff]


def check_rate_limit(path: str, client_ip: str) -> tuple[bool, Optional[int]]:
  """
  Returns (allowed, retry_after_seconds).
  retry_after_seconds is set when blocked.
  """
  limit = _RATE_LIMITED_PATHS.get(path)
  if limit is None:
    return True, None

  now = time.monotonic()
  key = _client_key(client_ip, path)

  with _lock:
    window = RATE_LIMIT_WINDOW_SECONDS
    timestamps = _prune(_buckets[key], now, window)

    if len(timestamps) >= limit:
      oldest = timestamps[0]
      retry_after = max(1, int(window - (now - oldest)) + 1)
      _buckets[key] = timestamps
      return False, retry_after

    timestamps.append(now)
    _buckets[key] = timestamps
    return True, None
