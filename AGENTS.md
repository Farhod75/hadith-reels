# AGENTS.md
# Hadith Reels — Agent Orchestration Rulebook
# github.com/Farhod75/hadith-reels
# Version: 1.0 — May 2026
#
# Claude Code reads this file before every task.
# Universal rules: QA_STANDARDS_AGENT_RULES.md (also in this repo)
# HV patterns inherited via: fix_patterns.md from hadith-verifier
# ============================================================

## ════════════════════════════════════════════════════════
## CRITICAL: READ THESE FIRST
## ════════════════════════════════════════════════════════

1. Read QA_STANDARDS_AGENT_RULES.md — all universal rules apply here
2. Check hadith-verifier/fix_patterns.md — all P001–P043 patterns apply here too
3. Never mix HV and HR changes in same commit
4. Port 3002 only (`npm run dev -- -p 3002`)

## ════════════════════════════════════════════════════════
## ORCHESTRATOR INSTRUCTIONS
## ════════════════════════════════════════════════════════

Same 5-step sequence as HV AGENTS.md. Additionally for HR:

### Before any HR build task
1. Confirm HV CI is green first — HR shares Supabase with HV
2. Check hadith_library has sufficient sahih hadiths for the feature
3. Confirm ElevenLabs voice IDs are current (Starter plan, 3 voices)
4. Never start a Remotion composition without checking HV seerah_context field exists

## ════════════════════════════════════════════════════════
## HR AGENT ASSIGNMENTS
## ════════════════════════════════════════════════════════

### 🔧 Code agent — HR specific rules
- page.tsx: Browse | Generate | My Reels | History tabs
- All tabs must have loading states and empty states
- SAMPLE_REELS must be replaced with Supabase fetch before any tab goes live
- Remotion compositions: HadithReel.tsx (adults) and KidsReel.tsx (kids)
- Never hardcode hadith text — always fetch from hadith_library
- HV cross-link banner must remain after </header> always
- Port: always 3002, never 3000 or 3001

### 🧪 Test agent — HR specific rules
- All CI tests mock /api/generate-reel, /api/tts, /api/reels
- Real ElevenLabs calls → @real-api tag only
- Real Remotion renders → @real-api tag only
- Test both Adults and Kids style in MOCK_REEL_RESPONSE
- Verify HV cross-link banner present in every page load test
- Add audit test when new reel field added to hadith_reels table

### 📝 Doc agent — HR specific rules
- CLAUDE.md (HR) must track: feature status table, pending agents, ElevenLabs voices
- fix_patterns.md: HR patterns start at P044 (P001–P043 are HV patterns)
- CHANGELOG.md: separate from HV
- README.md: must not be Next.js boilerplate (already replaced)

### 🚀 Git agent — HR specific rules
- Branch: main (same as HV — separate repos)
- Never commit to hadith-verifier repo from hadith-reels folder
- Verify correct repo: `git remote -v` before any push

### 👁 CI monitor — HR specific rules
- HR CI pipeline: .github/workflows/ci.yml (already added)
- Same pattern as HV: mock API tests in CI
- ElevenLabs and Remotion tests → @real-api only

## ════════════════════════════════════════════════════════
## HR API SHAPES (planned)
## ════════════════════════════════════════════════════════

### POST /api/generate-reel
```json
{
  "hadith_id": "uuid from hadith_library",
  "style": "adults | kids",
  "lang": "ar | uz | ru | en",
  "voice_id": "ElevenLabs voice ID"
}
```
Returns:
```json
{
  "reel_id": "uuid",
  "title": "string",
  "story": "string (Claude generated, Ar-Raheeq Al-Makhtum style)",
  "moral": "string",
  "seerah_context": "string (same field as HV analyze route)",
  "audio_url": "string (ElevenLabs TTS)",
  "status": "generating | ready | error"
}
```

### GET /api/reels
Returns hadith_reels table records with filters:
- ?style=adults|kids
- ?lang=ar|uz|ru|en
- ?grade=sahih|hasan
- ?limit=20&offset=0

