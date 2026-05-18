# agent-architecture-roadmap.md
# Hadith Reels — Agent Fleet Architecture & Migration Roadmap

> **Author:** Farhod Elbekov + Claude session, 2026-05-16
> **Status:** Draft — review and revise post-Hajj
> **Project:** hadith-reels (github.com/Farhod75/hadith-reels)
> **Companion docs:** `reel-creation-pipeline.md`, `reel-tracker.md`, `fix_patterns.md`

## Executive summary

This document describes the migration from the current **manual semi-automated pipeline** (Steps 1-8 in `reel-creation-pipeline.md`) to a **multi-agent fleet** that produces, audits, and publishes Hadith Reels with human-in-the-loop approval.

**Core principles (non-negotiable):**

1. **Religious correctness > automation speed.** Better to ship slowly than ship wrong.
2. **Human approves every public post.** No fully autonomous publishing for content about the Prophet ﷺ or the Quran.
3. **Tracker is a database, not a markdown file.** Agents must check against authoritative state, not best-effort docs.
4. **Audit before publish, always.** Every reel passes through an Auditor agent before it can be queued for human approval.
5. **Fail loud, fail safe.** Errors surface as Telegram alerts, not silent log entries.

---

## Part 1 — Current state assessment

### What works today (manual pipeline)

✅ Admin UI Steps 1-3 (Pick → Generate → Audio + Caption)
✅ Manual MP3 download and rename
✅ FFmpeg concat for narration merge
✅ Whisper STT for EN/RU/AR subtitles
✅ FFmpeg random-pick + concat for background variety
✅ Final FFmpeg merge with subtitles + drawtext + nasheed mix
✅ Manual Telegram upload + caption paste
✅ Markdown tracker for content log (`reel-tracker.md`)

### What's painful today

⚠️ Story text not editable in admin (P079) — forces full regenerate on errors
⚠️ Whisper Latin transliteration for UZ/TJ (P078) — ships without subtitles
⚠️ Tracker is markdown — not enforceable, not queryable by code
⚠️ Background clip random-pick doesn't log which clips were picked
⚠️ Hashtag blocks are pasted manually per language — error-prone
⚠️ No audit step between generation and post — relies on operator vigilance
⚠️ Generation errors (e.g. "Послание к Аллаха") catch ONLY if operator is native speaker
⚠️ No deduplication enforcement — only operator memory + tracker scan
⚠️ Asset reuse audit is manual and aspirational

### Risk profile of full automation today

❌ **Religious accuracy risk** — LLM hallucinations slip through (proven tonight: P079)
❌ **Duplicate posting risk** — no DB-level uniqueness constraint
❌ **Audio-text mismatch risk** — no validation that TTS said what the text says
❌ **Caption-content mismatch risk** — caption generated separately from story, could drift
❌ **Asset overuse risk** — no fingerprinting, repetitive content sneaks in

**Conclusion:** Building agents on top of the current foundation amplifies these risks. Prerequisites (Part 3) must come first.

---

## Part 2 — Target agent fleet

### Agent roles

| Agent | Role | Authority | Stateless? |
|---|---|---|---|
| **Curator** | Picks hadiths from library based on theme coverage, language gaps, calendar (Ramadan, Hajj season) | Suggests only | Stateless |
| **Generator** | Calls Claude API for story + moral + seerah_context | Produces | Stateless |
| **Narrator** | Calls ElevenLabs for TTS (story.mp3 + moral.mp3) | Produces | Stateless |
| **Renderer** | Runs FFmpeg pipeline (concat → Whisper → bg mix → final merge) | Produces | Stateless |
| **Auditor** | Reviews everything against 10-check spec (Part 4) | **GATES** post — can block | Stateless |
| **Approver** | Sends Telegram message to admin with reel preview + buttons | Awaits human input | Stateful (waits) |
| **Publisher** | After human approval: posts to @SahihHadithReels + writes to tracker DB | Acts | Stateless |
| **Notifier** | Sends success/failure alerts to admin Telegram | Reports | Stateless |
| **Auditor-Auditor (optional)** | Spot-checks Auditor's recent decisions for drift | Suggests retraining | Stateless |

### Agent fleet flow

