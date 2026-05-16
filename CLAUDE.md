# CLAUDE.md
# Hadith Reels — Context file for Claude Code
# github.com/Farhod75/hadith-reels
# Last updated: May 2026 — CI #13 ✅
# Read AGENTS.md and QA_STANDARDS_AGENT_RULES.md before every task
# ============================================================

## What this project does
AI-powered content studio that creates authentic Islamic hadith reels
for social media (Instagram, TikTok, YouTube Shorts, Telegram).
YOU create reels → YOU post → YOU monetize.
Revenue covers Vercel + Railway + Supabase + ElevenLabs + Claude API costs.
HadithVerifier.com stays free forever.

Core principle: Only sahih/hasan hadiths. Never daif. Human approves before posting.

## Business model
- NOT a user-facing reel creation tool
- YOU use the admin panel (/admin) to generate reels
- Public site (/) shows hadith library + watch reels
- Monetization: YouTube Partner + TikTok Creator + Islamic brand sponsors

## Tech stack
- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- AI: Anthropic Claude Sonnet (claude-sonnet-4-20250514)
- TTS: ElevenLabs Multilingual v2 (Hijazi AR, Abrar Sabbah RU/UZ)
- Video: Remotion (planned Phase 2)
- Database: Supabase (SHARED with hadith-verifier)
- Hosting: Vercel (port 3002 locally)
- Testing: Playwright (TypeScript)

## Project structure
```
hadith-reels/
├── app/
│   ├── page.tsx              — public: Hadith library + Watch reels tabs
│   ├── layout.tsx            — metadata, Inter font, theme
│   ├── globals.css
│   └── api/
│       ├── reels/route.ts    — GET hadith_library (sahih/hasan only)
│       ├── generate-reel/    — POST: Claude story+moral+seerah_context
│       ├── tts/route.ts      — ElevenLabs proxy (lang×style voice map)
│       ├── search/route.ts   — hadith search (stub — use /api/reels)
│       └── admin/
│           └── verify/       — POST: ADMIN_PASSWORD check
├── admin/
│   ├── page.tsx              — admin studio (password gated)
│   └── layout.tsx            — dark slate theme
├── tests/
│   └── hadith-reels.spec.ts  — Playwright CI tests (all mocked)
├── playwright.config.ts
├── next.config.js            — CSP headers (ElevenLabs + blob: audio)
├── .github/workflows/ci.yml  — push: E2E mocked only | manual: real API
├── AGENTS.md                 — agent orchestration rulebook
├── QA_STANDARDS_AGENT_RULES.md
├── CI_WORKFLOW_TEMPLATE.md
├── fix_patterns.md           — P046–P050
└── CLAUDE.md                 — this file
```

## Environment variables
```
NEXT_PUBLIC_SUPABASE_URL=https://xeirfeqnbjfyszykiraa.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...      ← ALWAYS use this server-side
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=sk_...
ADMIN_PASSWORD=***                    ← set in Vercel + .env.local
```

## Shared Supabase (with hadith-verifier)
- Project: xeirfeqnbjfyszykiraa.supabase.co
- Tables used: hadith_library (70 hadiths), hadith_reels
- NEVER drop or alter hadith_library without coordinating with HV
- RLS disabled — always use SUPABASE_SERVICE_ROLE_KEY server-side
- hadith_library columns: text_arabic, text_english, text_uzbek, text_russian
- NO text_tajik column — TJ shows Russian fallback (P050)

## Languages
| Code | Display text | Narration | Seerah source |
|---|---|---|---|
| ar | text_arabic | Hijazi (ElevenLabs) | Ar-Raheeq Al-Makhtum |
| en | text_english | EN voice | Ar-Raheeq Al-Makhtum |
| uz | text_uzbek (or EN) | Abrar Sabbah | Усваи Хасана |
| ru | text_russian | Abrar Sabbah | Усваи Хасана |
| tj | text_russian (fallback) | Tajik Cyrillic via Claude | Усваи Хасана |