### Hadith_reels table schema
```sql
CREATE TABLE hadith_reels (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  hadith_id UUID REFERENCES hadith_library(id),
  style TEXT NOT NULL CHECK (style IN ('adults', 'kids')),
  lang TEXT NOT NULL,
  title TEXT,
  story TEXT,
  moral TEXT,
  seerah_context TEXT,
  audio_url TEXT,
  video_url TEXT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT now()
);
```

## ════════════════════════════════════════════════════════
## HR VOICE MATRIX
## ════════════════════════════════════════════════════════

| Language | Style | Voice | ElevenLabs ID |
|---|---|---|---|
| Arabic | Adults | Hijazi | (store in .env.local) |
| Arabic | Kids | Abu Salem | (store in .env.local) |
| Russian | Adults/Kids | Abrar Sabbah | (store in .env.local) |
| Uzbek | Adults/Kids | Multilingual fallback | browser SpeechSynthesis |
| Tajik | Adults/Kids | Persian/Farsi fallback | browser SpeechSynthesis |

## ════════════════════════════════════════════════════════
## HR BUILD ORDER (agents follow this sequence)
## ════════════════════════════════════════════════════════

Phase 1 — Foundation (current)
- [x] page.tsx UI (Browse | Generate | My Reels tabs)
- [x] HV cross-link banner
- [ ] Supabase fetch in Browse tab (replaces SAMPLE_REELS)
- [ ] /api/reels GET route

Phase 2 — Content generation
- [ ] /api/generate-reel POST route (Claude story agent)
- [ ] /api/tts route (ElevenLabs proxy, same pattern as HV)
- [ ] Generate tab wired to real API

Phase 3 — Video
- [ ] Remotion HadithReel.tsx (Adults composition)
- [ ] Remotion KidsReel.tsx (Kids composition)
- [ ] MP4 export pipeline

Phase 4 — Automation
- [ ] Daily cron agent (1 Adults + 1 Kids per day)
- [ ] hadith_reels Supabase table populated
- [ ] HV Search tab "Watch Reel" button

Phase 5 — Monetization
- [ ] Stripe integration (Free/Pro/Family/Team)
- [ ] User reel history tab
- [ ] Custom branding for Team plan

## ════════════════════════════════════════════════════════
## SHARED INFRASTRUCTURE RULES
## ════════════════════════════════════════════════════════

- Supabase: xeirfeqnbjfyszykiraa.supabase.co (SHARED with HV)
- NEVER drop or alter hadith_library table without coordinating with HV
- NEVER disable RLS on new tables without explicit Farhod approval
- ElevenLabs: same API key as HV (Starter plan — 3 voices configured)
- Anthropic: same API key as HV

## ════════════════════════════════════════════════════════
## NEVER-DO LIST (HR specific)
## ════════════════════════════════════════════════════════

- Never use daif hadiths in reels — sahih and hasan only
- Never auto-publish reels — human reviews before any public post
- Never remove the HadithVerifier.com cross-link banner
- Never call real Remotion render in CI — always mock
- Never call real ElevenLabs in CI — always mock
- Never share ElevenLabs voice IDs in commit messages or README

---
*Last updated: May 2026*
*Read QA_STANDARDS_AGENT_RULES.md for full universal standards*
*HV fix patterns (P001–P043) also apply to this project*
## ════════════════════════════════════════════════════════
## ADDENDUM TO AGENTS.md (both HV and HR)
## Append to the bottom of each AGENTS.md
## ════════════════════════════════════════════════════════

## ── GOLDEN RULE: CI GREEN GATE ──────────────────────────
## Added: May 2026 — agreed with Farhod
## ─────────────────────────────────────────────────────────

### The rule
**NEVER move to the next task until CI is green.**

This applies to:
- Every feature build
- Every bug fix
- Every doc update
- Every spec change
- Moving from HV tasks to HR tasks (or vice versa)
- Starting any new Phase

### Why
- Red CI = broken code in main branch = next push builds on broken foundation
- Moving forward with red CI caused 10+ wasted CI runs (P037–P048)
- Each wasted run = 3-5 minutes + context switching + debugging time

