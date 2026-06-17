# Deployment Readiness Report — Project_12 + Supabase Edge

**Date:** 2026-06-08  
**Scope:** Close remaining deployment blockers (validation only)  
**B.4 / B.5:** Paused — not implemented  
**Mind-Sanctuary code:** Not modified in this pass

---

## Executive Summary

| Layer | Readiness | Live verified? |
|-------|-----------|----------------|
| Project_12 Docker/Linux | **Structurally ready** | ❌ No live Docker run (Docker not on validation host) |
| Project_12 endpoints (`/retrieve`, `/chat`, `/crisis-detection`) | **Code ready** | ❌ Blocked on Windows (`torch` DLL); pending Linux container |
| Vectorstore on disk | **Ready** | ✅ 36,464 chunks, FAISS index present |
| SafetyGuard / Arabic crisis | **Ready** | ✅ 25/25 Arabic + 5/5 EN heuristic tests |
| Supabase `chat` edge (B.3) | **Deployed** | ✅ HTTP 401 without JWT |
| Supabase `project12-bridge` | **Code ready, not deployed** | ❌ HTTP 404 on cloud |
| Edge secrets / production config | **Documented, not applied** | ⚠️ Staging `.env.staging` exists locally only |

### Go / No-Go Decision

| Environment | Decision | Rationale |
|-------------|----------|-----------|
| **Production** `PROJECT12_ENABLED=true` | **NO-GO** | No cloud-hosted P12 service; bridge not deployed; no live Linux E2E |
| **Staging** (controlled enable) | **CONDITIONAL GO** | Proceed only after: (1) `docker compose up` on Linux with `/ready=true`, (2) deploy `project12-bridge`, (3) set edge secrets with public `PROJECT12_SERVICE_URL` |
| **B.4 / B.5** | **NO-GO** | Explicitly paused |

---

## 1. Deployment Artifacts Audit

All artifacts generated during Phases B.2–B.3 and blocker closure:

| Artifact | Location | Purpose | Status |
|----------|----------|---------|--------|
| Phase B.2 implementation | `Mind-Sanctuary-main/PHASE_B2_IMPLEMENTATION.md` | Bridge layer design | Complete |
| Phase B.3 implementation | `Mind-Sanctuary-main/PHASE_B3_IMPLEMENTATION.md` | Chat augmentation | Complete |
| B.3 validation audit | `B3_VALIDATION_REPORT.md` | Component matrix | Complete |
| Staging E2E validation | `STAGING_VALIDATION_REPORT.md` | B.3 harness results | Complete |
| Windows torch RCA | `WINDOWS_TORCH_ROOT_CAUSE.md` | Native Windows blocker | Complete |
| Linux/Docker audit | `LINUX_DEPLOYMENT_VALIDATION.md` | Container static audit | Complete |
| Arabic crisis validation | `ARABIC_CRISIS_VALIDATION.md` | Heuristic fix + 25 tests | Complete |
| Cloud deployment checklist | `CLOUD_DEPLOYMENT_CHECKLIST.md` | Supabase + secrets | Complete |
| Crisis detection RCA | `Project_12/CRISIS_DETECTION_ROOT_CAUSE_REPORT.md` | OpenRouter 403 fix | Complete |
| P12 deployment guide | `Project_12/PROJECT12_DEPLOYMENT_GUIDE.md` | Ops runbook | Complete |
| P12 API docs | `Project_12/PROJECT12_API_DOCUMENTATION.md` | Endpoint reference | Complete |
| P12 security audit | `Project_12/PROJECT12_SECURITY_AUDIT.md` | Auth/rate limits | Complete |
| P12 production audit | `Project_12/PROJECT12_PRODUCTION_AUDIT.md` | Service hardening | Complete |
| Docker image spec | `Project_12/Dockerfile` | Container build | Present |
| Compose spec | `Project_12/docker-compose.yml` | Orchestration | Present |
| Env template | `Project_12/.env.example` | Service secrets | Present |
| Staging edge env (local) | `supabase/functions/.env.staging` | Staging-only flag | Present (not deployed) |
| Arabic crisis test | `Project_12/scripts/test_arabic_crisis.py` | 25-case validator | **25/25 PASS** |
| Service validator | `Project_12/scripts/validate_service.py` | Config + import check | Partial (import fails on Windows) |
| Edge unit tests | `project12Client_test.ts`, `project12ChatAugmentation_test.ts` | Deno | **9/9 PASS** |