## Seerah sources (P049)
- AR/EN: Ar-Raheeq Al-Makhtum (Safiur Rahman al-Mubarakpuri, 1976)
  Scholarly, eloquent, historical. Award: Muslim World League 1979.
- UZ/RU/TJ: Усваи Хасана (Uswa al-Hasana)
  Turkish multi-volume Seerah, translated to Russian/Uzbek.
  Emotional, devotional, warm. Better for Central Asian/Russian audience.

## Admin panel (/admin)
- Password gated via ADMIN_PASSWORD env var
- 4-step workflow: Pick hadith → Generate → Preview → Done
- Config: Adults/Kids style + 5 languages + grade filter
- Claude generates: title + story + moral + seerah_context + caption_intro
- ElevenLabs audio preview per section
- MP3 download button
- Auto-generated social caption with hashtags + source attribution
- One-click open: Instagram / TikTok / YouTube / Telegram

## Public page (/)
- Tab 1: Hadith library — browse 70 hadiths, search, grade filter
- Tab 2: Watch reels — coming soon + follow buttons (YT/IG/TG/TikTok)
- HV cross-link banner always visible
- Generate reel button NOT on public page (admin only)

## Run commands
```powershell
npm run dev -- -p 3002
npx playwright test tests/hadith-reels.spec.ts --project=chromium
vercel --prod --force
```

## CI workflow
Push triggers:
- ✅ Type check (continue-on-error)
- ✅ Build
- ✅ E2E tests (hadith-reels.spec.ts — mocked)
NOT in push CI:
- ❌ language-speech.spec.ts (real ElevenLabs)
Manual dispatch: run_real_api=true

## CI history
- #1–5 ❌ yml had language-speech step (P046)
- #6 ✅ correct yml + mocked spec (P046)
- #7–8 ❌ emoji tab button locator (P047/P048)
- #9 ✅ functional outcome tests (P048)
- #10 ✅ fix_patterns + AGENTS.md docs
- #11 ✅ admin studio deployed
- #12 ✅ dual seerah sources (P049)
- #13 ✅ TJ Russian fallback (P050)

## Fix patterns (HR specific, P046–P050)
P046: ci.yml had language-speech real ElevenLabs step
P047: emoji tab button locator breaks in headless CI
P048: test functionality not emoji label text
P049: dual seerah sources — Uswa al-Hasana for UZ/TJ/RU
P050: TJ has no text_tajik — Russian fallback for display

## Phase roadmap
| Phase | Feature | Status |
|---|---|---|
| 1 | Browse tab (real Supabase) | ✅ Done |
| 1 | Generate tab → Claude story | ✅ Done |
| 1 | TTS via ElevenLabs | ✅ Done |
| 1 | Admin studio (/admin) | ✅ Done |
| 1 | Public page (Browse+Watch) | ✅ Done |
| 1 | Dual seerah sources | ✅ Done |
| 2 | Remotion MP4 export | ⏳ Next |
| 3 | Telegram auto-post | ⏳ Quick win |
| 3 | Buffer API (IG/TikTok/YT) | ⏳ Pending |
| 4 | Daily cron agent | ⏳ Pending |
| 4 | YouTube monetization | ⏳ Pending |
| 5 | Stripe custom reels service | ⏳ Pending |

## Live URLs
- Public: https://hadith-reels.vercel.app
- Admin: https://hadith-reels.vercel.app/admin
- GitHub: https://github.com/Farhod75/hadith-reels
- Companion: https://hadithverifier.com (shared Supabase)
- Domain: hadithreels.com (coming)
# HR CLAUDE.md — append "May 2026 session learnings" section

Append the following section at the END of `hr-CLAUDE.md`. Do NOT replace the file.

---

## ── MAY 2026 SESSION LEARNINGS ─────────────────────────────────────────
## Documented after major HR development session (May 14-15, 2026)
## ─────────────────────────────────────────────────────────────────────────

### Port assignment — strictly enforced

- **HR dev server: port 3002** (set via `next dev -p 3002` in `package.json` scripts.dev)
- HV dev server: port 3001
- **Idris Learning App: port 3000** (hardcoded in `idris-learning-app/package.json` line: `"serve": "npx serve . -l 3000"`)

