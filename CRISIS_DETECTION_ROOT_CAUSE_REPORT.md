# Crisis-Detection Root Cause Report

**Date:** 2026-06-08  
**Endpoint:** `POST /crisis-detection`  
**Test input:** `"I feel hopeless and I don't want to continue living"`

---

## Symptom

Live validation returned **HTTP 500** with body:

```json
{
  "error": "internal_error",
  "detail": "An unexpected error occurred",
  "code": "INTERNAL_ERROR"
}
```

`/health`, `/retrieve`, and `/chat` passed.

---

## Exception Path (traced)

```
POST /crisis-detection
  → service/app.py: crisis_detection()
  → state.require_llm()                    ✓ OK
  → ThreadPoolExecutor → SafetyGuard.classify()
  → safety_guard.py: self.chain.invoke()
  → langchain_openai.ChatOpenAI
  → OpenRouter API POST /chat/completions
  → HTTP 403 PermissionDeniedError         ✗ UNCAUGHT
  → service/app.py: generic_exception_handler
  → HTTP 500 INTERNAL_ERROR
```

---

## Root Cause

**OpenRouter free-tier moderation blocks crisis-language inputs before the LLM can classify them.**

| Factor | Detail |
|--------|--------|
| Model | `openrouter/free` (routes to free models e.g. `openai/gpt-oss-120b:free`) |
| Error | `403 PermissionDeniedError` |
| Moderation reason | `self-harm/intent` |
| Flagged input | Safety classifier system prompt + user crisis text combined |
| Prior failures | Multiple `429` rate limits on other free models in same request chain |

**Irony:** The safety classifier cannot call the LLM on the exact messages it is designed to detect — OpenRouter's moderation rejects them.

This is **not** caused by:
- SafetyGuard prompt template syntax
- Pydantic request schema mismatch
- Model loading failure
- Missing environment variables (API key was valid — `/chat` worked)
- Dependency version bug

---

## Fix Applied (Project_12 only)

| File | Change |
|------|--------|
| `safety/heuristic_classifier.py` | **NEW** — keyword fallback classifier |
| `safety/safety_guard.py` | Catch all LLM exceptions; fallback to heuristic; handle empty/list content |
| `service/app.py` | Crisis endpoint never returns 500; timeout/exception → heuristic |
| `scripts/diagnose_crisis.py` | Diagnostic script |
| `scripts/test_crisis_endpoint.py` | Endpoint validation script |

**Mind-Sanctuary-main:** NOT modified.

---

## Validation Proof

### Direct SafetyGuard classify

```
Raw LLM call failed: PermissionDeniedError (403 moderation)
CLASSIFY_OK: SUICIDE_RISK
```

Log:
```json
{"component":"SafetyGuard","event":"llm_classify_failed","error_type":"PermissionDeniedError","moderation_block":true,"fallback":"heuristic"}
```

### HTTP endpoint (TestClient)

```
HTTP 200
{
  "category": "SUICIDE_RISK",
  "safety_guidance": "I'm sorry you're going through a difficult time..."
}
PASS: category=SUICIDE_RISK
```

---

## Final Endpoint Result

| Field | Value |
|-------|-------|
| HTTP status | **200** |
| category | **SUICIDE_RISK** |
| safety_guidance | Populated from `CrisisHandler` |
| User-visible error | None |

---

## Operational Notes

1. **Heuristic fallback** activates when OpenRouter returns 403/429 or on timeout — appropriate for crisis detection since blocked content is itself a strong signal.
2. **For production LLM classification**, consider `PROJECT12_LLM_MODEL` pointing to a paid/non-moderated model for SafetyGuard only (future config — not implemented in this fix).
3. **Unrelated issue observed** (not fixed per scope): FAISS `MemoryError` on low-RAM test host during full app startup — does not affect crisis-detection when LLM stack loads independently.
