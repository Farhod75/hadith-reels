-- ============================================================
-- Migration: hadith_candidates + hadith_promotions (HR-owned staging)
-- Project:   hadith-reels (HR)
-- Author:    Farhod Elbekov + Claude session, 2026-06-14
-- Status:    SAFE TO RUN NOW — neither table touches the shared hadith_library,
--            so NO HV coordination is required.
-- Companion: sourcing-pipeline-design.md §3.1
-- Note:      Supersedes sections B + D of the parked
--            20260614_sourcing_phase0_schema.sql (section C — the shared-table
--            columns — remains separate and HV-gated).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Staging table — every candidate lives here until a human approves it.
CREATE TABLE IF NOT EXISTS hadith_candidates (
  candidate_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  status              TEXT NOT NULL DEFAULT 'sourced',

  -- identity / provenance (no promotion without provenance)
  collection          TEXT NOT NULL,
  hadith_number       TEXT NOT NULL,
  narrator            TEXT,
  grade               TEXT NOT NULL,
  grading_source      TEXT NOT NULL,
  grade_confirmed     BOOLEAN NOT NULL DEFAULT false,
  source_urls         JSONB NOT NULL DEFAULT '{}'::jsonb,

  -- content
  text_arabic         TEXT NOT NULL,
  text_english        TEXT,
  text_russian        TEXT,
  text_uzbek_cyrillic TEXT,
  text_uzbek_latin    TEXT,
  text_tajik          TEXT,
  translation_meta    JSONB NOT NULL DEFAULT '{}'::jsonb,

  -- dedup (Stage 1)
  dedup_hard_hit      BOOLEAN NOT NULL DEFAULT false,
  dedup_fuzzy_hits    JSONB   NOT NULL DEFAULT '[]'::jsonb,

  -- A/B verify (Stage 3)
  verify_a            JSONB,
  verify_b            JSONB,
  verify_agreement    TEXT,
  red_flags           JSONB NOT NULL DEFAULT '[]'::jsonb,

  -- human gate (Stage 4/5)
  reviewed_by         TEXT,
  reviewed_at         TIMESTAMPTZ,
  review_action       TEXT,
  review_reason       TEXT,
  promote_mode        TEXT,
  promoted_library_id TEXT,

  CONSTRAINT uq_candidate_ref UNIQUE (collection, hadith_number),
  CONSTRAINT ck_grade         CHECK (grade IN ('sahih','hasan')),
  CONSTRAINT ck_status        CHECK (status IN
                               ('sourced','deduped','translated','verified',
                                'needs_human','approved','rejected','promoted')),
  CONSTRAINT ck_agreement     CHECK (verify_agreement IS NULL OR
                               verify_agreement IN ('pass','fail','disagree')),
  CONSTRAINT ck_review        CHECK (review_action IS NULL OR
                               review_action IN ('approve','edit_approve','reject','defer')),
  CONSTRAINT ck_promote_mode  CHECK (promote_mode IS NULL OR
                               promote_mode IN ('insert','augment_update'))
);

CREATE INDEX IF NOT EXISTS ix_candidates_status ON hadith_candidates (status);

-- Promotion audit trail — one row per promote action.
CREATE TABLE IF NOT EXISTS hadith_promotions (
  promotion_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  promoted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  candidate_id     UUID NOT NULL REFERENCES hadith_candidates(candidate_id),
  library_id       TEXT NOT NULL,
  promote_mode     TEXT NOT NULL CHECK (promote_mode IN ('insert','augment_update')),
  reviewed_by      TEXT NOT NULL,
  source_deeplink  TEXT,
  columns_written  TEXT[]
);

-- ---------- VERIFY (run after applying) ----------
-- SELECT table_name FROM information_schema.tables
--  WHERE table_name IN ('hadith_candidates','hadith_promotions');   -- expect 2 rows
-- SELECT count(*) FROM hadith_candidates;                            -- expect 0
