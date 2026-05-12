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