If port 3002 is occupied, do NOT default to 3000. Idris auto-starts there and HR will load Idris content via cache confusion. Kill the conflicting process or use a different port.

### TTS phonetic approach for non-English languages

**Current state (P074 — May 2026):**
- UZ + TJ use OpenAI `gpt-4o-mini-tts` (NOT `tts-1`) with per-language `instructions` parameter
- Voice map: UZ kids → Nova, UZ adults → Onyx, TJ kids → Nova, TJ adults → Onyx
- EN + AR + RU use ElevenLabs (no change)
- Pronunciation quality: ~80-90% native-like, not perfect

**Permanent fix queued (post-Hajj):** Voice cloning via ElevenLabs Professional Voice Clone using native speaker recordings. Nephew has begun recording Ar-Raheeq al-Makhtum in UZ and TJ — that source material becomes the cloned voice training set.

**Backup approach:** Phonetic Pronunciation Dictionary (PPD) — Supabase table with letter/word/phrase substitution rules per language. Design in separate doc; deferred unless voice cloning insufficient.

### Hadith Library data layer

**Schema columns:** `text_arabic`, `text_english`, `text_uzbek`, `text_russian`, `text_tajik` (added P075), `narrator`, `collection`, `hadith_number`, `grade`, `tags`, `source_url`, `authority`.

**Tajik translation pipeline:** AI-generated from Uzbek source via `scripts/translate-tajik.ts` (Claude Sonnet 4.5) → JSON review → `scripts/apply-tajik-translations.ts` writes to Supabase. See `hr-tj-translation-process.md`.