**Mind-Sanctuary application code:** Unchanged in this validation cycle.

---

## 2. Docker Readiness

### 2.1 Static audit — PASS with gaps

| Check | Result | Notes |
|-------|--------|-------|
| `Dockerfile` exists | ✅ | `python:3.10-slim`, uvicorn CMD |
| `docker-compose.yml` exists | ✅ | Port 8100, volumes, healthcheck |
| API key enforced at compose | ✅ | `${PROJECT12_API_KEY:?}` |
| PDF data in image | ✅ | `COPY data/` (11 PDFs) |
| Pre-built vectorstore in image | ❌ | Not copied — first boot auto-ingest |
| `libgomp1` for PyTorch | ⚠️ | Recommended addition |
| `torch` version pin | ⚠️ | Not pinned in `requirements.txt` |
| Memory limit | ⚠️ | Not set — recommend ≥4 GB |

### 2.2 Live Docker verification — NOT EXECUTED

```
docker: command not found (validation host)
```

**Cannot certify** `docker compose up --build` until run on a Linux host with Docker installed.

### 2.3 Expected live validation commands (ops)

```bash
cd Project_12
cp .env.example .env   # set PROJECT12_API_KEY, OPENROUTER_API_KEY
docker compose up --build -d
docker compose logs -f project12
curl http://localhost:8100/health
curl http://localhost:8100/ready    # wait until ready=true
```

---

## 3. Linux Readiness

| Component | Code / config | Live Linux |
|-----------|---------------|------------|
| Startup validation (`service/startup.py`) | ✅ | Pending container |
| Lazy model load (`service/loader.py`) | ✅ | Pending container |
| Security middleware (auth, rate limit) | ✅ | Pending container |
| Uvicorn entrypoint | ✅ | Pending container |
| HuggingFace cache volume | ✅ | Pending first download |
| Windows native dev | ❌ | Use Docker only (`WINDOWS_TORCH_ROOT_CAUSE.md`) |

**Linux readiness verdict:** **READY TO DEPLOY** (code + artifacts); **PENDING LIVE SMOKE** on Docker host.

---

## 4. Component Verification Matrix

### 4.1 Vectorstore loading — ✅ VERIFIED (disk)

| Check | Result |
|-------|--------|
| `vectorstore/index.faiss` | ✅ 56,008,749 bytes |
| `vectorstore/index.pkl` | ✅ 44,188,342 bytes |
| Document chunks | ✅ **36,464** |
| `validate_service.py` startup check | ✅ `vectorstore_files: OK` |
| Sample metadata | ✅ `A-Short-Textbook-of-Psychiatry.pdf` |

Loader path: `FAISS.load_local()` → `HybridRetriever` (`service/loader.py`).

### 4.2 Embeddings loading — ⚠️ CODE READY / LIVE BLOCKED

| Check | Result |
|-------|--------|
| Model config | `sentence-transformers/all-MiniLM-L6-v2` |
| Loader | `HuggingFaceEmbeddings` in `_load_retrieval_stack()` |
| Live load on Windows | ❌ `torch` WinError 1114 |
| Live load in Docker/Linux | **Not yet executed** |

### 4.3 Retrieval pipeline — ⚠️ CODE READY / LIVE BLOCKED

| Stage | Implementation | Live test |
|-------|----------------|-----------|
| Dense (FAISS) | `vectorstore.as_retriever(k=20)` | Pending |
| BM25 | `BM25Retriever` | Pending |
| Merge/dedup | `HybridRetriever` | Pending |
| Rerank | `CrossEncoder(ms-marco-MiniLM-L-6-v2)` | Pending |
| `/retrieve` endpoint | `service/app.py` POST | Pending |

`/retrieve` flow: `hybrid_retriever.get_relevant_documents` → `reranker.rerank` → `RetrieveResponse`.

### 4.4 SafetyGuard — ✅ VERIFIED (heuristic layer)

| Check | Result |
|-------|--------|
| English crisis | ✅ `SUICIDE_RISK`, `SELF_HARM`, `CRISIS_DISTRESS` |
| Arabic crisis | ✅ **25/25** (`test_arabic_crisis.py`) |
| Staging failure case | ✅ `أشعر باليأس ولا أرى أي أمل` → `CRISIS_DISTRESS` |
| Heuristic pre-check before LLM | ✅ `safety_guard.py` |
| LLM fallback on 403 | ✅ Documented (`CRISIS_DETECTION_ROOT_CAUSE_REPORT.md`) |
| Full `/crisis-detection` HTTP | Pending Linux (requires torch + LLM stack) |

