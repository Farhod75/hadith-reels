# sourcing-pipeline-design.md
# Hadith Reels — Content Sourcing & Library-Population Pipeline (DESIGN)
# ============================================================

> **Author:** Farhod Elbekov + Claude session, 2026-06-14
> **Status:** DRAFT FOR REVIEW — no code until this is approved + open decisions resolved
> **Project:** hadith-reels (github.com/Farhod75/hadith-reels)
> **Companion docs:** `agent-architecture-roadmap.md` (downstream reel fleet),
>   `reel-creation-pipeline.md` (reel production), `hr-CLAUDE.md` (library schema)
> **Scope:** This pipeline **fills the library** (gets new verified hadiths *in*).
>   It is *upstream* of reel production. It does NOT make reels.

---

## 0. Why this exists / what it is not

Today the library is a hand-curated set of **~74 hadiths** in `hadith_library`
(shared Supabase, also read by HV). Growing it is fully manual: find a hadith,
confirm grade, translate, paste a SQL insert. That is slow, error-prone, and the
bottleneck on every "we don't have a reel for X" gap.

This pipeline **semi-automates the prep** — sourcing, dedup, translation, and a
two-pass machine verification — and ends at a **mandatory human review gate**.
Nothing reaches `hadith_library` without an explicit human approval.

**Reconciliation with `agent-architecture-roadmap.md` Part 6 #6**
("adding new hadiths to the library — never automate"): that rule stands. The
*decision* to admit a hadith stays human. We automate everything *before* the
decision and present the human a complete, verified dossier to approve or reject.
Machines can **block** (reject); only a human can **admit**.

**This is high-stakes (religious text). The four hard guardrails below are
non-negotiable and are repeated wherever they bite.**

---

## 1. Hard guardrails (non-negotiable)

