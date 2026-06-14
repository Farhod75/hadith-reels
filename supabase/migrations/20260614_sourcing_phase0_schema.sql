-- ============================================================
-- Migration: Phase 0 — sourcing pipeline schema
-- Project:   hadith-reels (HR)
-- Author:    Farhod Elbekov + Claude session, 2026-06-14
-- Status:    DRAFT — DO NOT RUN until HV sign-off (touches SHARED hadith_library)
-- Companion: sourcing-pipeline-design.md (§3 data model, §9 Phase 0)
--            phase0-hv-coordination-note.md
-- ============================================================
-- Scope of THIS migration (DDL only — additive, reversible):
--   A. pgcrypto guard (for gen_random_uuid)
--   B. CREATE hadith_candidates   — HR-owned staging table        (SAFE)
--   C. ADD 3 nullable columns to hadith_library — SHARED w/ HV    (SENSITIVE)
--   D. CREATE hadith_promotions   — HR-owned audit trail          (SAFE)
--
-- NOT in this migration (separate, human-gated sub-step):
--   • Data backfill of text_tajik / text_uzbek_* for the 74 rows.
--     That runs through the Stage-5 augment-update gate, never raw SQL,
--     because native Tajik must be generated + human-reviewed first.
-- ============================================================


-- A. Extension guard (Supabase normally has pgcrypto; safe to re-run) --------
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- B. Staging table — HR owns it; HV never reads it; safe to iterate ----------
CREATE TABLE IF NOT EXISTS hadith_candidates (
  candidate_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  status              TEXT NOT NULL DEFAULT 'sourced',

  -- identity / provenance (G1: no promotion without provenance)
  collection          TEXT NOT NULL,
  hadith_number       TEXT NOT NULL,
  narrator            TEXT,
  grade               TEXT NOT NULL,
  grading_source      TEXT NOT NULL,          -- which Tier-1 authority graded it (§4)
  source_urls         JSONB NOT NULL,         -- {dorar, sunnah, hadeethenc} deep-links

  -- content
  text_arabic         TEXT NOT NULL,          -- canonical matn (source of truth)
  text_english        TEXT,
  text_russian        TEXT,
  text_uzbek_cyrillic TEXT,                   -- [G4] CANONICAL
  text_uzbek_latin    TEXT,                   -- [G4] derived
  text_tajik          TEXT,                   -- [G3] native Tajik Cyrillic

  -- per-field provenance: 'authoritative' | 'machine' | 'human_edited'
  translation_meta    JSONB NOT NULL DEFAULT '{}'::jsonb,

  -- dedup (Stage 1)
  dedup_hard_hit      BOOLEAN NOT NULL DEFAULT false,
  dedup_fuzzy_hits    JSONB   NOT NULL DEFAULT '[]'::jsonb,   -- advisory only (G2)

  -- A/B verify (Stage 3)
  verify_a            JSONB,                  -- pass A = Claude
  verify_b            JSONB,                  -- pass B = different model (D2)
  verify_agreement    TEXT,                   -- pass | fail | disagree
  red_flags           JSONB NOT NULL DEFAULT '[]'::jsonb,

  -- human gate (Stage 4/5)
  reviewed_by         TEXT,
  reviewed_at         TIMESTAMPTZ,
  review_action       TEXT,                   -- approve | edit_approve | reject | defer
  review_reason       TEXT,
  promote_mode        TEXT,                   -- insert | augment_update
  promoted_library_id TEXT,                   -- hadith_library row after promote

  CONSTRAINT uq_candidate_ref  UNIQUE (collection, hadith_number),
  CONSTRAINT ck_grade          CHECK (grade IN ('sahih','hasan')),   -- daif never reaches staging
  CONSTRAINT ck_status         CHECK (status IN
                                ('sourced','deduped','translated','verified',
                                 'needs_human','approved','rejected','promoted')),
  CONSTRAINT ck_agreement      CHECK (verify_agreement IS NULL OR
                                verify_agreement IN ('pass','fail','disagree')),
  CONSTRAINT ck_review         CHECK (review_action IS NULL OR
                                review_action IN ('approve','edit_approve','reject','defer')),
  CONSTRAINT ck_promote_mode   CHECK (promote_mode IS NULL OR
                                promote_mode IN ('insert','augment_update'))
);