```
                    ┌─────────────┐
                    │  Scheduler  │  (cron or manual trigger)
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Curator   │ ─► picks hadith + lang + style
                    └──────┬──────┘
                           │
                           ▼
                   /api/check-duplicate
                           │
                  ┌────────┴────────┐
                  │                 │
              Allowed           Duplicate
                  │                 │
                  ▼                 ▼
            ┌──────────┐     Re-curate or
            │ Generator│     escalate to operator
            └────┬─────┘
                 │
                 ▼
            ┌──────────┐
            │ Narrator │
            └────┬─────┘
                 │
                 ▼
            ┌──────────┐
            │ Renderer │
            └────┬─────┘
                 │
                 ▼
            ┌──────────┐
            │ Auditor  │ ─► runs 10-check spec
            └────┬─────┘
                 │
        ┌────────┴────────┐
        │                 │
    All pass        Any fail/flag
        │                 │
        ▼                 ▼
   ┌──────────┐    Send to admin
   │ Approver │    with failure
   └────┬─────┘    summary + options
        │
        ▼
   Telegram alert to ADMIN_CHAT_ID:
   ┌─────────────────────────────┐
   │ Reel R-027 ready for review │
   │ Hadith: Bukhari #6018       │
   │ Lang: AR Adults             │
   │ Audit: religious 92%        │
   │        grammar 88%          │
   │        duration 47s ✓       │
   │        size 28MB ✓          │
   │        dedup ✓              │
   │                             │
   │ [▶ Watch] [✅ Approve]      │
   │ [❌ Reject] [📝 Edit]       │
   └─────────────────────────────┘
        │
   ┌────┴────┐
Approved  Rejected
   │         │
   ▼         ▼
┌───────────┐  Log reason
│ Publisher │  Archive
└─────┬─────┘
      │
      ├─► Telegram post to @SahihHadithReels
      ├─► INSERT INTO reels_posted (...)
      └─► Notify operator: "R-027 live"
```

### Communication between agents

- **Synchronous within a job** — Curator → Generator → Narrator → Renderer → Auditor is one job ID
- **Asynchronous at human checkpoint** — Approver sends Telegram message, waits up to 24h, then auto-archives
- **All state in Supabase** — agents don't share in-process memory; they read/write to `reel_jobs` table

---

## Part 3 — Prerequisite chain (must build BEFORE agents)

These are the foundations. Building agents without them is fragile.

### P3.1 — Database tracker (replaces `reel-tracker.md`)

Schema:
```sql
CREATE TABLE reels_posted (
  reel_id            TEXT PRIMARY KEY,          -- R001, R002, ...
  posted_at          TIMESTAMPTZ NOT NULL,
  hadith_collection  TEXT NOT NULL,
  hadith_number      TEXT NOT NULL,
  narrator           TEXT,
  grade              TEXT,
  theme              TEXT,
  tags               TEXT[],
  language           TEXT NOT NULL,             -- en|uz|ar|ru|tj
  style              TEXT NOT NULL,             -- adults|kids
  story_keyword      TEXT,
  audio_files        JSONB,                     -- {story, moral, full}
  bg_clips_used      TEXT[],                    -- array of filenames
  bg_video_output    TEXT,
  nasheed            TEXT,
  subtitles          BOOLEAN,
  subtitle_file      TEXT,
  output_mp4         TEXT,
  duration_seconds   NUMERIC,
  file_size_bytes    BIGINT,
  telegram_msg_id    TEXT,
  telegram_url       TEXT,
  caption            TEXT,
  notes              TEXT,
  audit_scores       JSONB,                     -- religious, grammar, etc.
  approved_by        TEXT,                      -- admin telegram user
  created_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_no_duplicates
  ON reels_posted (hadith_collection, hadith_number, language, style);
```

API endpoints:
- `POST /api/check-duplicate` → 200 if available, 409 if duplicate
- `POST /api/log-reel` → write a new entry (called by Publisher)
- `GET /api/coverage-gaps` → returns themes/langs that are underserved
- `GET /api/asset-usage?asset=mubarak-bg.mp3` → returns last N uses

Migration: one-time script to read `reel-tracker.md` and INSERT all 5 existing rows.

### P3.2 — Editable story/moral text in admin (P079 fix)

