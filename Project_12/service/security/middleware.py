"""Security middleware: auth, rate limiting, abuse protection, request logging."""
import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import MAX_REQUEST_BODY_BYTES
from service.metrics import metrics
from service.models import ErrorResponse
from service.security.abuse import check_abuse
from service.security.auth import verify_request
from service.security.rate_limit import check_rate_limit

logger = logging.getLogger("project12.access")


def _client_ip(request: Request) -> str:
  forwarded = request.headers.get("X-Forwarded-For", "")
  if forwarded:
    return forwarded.split(",")[0].strip()
  if request.client:
    return request.client.host
  return "unknown"


class SecurityMiddleware(BaseHTTPMiddleware):
  def _log_request(self, method: str, path: str, status: int, duration_ms: float, client_ip: str) -> None:
    logger.info(
      '{"event":"request","method":"%s","path":"%s","status_code":%d,'
      '"duration_ms":%.2f,"client_ip":"%s"}',
      method,
      path,
      status,
      duration_ms,
      client_ip,
    )

  async def dispatch(self, request: Request, call_next):
    path = request.url.path
    method = request.method
    client_ip = _client_ip(request)
    start = time.monotonic()

    def respond(status_code: int, error: str, code: str, detail: str, headers: dict | None = None):
      duration_ms = (time.monotonic() - start) * 1000
      metrics.record_request(status_code)
      self._log_request(method, path, status_code, duration_ms, client_ip)
      return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=error, detail=detail, code=code).model_dump(),
        headers=headers or {},
      )

    # Payload size pre-check via Content-Length
    if method in ("POST", "PUT", "PATCH"):
      content_length = request.headers.get("content-length")
      if content_length:
        try:
          if int(content_length) > MAX_REQUEST_BODY_BYTES:
            return respond(
              413,
              "payload_too_large",
              "PAYLOAD_TOO_LARGE",
              f"Request body exceeds {MAX_REQUEST_BODY_BYTES} bytes",
            )
        except ValueError:
          return respond(400, "invalid_header", "INVALID_CONTENT_LENGTH", "Invalid Content-Length header")

    # Authentication
    authorized, auth_reason = verify_request(request)
    if not authorized:
      if auth_reason == "missing_key_config":
        metrics.record_auth_failure()
        return respond(
          503,
          "auth_not_configured",
          "AUTH_NOT_CONFIGURED",
          "PROJECT12_API_KEY is not configured on the server",
        )
      metrics.record_auth_failure()
      return respond(
        401,
        "unauthorized",
        "UNAUTHORIZED",
        "Missing or invalid API key. Provide Authorization: Bearer <key> or X-API-Key header.",
      )

    # Read body for abuse check and size validation (POST inference routes)
    body = b""
    if method == "POST" and path in ("/chat", "/crisis-detection", "/memory-search", "/retrieve"):
      body = await request.body()
      if len(body) > MAX_REQUEST_BODY_BYTES:
        return respond(
          413,
          "payload_too_large",
          "PAYLOAD_TOO_LARGE",
          f"Request body exceeds {MAX_REQUEST_BODY_BYTES} bytes",
        )

      allowed, abuse_reason = check_abuse(path, client_ip, body)
      if not allowed:
        metrics.record_rate_limit()
        return respond(
          429,
          "abuse_detected",
          "ABUSE_DETECTED",
          f"Too many identical requests. Reason: {abuse_reason}",
          headers={"Retry-After": "5"},
        )

      async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

      request = Request(request.scope, receive)

    # Per-IP rate limiting
    if method == "POST" and path in ("/chat", "/crisis-detection", "/memory-search"):
      allowed, retry_after = check_rate_limit(path, client_ip)
      if not allowed:
        metrics.record_rate_limit()
        return respond(
          429,
          "rate_limit_exceeded",
          "RATE_LIMIT_EXCEEDED",
          f"Rate limit exceeded for {path}",
          headers={"Retry-After": str(retry_after)},
        )

    try:
      response = await call_next(request)
    except Exception:
      duration_ms = (time.monotonic() - start) * 1000
      metrics.record_request(500)
      self._log_request(method, path, 500, duration_ms, client_ip)
      raise

    duration_ms = (time.monotonic() - start) * 1000
    metrics.record_request(response.status_code)
    self._log_request(method, path, response.status_code, duration_ms, client_ip)
    return response
