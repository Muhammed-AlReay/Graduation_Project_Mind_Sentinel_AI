# B.3 Validation & Stability Audit Report

**Date:** 2026-06-08  
**Scope:** Post crisis-detection fix; B.4/B.5 paused  
**Mind-Sanctuary:** Not modified in this audit cycle

---

## 1. Crisis-Detection Status

| Check | Before | After fix |
|-------|--------|-----------|
| `POST /crisis-detection` with crisis text | HTTP 500 | **HTTP 200** |
| Category for test input | N/A | **SUICIDE_RISK** |
| Root cause | OpenRouter 403 moderation | Documented in `CRISIS_DETECTION_ROOT_CAUSE_REPORT.md` |

---

## 2. B.3 Component Validation Matrix

| # | Component | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Project_12 `/health` | **PASS** (user live) | User validation |
| 2 | Project_12 `/retrieve` | **PASS** (user live) | User validation |
| 3 | Project_12 `/chat` | **PASS** (user live) | User validation |
| 4 | Project_12 `/crisis-detection` | **PASS** (post-fix) | `test_crisis_endpoint.py` HTTP 200 |
| 5 | `project12-bridge` | **CODE READY** | B.2 deployed; not called by frontend yet |
| 6 | Chat augmentation code | **IMPLEMENTED** | `chat/index.ts` + `project12ChatAugmentation.ts` |
| 7 | Augmentation active in prod | **NO** | `PROJECT12_ENABLED` defaults `false` |
| 8 | Provider chain | **UNCHANGED** | Gemini→Groq→OR→Lovable intact |
| 9 | Streaming | **UNCHANGED** | No `SessionChat` / `streamChat` changes |
| 10 | Failure fallback | **VERIFIED** (code + unit tests) | Silent skip on P12 failure |

---

## 3. Is Project_12 Actually Being Called?

| Path | When called | Currently active? |
|------|-------------|-------------------|
| `chat/index.ts` → `fetchChatAugmentation` | Every chat request when not interview mode | **Only if** `PROJECT12_ENABLED=true` on edge + P12 service reachable |
| `project12-bridge` | Client/edge explicit POST | **Not wired** from frontend yet |
| Default deployment | — | **NO** — flag false |

**Conclusion:** Code path exists; production traffic does **not** call Project_12 until edge secrets enable it.

---

## 4. Is Augmentation Actually Injected?

When `PROJECT12_ENABLED=true` and P12 returns data:

```
buildPersonalizedSystemPrompt({
  ...existing inputs,
  project12Augmentation: { retrievalContext, sources, crisisCategory }
})
```

Appended at **end** of system prompt via `buildProject12AugmentBlock()` — never replaces Dr. Sentinel base prompt.

### Example augmented prompt tail (illustrative)

```
[SUPPLEMENTAL CONTEXT — Project_12 reference layer]
This block is optional background only. Do not diagnose. Do not replace your Dr. Sentinel persona or language rules above.
Use only if it helps the user; otherwise ignore silently.

Educational reference excerpts (source material may be English; still reply in the user's language):
Generalized anxiety disorder is characterized by excessive worry lasting six months or more...

Reference sources:
- LibraryFile_151635_46.pdf (p. 42)
- LibraryFile_151635_46.pdf (p. 15)

Supplementary safety signal (metadata only — not diagnostic): SUICIDE_RISK
If this signal is present, prioritize warmth, grounding, and encouraging professional support. Do not quote this label to the user.
```

### Example retrieved sources (from `/retrieve`)

```json
{
  "sources": [
    {
      "content": "Major depressive disorder is characterized by...",
      "source": "LibraryFile_151635_46.pdf",
      "page": 42
    }
  ],
  "chunk_count": 7
}
```

---

## 5. Timeout & Latency

| Setting | Value | Behavior |
|---------|-------|----------|
| `PROJECT12_TIMEOUT_MS` | 1200ms | Per P12 call (retrieve + crisis parallel) |
| Cache | 5 min, `hash(userId:message)` | Skips duplicate retrieval |
| On timeout | `augmentation=null` | Chat proceeds immediately after timeout |
| Provider TTFB impact | ≤1.2s max added to prompt build | Zero if disabled or timeout |

**Telemetry headers on stream:**
- `X-Project12-Augmented: true|false`
- `X-Project12-Retrieval-Cached: true|false`
- `X-AI-Provider` — unchanged

---

## 6. Failure Fallback Behavior

| P12 failure | Chat behavior | User sees |
|-------------|---------------|-----------|
| Disabled | No P12 calls | Normal chat |
| Timeout | Skip augmentation | Normal chat |
| 5xx / network | Skip augmentation | Normal chat |
| Crisis 403 (fixed) | Heuristic SUICIDE_RISK in P12; augmentation may include crisis metadata | Normal chat stream |
| All providers fail | Existing 503 | Existing error toast |