Per `fix_patterns.md` P079:
- Replace read-only `<p>` with `<textarea>` for story, moral, seerah_context
- Add "Verified by [user]" checkbox before "Generate Story narration" enables
- This is the human escape hatch for LLM generation errors

### P3.3 — TTS-text validator (audio-vs-text fidelity)

After Narrator generates story.mp3 + moral.mp3:
1. Run Whisper on the generated audio
2. Diff transcription against source text (Levenshtein or semantic)
3. If similarity < 95%: flag for review
4. Catches: TTS hallucination, voice clone bugs, language mismatch

Implementation: ~50 lines of Python or a `/api/validate-tts` route.

### P3.4 — Whisper UZ/TJ Cyrillic pipeline (P078 Option C)

Per `fix_patterns.md` P078 — three options, pick C:
- Skip STT entirely
- Use the story/moral text from Claude as subtitle source (already in Cyrillic)
- Time-align via forced alignment (aeneas or Montreal Forced Aligner)
- This unblocks UZ/TJ reels for subtitle inclusion

### P3.5 — Telegram admin bot (Approver agent)

- Bot has admin chat ID hard-coded
- Sends rich message with reel preview, audit scores, inline buttons
- Inline buttons: Approve / Reject / Edit Caption / Watch
- Listens for button taps, updates `reel_jobs` row
- Timeout: 24h auto-archive if no response

Stack: Python `python-telegram-bot` or Node `node-telegram-bot-api`. Webhook deployment on existing Railway worker.

### P3.6 — Caption auto-generator (templated per language)

Currently captions are Claude-generated and inconsistent. Build a templated generator:

```python
TEMPLATE = {
    'en': "{title}\n\n{moral}\n\n📕 {collection} #{number}\n👤 {narrator}\n📖 Source: {seerah_source}\n\n🔍 Verify: hadithverifier.com\n\n{hashtags}",
    'ru': "{title}\n\n{moral}\n\n📕 {collection} #{number}\n👤 {narrator}\n📖 Источник: {seerah_source}\n\n🔍 Verify: hadithverifier.com\n\n{hashtags}",
    # ... uz, ar, tj
}

HASHTAGS = {
    'ru': "#ХадисДня #СахихАльБухари #ИсламскиеНапоминания #HadithReels #SahihHadithReels",
    # ... per lang
}
```

Caption Auditor checks that title/moral in caption ≡ title/moral in reel content.

### P3.7 — Asset fingerprinting + reuse audit API

```python
# At each random-pick step, log the exact clips used
def pick_and_log_backgrounds(library_dir, count=3):
    all_clips = list(Path(library_dir).glob('*.mp4'))
    picked = random.sample(all_clips, count)
    return [c.name for c in picked]  # returned to caller for logging

# In reels_posted.bg_clips_used array column
```

API: `GET /api/asset-fatigue` returns clips used in last N reels per language.

Auditor rule: if proposed reel reuses 2+ clips from immediately previous reel (same language), flag.

### Prerequisite dependency graph

```
P3.1 (DB) ───┬──► P3.5 (Telegram bot)
             ├──► P3.7 (Asset audit API)
             └──► All agents

P3.2 (Editable text) ───► Generator + Auditor

P3.3 (TTS validator) ───► Auditor

P3.4 (Whisper UZ/TJ) ───► Renderer (unblocks UZ/TJ subs)

P3.6 (Caption gen) ─────► Generator + Auditor
```

P3.1 is the keystone. Everything else can ship in parallel once DB exists.

---

## Part 4 — Auditor specification (the 10-check spec)

The Auditor is the most important — and most complex — agent. Specification:

### Check 1: Authenticity grade
- **Rule:** Hadith must be `sahih` or `hasan`. Never `daif` or fabricated.
- **Source:** Library DB column `grade`
- **Pass criteria:** Boolean
- **Failure mode:** Reject job immediately, alert operator
- **False negative risk:** Low (data exists in library)

### Check 2: Duplicate prevention
- **Rule:** No prior reel exists for (hadith_collection, hadith_number, language, style)
- **Source:** `SELECT 1 FROM reels_posted WHERE (...)`
- **Pass criteria:** Boolean (0 rows = pass)
- **Failure mode:** Reject, ask Curator to re-pick
- **False negative risk:** Low if DB constraint is enforced

