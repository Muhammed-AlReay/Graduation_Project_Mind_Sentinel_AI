# Project_12 API Documentation

**Base URL:** `http://localhost:8100` (default)  
**Version:** 1.1.0  
**Content-Type:** `application/json`

---

## Authentication

All endpoints except `/health` and `/ready` require service-to-service authentication.

```
Authorization: Bearer <PROJECT12_API_KEY>
```

Or:

```
X-API-Key: <PROJECT12_API_KEY>
```

| Response | Code | When |
|----------|------|------|
| `401` | `UNAUTHORIZED` | Missing or invalid API key |
| `503` | `AUTH_NOT_CONFIGURED` | Server has no `PROJECT12_API_KEY` set |

Set `PROJECT12_API_KEY` (minimum 16 characters) in the service environment.  
See [PROJECT12_SECURITY_AUDIT.md](./PROJECT12_SECURITY_AUDIT.md) for full security details.

---

## Endpoints Summary

| Method | Path | Auth | Rate limited |
|--------|------|------|--------------|
| `GET` | `/health` | No | No |
| `GET` | `/ready` | No | No |
| `GET` | `/metrics` | Yes | No |
| `POST` | `/retrieve` | Yes | No |
| `POST` | `/crisis-detection` | Yes | Yes |
| `POST` | `/memory-search` | Yes | Yes |
| `POST` | `/chat` | Yes | Yes |

---

## Monitoring

### `GET /health`

Liveness probe — returns immediately if the process is running.

**Response `200`:**
```json
{
  "status": "ok",
  "service": "project12",
  "version": "1.0.0"
}
```

---

### `GET /metrics`

Operational metrics — requires API key.

**Response `200`:**
```json
{
  "uptime_seconds": 3600.5,
  "request_count": 142,
  "error_count": 3,
  "rate_limit_count": 2,
  "auth_failure_count": 1
}
```

---

### `GET /ready`

Readiness probe — reports whether models and vectorstore are loaded.

**Response `200`:**
```json
{
  "ready": true,
  "checks": [
    { "name": "data_directory", "ok": true, "detail": "1 PDF(s) found" },
    { "name": "vectorstore_files", "ok": true, "detail": "/app/vectorstore" },
    { "name": "openrouter_api_key", "ok": true, "detail": "Configured" },
    { "name": "retrieval_stack", "ok": true, "detail": "Loaded" },
    { "name": "llm_stack", "ok": true, "detail": "Loaded" }
  ]
}
```

When not ready, `ready` is `false` but HTTP status remains `200` (standard k8s pattern — orchestrator reads body).

---

## Inference

### `POST /retrieve`

Hybrid BM25 + FAISS dense retrieval with cross-encoder reranking.

