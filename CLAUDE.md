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