| # | Guardrail | How it's enforced in this design |
|---|-----------|----------------------------------|
| G1 | **Never fabricate.** | Any field a model cannot verify is left **empty + flagged**, never filled with plausible text. Verifier prompts are instructed to *abstain*, not guess. Every row carries source URLs or it cannot be promoted. |
| G2 | **Curated authority ranking — embeddings never decide.** | Source precedence (who wins on grade/wording) is a **static rule table** (§4). Embeddings are used *only* to surface near-duplicates for the human; they never rank, grade, or auto-reject. (Mirrors HV's hard constraint.) |
| G3 | **Tajik native.** | TJ is *generated as native Tajik Cyrillic* (ҷ ӣ ӯ ҳ қ ғ), then reviewed by a Tajik-capable human in the gate. Ends the P050 Russian-fallback for *new* rows. Requires `text_tajik` column (§3, HV-coordinated). |
| G4 | **Uzbek Cyrillic + Latin (two-script).** | Canonical Uzbek stored once; the other script produced by a **deterministic, curated transliterator** (§7). Solves the 62-Latin / 12-Cyrillic split at the generation step — no manual migration. |

Plus the standing HR rules: **only sahih/hasan, never daif**; **human approves
every public-facing artifact**; **API/schema stability for the shared table**.

---

## 2. Pipeline at a glance

```
                         ┌──────────────────────────────────────┐
                         │  SOURCES (Tier-ranked, curated §4)    │
                         │  Dorar.net · Sunnah.com · HadeethEnc  │
                         └──────────────────┬───────────────────┘
                                            │
   Stage 0  ACQUIRE ───────────────────────▼───────────────────────────────
   pull matn + collection/number + grade + grading-source + source URLs
   daif → DROP at the door (G: sahih/hasan only)
                                            │
   Stage 1  DEDUP ──────────────────────────▼──────────────────────────────
   A) hard key (collection, number) vs LIVE library (74) + pending candidates
   B) fuzzy matn similarity → "possible dup" FLAG for human (never auto-drop) [G2]
                                            │
   Stage 2  TRANSLATE ──────────────────────▼──────────────────────────────
   EN/RU/UZ/TJ. Prefer authoritative existing translation; LLM only fills gaps
   and is MARKED machine-translated. TJ native [G3]. UZ canonical + transliterate [G4]
                                            │
   Stage 3  A/B VERIFY ─────────────────────▼──────────────────────────────
   Two independent passes must AGREE on: matn exists at cited ref · grade correct
   · translations faithful (back-translation) · no added content [G1]
   AGREE-PASS → queue | AGREE-FAIL → reject+log | DISAGREE → escalate w/ both views
   (verifier can BLOCK, cannot ADMIT)
                                            │
   Stage 4  HUMAN GATE (mandatory) ─────────▼──────────────────────────────
   Admin queue: Arabic · all langs · grade+source deeplink · dedup status ·
   A/B outputs+disagreements · red flags →  Approve / Edit→approve / Reject / Defer
                                            │ (approve only)
   Stage 5  PROMOTE ────────────────────────▼──────────────────────────────
   INSERT into hadith_library (live, shared) · write audit row · refresh coverage
   idempotent on hard key · adds rows only, never alters schema at runtime
```

Staging is fully isolated: the **live `hadith_library` never sees an unverified
row.** Candidates live in a separate `hadith_candidates` table until promoted.

---

## 3. Data model

### 3.1 Staging table (NEW, HR-owned, safe to iterate)

`hadith_candidates` — holds everything until the human approves. HR owns it; HV
never reads it, so we can change it freely.

```sql
CREATE TABLE hadith_candidates (
  candidate_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  status            TEXT NOT NULL DEFAULT 'sourced',
                    -- sourced | deduped | translated | verified
                    -- | needs_human | approved | rejected | promoted

  -- Identity / provenance (G1: no promotion without provenance)
  collection        TEXT NOT NULL,          -- e.g. 'bukhari'
  hadith_number     TEXT NOT NULL,          -- normalized string
  narrator          TEXT,
  grade             TEXT NOT NULL,          -- sahih | hasan  (daif never reaches here)
  grading_source    TEXT NOT NULL,          -- which Tier-1 authority graded it (§4)
  source_urls       JSONB NOT NULL,         -- {dorar, sunnah, hadeethenc} deep-links

  -- Content
  text_arabic           TEXT NOT NULL,      -- canonical matn (source of truth)
  text_english          TEXT,
  text_russian          TEXT,
  text_uzbek_latin      TEXT,
  text_uzbek_cyrillic   TEXT,
  text_tajik            TEXT,               -- native Tajik Cyrillic [G3]

  -- Per-field translation provenance: 'authoritative' | 'machine' | 'human_edited'
  translation_meta  JSONB DEFAULT '{}',

  -- Dedup
  dedup_hard_hit    BOOLEAN DEFAULT false,  -- exact (collection,number) collision
  dedup_fuzzy_hits  JSONB DEFAULT '[]',     -- [{library_id, score, reason}] advisory [G2]

  -- A/B verification (Stage 3)
  verify_a          JSONB,                  -- {verdict, checks{}, notes}
  verify_b          JSONB,
  verify_agreement  TEXT,                   -- pass | fail | disagree
  red_flags         JSONB DEFAULT '[]',

  -- Human gate audit (Stage 4/5)
  reviewed_by       TEXT,
  reviewed_at       TIMESTAMPTZ,
  review_action     TEXT,                   -- approve | edit_approve | reject | defer
  review_reason     TEXT,
  promoted_library_id TEXT,                 -- FK-ish into hadith_library after promote

  UNIQUE (collection, hadith_number)        -- one candidate per ref at a time
);
```

### 3.2 Live table changes (`hadith_library` — SHARED WITH HV ⚠️)

Current columns: `text_arabic, text_english, text_uzbek, text_russian` (+ id,
collection, number, narrator, grade, tags, theme). **No `text_tajik`.**

Required migration **before the pipeline can promote**:

```sql
ALTER TABLE hadith_library ADD COLUMN IF NOT EXISTS text_tajik          TEXT;  -- [G3] backfill all 74 (D3)
ALTER TABLE hadith_library ADD COLUMN IF NOT EXISTS text_uzbek_cyrillic TEXT;  -- [G4] CANONICAL (D4)
ALTER TABLE hadith_library ADD COLUMN IF NOT EXISTS text_uzbek_latin    TEXT;  -- [G4] derived
-- D4 = Cyrillic canonical. Legacy text_uzbek (mixed: 62 Latin / 12 Cyrillic) is
-- KEPT for HV back-compat; which script HV displays from it is an HV-coordination item.
-- Backfill (one-time, via augment-update §Stage 5):
--   12 Cyrillic rows  → text_uzbek_cyrillic directly (already canonical)
--   62 Latin rows     → transliterate Latin→Cyrillic + gate spot-check → canonical;
--                       originals preserved in text_uzbek_latin
--   all 74            → text_tajik filled (native Tajik Cyrillic, reviewed)
```

> **⚠️ HV-COORDINATION REQUIRED.** `hr-CLAUDE.md`: *"NEVER drop or alter
> hadith_library without coordinating with HV."* These are **additive** columns
> (HV keeps working — its reads of existing columns are untouched), but the
> change must be reviewed with the HV side and applied as one explicit migration,
> not silently. This is a **blocking dependency** (§9, Phase 0).

---

## 4. Curated source authority (the §G2 rule table)

This is a **static, human-maintained precedence table.** No model and no
embedding may override it.

| Source | Tier | Authoritative for | Notes |
|--------|------|-------------------|-------|
| **Dorar.net** | 1 | **Grading** (sahih/hasan/daif) + Arabic matn | Primary grader. If Dorar grades daif → drop at Stage 0. |
| **Sunnah.com** | 1 | **Arabic matn** + **English** (recognized translators) + collection/number | Canonical for citation + EN where a vetted translation exists. |
| **HadeethEnc.com** | 1 | **Multilingual reference translations** (RU/others) | Use as a translation reference / cross-check, not as grader. |

**Conflict rules (deterministic):**
1. **Grade** comes from Dorar. If a source disagrees, Dorar wins; mismatch is a
   `red_flag` for the human, never silently reconciled.
2. **Arabic matn** comes from Sunnah.com if present, else Dorar. Material wording
   differences between the two → `red_flag`.
3. **Citation (collection, number)** must match across at least two Tier-1
   sources or it is flagged.
4. Nothing outside this table is a source. (No forums, no aggregators, no blogs.)

---

## 5. Stage detail

### Stage 0 — Acquire
- Per source, a small **adapter** (Python) returns a normalized record:
  `{collection, number, narrator, grade, grading_source, arabic, source_urls}`.
- **Daif is dropped here** (G: sahih/hasan only). Logged, not queued.
- Provenance (`source_urls` as deep-links, not homepages) is mandatory (G1) and
  reused later for the reply/caption deep-links the project already requires.
- *Access note / Decision D1:* confirm current programmatic access for each
  source (Sunnah.com API key; Dorar query endpoint; HadeethEnc structured pages).
  Where no API exists, adapter does polite, rate-limited, cached fetches.

### Stage 1 — Dedup (vs **live** 74, not a doc)
- **1A Hard key** — normalize `(collection, hadith_number)` and match against the
  *live* `hadith_library` **and** pending candidates. Hit → `dedup_hard_hit=true`,
  candidate parked (human can still decide it's a different-language addition).
- **1B Fuzzy matn** — normalize Arabic (strip diacritics, unify alef/hamza forms,
  drop the isnād chain, compare matn), score similarity. High score → push a
  `dedup_fuzzy_hits` entry. **Advisory only — surfaced to the human, never an
  auto-drop** (G2). Embedding retrieval is allowed *only* to *find* candidates to
  show; it does not decide.

### Stage 2 — Translate (EN / RU / UZ / TJ)
- **Order of preference per field (G1):**
  1. Authoritative existing translation from a Tier-1 source → tag `authoritative`.
  2. Else LLM translation of the **matn only** (no embellishment) → tag `machine`.
- LLM is instructed to **translate faithfully, flag uncertainty, never add a
  "the Prophet ﷺ said X" that isn't in the matn** (same fabrication risk as the
  reel generator, ref `reel-creation-pipeline.md` Step 2).
- **TJ (G3):** generate native Tajik Cyrillic; mark `machine`; the gate routes it
  to a Tajik-capable reviewer.
- **UZ (G4):** generate canonical script, then `transliterate()` (§7) fills the
  other. Both `text_uzbek_latin` and `text_uzbek_cyrillic` populated before the gate.

### Stage 3 — A/B verify (two independent passes)
Two **independent** passes — **pass A = Claude, pass B = a different model (D2)**,
and **B never sees A's output** — each emit a structured verdict over the same checks:

| Check | Question | Cross-checked against |
|-------|----------|-----------------------|
| C1 ref-exists | Does this matn exist at the cited collection/number? | Sunnah.com + Dorar |
| C2 grade | Is sahih/hasan correct? | Dorar (authority) |
| C3 faithful | Do EN/RU/UZ/TJ match the matn? | back-translation diff |
| C4 no-fabrication | Any content not in the source? | matn vs translations |

- **Agreement logic:**
  `A=pass ∧ B=pass` → `verify_agreement='pass'` → queue to human.
  `A=fail ∨ B=fail` (and they agree on failure) → `reject` + log reason.
  Any **disagreement** → `disagree` → escalate to human **with both verdicts shown**.
- The verifier **can BLOCK, cannot ADMIT** (G1 + roadmap principle). A "pass"
  only means *"eligible for human review,"* never *"insert."*
- **Pass-B selection matters (D2 caveat):** B must be competent on Arabic + Islamic
  content. A weak B inflates false `disagree` escalations → review fatigue. The
  first batch (D5) is a **calibration run**: measure the disagreement rate and
  sample for false positives before scaling B's role.

### Stage 4 — Human review gate (mandatory)
Admin queue card per candidate shows, in one view:
- Arabic matn · EN · RU · UZ (both scripts) · TJ — each with its provenance tag.
- Grade + **grading-source deep-link** (Dorar) + the Sunnah.com/HadeethEnc deep-links.
- Dedup: hard-hit banner + fuzzy "possible duplicates" list (links into library).
- A/B verifier verdicts side-by-side; **disagreements highlighted**.
- Red flags list.

Actions: **Approve · Edit-then-approve · Reject (reason required) · Defer.**
Editing writes back to the candidate and re-tags touched fields `human_edited`.
This is the **only** path forward.

### Stage 5 — Promote
On approve, **promote runs in one of two modes** (chosen at the gate):
- **INSERT (new hadith):** add a new `hadith_library` row. Idempotent on the hard
  key (no double-insert), inside a transaction.
- **AUGMENT-UPDATE (existing hadith, missing language/script):** when Stage 1
  hard-key matched an existing row and the human confirms it's the *same* hadith,
  **UPDATE** that row to fill the missing column(s) (e.g. `text_tajik`,
  `text_uzbek_cyrillic`) instead of inserting a duplicate. **The D3 backfill of TJ
  across all 74 rows uses this path** — same code, run as a batch.

Then, regardless of mode:
1. Carry the **canonical Dorar/Sunnah deep-link** onto the promoted row, so the
   downstream reel/caption layer reuses it (project requires deep-links, not
   homepages) and never re-derives the source.
2. Write an **audit row** (`who/when/candidate_id/verifier scores/action/mode`).
3. Set candidate `status='promoted'`, store `promoted_library_id`.
4. Refresh coverage stats (themes / languages / scripts now covered) so the
   downstream Curator (roadmap) and the reel-gap view stay accurate.

---

## 6. Where it runs (fits the stack)

- **Python ETL** (his Supabase-ETL lane) does the heavy batch: Stage 0–3, writing
  rows into `hadith_candidates`. Source adapters, dedup normalization, and the
  transliterator live here, unit-tested with **pytest**.
- **Next.js admin** (`/admin/library-queue`, password-gated) owns Stage 4–5: the
  human gate UI and the `promote` API route into the shared table.
- **API surface (HR Next.js):**
  `GET /api/candidates` (queue) · `POST /api/candidates/:id/review` (approve/reject/
  edit/defer) · `POST /api/candidates/:id/promote` · `POST /api/dedup-check`
  (reused by admin + Curator). Keep these additive; do not touch HV-facing routes.
- **Testing (his wheelhouse — call it a first-class deliverable):**
  - pytest: adapters parse correctly, daif is dropped, dedup hard/fuzzy logic,
    transliterator round-trips, verifier-agreement state machine.
  - Playwright: queue renders, gate actions move status correctly, **reject blocks
    promotion**, edit re-tags provenance, promote is idempotent.
  - CI stays mocked for external APIs (HR CI rule: no real ElevenLabs/Claude on push).

---

## 7. Uzbek two-script (priority-2 feature, solved here)

The 62-Latin / 12-Cyrillic split is fixed **at generation, not by manual
migration** (your stated approach):

- **Cyrillic canonical (D4) + deterministic transliterator.** Cyrillic is the
  human-reviewed source of truth; `transliterate()` produces Latin on write into
  `text_uzbek_latin`. Both columns persisted (O(1) reads; TTS uses Cyrillic
  directly from the reviewed canonical — no conversion before audio).
- **The transliterator is a curated rule map, not an LLM** (deterministic,
  reviewable), and is **bidirectional**: runtime uses **Cyrillic→Latin**; the
  one-time backfill of legacy Latin rows uses **Latin→Cyrillic**. It handles the
  known edge cases (`e`/`ye`, `o‘`/`ў`, `g‘`/`ғ`, `q`/`қ`, `h`/`ҳ`, tutuq belgisi
  `ʼ`, soft/hard signs, Russian-loanword letters `ц/щ/я/ю/ё`). Ambiguous cases are
  **flagged to the human in the gate**, never guessed silently (G1/G4).
- **Backfill:** the 12 Cyrillic rows are already canonical; the 62 Latin rows →
  Latin→Cyrillic + **gate spot-check** to set canonical, originals preserved in
  `text_uzbek_latin`. One-time, via the Stage-5 augment-update path.

---

## 8. Decisions — RESOLVED 2026-06-14

- **D1 — Source access.** ✅ Confirmed available. Stage 0 adapters proceed:
  Sunnah.com (API key on hand), Dorar.net (endpoint), HadeethEnc (fetch + cache).
- **D2 — A/B verifier.** ✅ **Different model for pass B** (true independence).
  Pass A = Claude; pass B = a second, independent model; B never sees A's output.
  Caveat (folded into Stage 3): pass-B model MUST be competent on Arabic/Islamic
  content, or false-disagreements flood the gate (see review-fatigue note, §9).
- **D3 — `text_tajik` scope.** ✅ **Backfill TJ for all 74 in the same migration**
  (HV-coordinated). This uses the Stage-5 **augment-update** path (§5 Stage 5),
  not new-row inserts — the same mechanism as "same hadith, new language."
- **D4 — Uzbek canonical script.** ✅ **CYRILLIC canonical** (Claude's call).
  The highest-stakes output is the religious **audio** (TTS), which uses Cyrillic
  and pronounces it best. Making Cyrillic the human-reviewed canonical puts the
  exact, gate-approved text directly into TTS with **zero transliteration between
  review and audio** — the error-prone step is removed from the highest-stakes
  channel. Latin is **derived** (Cyrillic→Latin transliterator + gate spot-check)
  and serves on-screen reading, where minor residue is tolerable. **Reversible** —
  both columns persist — so Latin's official-script future is not abandoned. Also
  keeps UZ + TJ both Cyrillic-native at the source-of-truth layer (one parallel
  reviewer workflow).
- **D5 — Batch size / cadence.** ✅ **Small human-digestible batches** (~10
  candidates/run). The **first batch is also a calibration run** for the A/B
  disagreement rate before scaling (§9).

---

## 9. Build phasing (after this doc + decisions are approved)

| Phase | Deliverable | Depends on | Gate |
|-------|-------------|-----------|------|
| **0** | **Schema migration** (`hadith_candidates` + additive `hadith_library` cols) **+ backfill TJ (74) & UZ Cyrillic via augment-update** — **coordinated with HV** | D3, D4 | HV sign-off + migration verified in Supabase before any promote path exists |
| 1 | Stage 0 adapters + daif-drop + provenance (pytest) | D1 | candidates land in staging, daif never does |
| 2 | Stage 1 dedup (hard + fuzzy advisory) | live count confirmed | no auto-drop on fuzzy |
| 3 | Stage 2 translate + UZ transliterator (pytest round-trip) | D4 | provenance tags correct; TJ native |
| 4 | Stage 3 A/B verify state machine | D2 | verifier can block, cannot admit |
| 5 | Stage 4 admin gate UI (Playwright) | 1–4 | reject blocks promote; edit re-tags |
| 6 | Stage 5 promote + audit + coverage refresh | 0,5 | idempotent; additive-only; audit row written |

Each phase: atomic commits, docs updated **in the same session** (`fix_patterns.md`
for fixes from P090+; `CLAUDE.md`/`FEATURES.md`/`CHANGELOG.md` for the feature),
verified with git before "done."

**Cadence (D5):** sourcing runs in small batches (~10 candidates/run). The **first
batch is an A/B calibration run** — measure the pass-A/pass-B disagreement rate,
sample false positives, tune pass-B before scaling. Keeps the gate queue digestible
and review fatigue low.

---

## 10. What this design deliberately does NOT do

- It does not auto-admit anything (G1 + roadmap Part 6 #6).
- It does not let embeddings grade, rank, or drop (G2).
- It does not alter `hadith_library` schema at insert time (only the one
  coordinated Phase-0 migration does, additively).
- It does not touch HV-facing API routes or the reel-production pipeline.
- It does not source from anything outside the §4 curated Tier-1 table.

---

## References
- `agent-architecture-roadmap.md` — downstream reel fleet; Part 6 #6 reconciliation
- `reel-creation-pipeline.md` — Step 2 fabrication-risk precedent
- `hr-CLAUDE.md` — shared `hadith_library` schema, P049/P050, shared-DB rule
- `fix_patterns.md` — P050 (TJ fallback), P078 (Whisper UZ/TJ); new patterns from P090
- HV hard constraint — authority ranking exact/curated, embeddings never rank (mirrored as G2)

## Change log
| Date | Change | By |
|------|--------|----|
| 2026-06-14 | Initial design draft for review | Farhod / Claude session |
| 2026-06-14 | Decisions D1–D5 resolved. D4 = **Cyrillic canonical**. Added Stage-5 **INSERT vs AUGMENT-UPDATE** modes (D3 TJ-74 backfill uses augment-update). A/B pass-B = **different model** + calibration run. Deep-link carried forward to promoted rows. | Farhod / Claude session |