**Request:**
```json
{
  "query": "What are the symptoms of major depressive disorder?",
  "top_k": 7
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | — | Search query (1–4000 chars) |
| `top_k` | integer | No | 7 | Number of chunks to return (1–20) |

**Response `200`:**
```json
{
  "query": "What are the symptoms of major depressive disorder?",
  "context": "chunk1 text\n\nchunk2 text...",
  "sources": [
    {
      "content": "Major depressive disorder is characterized by...",
      "source": "LibraryFile_151635_46.pdf",
      "page": 42,
      "score": null
    }
  ],
  "chunk_count": 7
}
```

**Errors:**
- `503` — retrieval stack not loaded
- `500` — unexpected error

---

### `POST /crisis-detection`

LLM-based safety classification using `SafetyGuard`.

**Request:**
```json
{
  "text": "I don't want to live anymore"
}
```

**Response `200`:**
```json
{
  "category": "SUICIDE_RISK",
  "safety_guidance": "I'm sorry you're going through a difficult time 💔\n\n..."
}
```

**Categories:** `SAFE`, `SUICIDE_RISK`, `SELF_HARM`, `CRISIS_DISTRESS`

**Errors:**
- `503` — LLM stack not loaded (missing API key)
- `504` — classification timed out
- `500` — unexpected error

---

### `POST /memory-search`

Search patient memory stores: profiles, concerns, notes, QA logs, chat history.

**Request:**
```json
{
  "query": "anxiety",
  "patient_id": "PSY-A1B2C3D4",
  "max_results": 10
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | Yes | — | Substring search term |
| `patient_id` | string | No | all patients | Filter to specific patient |
| `max_results` | integer | No | 10 | Max matches (1–50) |

**Response `200`:**
```json
{
  "query": "anxiety",
  "matches": [
    {
      "patient_id": "PSY-A1B2C3D4",
      "match_type": "concern",
      "content": "I've been feeling anxious about work",
      "metadata": {}
    }
  ],
  "total": 1
}
```

**Match types:** `concern`, `note`, `qa`, `chat`, `profile`

---

### `POST /chat`

Full RAG pipeline: safety classification → retrieval → LLM generation → optional memory persistence.

**Request:**
```json
{
  "message": "What is generalized anxiety disorder?",
  "patient_id": "PSY-A1B2C3D4",
  "chat_history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hello, how can I help?" }
  ],
  "include_explanation": true,
  "persist_memory": true
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `message` | string | Yes | — | User message (1–4000 chars) |
| `patient_id` | string | No | null | Patient ID for memory context |
| `chat_history` | array | No | `[]` | Prior messages (max 40) |
| `include_explanation` | boolean | No | `false` | Include retrieval explanation |
| `persist_memory` | boolean | No | `true` | Save to JSON memory stores |

**Response `200`:**
```json
{
  "answer": "🤖 Assistant Response:\nGeneralized anxiety disorder (GAD) is...",
  "safety_category": "SAFE",
  "safety_guidance": null,
  "sources": [
    {
      "content": "...",
      "source": "LibraryFile_151635_46.pdf",
      "page": 15
    }
  ],
  "explanation": "🔎 Query Analysis:\n- Original query: ...",
  "patient_id": "PSY-A1B2C3D4"
}
```

When crisis detected, `safety_guidance` is populated and prepended in `answer`.

**Errors:**
- `503` — retrieval or LLM stack not loaded
- `504` — LLM or retrieval timed out
- `422` — validation error (empty message, etc.)
- `500` — unexpected error

---

## Error Response Format

All errors return a consistent JSON body:

```json
{
  "error": "service_unavailable",
  "detail": "LLM stack not loaded",
  "code": "SERVICE_UNAVAILABLE"
}
```

| HTTP Status | `code` | Meaning |
|-------------|--------|---------|
| 401 | `UNAUTHORIZED` | Missing or invalid API key |
| 413 | `PAYLOAD_TOO_LARGE` | Request body exceeds size limit |
| 422 | `VALIDATION_ERROR` | Invalid request body |
| 429 | `RATE_LIMIT_EXCEEDED` | Per-IP rate limit hit |
| 429 | `ABUSE_DETECTED` | Identical request flood |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 503 | `AUTH_NOT_CONFIGURED` | Server API key not configured |
| 503 | `SERVICE_UNAVAILABLE` | Models not loaded |
| 504 | `TIMEOUT` | Operation exceeded timeout |

---

## OpenAPI / Swagger

Interactive docs available at:
- **Swagger UI:** `http://localhost:8100/docs`
- **ReDoc:** `http://localhost:8100/redoc`
- **OpenAPI JSON:** `http://localhost:8100/openapi.json`

---

## Example cURL Commands

```bash
# Set your API key
export PROJECT12_API_KEY="your-secret-key-here"

# Health (no auth)
curl http://localhost:8100/health

# Readiness (no auth)
curl http://localhost:8100/ready

# Metrics (auth required)
curl http://localhost:8100/metrics \
  -H "Authorization: Bearer $PROJECT12_API_KEY"

# Retrieve
curl -X POST http://localhost:8100/retrieve \
  -H "Authorization: Bearer $PROJECT12_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "symptoms of depression"}'

# Crisis detection
curl -X POST http://localhost:8100/crisis-detection \
  -H "Authorization: Bearer $PROJECT12_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel hopeless and overwhelmed"}'

# Memory search
curl -X POST http://localhost:8100/memory-search \
  -H "Authorization: Bearer $PROJECT12_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "anxiety", "max_results": 5}'

# Chat
curl -X POST http://localhost:8100/chat \
  -H "Authorization: Bearer $PROJECT12_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is PTSD?", "include_explanation": true}'
```

---

## Environment Variables

See [PROJECT12_DEPLOYMENT_GUIDE.md](./PROJECT12_DEPLOYMENT_GUIDE.md) for full configuration reference.

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | Required for `/chat` and `/crisis-detection` |
| `PROJECT12_PORT` | `8100` | Service port |
| `PROJECT12_AUTO_INGEST` | `false` | Auto-build vectorstore on startup |
| `PROJECT12_LLM_TIMEOUT_SECONDS` | `30` | LLM/retrieval timeout |
| `PROJECT12_RETRIEVAL_TOP_K` | `7` | Default chunks for retrieval |
