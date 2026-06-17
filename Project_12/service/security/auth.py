"""Service-to-service API key authentication."""
import secrets
from typing import Optional

from fastapi import Request

from config import API_KEY, AUTH_ENABLED, PUBLIC_PATHS


def _extract_token(request: Request) -> Optional[str]:
  auth_header = request.headers.get("Authorization", "")
  if auth_header.lower().startswith("bearer "):
    return auth_header[7:].strip()

  api_key_header = request.headers.get("X-API-Key", "").strip()
  if api_key_header:
    return api_key_header

  return None


def is_public_path(path: str) -> bool:
  return path in PUBLIC_PATHS


def verify_request(request: Request) -> tuple[bool, str]:
  """
  Returns (authorized, reason).
  reason is one of: ok | missing_key_config | missing_token | invalid_token
  """
  if not AUTH_ENABLED:
    return True, "ok"

  if is_public_path(request.url.path):
    return True, "ok"

  if not API_KEY:
    return False, "missing_key_config"

  token = _extract_token(request)
  if not token:
    return False, "missing_token"

  if secrets.compare_digest(token, API_KEY):
    return True, "ok"

  return False, "invalid_token"