### 4.5 `/chat` — ⚠️ CODE READY / LIVE BLOCKED

Pipeline (`service/chat_service.py`):

1. `SafetyGuard.classify(message)`
2. `hybrid_retriever` + `reranker`
3. LLM `invoke` with RAG context
4. Optional memory persistence
5. Returns `ChatResponse` with sources + safety category

Requires: retrieval stack + LLM stack + OpenRouter key.

### 4.6 `/retrieve` — ⚠️ CODE READY / LIVE BLOCKED

- Auth: Bearer `PROJECT12_API_KEY` (except `/health`, `/ready`)
- Returns: `context`, `sources[]`, `chunk_count`
- Live HTTP: **pending Docker**

### 4.7 `/crisis-detection` — ⚠️ PARTIAL

| Path | Status |
|------|--------|
| Heuristic (EN + AR) | ✅ Verified |
| LLM classify + timeout fallback | Code ready |
| HTTP 200 on crisis text (post-fix) | Verified in prior cycle via `test_crisis_endpoint.py` on capable host |
| Live on this Windows host | ❌ torch import blocks `service.app` |

---

## 5. project12-bridge Deployment Readiness

### 5.1 Code — ✅ READY

| Check | Result |
|-------|--------|
| `supabase/functions/project12-bridge/index.ts` | Implemented |
| JWT via `requireAuth` | ✅ |
| Modes: retrieve, crisis_detection, memory_search | ✅ |
| Uses `project12Client.ts` | ✅ |
| Kill switch `PROJECT12_ENABLED` | ✅ |
| Deno unit tests | **9/9 PASS** |
| `config.toml` `verify_jwt = true` | ✅ |

### 5.2 Cloud — ❌ NOT DEPLOYED

```
POST https://fsterbxivhhzipfgpvou.supabase.co/functions/v1/project12-bridge
→ HTTP 404
```

Compare: `chat` → **HTTP 401** (deployed, auth working).

### 5.3 Deploy command (ops, not executed)

```bash
cd Mind-Sanctuary-main
supabase functions deploy project12-bridge
```

---

## 6. Supabase Edge Secrets Checklist

### 6.1 Required for Project_12 integration (staging)

| Secret | Required when | Example / notes |
|--------|---------------|-----------------|
| `PROJECT12_ENABLED` | Always set explicitly | `false` prod / `true` staging |
| `PROJECT12_SERVICE_URL` | When enabled | `https://project12.<domain>` — **not localhost** |
| `PROJECT12_API_KEY` | When enabled | ≥16 chars; must match P12 service |
| `PROJECT12_TIMEOUT_MS` | Optional | `1200` |
| `PROJECT12_CACHE_TTL_MS` | Optional | `300000` |

### 6.2 Required for edge auth + chat (existing)

| Secret | Purpose |
|--------|---------|
| `SUPABASE_URL` | JWT validation in `requireAuth` |
| `SUPABASE_ANON_KEY` | JWT validation |
| `OPENROUTER_API_KEY` | Chat provider chain |
| `GEMINI_API_KEY` | Optional provider |
| `GROQ_API_KEY` | Optional provider |
| `LOVABLE_API_KEY` | Optional provider |

### 6.3 Set via CLI (staging — not applied to cloud in this pass)

```bash
supabase secrets set PROJECT12_ENABLED=true
supabase secrets set PROJECT12_SERVICE_URL=https://<p12-host>
supabase secrets set PROJECT12_API_KEY=<shared-secret>
supabase secrets set PROJECT12_TIMEOUT_MS=1200
```

**Production policy:** Keep `PROJECT12_ENABLED=false` until staging E2E sign-off.

---

## 7. Required Production Configuration

### 7.1 Project_12 service (`.env` / container)

| Variable | Production value |
|----------|------------------|
| `PROJECT12_API_KEY` | Strong secret ≥16 chars |
| `OPENROUTER_API_KEY` | Valid non-free-tier recommended for crisis LLM |
| `PROJECT12_AUTH_ENABLED` | `true` |
| `PROJECT12_HOST` | `0.0.0.0` |
| `PROJECT12_PORT` | `8100` |
| `PROJECT12_AUTO_INGEST` | `true` (first boot) or `false` if vectorstore baked |
| `PROJECT12_LOG_LEVEL` | `INFO` |
| `PROJECT12_LLM_TIMEOUT_SECONDS` | `30` |
| `HF_HOME` | `/app/.cache/huggingface` (Docker) |

