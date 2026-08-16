-- ============================================================
-- Migration: add Uzbek two-script columns to hadith_library
-- Project:   hadith-reels (HR)  ·  Shared table read by HV
-- Author:    Farhod Elbekov + Claude session, 2026-06-14
-- Status:    APPLIED — verified in prod 2026-08-16 (both columns present in
--            information_schema). Backfill done separately; see P097.
-- Context:   text_tajik already exists + filled (74/74). Only the two Uzbek
--            script columns are missing (verified via information_schema).
-- Companion: sourcing-pipeline-design.md (§7 Uzbek two-script, D4 = Cyrillic canonical)
-- ============================================================
-- Additive + nullable ONLY: no rename, no drop, no NOT NULL, no default,
-- no type change. Catalog-only change in Postgres — no table rewrite,
-- HV reads of existing columns (incl. legacy text_uzbek) are unaffected.
-- ============================================================

ALTER TABLE hadith_library ADD COLUMN IF NOT EXISTS text_uzbek_cyrillic TEXT;  -- [G4] CANONICAL (D4)
ALTER TABLE hadith_library ADD COLUMN IF NOT EXISTS text_uzbek_latin    TEXT;  -- [G4] derived

-- Legacy text_uzbek (live: 61 Latin / 13 Cyrillic) is intentionally LEFT
-- UNCHANGED for HV back-compat. Backfill of the two new columns is a
-- SEPARATE, human-gated sub-step (transliterator + review), not raw SQL.

-- ---------- ROLLBACK (down) — safe only BEFORE backfill ----------
-- ALTER TABLE hadith_library DROP COLUMN IF EXISTS text_uzbek_latin;
-- ALTER TABLE hadith_library DROP COLUMN IF EXISTS text_uzbek_cyrillic;

-- ---------- VERIFY (run after applying) ----------
-- SELECT column_name FROM information_schema.columns
--  WHERE table_name = 'hadith_library'
--    AND column_name IN ('text_uzbek_cyrillic','text_uzbek_latin');   -- expect 2 rows
-- SELECT count(*) FROM hadith_library;                                 -- expect 74 (unchanged)
