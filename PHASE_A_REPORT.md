# Phase A Report — Localization, Language Enforcement, Stop Generation, Voice

**Date:** 2026-06-08  
**Scope:** Implementation only — no deployment.

---

## Summary

Phase A delivers full Arabic UI parity fixes, strict reply-language enforcement, a Stop Generation control, and voice/text response separation.

---

## 1. Arabic localization & RTL

| Item | Status |
|------|--------|
| `ar.json` parity with `en.json` | **PASS** — `missing=0, extra=0` |
| Missing `dashboard.viewJourney` | Added: `"رحلتك النفسية"` |
| RTL via `i18n.ts` + `useDirection` | Unchanged (already applied on `<html dir="rtl">`) |
| Interview / activities / chat strings | Already parallel (~1135 lines) |
| New keys | `chat.stopGeneration`, `login.forgotPassword.*` (AR + EN) |

**Files:** `src/locales/ar.json`, `src/locales/en.json`

---

## 2. Mixed-language chat fix

**Problem:** UI language was sent but latest user message language was not used to enforce replies.

**Solution:**
- `detectMessageLanguage()` — Arabic script vs Latin detection
- `buildLanguagePersonalization()` — **STRICT** Arabic-only / English-only blocks
- Chat edge passes `lastUserLanguageHint` from latest user message into `buildPersonalizedSystemPrompt`
- Project_12 retrieval excerpts may be English — prompt instructs translation into user language

**Files:**
- `supabase/functions/_shared/promptPersonalization.ts`
- `supabase/functions/chat/index.ts`
- `src/lib/ai/promptPersonalization.ts`
- `src/lib/detectMessageLanguage.ts`

**Provider chain & Project_12:** Unchanged — augmentation still pre-stream only.

---

## 3. Stop Generation button

- `ChatInput`: shows red **Stop** (`Square` icon) when `isGenerating && onStop`
- `SessionChat`: `stopGenerationRef` aborts `AbortController`, cancels paced stream, saves partial assistant text or removes empty bubble
- Input remains enabled during generation (user can type next message)

**Files:** `src/components/chat/ChatInput.tsx`, `src/components/SessionChat.tsx`

---

## 4. Voice behavior

| User sends | Assistant receives |
|------------|-------------------|
| Text message | Text stream only — **no auto TTS** |
| Voice message | Text stream + voice reply pipeline (`generateAssistantVoice`) |

**Change:** TTS block gated with `if (user && voice)` (was `if (user)`).

---

## Tests

```
npm test — 58/58 PASS
```

New/updated:
- `prompt-personalization.test.ts` — strict language + `detectMessageLanguage`
- Locale parity: `[OK] ar: missing=0`

---

## Rollback

- Revert `SessionChat.tsx` TTS guard and stop handler
- Revert `buildLanguagePersonalization` strict blocks
- Remove `chat.stopGeneration` keys (optional)

---

*End of Phase A report.*
