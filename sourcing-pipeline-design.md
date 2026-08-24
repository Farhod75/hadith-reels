# sourcing-pipeline-design.md
# Hadith Reels — Content Sourcing & Library-Population Pipeline (DESIGN)
# ============================================================

> **Author:** Farhod Elbekov + Claude session, 2026-06-14
> **Status:** PARTLY BUILT — see §11 "What actually exists" (updated 2026-08-23).
>   The 2026-06-14 draft said "no code until approved." Code was written the same
>   week and the doc was never updated, so a later session read it as unbuilt.
>   §11 is now the source of truth for build state; the rest is the design intent.
> **Project:** hadith-reels (github.com/Farhod75/hadith-reels)
> **Companion docs:** `agent-fleet-roadmap.md` (downstream reel fleet),
>   `reel-creation-pipeline.md` (reel production), `CLAUDE.md` (library schema,
>   Workflows H and I)
> **Scope:** This pipeline **fills the library** (gets new verified hadiths *in*).
>   It is *upstream* of reel production. It does NOT make reels.

---

## 0. Why this exists / what it is not

The library is a hand-curated set in `hadith_library` (shared Supabase, also read
by HV). **Live count is 69, not the 74 this doc was written against** — four
duplicate rows and one non-hadith (Quran 41:35) were removed 2026-08-11. Of those
69, only 13 have ever been used in a reel. Growing it is fully manual: find a
hadith, confirm grade, translate, paste a SQL insert. That is slow, error-prone,
and the bottleneck on every "we don't have a reel for X" gap. **41 reels have
been produced from 13 hadiths — the library, not the tooling, is the ceiling.**

This pipeline **semi-automates the prep** — sourcing, dedup, translation, and a
two-pass machine verification — and ends at a **mandatory human review gate**.
Nothing reaches `hadith_library` without an explicit human approval.

**Reconciliation with `agent-fleet-roadmap.md` Part 6 #6**
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
| G3 | **Tajik native.** | TJ is *generated as native Tajik Cyrillic* (ҷ ӣ ӯ ҳ қ ғ) **from the Arabic matn**, then reviewed by a Tajik-capable human in the gate. Ends the P050 Russian-fallback for *new* rows. **Enforced in code:** `translate-candidates.py` refuses a candidate with no `text_arabic` rather than fall back to another language column. |
| G4 | **Uzbek Cyrillic + Latin (two-script).** | Canonical Uzbek stored once; the other script produced by a **deterministic, curated transliterator** (§7). Solves the Latin/Cyrillic split at the generation step — no manual migration. |

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
   A) hard key (collection, number) vs LIVE library (69) + pending candidates
   B) fuzzy matn similarity → "possible dup" FLAG for human (never auto-drop) [G2]
                                            │
   Stage 2  TRANSLATE ──────────────────────▼──────────────────────────────
   EN/RU/UZ/TJ from the ARABIC MATN ONLY. Never from another translation.
   TJ native [G3]. UZ Cyrillic canonical, Latin derived [G4]
                                            │
   Stage 3  A/B VERIFY ─────────────────────▼──────────────────────────────
   Two independent passes on FAITHFULNESS TO THE MATN (P120 scope):
   added · omitted · changed · register.  Conventions are NOT checked here.
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

**Deterministic checks run ALONGSIDE, not inside, the model stages** — see §5
Stage 3 and P120. `audit-library.py` covers orthography, script, grade and source
integrity; `lint-content.py` covers divine-name substitution. Neither is a model.

---

## 3. Data model

### 3.1 Staging table (NEW, HR-owned, safe to iterate)

`hadith_candidates` — holds everything until the human approves. HR owns it; HV
never reads it, so we can change it freely.

**BUILT AND LIVE** since 2026-06-14 (`20260614_hadith_candidates_staging.sql`,
committed `dbc74ba`). The shipped table adds `updated_at` and `promote_mode` and
carries CHECK constraints not in this draft — read the live schema, not this block:

