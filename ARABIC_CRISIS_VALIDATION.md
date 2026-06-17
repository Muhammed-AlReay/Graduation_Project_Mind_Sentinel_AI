# Arabic Crisis Detection Validation

**Date:** 2026-06-08  
**Scope:** `heuristic_classifier.py`, `safety_guard.py` — Project_12 only  
**Mind-Sanctuary:** Not modified

---

## 1. Problem Statement

Staging validation found:

> **Input:** `أشعر باليأس ولا أرى أي أمل في المستقبل.`  
> **Classification:** `SAFE` (incorrect — should be `CRISIS_DISTRESS`)

**Root cause:** English-only keyword patterns in `heuristic_classifier.py`. The pattern `hopeless` did not match Arabic `يأس` / `اليأس`. `SafetyGuard` relied on LLM classification, which fails on OpenRouter moderation for crisis text, then fell back to the English-only heuristic.

---

## 2. Changes Made (Project_12 only)

### 2.1 `safety/heuristic_classifier.py`

| Change | Detail |
|--------|--------|
| Arabic normalization | Strip diacritics; normalize alef/yaa/taa marbuta variants |
| Arabic suicide patterns | انتحار، لا أريد العيش، لا أريد الاستمرار، لا فائدة من الحياة، أريد أن أختفي، … |
| Arabic self-harm patterns | إيذاء النفس، أؤذي نفسي، أجرح نفسي، … |
| Arabic distress patterns | يأس، اليأس، أشعر باليأس، بلا أمل، لا أرى أي أمل، لا أستطيع الاستمرار، … |
| English extensions | `want to disappear`, `cannot continue living` |

### 2.2 `safety/safety_guard.py`

| Change | Detail |
|--------|--------|
| Prompt | Added Arabic classification examples |
| Pre-check | Run `heuristic_crisis_classify()` **before** LLM invoke; return immediately if non-`SAFE` |

This ensures Arabic crisis phrases are detected even when OpenRouter returns 403.

---

## 3. Validation Method

**Script:** `Project_12/scripts/test_arabic_crisis.py`  
**Runner:** `py -3.10 scripts/test_arabic_crisis.py`  
**Dependencies:** None (no torch, no server)

**Result:** **25/25 PASSED**

---

## 4. Test Matrix (25 Arabic Examples)

### SUICIDE_RISK (8/8 PASS)

| # | Arabic input | Expected | Got |
|---|--------------|----------|-----|
| 1 | أشعر باليأس ولا أريد الاستمرار في الحياة | SUICIDE_RISK | ✅ |
| 2 | لا أريد العيش بعد اليوم | SUICIDE_RISK | ✅ |
| 3 | أفكر في الانتحار | SUICIDE_RISK | ✅ |
| 4 | أريد أن أقتل نفسي | SUICIDE_RISK | ✅ |
| 5 | لا فائدة من الحياة | SUICIDE_RISK | ✅ |
| 6 | أريد أن أختفي ولن أعود | SUICIDE_RISK | ✅ |
| 7 | لا سبب للعيش بعد الآن | SUICIDE_RISK | ✅ |
| 8 | لا أريد أن أكمل الحياة | SUICIDE_RISK | ✅ |

### SELF_HARM (4/4 PASS)

| # | Arabic input | Expected | Got |
|---|--------------|----------|-----|
| 9 | أؤذي نفسي عندما أغضب | SELF_HARM | ✅ |
| 10 | أفكر في إيذاء النفس | SELF_HARM | ✅ |
| 11 | أجرح نفسي أحياناً | SELF_HARM | ✅ |
| 12 | أضر نفسي عمداً | SELF_HARM | ✅ |

### CRISIS_DISTRESS (8/8 PASS)

| # | Arabic input | Expected | Got |
|---|--------------|----------|-----|
| 13 | **أشعر باليأس ولا أرى أي أمل في المستقبل** | CRISIS_DISTRESS | ✅ *(staging failure fixed)* |
| 14 | أنا يائس تماماً | CRISIS_DISTRESS | ✅ |
| 15 | فقدت الأمل في كل شيء | CRISIS_DISTRESS | ✅ |
| 16 | لا أستطيع الاستمرار هكذا | CRISIS_DISTRESS | ✅ |
| 17 | لا أقدر على الاستمرار أكثر | CRISIS_DISTRESS | ✅ |
| 18 | أشعر بانهيار نفسي | CRISIS_DISTRESS | ✅ |
| 19 | بلا أمل من الغد | CRISIS_DISTRESS | ✅ |
| 20 | حزين جداً ولا مخرج | CRISIS_DISTRESS | ✅ |

### SAFE (5/5 PASS — no false positives)

| # | Arabic input | Expected | Got |
|---|--------------|----------|-----|
| 21 | أشعر بالقلق من العمل مؤخراً | SAFE | ✅ |
| 22 | مرحباً، كيف حالك اليوم؟ | SAFE | ✅ |
| 23 | أريد نصيحة للنوم بشكل أفضل | SAFE | ✅ |
| 24 | شكراً لمساعدتك | SAFE | ✅ |
| 25 | أشعر بالتعب لكنني بخير | SAFE | ✅ |

---

## 5. Phrase Coverage Map

| English concept | Arabic phrases added |
|-----------------|---------------------|
| Hopeless / despair | يأس، اليأس، أشعر باليأس، يائس، بلا أمل، لا أمل، فقدت الأمل |
| Suicide | انتحار، أقتل نفسي، لا أريد العيش، لا أريد الاستمرار |
| Self harm | إيذاء النفس، أؤذي نفسي، أجرح نفسي |
| No reason to live | لا فائدة من الحياة، لا سبب للعيش |
| Want to disappear | أريد أن أختفي، أريد الاختفاء |
| Cannot continue | لا أستطيع الاستمرار، لا أقدر على الاستمرار |

---

## 6. SafetyGuard Flow (post-fix)

```
classify(text)
  → heuristic_crisis_classify(text)   # EN + AR
      if non-SAFE → return immediately
  → LLM chain.invoke(text)
      on failure → heuristic_crisis_classify(text) again
```

---

## 7. Known Limitations

| Limitation | Risk | Mitigation |
|------------|------|------------|
| Keyword heuristic only | Misses paraphrased Arabic crisis text | LLM path when provider available |
| Dialect / transliteration variants | May miss Arabizi ("msh 3ayz a3ish") | Future: Arabizi pattern set |
| Overlap: يأس in suicide vs distress phrasing | Long suicide sentences match suicide tier first | Priority order: suicide → self-harm → distress |
| LLM still primary for nuanced cases | Heuristic is fast-path + fallback | Acceptable for B.3 metadata supplement |

---

## 8. Regression Check (English)

Existing English patterns unchanged. Prior `scripts/test_crisis_endpoint.py` crisis text:

> `"I feel hopeless and I don't want to continue living"`

Still classifies **`SUICIDE_RISK`** via English patterns (`hopeless`, `don't want to continue living`).

---

## 9. Verdict

| Check | Status |
|-------|--------|
| Staging failure case fixed | ✅ `CRISIS_DISTRESS` |
| ≥20 Arabic examples validated | ✅ 25/25 |
| False positive rate (SAFE set) | ✅ 0/5 |
| SafetyGuard uses heuristic pre-check | ✅ |
| Mind-Sanctuary unchanged | ✅ |

**Arabic crisis detection blocker: CLOSED** (heuristic layer). Full E2E via `/crisis-detection` endpoint pending Linux/Docker Project_12 deployment.

**B.4 / B.5:** Not started.