**Known data quality issues to fix post-Hajj:**
- UZ Cyrillic intrusions in Latin transliterations (P050-related, multiple rows)
- A few UZ source typos (e.g. "o'z uchun" should be "o'zi uchun" in hadith #13)
- Russian seed needs same audit
- AR text never audited for diacritics consistency

### Cross-repo integration with HV

HV (`hadithverifier.com`) and HR (`hadithreels.com`) share the same Supabase database. HR is the accessibility layer for HV: users who can't read EN or AR use HR Library to verify hadiths in UZ/TJ/RU.

**Caption link per-language (post-Hajj task):**
Telegram/social caption "Verify: hadithverifier.com" must route by reel language:
- UZ reel → `hadithverifier.com/uz`
- TJ reel → `hadithverifier.com/tj`
- RU reel → `hadithverifier.com/ru`
- AR reel → `hadithverifier.com/ar`
- EN reel → `hadithverifier.com`

Requires HV to support locale routing (currently single-page EN). Two-repo coordinated change.

### Telegram distribution — channel strategy

@SahihHadithReels is the production reel channel. Currently linear feed, no language separation.

**Post-Hajj decisions to make:**
- (A) Hashtag system — every post tagged `#UZ #TJ #RU` for filter. Easiest.
- (B) Separate channels per language. More overhead, real separation.
- (C) Telegram Forum mode (topics). Best UX but channel restructure required.

Plus Instagram Reels, TikTok, YouTube Shorts expansion.

### Security considerations — non-negotiable post-Hajj work

See `hr-security-considerations.md` for full analysis. Summary:
- HV `/api/analyze` route accepts user-pasted text → prompt injection vulnerable. Highest priority.
- HR reel generation is admin-only → lower risk but still validate output schema.
- Cloning risk: repos public, attribution needs cryptographic proof.
- Supabase RLS currently disabled — needs re-enabling with proper admin-only write policy.

### Documentation discipline (lesson)

This session generated 6+ hours of decisions that were almost lost to chat-only context. Document AS YOU GO, not at the end. Per AGENTS_ADDENDUM.md Session Startup Protocol, every new chat should read all governance/spec md files before first technical direction.

### Sonnet 4 → Sonnet 4.5 migration deadline

Anthropic email (May 13, 2026) — `claude-sonnet-4-20250514` retires June 15, 2026. All routes using it must migrate to `claude-sonnet-4-5` or successor before that date.

**Routes to update (post-Hajj):**
- `app/api/analyze/route.ts` (HV) — verdict generation
- `app/api/dua/route.ts` (HV) — dua corrector
- Reel content generation route (HR)
- `scripts/translate-tajik.ts` (HR) — already on `claude-sonnet-4-5` ✅
- Any other Claude API calls

Test after migration; some prompts may behave differently.

### Agent fleet — post-Hajj construction

See `hr-agent-fleet-roadmap.md` for full plan. Summary: 11 specialist agents in Anthropic Skills format, per-repo deployment, orchestrator dispatches via Claude Code agent view (subagents primitive). Build sequence:
1. Orchestrator
2. TTS-validating (SKILL.md exists, scripts to write)
3. STT-validating
4. A/B-comparing (Claude + ChatGPT + Kimi)
5. CI-monitoring
6. Pre-push-validating
7. Code, Test, Doc, Git, Upskilling agents (round 2)

### Post-Hajj priority list (frozen 05/18/2026)

| # | Task | Why |
|---|---|---|
| 1 | Sonnet 4 → 4.5 migration before June 15 | Hard deadline; API retirement |
| 2 | Voice cloning UZ + TJ from nephew's recordings | Permanent fix for accent issues |
| 3 | HV security hardening — prompt injection mitigation | Religious correctness depends on it |
| 4 | Caption per-language links (HR + HV coordinated) | UX gap |
| 5 | UZ seed audit (Cyrillic intrusions) | Data quality |
| 6 | RU + AR seed audits | Same |
| 7 | Agent fleet build (orchestrator + 6 specialists first) | Per roadmap |
| 8 | Supabase RLS re-enable with admin-only write | Security |
| 9 | Seed more hadiths from islom.uz/islom.tj/islamhouse.com | Library coverage |
| 10 | Audiobook feature (Ar-Raheeq + Усваи Ҳасана + Quran narration) | New feature line |
| 11 | Telegram tabs strategy (A/B/C) decision + implementation | Distribution |
| 12 | Phonetic PPD table (Supabase) as voice clone backup | Defensive |

Dates approximate. Hajj timing: depart 05/19/2026, return 06/06/2026.

---

End of May 2026 session learnings section.
# HR CLAUDE.md — second append: video backgrounds + engineering standards

Append at the END of `hr-CLAUDE.md`, AFTER the May 2026 session learnings section. Do NOT replace the file.

---

## ── VIDEO BACKGROUNDS ARCHITECTURE ──────────────────────────────────────
## Added: May 2026 — design decision for reel visual variety
## ─────────────────────────────────────────────────────────────────────────

### Current state (manual pipeline)

`out/backgrounds/` contains static MP4 files used as reel backgrounds:
- `garden.mp4` — kids reel default
- `mosque.mp4` — adults reel default

ffmpeg uses `-stream_loop -1 -i <background>.mp4` to loop the background through the narration duration. Same background per language/style.

### Planned state (post-Hajj — `video_backgrounds` Supabase table)

**Goal:** visual variety across reels without manual selection. Same hadith reel generated tomorrow looks different from today.

**Schema (Supabase table already created, schema TBD):**

```sql
CREATE TABLE video_backgrounds (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,                    -- e.g. 'garden-1', 'mosque-2'
  category TEXT NOT NULL,                -- 'kids', 'adults', 'ramadan', 'seasonal'
  style TEXT,                            -- 'bright', 'dark', 'colorful', 'elegant'
  file_path TEXT NOT NULL,               -- 'out/backgrounds/clips/garden-1.mp4'
  duration_seconds NUMERIC NOT NULL,     -- typical 5-15 sec chunks
  width INTEGER NOT NULL,                -- 1080
  height INTEGER NOT NULL,               -- 1920
  tags TEXT[] DEFAULT '{}',              -- ['nature','flowers','outdoor']
  use_count INTEGER DEFAULT 0,           -- rotation: lowest count picks next
  is_active BOOLEAN DEFAULT true,        -- disable without delete
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_video_bg_category_active ON video_backgrounds(category, is_active);
CREATE INDEX idx_video_bg_use_count ON video_backgrounds(use_count ASC);
```

**Chunking strategy:** record/source long background videos (60+ seconds), split into 5-15 second chunks via ffmpeg, store each as a row. Same visual concept (mosque architecture, garden) but different camera angles/moments.

**Selection algorithm for reel generation:**

```typescript
// pseudo-code
async function pickBackgrounds(category: string, neededDurationSec: number) {
  // Query backgrounds ordered by lowest use_count (rotation)
  const candidates = await supabase
    .from('video_backgrounds')
    .select('*')
    .eq('category', category)
    .eq('is_active', true)
    .order('use_count', { ascending: true })
    .limit(20)

  // Pick chunks until total duration covers narration + 5sec buffer
  const selected: VideoBackground[] = []
  let totalDuration = 0
  while (totalDuration < neededDurationSec + 5 && candidates.length) {
    const next = candidates.shift()!
    selected.push(next)
    totalDuration += next.duration_seconds
  }

  // Increment use_count for selected
  await supabase
    .from('video_backgrounds')
    .update({ use_count: supabase.raw('use_count + 1') })
    .in('id', selected.map(c => c.id))

  return selected
}
```

**ffmpeg concat for multi-chunk background:**

```powershell
# Build concat list file
$concatList = $selected | ForEach-Object { "file '$($_.file_path)'" } | Out-File -Encoding UTF8 "out/concat-bg.txt"

# Concatenate chunks into one background.mp4 long enough for narration
ffmpeg -y -f concat -safe 0 -i "out/concat-bg.txt" -c copy "out/dynamic-bg.mp4"

# Then use out/dynamic-bg.mp4 in the main render command (no more -stream_loop needed)
```

**Why this is better than `-stream_loop -1`:** loop creates obvious repetition users notice on 30-second reels. Concatenating different chunks looks like one continuous variety video.

### Acceptance criteria

- 20+ chunks per category seeded
- Reel generation script (orchestrator agent) picks 3-5 chunks per reel based on duration
- Two reels for the same hadith look visually different
- Use_count rotation ensures no chunk dominates

### Owner

Reel-rendering agent (Tier 1, post-Hajj fleet build). Until then, the existing single-background `-stream_loop` flow continues working.

### Risks

- File size: 20 chunks × 5MB each = 100MB committed if stored in git. Better path: store in Supabase Storage bucket or external CDN; DB table tracks metadata + URL only.
- Visual continuity: random concat may produce jarring cuts. Mitigation: tag chunks with "transition_safe" boolean for chunks with smooth start/end frames.

---

## ── ENGINEERING STANDARDS REPO ──────────────────────────────────────────
## Added: May 2026 — external reference doc
## ─────────────────────────────────────────────────────────────────────────

**Repo:** https://github.com/Farhod75/engineering-standards

**Purpose:** Public, enterprise-grade QA reference document covering universal standards across all Farhod's projects (HV, HR, Idris, future apps). Mirrors the rules in `QA_STANDARDS.md` and `QA_STANDARDS_AGENT_RULES.md` but in a portfolio-presentable form.

**Why it lives outside HV/HR repos:** universal patterns belong in a universal repo. Cloning HV doesn't give you all of Farhod's QA conventions; the engineering-standards repo does.

**Usage:**
- Add to GitHub profile pinned repos for hiring visibility
- Reference in CV / LinkedIn posts about CT-AI certification
- Future agents (doc-writing, test-writing) can clone this repo as reference

**Maintenance:**
- Post-Hajj: doc-writing agent keeps it synced when project-specific QA rules generalize to universal patterns
- New ISTQB/CT-AI/CT-GenAI patterns get added here first, then propagated to per-project AGENTS_ADDENDUM if applicable

**Add to AGENTS_ADDENDUM.md self_upskilling watchlist:** "Engineering-standards repo — Farhod's own QA reference, source of truth for universal patterns. Reference when proposing new fix_patterns entries."

---

End of second append.