```sql
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint WHERE conrelid = 'hadith_candidates'::regclass;
```

Constraints as shipped: `ck_status` (sourced | deduped | translated | verified |
needs_human | approved | rejected | promoted) · `ck_grade` (sahih | hasan only —
daif cannot be represented) · `ck_agreement` (pass | fail | disagree) ·
`ck_review` (approve | edit_approve | reject | defer) · `ck_promote_mode`
(insert | augment_update) · `uq_candidate_ref` UNIQUE (collection, hadith_number).

### 3.2 Live table changes (`hadith_library` — SHARED WITH HV ⚠️)

**APPLIED.** `text_tajik`, `text_uzbek_cyrillic` and `text_uzbek_latin` are all
live and verified in `information_schema`. `text_tajik` is filled for all 69 rows.

The migration file `20260614_add_uzbek_script_columns.sql` sat UNTRACKED on one
machine for two months — applied to production but absent from git, so it would
not have survived a clone. Committed 2026-08-16 (`2464a6c`). Its header still said
"DRAFT — DO NOT RUN until HV nod"; corrected to APPLIED at the same time.

> **⚠️ HV-COORDINATION REQUIRED** for any future change. `CLAUDE.md`: *"NEVER drop
> or alter hadith_library without coordinating with HV."* The columns above are
> **additive** (HV's reads of existing columns are untouched). Legacy `text_uzbek`
> is intentionally LEFT UNCHANGED for HV back-compat.

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

### Stage 0 — Acquire — **BUILT, BLOCKED ON A KEY**
- Per source, a small **adapter** (Python) returns a normalized record:
  `{collection, number, narrator, grade, grading_source, arabic, source_urls}`.
- Shipped: `scripts/source-candidates.py` runner + `scripts/lib/source_sunnah.py`,
  `source_dorar.py`, with pytest coverage. `--source mock|live`, `--refs bukhari:527`.
- **Daif is dropped here** (G: sahih/hasan only). Logged, not queued. The Dorar
  authority verdict is implemented and tested: a Dorar `daif` OVERRIDES a Sunnah
  `sahih` and drops the candidate; a Dorar no-match leaves `grade_confirmed=false`
  so the row cannot auto-promote.
- **BLOCKER:** `--source live` requires `SUNNAH_API_KEY`, which is not in
  `.env.local` and is not recoverable — D1 recorded having one on 2026-06-14 but it
  was never persisted. Keys are issued by filing a GitHub issue against
  `sunnah-com/api`; **request filed 2026-08-21 as issue #3675, still open.**
  Turnaround is volunteer-paced.
- **Mock mode cannot currently produce a valid candidate** — its fixtures carry no
  Arabic, so G1's `text_arabic NOT NULL` correctly drops them at the door. The
  guardrail works; the fixture is thin. Stage 2 was developed against a candidate
  seeded directly from a library row instead.

### Stage 1 — Dedup (vs **live** 69, not a doc) — **BUILT**
- **1A Hard key** — normalize `(collection, hadith_number)` and match against the
  *live* `hadith_library` **and** pending candidates. Hit → `dedup_hard_hit=true`,
  candidate parked (human can still decide it's a different-language addition).
- **1B Fuzzy matn** — normalize Arabic (strip diacritics, unify alef/hamza forms,
  drop the isnād chain, compare matn), score similarity. High score → push a
  `dedup_fuzzy_hits` entry. **Advisory only — surfaced to the human, never an
  auto-drop** (G2). Embedding retrieval is allowed *only* to *find* candidates to
  show; it does not decide.
- Shipped: `scripts/lib/dedup.py` + `upload-candidates.py`, pytest-covered
  (`new` / `duplicate` / `review_fuzzy` states all asserted).

### Stage 2 — Translate (EN / RU / UZ / TJ) — **BUILT 2026-08-23**
`scripts/translate-candidates.py` (+ `scripts/derive-uzbek-latin.ts`). Workflow I.

- **Source is the ARABIC MATN, always.** The draft's "prefer authoritative existing
  translation, LLM only fills gaps" was not implemented, and deliberately so:
  P075 built the current `text_tajik` by translating `text_uzbek` → `text_tajik`,
  a translation of a translation whose errors compound. «Неки» for «Некӣ» (R037)
  is what that produces. Translating #527 from the Arabic returned «Некӣ» with
  U+04E3 correctly. The script REFUSES a candidate with no `text_arabic` rather
  than fall back (G3). Reinstating authoritative-translation preference is a future
  option, but it must never become a fallback chain.
- **Fabrication rules live in the system prompt**, not just register guidance: add
  no clause, supply no attribution the matn lacks, add no comparison, add no
  ranking or elevation, emit `[UNCERTAIN: note]` rather than guess. A translator
  asked only for a "reverent" register smooths a terse matn into something fuller —
  the same length-pressure failure as P116.
- **Per-field provenance** to `translation_meta`: `machine` | `authoritative` |
  `human_edited`, plus model, source field and timestamp. This is what routes a
  field to review at Stage 4.
- **UZ (G4):** the model writes CYRILLIC only (canonical, D4). `text_uzbek_latin`
  is DERIVED by `derive-uzbek-latin.ts` calling `deriveBothScripts` in
  `scripts/lib/uzbek-translit.ts` — tested for okina (U+02BB after o/g) vs tutuq
  (U+02BC elsewhere) and apostrophe folding, 11/11 passing. **Do not port that
  transliterator to Python.** A second implementation drifts, and okina rules are
  precisely where drift corrupts silently.
- Dry-run by default; `--commit` writes and sets `status='translated'`.
- Model: `claude-sonnet-5`.

### Stage 3 — A/B verify (two independent passes) — **DESIGNED, NOT BUILT**

Two **independent** passes — **pass A = `claude-sonnet-5`, pass B = `gpt-5.6-terra`**
(D2 satisfied: different company, different training, uncorrelated failure modes),
and **B never sees A's output**.

**Scope is measured, not assumed (P120).** Both passes judge FAITHFULNESS TO THE
MATN only:

| Check | Question |
|-------|----------|
| added | Any clause, action, ranking, comparison, attribution or source not in the Arabic? |
| omitted | Anything in the Arabic missing from the translation? |
| changed | A word rendered as something the Arabic does not say? |
| register | Paraphrase where translation is required? |

They do **NOT** check project conventions. Probing `gpt-5.6-terra` on Bukhari #527
with planted defects (two identical runs, `scripts/probe-passb.py`) showed it
catches added content in EN and TJ and a dual→singular meaning change in RU —
citing بِرُّ الْوَالِدَيْنِ as dual — but **passes «Аллоҳ»→«Худо» at high
confidence**, because that translation is faithful to اللَّه and is wrong only on
a rule the model was never given. Putting the rules in the prompt would turn a
judgement engine into a rules engine and degrade both.

**Convention defects have deterministic owners and must be clean BEFORE Stage 3:**

| Defect class | Owner |
|---|---|
| added / omitted / changed / register | pass A + pass B (models) |
| divine-name substitution | `lint-content.py` |
| diacritics, homoglyphs, okina, script mixing | `audit-library.py` |
| grade, source URL, empty language fields | `audit-library.py` |

The original C1 (ref-exists) and C2 (grade) checks are NOT model work — they are
lookups against Sunnah.com and Dorar, already implemented in Stage 0's adapters
and its Dorar authority verdict. Do not re-ask a model what an API already answered.

**Verdict handling:**
- both pass → `status='verified'`
- both fail → `status='needs_human'`, both verdicts stored
- **disagree → `status='needs_human'`.** Disagreement is the signal Stage 3 exists
  to produce; it is never resolved by a third pass or by preferring one model.
- The verifier **can BLOCK, cannot ADMIT** (G1 + roadmap principle). A "pass" only
  means *"eligible for human review,"* never *"insert."*
- `verify_a` / `verify_b` hold the raw structured verdicts; `verify_agreement` is
  `pass` | `fail` | `disagree` per `ck_agreement`.

**Calibration (D5):** the first batch of ~10 is a calibration run for the
disagreement rate before any scaling. Near-zero means the passes are correlated and
the second is buying nothing; very high means the checks are mistuned and Stage 4
will drown. **Re-run `probe-passb.py` whenever either model version changes** —
competence is not inherited across versions.

### Stage 4 — Human review gate (mandatory) — **SQL ONLY, BY CHOICE**
Admin queue card per candidate shows, in one view:
- Arabic matn · EN · RU · UZ (both scripts) · TJ — each with its provenance tag.
- Grade + **grading-source deep-link** (Dorar) + the Sunnah.com/HadeethEnc deep-links.
- Dedup: hard-hit banner + fuzzy "possible duplicates" list (links into library).
- A/B verifier verdicts side-by-side; **disagreements highlighted**.
- Red flags list.

Actions: **Approve · Edit-then-approve · Reject (reason required) · Defer.**
Editing writes back to the candidate and re-tags touched fields `human_edited`.
This is the **only** path forward.

**Current reality:** the UI is not built. Review is done with SQL against
`hadith_candidates`, deliberately — "promote today, UI later." The gate is real
either way; it is the human, not the interface.

### Stage 5 — Promote — **BUILT (P094)**
`scripts/promote-candidates.py`. Dry-run default, audit rows written, idempotency
proven in testing.

On approve, **promote runs in one of two modes** (chosen at the gate):
- **INSERT (new hadith):** add a new `hadith_library` row. Idempotent on the hard
  key (no double-insert), inside a transaction.
- **AUGMENT-UPDATE (existing hadith, missing language/script):** when Stage 1
  hard-key matched an existing row and the human confirms it's the *same* hadith,
  **UPDATE** that row to fill the missing column(s) instead of inserting a duplicate.

Then, regardless of mode:
1. Carry the **canonical Dorar/Sunnah deep-link** onto the promoted row (precedence
   dorar > sunnah > first) so the downstream reel/caption layer reuses it and never
   re-derives the source.
2. Write an **audit row** (`who/when/candidate_id/verifier scores/action/mode`).
3. Set candidate `status='promoted'`, store `promoted_library_id`.
4. Refresh coverage stats so the downstream Curator and the reel-gap view stay accurate.

> **Note on D3.** The draft said the TJ backfill across all rows would run through
> this augment-update path. It did not — `text_tajik` was filled by P075's
> Uzbek→Tajik translation, outside this pipeline, which is the origin of the
> defects G3 now exists to prevent. The backfill is DONE but not by the intended
> route, and the existing Tajik column carries that provenance.

---

## 6. Where it runs (fits the stack)

- **Python ETL** does the heavy batch: Stage 0–3, writing rows into
  `hadith_candidates`. Source adapters, dedup normalization and the translator live
  here, unit-tested with **pytest** (49 offline tests in `scripts/lib`, no network).
- **TypeScript** owns the Uzbek transliterator (`scripts/lib/uzbek-translit.ts`,
  11 tests) and its Stage-2 caller. Deliberately not ported — see Stage 2.
- **Next.js admin** (`/admin/library-queue`, password-gated) will own Stage 4–5.
- **API surface (HR Next.js):**
  `GET /api/candidates` · `POST /api/candidates/:id/review` ·
  `POST /api/candidates/:id/promote` · `POST /api/dedup-check`.
  Keep these additive; do not touch HV-facing routes.
- **Testing (a first-class deliverable):**
  - pytest: adapters parse correctly, daif is dropped, dedup hard/fuzzy logic,
    transliterator round-trips, verifier-agreement state machine.
  - Playwright: queue renders, gate actions move status correctly, **reject blocks
    promotion**, edit re-tags provenance, promote is idempotent.
  - CI stays mocked for external APIs (HR CI rule: no real ElevenLabs/Claude on push).
  - **The pre-push hook now classifies and tests Python (P119).** Before that fix a
    `.py` change ran only `npx tsc --noEmit` and pushed green — every script in this
    pipeline was unprotected.

---

## 7. Uzbek two-script (solved)

- **Cyrillic canonical (D4) + deterministic transliterator.** Cyrillic is the
  human-reviewed source of truth; `deriveBothScripts()` produces Latin on write into
  `text_uzbek_latin`. Both columns persisted (O(1) reads; TTS uses Cyrillic directly
  from the reviewed canonical — no conversion before audio).
- **The transliterator is a curated rule map, not an LLM** (deterministic,
  reviewable), and is **bidirectional**: runtime uses **Cyrillic→Latin**; legacy
  backfill uses **Latin→Cyrillic**. It handles the known edge cases (`e`/`ye`,
  `oʻ`/`ў`, `gʻ`/`ғ`, `q`/`қ`, `h`/`ҳ`, tutuq belgisi, soft/hard signs, Russian-
  loanword letters `ц/щ/я/ю/ё`). Ambiguous cases are **flagged to the human**,
  never guessed silently (G1/G4).
- **Verified on Bukhari #527:** `oʻz`, `oʻqish`, `soʻngra` all carry U+02BB, and
  `audit-library.py` independently agrees. The okina defect that reached five
  captions did not recur.

---

## 8. Decisions

- **D1 — Source access.** ⚠️ **REOPENED.** Recorded ✅ on 2026-06-14 ("Sunnah.com
  API key on hand"), but the key was never written to `.env.local` and is gone.
  Stage 0 live is blocked. Request filed 2026-08-21, `sunnah-com/api` issue #3675.
  Dorar and HadeethEnc need no key. An offline dump was offered as an alternative
  in the request and would suit the batch cadence.
- **D2 — A/B verifier.** ✅ **RESOLVED 2026-08-23.** Pass A = `claude-sonnet-5`,
  pass B = `gpt-5.6-terra`. Different company, so genuinely uncorrelated failure
  modes. Competence measured, not assumed — see Stage 3 and P120.
- **D3 — `text_tajik` scope.** ✅ Done, but NOT via the intended augment-update
  path — see the note under Stage 5.
- **D4 — Uzbek canonical script.** ✅ **CYRILLIC canonical.** The highest-stakes
  output is the religious **audio** (TTS), which uses Cyrillic and pronounces it
  best. Making Cyrillic the human-reviewed canonical puts the exact, gate-approved
  text directly into TTS with **zero transliteration between review and audio** —
  the error-prone step is removed from the highest-stakes channel. Latin is
  **derived** and serves on-screen reading, where minor residue is tolerable.
  **Reversible** — both columns persist. Also keeps UZ + TJ both Cyrillic-native at
  the source-of-truth layer (one parallel reviewer workflow).
- **D5 — Batch size / cadence.** ✅ **Small human-digestible batches** (~10
  candidates/run). The **first batch is also a calibration run** for the A/B
  disagreement rate before scaling (§9).

---

## 9. Build phasing

| Phase | Deliverable | State |
|-------|-------------|-------|
| **0** | Schema migration (`hadith_candidates` + additive `hadith_library` cols) | ✅ applied + committed (`dbc74ba`, `101a020`, `2464a6c`) |
| 1 | Stage 0 adapters + daif-drop + provenance (pytest) | ✅ built · ⚠️ live run blocked on issue #3675 |
| 2 | Stage 1 dedup (hard + fuzzy advisory) | ✅ built, pytest-covered |
| 3 | Stage 2 translate + UZ transliterator | ✅ built 2026-08-23, verified on #527 |
| 4 | Stage 3 A/B verify state machine | ⬜ **NEXT** — D2 resolved, scope set by P120 |
| 5 | Stage 4 admin gate UI (Playwright) | ⬜ SQL gate in use meanwhile, by choice |
| 6 | Stage 5 promote + audit + coverage refresh | ✅ built (P094) |

Each phase: atomic commits, docs updated **in the same session** (`fix_patterns.md`
for fixes; `CLAUDE.md`/`FEATURES.md`/`CHANGELOG.md` for the feature), verified with
git before "done." **Verify with `git show HEAD:<path>`, not `git status`** — an
empty status also means the change was never written (P119).

**Cadence (D5):** sourcing runs in small batches (~10 candidates/run). The **first
batch is an A/B calibration run** — measure the disagreement rate, sample false
positives, tune before scaling. Keeps the gate queue digestible and review fatigue low.

---

## 10. What this design deliberately does NOT do

- It does not auto-admit anything (G1 + roadmap Part 6 #6).
- It does not let embeddings grade, rank, or drop (G2).
- It does not alter `hadith_library` schema at insert time (only the one
  coordinated Phase-0 migration does, additively).
- It does not touch HV-facing API routes or the reel-production pipeline.
- It does not source from anything outside the §4 curated Tier-1 table.
- It does not ask a model to check what a deterministic script already checks (P120).
- It does not translate from a translation (G3).

---

## 11. What actually exists (2026-08-23)

Read this before trusting anything above. Verify with `git show`, not memory.

| Component | File | State |
|---|---|---|
| Staging schema | `supabase/migrations/20260614_hadith_candidates_staging.sql` | live |
| Library columns | `supabase/migrations/20260614_add_uzbek_script_columns.sql` | live |
| Phase 0 schema | `supabase/migrations/20260614_sourcing_phase0_schema.sql` | live |
| Stage 0 acquire | `scripts/source-candidates.py`, `scripts/lib/source_{sunnah,dorar}.py` | built, blocked on key |
| Stage 1 dedup | `scripts/lib/dedup.py`, `scripts/upload-candidates.py` | built |
| Stage 2 translate | `scripts/translate-candidates.py`, `scripts/derive-uzbek-latin.ts` | built |
| Stage 3 verify | — | **not built** |
| Stage 4 gate | SQL | by choice |
| Stage 5 promote | `scripts/promote-candidates.py` | built (P094) |
| Library audit | `scripts/audit-library.py` | built, 69 rows clean |
| Pass-B probe | `scripts/probe-passb.py` | throwaway evidence for P120 |

**Live counts:** `hadith_library` = 69 · `hadith_candidates` = 1 (Bukhari #527,
`status='translated'`, seeded from a library row to develop Stage 2 against —
NOT a real sourcing result) · `hadith_promotions` = 0. **Nothing has ever flowed
through this pipeline end to end.**

---

## References
- `agent-fleet-roadmap.md` — downstream reel fleet; Part 6 #6 reconciliation
- `reel-creation-pipeline.md` — Step 2 fabrication-risk precedent
- `CLAUDE.md` — shared `hadith_library` schema, Workflows H and I, shared-DB rule
- `fix_patterns.md` — P050 (TJ fallback), P075 (UZ→TJ chain), P078 (Whisper UZ/TJ),
  P094 (promote), P119 (Python CI gate), P120 (verifier competence per defect class)
- HV hard constraint — authority ranking exact/curated, embeddings never rank (G2)

## Change log
| Date | Change | By |
|------|--------|----|
| 2026-06-14 | Initial design draft for review | Farhod / Claude session |
| 2026-06-14 | Decisions D1–D5 resolved. D4 = **Cyrillic canonical**. Added Stage-5 **INSERT vs AUGMENT-UPDATE** modes. A/B pass-B = **different model** + calibration run. Deep-link carried forward to promoted rows. | Farhod / Claude session |
| 2026-08-23 | Doc reconciled with reality after two months of undocumented building. Added §11 build state. Library count corrected 74 → 69. **D1 REOPENED** — Sunnah key lost, issue #3675 filed. **D2 resolved** — pass B = `gpt-5.6-terra`, competence measured (P120). Stage 2 built and marked matn-only, overriding the draft's authoritative-first order (P075 chain is why). Stage 3 scope narrowed to faithfulness; conventions moved to `lint-content.py` / `audit-library.py`. D3 noted as done but via the wrong path. | Farhod / Claude session |