### 7.2 Supabase edge (production)

| Variable | Production value |
|----------|------------------|
| `PROJECT12_ENABLED` | **`false`** until sign-off |
| `PROJECT12_SERVICE_URL` | Public HTTPS URL when enabled |
| `PROJECT12_API_KEY` | Same as P12 service |
| Provider keys | At least one of Gemini/Groq/OpenRouter/Lovable |

### 7.3 Infrastructure

| Requirement | Value |
|-------------|-------|
| P12 container RAM | ≥ **4 GB** |
| P12 HTTPS endpoint | Required for Supabase edge egress |
| Firewall | Allow Supabase → P12 :443 |
| First-boot time | 15–45 min (models + optional ingest) |

---

## 8. Validation Executed This Pass

| Test | Command / method | Result |
|------|------------------|--------|
| Vectorstore integrity | pickle load `index.pkl` | ✅ 36,464 chunks |
| Startup config checks | `validate_service.py` | ✅ 4/4 checks (import fails on torch) |
| Arabic crisis heuristic | `test_arabic_crisis.py` | ✅ 25/25 |
| EN/AR SafetyGuard heuristic | inline 5 cases | ✅ 5/5 |
| Edge client unit tests | `deno test` | ✅ 9/9 |
| Cloud `chat` probe | HTTP POST no JWT | ✅ 401 |
| Cloud `project12-bridge` probe | HTTP POST no JWT | ❌ 404 |
| Docker compose live | `docker compose up` | ❌ Docker not installed |

---

## 9. Remaining Blockers

| ID | Blocker | Severity | Owner | Closes when |
|----|---------|----------|-------|-------------|
| **B1** | No live Docker/Linux run of full P12 stack | **Critical** | Ops | `/ready=true`, `/retrieve` 200, `/crisis-detection` 200, `/chat` 200 |
| **B2** | `project12-bridge` not deployed to Supabase | **Critical** | Ops | HTTP 401 (not 404) on bridge URL |
| **B3** | No public `PROJECT12_SERVICE_URL` | **Critical** | Ops | HTTPS endpoint reachable from edge |
| **B4** | Edge staging secrets not set in Supabase cloud | **High** | Ops | Secrets visible in dashboard |
| **B5** | Dockerfile gaps (`libgomp1`, vectorstore bake-in, torch pin) | **Medium** | Project_12 | Hardened image built |
| **B6** | Full cloud E2E (JWT + P12 ON + `X-Project12-Augmented`) | **High** | Ops | Staging smoke matrix green |
| **B7** | Windows native torch unusable | **Info** | — | Use Docker only (documented) |

### Blockers closed since last report

| ID | Item | Status |
|----|------|--------|
| ~~B-AR~~ | Arabic crisis `SAFE` misclassification | ✅ **CLOSED** (25/25) |
| ~~B-WIN~~ | Windows torch root cause documented | ✅ **CLOSED** (RCA written) |

---

## 10. Recommended Deployment Sequence

```
1. Linux VM with Docker (≥4 GB RAM)
2. cd Project_12 && docker compose up --build -d
3. Wait for GET /ready → ready=true
4. Smoke: POST /retrieve, /crisis-detection, /chat (with Bearer key)
5. Expose HTTPS URL (reverse proxy / cloud run)
6. supabase functions deploy project12-bridge
7. supabase secrets set (staging values)
8. Staging E2E: chat + bridge with JWT
9. Sign-off → consider PROJECT12_ENABLED=true (staging only)
10. Production: remain false until explicit approval
```

---

## 11. Final Verdict

| Question | Answer |
|----------|--------|
| Is code deployment-ready? | **Yes** — B.2 bridge, B.3 augmentation, P12 service code, Arabic crisis fix |
| Is infrastructure deployment-ready? | **No** — P12 not hosted; bridge not deployed; secrets not in cloud |
| Can we enable production Project_12? | **NO-GO** |
| Can we proceed to staging deploy (ops steps)? | **CONDITIONAL GO** — execute §10 on Linux host |
| B.4 / B.5 | **Paused — do not start** |

---

**Report complete. No new features implemented. Mind-Sanctuary unchanged. B.4 and B.5 remain paused.**