### Check 3: Religious accuracy of generated text
- **Rule:** Story must not contradict the hadith's source, must not put words in Prophet's ﷺ mouth that aren't in the hadith
- **Source:** Claude self-review with strict prompt: *"Compare this generated story against the original hadith text. Flag any quote attributed to the Prophet ﷺ that does not appear verbatim in the source hadith. Flag any factual claim about the Prophet's life that contradicts established seerah."*
- **Pass criteria:** Confidence score ≥ 85%
- **Failure mode:** Flag to human, do not auto-reject
- **False negative risk:** **HIGH** — LLM judging LLM has same blind spots. This is why human approval remains.

### Check 4: Grammatical correctness
- **Rule:** Story and moral text are grammatical in target language
- **Source:** Native-language LLM grader, plus rule-based checks for common errors:
  - RU: "Посланник Аллаха" (not "Послание к Аллаха") ← this exact check from P079
  - AR: diacritic correctness, no mixed scripts
  - UZ/TJ: Cyrillic script consistency, no Latin character leakage
- **Pass criteria:** Confidence score ≥ 90%
- **Failure mode:** Flag with specific error highlight to human

### Check 5: TTS audio-vs-text fidelity (P3.3)
- **Rule:** Whisper transcription of TTS audio ≡ source text (similarity ≥ 95%)
- **Source:** Run Whisper on story.mp3, diff against generated story text
- **Pass criteria:** Levenshtein similarity ≥ 95%
- **Failure mode:** Flag — TTS may have hallucinated or mispronounced
- **Notes:** Per P078, UZ/TJ Whisper output won't match Cyrillic source — use Latin→Cyrillic mapper first, OR exempt UZ/TJ from this check until P3.4 ships

### Check 6: Reel duration in range
- **Rule:** 30s ≤ duration ≤ 90s
- **Source:** `ffprobe`
- **Pass criteria:** Boolean
- **Failure mode:** Reject, ask Renderer to retry (could indicate broken concat)

### Check 7: File size within platform limits
- **Rule:** File size ≤ 50 MB for Telegram native upload
- **Source:** File system
- **Pass criteria:** Boolean
- **Failure mode:** Reject, ask Renderer to lower bitrate

### Check 8: Subtitle rendering (if subtitles enabled)
- **Rule:** First subtitle frame renders correctly (no mojibake, correct script)
- **Source:** Extract one frame at the timestamp of first subtitle entry, run OCR (Tesseract), compare to expected text
- **Pass criteria:** OCR result has ≥ 70% character overlap with expected
- **Failure mode:** Flag — likely UTF-8 / libass encoding issue
- **Skipped for:** UZ/TJ until P3.4 ships

### Check 9: Caption-reel consistency
- **Rule:** Caption title matches reel content title; caption hadith # matches reel hadith #
- **Source:** Structured comparison (caption is template-generated, so this is exact match)
- **Pass criteria:** Boolean
- **Failure mode:** Reject, regenerate caption

### Check 10: Asset reuse fatigue
- **Rule:** Background nasheed not used in last 2 reels of same language; bg_clips not 100% overlap with previous reel in same language
- **Source:** `GET /api/asset-fatigue?lang=ru&style=adults`
- **Pass criteria:** Boolean
- **Failure mode:** Flag (not reject) — operator can override

### Audit output format

```json
{
  "reel_id": "R027",
  "audit_timestamp": "2026-06-15T14:23:11Z",
  "overall_status": "FLAG_FOR_HUMAN_REVIEW",
  "checks": {
    "grade": { "status": "PASS" },
    "duplicate": { "status": "PASS" },
    "religious_accuracy": { "status": "FLAG", "score": 0.87, "notes": "Quote in line 3 not verbatim in source" },
    "grammar": { "status": "PASS", "score": 0.94 },
    "tts_fidelity": { "status": "PASS", "score": 0.96 },
    "duration": { "status": "PASS", "value": 52.3 },
    "size": { "status": "PASS", "value": "28 MB" },
    "subtitles": { "status": "PASS" },
    "caption_consistency": { "status": "PASS" },
    "asset_fatigue": { "status": "FLAG", "notes": "Same nasheed as R025" }
  },
  "recommendation": "AWAIT_HUMAN_APPROVAL"
}
```

---