CREATE INDEX IF NOT EXISTS ix_candidates_status ON hadith_candidates (status);


-- ============================================================
-- C. SHARED TABLE CHANGES — hadith_library (READ BY HV)
--    ⚠️  Requires HV sign-off before running.
--    Additive + nullable ONLY: no rename, no drop, no NOT NULL,
--    no default-backfill, no type change.
--    Adding nullable columns is a catalog-only change in Postgres —
--    no full-table rewrite; HV reads of existing columns are unaffected.
-- ============================================================
ALTER TABLE hadith_library ADD COLUMN IF NOT EXISTS text_tajik          TEXT;  -- [G3] native Tajik Cyrillic
ALTER TABLE hadith_library ADD COLUMN IF NOT EXISTS text_uzbek_cyrillic TEXT;  -- [G4] CANONICAL
ALTER TABLE hadith_library ADD COLUMN IF NOT EXISTS text_uzbek_latin    TEXT;  -- [G4] derived
-- Legacy text_uzbek (mixed: 62 Latin / 12 Cyrillic) is intentionally LEFT
-- UNCHANGED for HV back-compat. HV adopts the new columns on its own timeline.


-- D. Promotion audit trail — HR-owned. One row per promote action (G1) -------
--    NOTE: library_id is TEXT to stay agnostic to hadith_library's PK type.
--    Confirm hadith_library PK type during HV review; TEXT safely stores it.
--    Deliberately NO FK to hadith_library (avoid coupling the shared table).
CREATE TABLE IF NOT EXISTS hadith_promotions (
  promotion_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  promoted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  candidate_id     UUID NOT NULL REFERENCES hadith_candidates(candidate_id),
  library_id       TEXT NOT NULL,            -- hadith_library row affected
  promote_mode     TEXT NOT NULL CHECK (promote_mode IN ('insert','augment_update')),
  reviewed_by      TEXT NOT NULL,
  verify_a         JSONB,
  verify_b         JSONB,
  source_deeplink  TEXT,                     -- canonical Dorar/Sunnah link carried forward
  columns_written  TEXT[]                    -- e.g. {text_tajik} for an augment-update
);


-- ============================================================
-- ROLLBACK (down) — run in REVERSE order if needed.
-- ⚠️  DROP COLUMN on hadith_library is only safe BEFORE the data backfill;
--     after backfill it destroys native TJ/UZ content. Back up first.
-- ============================================================
-- DROP TABLE IF EXISTS hadith_promotions;
-- ALTER TABLE hadith_library DROP COLUMN IF EXISTS text_uzbek_latin;
-- ALTER TABLE hadith_library DROP COLUMN IF EXISTS text_uzbek_cyrillic;
-- ALTER TABLE hadith_library DROP COLUMN IF EXISTS text_tajik;
-- DROP TABLE IF EXISTS hadith_candidates;


-- ============================================================
-- VERIFY (run after applying; paste output as ground truth)
-- ============================================================
-- 1) New columns present on the shared table:
-- SELECT column_name, data_type, is_nullable
--   FROM information_schema.columns
--  WHERE table_name = 'hadith_library'
--    AND column_name IN ('text_tajik','text_uzbek_cyrillic','text_uzbek_latin');
--
-- 2) Staging + audit tables exist:
-- SELECT table_name FROM information_schema.tables
--  WHERE table_name IN ('hadith_candidates','hadith_promotions');
--
-- 3) HV unaffected — existing columns intact + LIVE row count
--    (dedup baseline must use this live number, never a doc):
-- SELECT count(*) AS live_rows FROM hadith_library;   -- confirm against current count