# Phase C Report — Image Upload, File Types, Mental-Health Prompt

**Date:** 2026-06-08  
**Scope:** Implementation only — no deployment.

---

## Summary

Phase C wires chat image upload (drag/drop/paste/button), enforces allowed file types, applies a 3-images-per-12-hours rate limit, and extends the system prompt with psychology-focused guidance without removing existing content.

---

## 7. Image support

| Feature | Implementation |
|---------|----------------|
| Upload button | `ChatInput` paperclip → file picker (was blocked by toast; now wired) |
| Drag and drop | Existing `onDrop` in `ChatInput` |
| Paste image | Existing `onPaste` in `ChatInput` |
| Send with message | `SessionChat` stores `{ text, attachments }` JSON in `chat_messages.content` |
| Rate limit | **3 images / 12 hours / user** — `src/lib/imageUploadRateLimit.ts` (localStorage) |

**Files:** `SessionChat.tsx`, `ChatInput.tsx`, `imageUploadRateLimit.ts`

---

## 8. Allowed file types

**Allowed:** `txt`, `png`, `jpg`, `jpeg`, `webp`  
**Rejected:** pdf, doc, docx, exe, and all other types

**Files:**
- `src/lib/uploadAttachment.ts` — `ALLOWED_MIME` / `ALLOWED_EXT`
- `src/components/chat/ChatInput.tsx` — `accept` attribute

---

## 9. Mental-health guidance (prompt extension)

Appended block at end of `buildPersonalizedSystemPrompt` (after all existing content + Project_12 block):

- Therapeutic / psychoeducational scope only
- Image analysis through mental-health lens
- No general-purpose object ID
- Professional referral for diagnosis/crisis
- Explicit: prior instructions remain in full effect

**Files:**
- `supabase/functions/_shared/promptPersonalization.ts`
- `src/lib/ai/promptPersonalization.ts` (mirror)

**Project_12:** Unchanged — still supplemental context only.

---

## Tests

```
npm test — 58/58 PASS
```

| Test file | Coverage |
|-----------|----------|
| `upload-validation.test.ts` | Rejects pdf; accepts png/txt |
| `image-upload-rate-limit.test.ts` | 3-upload cap |
| `prompt-personalization.test.ts` | Language strict rules |

---

## Files modified

| File | Change |
|------|--------|
| `src/lib/uploadAttachment.ts` | Allowlist only |
| `src/lib/imageUploadRateLimit.ts` | New |
| `src/components/chat/ChatInput.tsx` | Rate limit + accept list |
| `src/components/SessionChat.tsx` | Attachment send wiring |
| `supabase/functions/_shared/promptPersonalization.ts` | Guidance append |
| `src/lib/ai/promptPersonalization.ts` | Guidance append |
| `src/test/upload-validation.test.ts` | Updated expectations |
| `src/test/image-upload-rate-limit.test.ts` | New |

---

*End of Phase C report.*