**No HTTP 500 from P12 failures in chat path.**

---

## 7. A/B Comparison (Architectural Analysis)

| Dimension | A: Without Project_12 | B: With Project_12 enabled |
|-----------|----------------------|---------------------------|
| **Empathy** | Dr. Sentinel persona + emotion heuristics | Same persona + optional warmth signal on crisis metadata |
| **Accuracy (clinical facts)** | General LLM knowledge | Grounded in psychiatry PDF excerpts when retrieved |
| **Therapeutic relevance** | CBT/ACT techniques in prompt | Same + condition-specific reference context |
| **Source grounding** | None cited | PDF page citations in supplement |
| **Response quality (Arabic)** | Language rules preserved | Supplement English-only; model instructed to reply in user language |
| **Response quality (English)** | Baseline | Potentially richer on clinical topics |
| **Risk** | LLM hallucination on clinical facts | Reduced for topics in PDF corpus |
| **Latency** | Baseline | +0–1200ms before stream |

**Live A/B chat comparison:** Not executed (requires staging with `PROJECT12_ENABLED=true` + user sessions). Recommend before production enable.

---

## 8. Arabic / English / Mobile / Streaming

| Check | Status | Notes |
|-------|--------|-------|
| Arabic responses | **PASS** (by design) | Language block unchanged; P12 supplement explicitly says reply in user language |
| English responses | **PASS** (by design) | Unchanged base prompt |
| Streaming | **PASS** | SSE path untouched; augmentation is pre-stream |
| Mobile | **PASS** | No new client requests on mount |

---

## 9. Performance Report

| Metric | Value |
|--------|-------|
| Crisis-detection latency (with 403 fallback) | ~1.7–1.9s (includes failed LLM attempt) |
| Crisis-detection latency (heuristic only, if LLM skipped) | <5ms potential (future optimization) |
| Retrieval cache hit | 0ms upstream, `cached: true` |
| Chat augmentation parallel budget | 2 × 1.2s max (retrieve + crisis) |
| Memory (local test) | FAISS load hit `MemoryError` on 8GB-class host — deploy with adequate RAM |

---

## 10. Risks

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | OpenRouter free tier blocks crisis LLM calls | **High** | Heuristic fallback (fixed); consider paid safety model |
| R2 | `PROJECT12_ENABLED=true` without staging test | **High** | Keep false until staging A/B complete |
| R3 | FAISS memory on small instances | **Medium** | Min 4GB+ RAM for vectorstore; use Docker memory limits |
| R4 | English PDF supplement + Arabic chat | **Low** | Prompt instructs reply in user language |
| R5 | Heuristic vs LLM classification divergence | **Medium** | Acceptable for fallback; log `llm_classify_failed` |
| R6 | B.3 crisis metadata in prompt without B.4 client merge | **Low** | Supplementary only; client `detectCrisis` unchanged |

---

## 11. Recommendation

| Action | Priority |
|--------|----------|
| **Deploy crisis-detection fix** to Project_12 service | **P0** — blocking issue resolved |
| Keep `PROJECT12_ENABLED=false` in production edge | **P0** |
| Staging test: enable flag, verify `X-Project12-Augmented: true` on chat | **P1** |
| Run live A/B on 10+ chat turns (EN + AR) | **P1** |
| Consider `PROJECT12_SAFETY_MODEL` env for non-free OpenRouter model | **P2** |
| **Do not start B.4** until staging B.3 sign-off | **Required** |
| Allocate ≥4GB RAM to Project_12 container | **P1** |

### Production readiness verdict

| Layer | Verdict |
|-------|---------|
| Project_12 crisis-detection | **READY** (post-fix) |
| Project_12 retrieve/chat/health | **READY** (per user live tests) |
| B.3 chat augmentation code | **READY for staging** — not for prod until flag enabled + A/B |
| B.4 crisis client merge | **PAUSED** |
| Overall production enable | **NOT RECOMMENDED** until staging validation |

---

## 12. Test Scenarios Executed

| Scenario | Result |
|----------|--------|
| Crisis text → SafetyGuard classify | **PASS** → SUICIDE_RISK |
| Crisis text → HTTP /crisis-detection | **PASS** → HTTP 200 |
| OpenRouter 403 → heuristic fallback | **PASS** |
| P12 disabled → augmentation null | **PASS** (unit test) |
| Provider chain unchanged | **PASS** (code review) |
| Mind-Sanctuary unmodified this cycle | **PASS** |
| Live chat A/B EN/AR | **NOT RUN** — needs staging |
| Live project12-bridge E2E | **NOT RUN** — no frontend caller |
