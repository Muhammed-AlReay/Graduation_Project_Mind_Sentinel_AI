# Project_12 Security Audit — Phase A.5

**Date:** 2026-06-08  
**Scope:** Project_12 only — Mind-Sanctuary-main untouched  
**Version:** 1.1.0

---

## Pre-Implementation Architecture

```mermaid
flowchart LR
    Client[Any HTTP Client] --> API[FastAPI — no auth]
    API --> Endpoints[All endpoints open]
    API --> Logs[Minimal logging]
```

### Attack surface before hardening

| Vector | Exposure |
|--------|----------|
| Unauthenticated API | Anyone on network can call all endpoints |
| No rate limiting | LLM cost abuse, DoS via `/chat` |
| No payload limits | Large body attacks |
| User content in error logs | Potential PII leakage |
| No abuse detection | Prompt flooding, retry storms |
| No operational metrics | Blind to attacks |

---

## Post-Implementation Architecture

```mermaid
flowchart TB
    Client[Client / Edge Function] --> MW[SecurityMiddleware]

    subgraph MW["Security Middleware Stack"]
        SIZE[Payload size check]
        AUTH[API key auth]
        ABUSE[Duplicate flood detection]
        RATE[Per-IP rate limit]
        LOG[Access logging — no body]
    end

    MW -->|401/413/429| REJECT[Structured error]
    MW -->|authorized| APP[Route handlers]
    APP --> METRICS[MetricsCollector]
    APP --> CORE[RAG / LLM / Memory]

    HC["/health /ready"] --> MW
    MET["/metrics"] --> MW
```

---

## Files Modified

| File | Change |
|------|--------|
| `config.py` | Added `PROJECT12_API_KEY`, rate limits, abuse settings, payload limits |
| `service/app.py` | Security middleware, `/metrics`, sanitized error responses |
| `service/models.py` | Added `MetricsResponse` |
| `service/startup.py` | API key validation on startup |
| `.env.example` | Security environment variables |
| `docker-compose.yml` | Required `PROJECT12_API_KEY`, rate limit env vars |

## Files Created

| File | Purpose |
|------|---------|
| `service/security/__init__.py` | Package marker |
| `service/security/auth.py` | Bearer / X-API-Key verification |
| `service/security/rate_limit.py` | Per-IP sliding window limiter |
| `service/security/abuse.py` | Identical-request flood detection |
| `service/security/middleware.py` | Combined security + access logging |
| `service/metrics.py` | Request/error counters |
| `PROJECT12_SECURITY_AUDIT.md` | This document |

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant MW as SecurityMiddleware
    participant A as auth.py
    participant H as Route Handler

    C->>MW: POST /chat + Authorization: Bearer <key>
    MW->>MW: Check Content-Length ≤ 64KB

    alt path is /health or /ready
        MW->>H: pass through (no auth)
    else path is protected
        MW->>A: verify_request()
        alt PROJECT12_API_KEY not configured
            A-->>MW: unauthorized (503 AUTH_NOT_CONFIGURED)
            MW-->>C: 503
        else no token
            A-->>MW: missing_token
            MW-->>C: 401 UNAUTHORIZED
        else invalid token
            A-->>MW: invalid_token
            MW-->>C: 401 UNAUTHORIZED
        else valid (constant-time compare)
            A-->>MW: ok
        end
    end

    MW->>MW: abuse check + rate limit
    MW->>H: forward request
    H-->>MW: response
    MW->>MW: log endpoint + status + duration (no body)
    MW-->>C: 200 response
```

### Accepted auth headers

```
Authorization: Bearer <PROJECT12_API_KEY>
X-API-Key: <PROJECT12_API_KEY>
```

### Public endpoints (no auth)

| Endpoint | Reason |
|----------|--------|
| `GET /health` | Kubernetes liveness probe |
| `GET /ready` | Kubernetes readiness probe |

All other endpoints including `GET /metrics` and `POST /retrieve` require authentication.

---

## Request Flow

```mermaid
flowchart TD
    REQ[Incoming request] --> METHOD{POST?}
    METHOD -->|yes| CL[Check Content-Length]
    CL -->|> 64KB| E413[413 PAYLOAD_TOO_LARGE]
    CL --> AUTH{Public path?}
    METHOD -->|GET| AUTH

    AUTH -->|yes| HANDLER[Route handler]
    AUTH -->|no| KEY{Valid API key?}
    KEY -->|no| E401[401 UNAUTHORIZED]
    KEY -->|yes| BODY[Read body]

    BODY --> SIZE{Body > 64KB?}
    SIZE -->|yes| E413
    SIZE --> ABUSE{Duplicate flood?}
    ABUSE -->|yes| E429A[429 ABUSE_DETECTED]
    ABUSE --> RATE{Rate limited path?}

    RATE -->|yes, over limit| E429B[429 RATE_LIMIT_EXCEEDED]
    RATE -->|ok| HANDLER

    HANDLER --> PYDANTIC{Valid schema?}
    PYDANTIC -->|no| E422[422 VALIDATION_ERROR]
    PYDANTIC -->|yes| EXEC[Execute inference]
    EXEC --> LOG[Log method path status duration_ms client_ip]
    LOG --> RESP[Return response]
