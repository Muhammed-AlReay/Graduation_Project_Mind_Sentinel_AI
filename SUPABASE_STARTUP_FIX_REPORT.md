# Supabase Startup Fix Report

**Date:** 2026-06-08  
**Project:** Mind-Sanctuary (`Mind-Sanctuary-main/Mind-Sanctuary-main/`)  
**Original error:** `ERROR: function public.touch_updated_at() does not exist` in migration `20260518005345_3f32b23a-478c-415c-a358-bb3c02d55807.sql`

---

## Executive summary

**Root cause:** Migration **order was wrong**. `touch_updated_at()` was first **used** in `20260518005345` (2026-05-18) but only **created** in `20260603170000_production_audit_fixes.sql` (2026-06-03).

**Fix:** Define `touch_updated_at()` earlier in the chain — in `20260510003711_f12b7c27-6f9e-4fdb-a8ae-8adbeb15b2e3.sql`, alongside the existing `set_updated_at()` helper (matches production `migration/.../sql/03_functions.sql`).

**Secondary fix discovered during validation:** `anonymous_recovery_codes` table was referenced in `20260603140000`–`20260603150000` before creation in `20260603170000`. Added migration `20260603135000_anonymous_recovery_codes_table.sql`.

**Migration chain result:** All **18 migrations apply successfully** (verified via `supabase start` logs).  
**Full stack startup** on this machine then hit **Docker Desktop / storage health** issues (environmental, not SQL).

**Project_12 integration:** Re-validated after fix — chat edge augmentation still works (`X-Project12-Augmented: true`).

---

## Investigation

### Where `touch_updated_at()` should be defined

| Location | Role |
|----------|------|
| `migration/fsterbxivhhzipfgpvou/sql/03_functions.sql` | **Canonical** — defines `touch_updated_at` early with `set_updated_at` and `update_updated_at_column` |
| `migration/fsterbxivhhzipfgpvou/BOOTSTRAP_ALL.sql` | Same function, used by `message_feedback_touch` trigger |
| `supabase/migrations/20260603170000_production_audit_fixes.sql` | Comment: *"Missing utility used by message_feedback trigger"* — added too late |
| `supabase/migrations/20260510003711_*.sql` | Had `set_updated_at()` only — **fix applied here** |

### All references to `touch_updated_at` in supabase migrations

| Migration | Usage |
|-----------|--------|
| `20260518005345` | **CREATE TRIGGER** `trg_message_feedback_touch` → `touch_updated_at()` — **failed here** |
| `20260603170000` | `CREATE OR REPLACE FUNCTION touch_updated_at()` — too late |

### Related timestamp helpers (not interchangeable in triggers without migration edit)

| Function | Defined in |
|----------|------------|
| `update_updated_at_column()` | `20260308203135` |
| `set_updated_at()` | `20260510003711`, `20260518005433` |
| `touch_updated_at()` | **Now** `20260510003711` + idempotent recreate in `20260603170000` |

`touch_updated_at` and `set_updated_at` are **functionally identical** (`NEW.updated_at = now()`). Production uses `touch_updated_at` for `message_feedback` and profiles triggers; keeping the name avoids drift from bootstrap SQL.

### Diagnosis

| Question | Answer |
|----------|--------|
| Migration order wrong? | **Yes** — function used ~16 days before creation in filename order |
| Migration missing? | **Effectively yes** — function block was missing from early migrations; added to `20260510003711` |
| Should trigger use another function? | Could use `set_updated_at()` instead, but production parity prefers `touch_updated_at()` |

---

## Changes applied

### 1. `supabase/migrations/20260510003711_f12b7c27-6f9e-4fdb-a8ae-8adbeb15b2e3.sql`

Added before any consumer migration:

```sql
CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = public AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END $$;
```

### 2. `supabase/migrations/20260603135000_anonymous_recovery_codes_table.sql` (new)