### How to enforce
Before declaring any task complete, the orchestrator MUST:
1. Confirm CI run number from GitHub Actions
2. Confirm green ✅ status
3. Only then mark task done and move to next

### Exception
Documentation-only commits (CLAUDE.md, fix_patterns.md, README.md):
- These cannot break CI
- Can be pushed while watching another CI run
- But still must not contain code changes

### What to do if CI is red
1. STOP — do not start next task
2. CI monitor agent reads the failure
3. Check fix_patterns.md first
4. Fix the failing test
5. Push fix
6. Wait for green
7. THEN move forward

## ── NEVER-DO LIST ADDITIONS (P046–P048) ─────────────────

- P046: Never add language-speech or ElevenLabs steps to CI push workflow
- P047: Never use getByText() or filter({ hasText }) on buttons with emojis
- P048: Never test UI label text — test functional outcome instead
- P048: For emoji tab buttons use page.evaluate() to click by textContent
- P048: For lang buttons scope to header: page.locator('header').locator('button', { hasText: 'EN' })

## ── TEST DESIGN CHECKLIST (before writing any new test) ──

Ask these questions before writing each test:
1. Am I testing a label/text or a functional outcome? → Test outcome
2. Does the element I'm targeting contain an emoji? → Use evaluate()
3. Am I calling a real external API? → Mock it or tag @real-api
4. Is this locator scoped to a specific container? → If not, scope it
5. Would this test pass if the feature was broken? → If yes, rewrite it
## ════════════════════════════════════════════════════════
## MANDATORY PRE-PUSH PROTOCOL (added May 2026)
## Why: CI #122–143 = 20+ wasted runs from not testing locally first
## ════════════════════════════════════════════════════════

### THE RULE
**NEVER run `git push` without running tests locally first.**
This is non-negotiable. No exceptions except `--no-verify` for
doc-only commits (CLAUDE.md, fix_patterns.md, README.md).

### What to run before EVERY push

#### For hadith-verifier:
```powershell
# Must ALL pass before git push:
npx tsc --noEmit
npx playwright test tests/hadith-verifier.spec.ts --project=chromium --reporter=list
npx playwright test tests/api.spec.ts --project=chromium --reporter=list
```

#### For hadith-reels:
```powershell
# Must ALL pass before git push:
npx tsc --noEmit
npm run build
npx playwright test tests/hadith-reels.spec.ts --project=chromium --reporter=list
```

### Automated enforcement — pre-push Git hook
The pre-push hook in `.git/hooks/pre-push` runs these automatically.
If any test fails → push is BLOCKED.
Install once per machine:
```powershell
# hadith-verifier:
Copy-Item ".githooks\pre-push" ".git\hooks\pre-push"

# hadith-reels:
Copy-Item ".githooks\pre-push" ".git\hooks\pre-push"
```

### Test agent checklist (run in this order)
Before declaring any code task complete:
- [ ] tsc --noEmit passes
- [ ] Playwright mocked tests pass locally
- [ ] If new API field added → audit_spec.ts updated
- [ ] If new component added → spec test added
- [ ] fix_patterns.md entry written
- [ ] ONLY THEN → git push

### What caused CI #122–143 failures (all preventable)
| CI run | Root cause | Could have caught locally? |
|---|---|---|
| #122–131 | Selector/timeout issues | ✅ Yes — playwright test locally |
| #132 | P043 fix not pushed | ✅ Yes — git status check |
| #133 | Severity test calls real Claude | ✅ Yes — playwright test locally |
| #135–136 | audit_spec in CI | ✅ Yes — check ci.yml before push |
| #137 | Package-lock out of sync | ✅ Yes — npm ci locally |
| #138–140 | Remotion type errors | ✅ Yes — tsc --noEmit |
| #141–143 | Syntax errors in TypeScript | ✅ Yes — tsc --noEmit |

**All 20+ CI failures were preventable with local testing.**

### Starting from CI #144 — target: zero preventable failures
Every push must be preceded by local test run.
If CI fails after local tests passed → it is an environment issue.
If CI fails and local tests would have caught it → process violation.