```

---

## Protections Implemented

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| API authentication | `PROJECT12_API_KEY` via Bearer or X-API-Key; `secrets.compare_digest` | **DONE** |
| 401 on invalid key | Middleware returns structured `UNAUTHORIZED` | **DONE** |
| Payload size limit | 64KB max (`PROJECT12_MAX_REQUEST_BYTES`) | **DONE** |
| Text length validation | Pydantic `max_length` on all text fields | **DONE** |
| Malformed JSON | FastAPI returns 422; no body content in error detail | **DONE** |
| Invalid parameters | Pydantic validation with structured `VALIDATION_ERROR` | **DONE** |
| Per-IP rate limiting | Sliding window on `/chat`, `/crisis-detection`, `/memory-search` | **DONE** |
| Oversized requests | Content-Length + body size double check | **DONE** |
| Prompt flooding | Rate limits + identical-body dedup | **DONE** |
| Repeated retries | Abuse module blocks >5 identical POSTs in 10s | **DONE** |
| Access logging | endpoint, status, duration_ms, client_ip only | **DONE** |
| No secret logging | Keys never logged; validation errors sanitized | **DONE** |
| No user content logging | Request/response bodies never logged | **DONE** |
| GET /metrics | uptime, request_count, error_count + breakdowns | **DONE** |

### Rate limits (defaults, per IP per 60s window)

| Endpoint | Limit |
|----------|-------|
| `POST /chat` | 20 |
| `POST /crisis-detection` | 40 |
| `POST /memory-search` | 60 |

---

## Attack Surface (Remaining)

| Surface | Risk | Mitigation status |
|---------|------|-------------------|
| Network exposure | High if port 8100 public | Deploy behind private network / reverse proxy |
| Single shared API key | Medium — no per-client identity | Rotate key; use separate keys per environment |
| In-memory rate limits | Medium — resets on restart; not shared across replicas | Use Redis rate limiter for multi-instance |
| `/retrieve` not rate limited | Medium — CPU abuse via embedding search | Add rate limit in Phase B if needed |
| Swagger UI at `/docs` | Low — requires auth but exposes schema | Disable in production via env flag (future) |
| FAISS deserialization | Medium — only load self-built index | Document trust boundary |
| OpenRouter API key in env | Medium | Use secrets manager in production |
| Patient memory JSON files | Medium — no encryption at rest | Encrypt volume or migrate to DB in Phase B |
| TLS termination | High if not configured | Terminate TLS at reverse proxy |

---

## Remaining Risks

| # | Risk | Severity | Recommendation |
|---|------|----------|----------------|
| R1 | No TLS on service itself | High | Terminate TLS at nginx/Caddy/cloud LB |
| R2 | Single API key for all callers | Medium | Per-environment keys; rotate quarterly |
| R3 | Rate limits not distributed | Medium | Redis-backed limiter for horizontal scaling |
| R4 | `/retrieve` unbounded CPU cost | Medium | Add rate limit + auth (auth done) |
| R5 | No IP allowlist | Low | Restrict at network layer for internal-only |
| R6 | Swagger exposes API in staging | Low | Set `PROJECT12_DISABLE_DOCS=true` (future) |
| R7 | Memory search returns patient data | Medium | Callers must be trusted; audit access |

---

## Error Codes Reference

| HTTP | Code | Meaning |
|------|------|---------|
| 400 | `BAD_REQUEST` | Malformed request |
| 401 | `UNAUTHORIZED` | Missing or invalid API key |
| 413 | `PAYLOAD_TOO_LARGE` | Body exceeds size limit |
| 422 | `VALIDATION_ERROR` | Invalid parameters |
| 429 | `RATE_LIMIT_EXCEEDED` | Per-IP rate limit hit |
| 429 | `ABUSE_DETECTED` | Identical request flood |
| 503 | `AUTH_NOT_CONFIGURED` | Server missing `PROJECT12_API_KEY` |
| 503 | `SERVICE_UNAVAILABLE` | Models not loaded |
| 504 | `TIMEOUT` | LLM/retrieval timeout |

---

## Production Readiness Verdict

| Criterion | Phase A | Phase A.5 |
|-----------|---------|-----------|
| API authentication | FAIL | **PASS** |
| Request validation | Partial | **PASS** |
| Rate limiting | FAIL | **PASS** |
| Abuse protection | FAIL | **PASS** |
| Safe logging | Partial | **PASS** |
| Operational metrics | Partial | **PASS** |
| TLS | FAIL | FAIL (proxy required) |
| Distributed rate limits | N/A | FAIL (single-instance) |

### Overall: **READY for secure internal integration**

Project_12 is ready to be called from Mind-Sanctuary edge functions via service-to-service authentication. Deploy on a private network with TLS termination at the reverse proxy. Set `PROJECT12_API_KEY` in both the service and the calling edge function environment.

**Mind-Sanctuary-main was not modified.**
