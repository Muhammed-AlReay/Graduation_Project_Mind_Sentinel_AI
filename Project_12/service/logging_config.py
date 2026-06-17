"""Structured logging configuration for the Project_12 service."""
import logging
import sys
from datetime import datetime, timezone

from config import LOG_LEVEL


class JsonFormatter(logging.Formatter):
  """Emit single-line JSON-ish log records for production log aggregation."""

  def format(self, record: logging.LogRecord) -> str:
    payload = {
      "timestamp": datetime.now(timezone.utc).isoformat(),
      "level": record.levelname,
      "logger": record.name,
      "message": record.getMessage(),
    }
    if record.exc_info and record.exc_info[1]:
      payload["exception"] = self.formatException(record.exc_info)
    return str(payload)


def setup_logging() -> None:
  root = logging.getLogger()
  root.handlers.clear()
  handler = logging.StreamHandler(sys.stdout)
  handler.setFormatter(JsonFormatter())
  root.addHandler(handler)
  root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
  logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
