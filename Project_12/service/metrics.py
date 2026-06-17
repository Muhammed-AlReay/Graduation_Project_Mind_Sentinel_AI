"""In-process request metrics for monitoring."""
import threading
import time
from dataclasses import dataclass, field

_start_time = time.monotonic()
_lock = threading.Lock()


@dataclass
class MetricsSnapshot:
  uptime_seconds: float
  request_count: int
  error_count: int
  rate_limit_count: int
  auth_failure_count: int


class MetricsCollector:
  def __init__(self) -> None:
    self.request_count = 0
    self.error_count = 0
    self.rate_limit_count = 0
    self.auth_failure_count = 0

  def record_request(self, status_code: int) -> None:
    with _lock:
      self.request_count += 1
      if status_code >= 400:
        self.error_count += 1

  def record_rate_limit(self) -> None:
    with _lock:
      self.rate_limit_count += 1
      self.error_count += 1

  def record_auth_failure(self) -> None:
    with _lock:
      self.auth_failure_count += 1
      self.error_count += 1

  def snapshot(self) -> MetricsSnapshot:
    with _lock:
      return MetricsSnapshot(
        uptime_seconds=round(time.monotonic() - _start_time, 2),
        request_count=self.request_count,
        error_count=self.error_count,
        rate_limit_count=self.rate_limit_count,
        auth_failure_count=self.auth_failure_count,
      )


metrics = MetricsCollector()