## Part 5 — Migration phases

### Phase 0 — Current state (TODAY)
- Manual pipeline per `reel-creation-pipeline.md`
- Markdown tracker per `reel-tracker.md`
- Operator does all audit work via eyeballs and ears

### Phase 1 — DB-backed tracker (POST-HAJJ, week 1)
- Build P3.1 (Supabase table + API)
- Migrate `reel-tracker.md` → `reels_posted` table
- Admin Step 3 calls `/api/check-duplicate` before "Copy caption"
- Markdown tracker becomes auto-generated reflection of DB state
- **Outcome:** No more duplicate-by-omission risk

### Phase 2 — Story/moral editable + caption template (POST-HAJJ, week 2)
- Build P3.2 (editable textareas)
- Build P3.6 (caption template generator)
- Operator can fix LLM errors inline, captions become deterministic
- **Outcome:** P079 closed; caption inconsistency eliminated

### Phase 3 — TTS validator + Whisper UZ/TJ (POST-HAJJ, week 3-4)
- Build P3.3 (TTS audio-vs-text validator)
- Build P3.4 (Whisper Latin→Cyrillic for UZ/TJ)
- Subtitles now reliable across all 5 languages
- **Outcome:** P078 closed; TTS hallucinations caught

### Phase 4 — Auditor agent (POST-HAJJ, month 2)
- Implement all 10 checks in Part 4
- Wire as a step in the manual pipeline first (run Auditor on already-rendered reels, get baseline audit scores)
- **Outcome:** Auditor runs but doesn't gate yet — operator still publishes manually

### Phase 5 — Telegram approver bot (POST-HAJJ, month 2-3)
- Build P3.5 (Telegram bot with inline buttons)
- Auditor sends to bot; bot sends to admin; admin taps Approve → Publisher runs
- **Outcome:** Human-in-the-loop pattern operational, but operator still triggers pipeline manually

### Phase 6 — Curator + Generator agents (POST-HAJJ, month 3-4)
- Curator picks from coverage gaps
- Generator + Narrator + Renderer chained as a single job
- Operator becomes "scheduler" + "approver" only
- **Outcome:** Pipeline kicks off from one trigger, surfaces in Telegram for approval

### Phase 7 — Full fleet (POST-HAJJ, month 4-6)
- All agents wired
- Scheduler runs daily at fixed time
- Auditor + Telegram bot + Publisher form the safety net
- **Outcome:** Daily reel production from one human approval per day

---

## Part 6 — Things that should NEVER be automated

Hard rules. These stay manual forever, regardless of how mature the fleet gets.

1. **Picking which hadith to feature on Ramadan day 1, Eid, Hajj season, or Anniversary of the Prophet's ﷺ death.** Significant calendar dates deserve human curation.
2. **Approval of any reel mentioning a contemporary scholar, contemporary fatwa, or contested issue.** Even if the hadith itself is sahih, framing matters.
3. **Any reel where the operator has personal reason to be cautious** (e.g., during Hajj, illness, distraction). Operator can disable the fleet entirely with one toggle.
4. **Posting to channels other than @SahihHadithReels.** Cross-posting to Instagram or YouTube Shorts must remain a deliberate human act.
5. **Responding to comments on posts.** Engagement is human work, not agent work.
6. **Adding new hadiths to the library.** Source verification (Dorar.net, Sunnah.com, HadeethEnc.com) requires human judgment.

---

## Part 7 — Failure modes and recovery

| Failure | Detection | Recovery |
|---|---|---|
| Curator picks already-posted hadith | `check-duplicate` returns 409 | Curator re-picks with exclusion list |
| Generator returns story with fabricated quote | Auditor Check 3 flags | Operator rejects, Generator retries with stricter prompt |
| Narrator TTS mispronounces religious term | Auditor Check 5 (Whisper diff) flags | Operator rejects, Narrator retries (different voice or speed) |
| Renderer produces 0-byte MP4 | Auditor Check 6+7 fail | Auto-retry once, then alert operator |
| Whisper produces garbage subtitles | Auditor Check 8 OCR fails | Fall back to no-subtitles, log to P078 patterns |
| Telegram bot can't reach admin | Bot retries with 5/10/30 min backoff, then SMS fallback (Twilio) | Operator can approve via SMS or web fallback |
| Publisher fails to post (Telegram API down) | Catch + retry; if 3 retries fail, alert | Operator posts manually, marks job complete via admin UI |
| Operator approves a bad reel by mistake | Auditor-Auditor flags within 1h via post-hoc check | Operator deletes reel, marks "approved_in_error" in DB |
| Whole fleet hangs | Cron health-check on `reel_jobs` table for stuck jobs > 1h | Operator runs `npm run fleet:kill-stuck-jobs` |