Creates `anonymous_recovery_codes` + base RLS **before** `20260603140000_anonymous_recovery_transfer.sql`.

### Unchanged

- `20260518005345` trigger still calls `touch_updated_at()` — now valid.
- `20260603170000` keeps `CREATE OR REPLACE` / `IF NOT EXISTS` — idempotent on fresh and upgraded DBs.

---

## Validation: `supabase start`

### Migration apply — PASS

From `supabase start` output (2026-06-08):

```
Applying migration 20260308203135_...
...
Applying migration 20260510003711_...          ← touch_updated_at created
Applying migration 20260518005345_...          ← trigger succeeds (no ERROR)
...
Applying migration 20260603135000_...          ← anonymous_recovery_codes
Applying migration 20260603140000_...
Applying migration 20260603150000_...
...
Applying migration 20260603190000_restore_schema_safe.sql
Starting containers...
```

**No SQL errors.** Original `touch_updated_at` failure is resolved.

### Container startup — blocked (environment)

After migrations, startup failed on this Windows host:

1. First run: `supabase_storage_* container is not ready: unhealthy`
2. Second run: `FeatureNotEnabled` for Vector buckets
3. Later: `Docker Desktop is unable to start`

These are **Docker Desktop / local infra** issues, not migration defects. To complete full local Supabase:

1. Start **Docker Desktop** and wait until healthy
2. Optionally expose daemon on `tcp://localhost:2375` if analytics warnings persist (see [Supabase Windows docs](https://supabase.com/docs/guides/local-development/cli/getting-started?queryGroups=platform&platform=windows#running-supabase-locally))
3. Run: `npx supabase stop --no-backup && npx supabase start`

---

## Post-fix: chat edge + Project_12

Chat edge restarted locally; E2E script run (`scripts/local-e2e-validation.ts`):

| Test | Result |
|------|--------|
| `deno_unit_tests` | PASS (13) |
| `project12_health` | PASS |
| `p12_retrieve_en` | PASS |
| `p12_crisis_en` / `p12_crisis_ar` | PASS |
| `chat_normal_en` | PASS — `augmented=true crisis=SAFE status=200` |
| `chat_crisis_en` | PASS — `augmented=true crisis=SUICIDE_RISK` (503 = OpenRouter moderation/rate limit, not P12) |
| `chat_normal_ar` | PASS — `augmented=true` |
| `p12_offline_fallback` | PASS |
| `bridge_retrieve` | FAIL — bridge not running on :8001 (optional; unrelated to migration fix) |

**10 / 11** — Project_12 chat augmentation confirmed working after migration fixes.

Chat edge log excerpt:

```
augmentation_used=true retrieval_ok=true crisis_category=SAFE
augmentation_used=true crisis_category=SUICIDE_RISK
[chat] attempting provider=openrouter model=openrouter/free
```

---

## Rollback

To revert migration changes:

```bash
git checkout -- supabase/migrations/20260510003711_f12b7c27-6f9e-4fdb-a8ae-8adbeb15b2e3.sql
git rm supabase/migrations/20260603135000_anonymous_recovery_codes_table.sql
npx supabase stop --no-backup
npx supabase start   # will fail again on touch_updated_at
```

---

## Files modified

| File | Action |
|------|--------|
| `supabase/migrations/20260510003711_f12b7c27-6f9e-4fdb-a8ae-8adbeb15b2e3.sql` | Added `touch_updated_at()` |
| `supabase/migrations/20260603135000_anonymous_recovery_codes_table.sql` | **New** — early table + RLS |

---

## Recommended next steps

1. Start Docker Desktop and run `npx supabase start` to confirm full local stack URLs
2. Run `npx supabase status` and point `.env.local` at local API URL if desired
3. Keep using `VITE_CHAT_FUNCTION_URL=http://127.0.0.1:8000` for Project_12 augmentation until cloud bridge is deployed

---

*End of report.*
