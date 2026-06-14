# Phase 0 — HV coordination note

**For:** the HV (hadithverifier.com) side, before applying the Phase 0 migration
**Migration file:** `20260614_sourcing_phase0_schema.sql`
**Shared object affected:** `hadith_library` (Supabase `xeirfeqnbjfyszykiraa`)
**Requested by:** HR (hadith-reels) sourcing pipeline — `sourcing-pipeline-design.md`

---

## What this migration does to the shared table

Adds **three nullable columns** to `hadith_library`. Nothing else on the shared
table is touched.

| Column | Purpose |
|--------|---------|
| `text_tajik` | Native Tajik Cyrillic (ends the P050 Russian-fallback for *new*/backfilled rows) |
| `text_uzbek_cyrillic` | Canonical Uzbek (Cyrillic) |
| `text_uzbek_latin` | Derived Uzbek (Latin) |

The HR-owned tables it also creates (`hadith_candidates`, `hadith_promotions`)
are **not read by HV** and are out of scope for HV review.

## Why it is safe for HV

- **Additive + nullable only.** No rename, no drop, no type change, no `NOT NULL`,
  no default that would rewrite rows.
- In Postgres, adding a nullable column with no default is a **catalog-only**
  change — no full-table rewrite, negligible lock. Existing rows are untouched.
- **Legacy `text_uzbek` is left exactly as-is.** HV keeps reading it. HV is not
  forced to change anything.
- HV reads of existing columns return identical results before and after.

## What HV must confirm before sign-off (3 items)

1. **No positional INSERTs into `hadith_library`.** Adding columns at the end
   breaks any `INSERT INTO hadith_library VALUES (...)` that omits a column list
   (it would now be 3 values short). Confirm HV always inserts with an explicit
   column list (standard for the Supabase client / ORMs — just verify).
2. **No strict column-count / `SELECT *` assumptions** that would choke on extra
   columns. (Returning three extra nulls is normally a no-op — confirm.)
3. **No RLS policy work needed.** RLS is disabled; everything uses
   `SUPABASE_SERVICE_ROLE_KEY` server-side. Confirm no policy depends on the
   table's column set.

If all three are clear, the change is non-breaking for HV.

## Deferred to HV's own timeline (NOT decided here)

This migration only makes the columns **available**. HV decides separately, later:
- Whether to switch its **TJ display** from the P050 Russian fallback to native
  `text_tajik` once backfilled.
- Whether to switch its **UZ reads** to `text_uzbek_cyrillic` / `text_uzbek_latin`.

No HR change forces either; HV adopts when ready.

## Timing & rollback

- **Timing:** apply in a window when HV is **not** mid-deploy/mid-migration, to
  avoid overlapping schema changes. The change itself is fast.
- **Rollback:** clean (`DROP COLUMN`) **only before the data backfill**. After the
  74-row TJ/UZ backfill, dropping the columns destroys native content — back up
  first. The backfill is a **separate, human-gated sub-step**, not part of this
  migration.

## Sign-off

- [ ] HV confirms items 1–3 above
- [ ] Migration applied + verified (run the VERIFY queries at the bottom of the SQL)
- [ ] Live `hadith_library` row count recorded (dedup baseline)