---

## Part 8 — Cost projection (rough)

Per reel, additional costs ON TOP of current manual pipeline:

| Item | Cost | Notes |
|---|---|---|
| Claude self-review (Check 3) | ~$0.03 | Sonnet on ~2KB input |
| Native-language grader (Check 4) | ~$0.02 | Sonnet on ~1KB input |
| Whisper TTS diff (Check 5) | ~$0.001 | Whisper local or $0.006/min API |
| OCR for subtitle check (Check 8) | $0 | Tesseract local |
| Total audit cost per reel | **~$0.05** | Negligible |

| Item | Cost | Notes |
|---|---|---|
| Supabase Pro (if needed for higher tier) | $25/mo | Probably stay on free until volume justifies |
| Railway worker for bot | $5/mo | Already in budget |
| Total infra delta | **~$5/mo** | Within current hosting envelope |

**Conclusion:** Cost is not the constraint. Engineering time is.

---

## Part 9 — Estimated engineering effort

| Phase | Effort | Critical path |
|---|---|---|
| P3.1 (DB) | 1-2 days | Yes |
| P3.2 (Editable text) | 0.5 day | Yes |
| P3.3 (TTS validator) | 1 day | Yes |
| P3.4 (Whisper UZ/TJ) | 2-3 days | Yes |
| P3.5 (Telegram bot) | 2 days | Yes |
| P3.6 (Caption gen) | 1 day | No (parallel) |
| P3.7 (Asset audit API) | 0.5 day | No (parallel) |
| Phase 4 (Auditor) | 3-5 days | Yes |
| Phase 5 (Approver wiring) | 1 day | Yes |
| Phase 6 (Curator + chain) | 2-3 days | Yes |
| Phase 7 (Scheduler + monitoring) | 2 days | Yes |
| **Total to full fleet** | **16-22 working days** | |

Realistic calendar time (working 50% on this post-Hajj alongside QA contract work): **6-10 weeks**.

---

## Part 10 — Open questions to revisit post-Hajj

1. Should the Auditor's Check 3 (religious accuracy) call a **different Claude personality** trained more specifically on Islamic content? Or is the same Claude with a strict prompt sufficient?
2. Should we add a **mufti review checkpoint** for any reel touching contested fiqh? (E.g., reels about music permissibility, gender interactions.) → Yes, with which scholars in network?
3. Should the channel begin **cross-posting to Instagram Reels and YouTube Shorts** once the fleet is mature? If yes, separate Publisher per platform.
4. Should we maintain a **bench of pre-approved hadiths with pre-rendered reels** as a buffer for travel / illness / busy weeks?
5. How do we handle **breaking events** (e.g., death of a scholar, major Muslim community event) that warrant a topical reel outside the agent fleet's normal cadence?
6. At what point does the channel justify **a part-time human editor** (not Farhod) reviewing all reels before approval?
7. How does this architecture handle **the post-Hajj period** when Farhod is back but on jet lag / reduced capacity for 1-2 weeks?

---

## References

- `reel-creation-pipeline.md` — current manual pipeline (8 steps)
- `reel-tracker.md` — current markdown tracker (to be replaced by DB in P3.1)
- `fix_patterns.md` P078 — Whisper UZ/TJ Latin transliteration limitation
- `fix_patterns.md` P079 — Admin story/moral not editable before TTS
- `hr-CLAUDE.md` — project context, phase roadmap
- `hr-CLAUDE-append-3.md` — business model, monetization
- `AGENTS_ADDENDUM.md` — Golden Rule, atomic commit discipline
- Hadith Verifier app (HV project) — human-in-the-loop pattern reference

## Change log

| Date | Change | By |
|---|---|---|
| 2026-05-16 | Initial draft created pre-Hajj | Farhod / Claude session |
