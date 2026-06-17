# Project_12 Deployment Guide

**Service:** Project_12 AI Intelligence Layer  
**Default port:** 8100  
**Runtime:** Python 3.10+ or Docker

---

## Prerequisites

- Python 3.10+ **or** Docker + Docker Compose
- `PROJECT12_API_KEY` (min 16 characters) — **required for all endpoints except `/health` and `/ready`**
- `OPENROUTER_API_KEY` for `/chat` and `/crisis-detection`
- ~2 GB disk for HuggingFace model cache
- PDF source file in `data/` (included: `LibraryFile_151635_46.pdf`)

---

## Option 1: Docker (Recommended)

### 1. Configure environment

```bash
cd Project_12
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY
```

### 2. Build and start

```bash
docker compose up --build -d
```

First startup may take **5–15 minutes** while:
1. HuggingFace models download
2. FAISS vectorstore is auto-built (`PROJECT12_AUTO_INGEST=true` in Docker)

### 3. Verify

```bash
# Liveness
curl http://localhost:8100/health

# Readiness (wait until ready=true)
curl http://localhost:8100/ready

# Test retrieval (no API key needed)
curl -X POST http://localhost:8100/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "anxiety symptoms"}'
```

### 4. View logs

```bash
docker compose logs -f project12
```

### 5. Stop

```bash
docker compose down
```

### Docker volumes

| Volume | Purpose |
|--------|---------|
| `project12_vectorstore` | FAISS index (persists across rebuilds) |
| `project12_memory` | Patient JSON memory stores |
| `project12_hf_cache` | HuggingFace model cache |

---

## Option 2: Local Python

### 1. Create virtual environment

> **Note:** The bundled `venv310/` may reference a foreign Python install. Create a fresh venv:

```bash
cd Project_12
python3.10 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Set OPENROUTER_API_KEY
```

### 3. Build vectorstore (if missing)

```bash
python ingest.py
```

### 4. Validate

```bash
python scripts/validate_service.py
```

### 5. Start service

```bash
python -m uvicorn service.app:app --host 0.0.0.0 --port 8100
```

Or:

```bash
python -m service.app
```

### 6. Access

- API: `http://localhost:8100`
- Swagger: `http://localhost:8100/docs`

---

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `OPENROUTER_API_KEY` | — | For LLM endpoints | OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | No | LLM API base URL |
| `PROJECT12_BASE_DIR` | Project root | No | Anchor for all relative paths |
| `PROJECT12_DATA_DIR` | `{BASE}/data` | No | PDF source directory |
| `PROJECT12_VECTORSTORE_DIR` | `{BASE}/vectorstore` | No | FAISS index directory |
| `PROJECT12_MEMORY_DATA_DIR` | `{BASE}/memory_data` | No | JSON memory stores |
| `PROJECT12_HOST` | `0.0.0.0` | No | Bind address |
| `PROJECT12_PORT` | `8100` | No | Bind port |
| `PROJECT12_LOG_LEVEL` | `INFO` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `PROJECT12_AUTO_INGEST` | `false` | No | Auto-build vectorstore if missing |
| `PROJECT12_LLM_TIMEOUT_SECONDS` | `30` | No | LLM/retrieval timeout |
| `PROJECT12_RETRIEVAL_TOP_K` | `7` | No | Default rerank top-k |
| `PROJECT12_LLM_MODEL` | `openrouter/free` | No | LLM model ID |
| `PROJECT12_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | No | Embedding model |
| `PROJECT12_RERANKER_MODEL` | `ms-marco-MiniLM-L-6-v2` | No | Cross-encoder model |

---

## Startup Validation Checklist

On startup, the service runs these checks automatically:

| Check | Pass condition |
|-------|---------------|
| `data_directory` | `data/` exists with at least one PDF |
| `vectorstore_files` | `vectorstore/index.faiss` + `index.pkl` exist |
| `vectorstore_build` | Auto-ingest succeeds (if enabled) |
| `openrouter_api_key` | API key is set and non-placeholder |
| `retrieval_stack` | Embeddings + FAISS + BM25 + reranker loaded |
| `llm_stack` | LLM + SafetyGuard + CrisisHandler loaded |

`GET /ready` returns the full report.

---

## Kubernetes / Orchestrator Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8100
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /ready
    port: 8100
  initialDelaySeconds: 60
  periodSeconds: 15
  failureThreshold: 10
```

Allow **120s start period** for first-time model download.

---

## Rebuilding Vectorstore

When PDFs in `data/` change:

```bash
# Local
python ingest.py

# Docker
docker compose exec project12 python ingest.py
```

Or delete the vectorstore volume and restart with `PROJECT12_AUTO_INGEST=true`:

```bash
docker compose down
docker volume rm project12_vectorstore
docker compose up -d
```

---

## Rollback

| Action | Command |
|--------|---------|
| Stop service | `docker compose down` or kill uvicorn |
| Revert code | `git checkout -- Project_12/` |
| Reset vectorstore | Delete `vectorstore/` directory |
| CLI still works | `python main.py` (unaffected by service) |

No Mind-Sanctuary components are affected.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `/ready` shows `vectorstore_files: false` | Index not built | Run `python ingest.py` or set `AUTO_INGEST=true` |
| `/ready` shows `llm_stack: false` | Missing API key | Set `OPENROUTER_API_KEY` in `.env` |
| Slow first start | Model download | Pre-cache via Docker volume or build-time download |
| `503` on `/chat` | LLM not loaded | Check API key and `/ready` |
| `504` timeout | LLM slow | Increase `PROJECT12_LLM_TIMEOUT_SECONDS` |
| `venv310` won't run | Foreign Python path | Create fresh `.venv` (see Option 2) |
| Memory not persisting | Wrong `MEMORY_DATA_DIR` | Check env var and volume mount |

---

## Security (Phase A.5)

1. Set `PROJECT12_API_KEY` to a random string of at least 16 characters
2. Pass the same key to Mind-Sanctuary edge functions as `Authorization: Bearer <key>`
3. Deploy behind reverse proxy with TLS (nginx, Caddy, cloud LB)
4. Do not expose port 8100 to the public internet
5. Rotate keys if `.env` was ever committed
6. See [PROJECT12_SECURITY_AUDIT.md](./PROJECT12_SECURITY_AUDIT.md) for full details

---

## Next Steps (Phase B — separate)

Integration with Mind-Sanctuary-main requires:
1. Supabase edge function `project12-bridge` (not yet created)
2. `PROJECT12_SERVICE_URL` in edge function env
3. Feature flag `PROJECT12_ENABLED` in chat pipeline

See `AI_INTEGRATION_PLAN.md` at repository root for full integration plan.
