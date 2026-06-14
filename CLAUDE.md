# CLAUDE.md
# Project constitution for hadith-reels
# Auto-loaded by Claude Code on every session
# Last updated: 2026-06-13

---

## 🧑 WHO

**Developer:** Farhod Elbekov — SDET / AI QA Engineer, Charlotte NC
**Stack:** Next.js 14 + TypeScript + Supabase + Claude API + Vercel + multilingual TTS
**Repo:** github.com/Farhod75/hadith-reels
**Sister project to:** hadithverifier.com
**Built as:** sadaqah jariyah — daily authentic hadith reels for social media
---
## 📝 DOCUMENTATION DISCIPLINE (STRICT — applies to HV + HR)
**EVERY fix, update, or enhancement MUST be documented in the same session it ships.**
- Fixes → `fix_patterns.md` (log immediately after CI green, never deferred)
- Features / enhancements → `CLAUDE.md` + `FEATURES.md` + `CHANGELOG.md`
- Process changes → keep `reel-creation-pipeline.md` and related process docs current
- Update docs BEFORE or ALONGSIDE the code push — never "document later"
- Verify doc updates with git (`git show` / `git log`), exactly like code
- Rationale: docs falling behind capabilities is itself a defect. This rule is
 non-negotiable and a Claude session must not slip it.
---
## ⚠️ DEV ENVIRONMENT GOTCHA — PowerShell file writes get reverted
**On this machine, PowerShell file-API writes to repo files are silently REVERTED**
(`Set-Content`, `Add-Content`, `[System.IO.File]::WriteAllBytes`/`WriteAllText`).
The write appears to succeed, Windows `dir` briefly shows the new size, but git
reads the OLD content (stale blob) and the change never persists/commits.
Likely cause: antivirus controlled-folder-access or a sync/backup tool intercepting writes.
- **FIX: edit repo files in VS Code** (its save path is NOT intercepted) — never via PowerShell file APIs.
- This also explains earlier BOM/encoding struggles with `Set-Content`.
- Symptom to recognize: `git hash-object <file>` returns the SAME sha as HEAD even
  after you "wrote" changes; `git status` says clean despite a changed file.
- TODO: investigate root cause (Windows Defender controlled folder access, or sync tool).
---
## 🐑 Talking-mascot kids lane (added 2026-06-13)
- **Mascot stills:** Nano Banana Pro (Gemini, paid API key). Locked reusable
  assets in **tracked** `assets/mascot/` (NOT gitignored `out/`). Edit an
  existing mascot to add poses/outfits — don't re-roll — to keep the face.
- **Lip-sync:** `generate-talking-clip.py` → fal `veed/fabric-1.0` (`FAL_KEY`).
- **DEV GOTCHAS (this session):**
  - Browser image downloads can save with a corrupted extension
    (e.g. `lamb-boy-v1.pn.jpg`). Rename cleanly in VS Code/Explorer;
    Fabric accepts jpg regardless of the wrong-looking name.
  - Install the fal client with `python -m pip install fal-client`
    (not bare `pip`) so it lands in the interpreter running the script.
- **Guardrail:** kids mascots are generic animals only — never the Prophet,
  prophets, angels, Allah, or named Sahaba.

  ### Scene-baked mascots + render-mascot-reel.ps1 (added 2026-06-13)
- **Scene generation:** Nano Banana Pro, attach the locked base mascot
  (`lamb-boy-v1` / `lamb-girl-v1`) as a face reference, prompt the new scene.
  Keeps face consistent across environments. Download to `assets/mascot/`.
- **Render:** `render-mascot-reel.ps1` — talking clips are the audio spine
  (NOT a silent background); nasheed mixes under the voice at 0.20.
- **Route-A motion coupling:** Fabric animates the whole image, so objects
  near/above the head drift with head motion. Keep the mascot large and
  centered, offset moons/large objects to a corner, leave headroom. Route B
  (green-screen over looping scene video) is the fix for fully-static bg — deferred.
- **Downloaded-script gotcha:** new `.ps1` files saved from a browser are
  execution-policy blocked; clear with `Unblock-File .\script.ps1` (metadata
  change, not a content write — revert gotcha doesn't apply).

  ### Narration splitting (split-narration.py, added 2026-06-13)
- Fabric caps ~30s/clip. `split-narration.py --base <base> --audio <story> <moral>`
  concats + splits at silences into out/talking/<base>-clipNN.mp3 (<=28s each),
  then prints the generate-clip loop + render command.
- **Content rule:** ONE mascot + ONE voice per reel (mixing mascots mid-reel
  = two voices). Assign the mascot to fit the hadith; expand the cast reactively
  as the library grows (not up front).

## 🎯 PROJECT GOAL

Generate short-form video reels (15-60s) with authentic hadiths for Instagram/TikTok/YouTube Shorts.

**Features:**
- Daily hadith from Tier 1 sources (Sunnah.com, Dorar.net)
- Multi-language: EN, UZ, AR, RU, TJ
- TTS narration (OpenAI Nova for UZ/TJ, native Claude voices for EN/AR/RU)
- Auto-generated visuals (gradient backgrounds, Arabic calligraphy overlay)
- One-tap publish to social platforms
- Severity validation: NEVER publishes weak or fabricated hadiths

---

## 🚨 HARD RULES (NEVER VIOLATE)

### 1. Authenticity Gate (CRITICAL)
- EVERY hadith MUST be verified Sahih or Hasan before TTS generation.
- ALWAYS call hadithverifier.com API first → only proceed if severity = "AUTHENTIC".
- NEVER publish hadiths with severity HIGH/CRITICAL (weak/fabricated).
- Reference URL must resolve 200 OK + be in TRUSTED_DOMAINS.

### 2. TTS Voice Selection (P071)
- **EN/RU/AR:** Browser-native speechSynthesis (free, works on iOS Safari).
- **UZ/TJ:** OpenAI Nova API (browser voices don't exist for these languages).
- NEVER fall back to "tr-TR" Turkish for UZ — pronunciation diverges enough to confuse listeners.

### 3. Video Generation
- Use FFmpeg server-side, NEVER client-side WebCodecs (too inconsistent across iOS/Android).
- Background: gradient + Arabic calligraphy SVG overlay, NO copyrighted imagery.
- Duration: 15s minimum, 60s maximum for Shorts/Reels compatibility.
- Always include `alhamdulillah` ending fade.

### 4. CI Smart Push Gate (HR pattern — applies to all projects)
- TypeScript check on every push (warning only).
- Playwright tests block deploy if red.
- log-agent generates `bug-queue.json` artifact after every run.
- docs-agent auto-commits CHANGELOG.md on every push.
- language-agent (multilingual) runs manual dispatch only — expensive.

### 5. Source Authority
- Tier 1 only for reels: Sunnah.com, Dorar.net, HadeethEnc.com
- NEVER cite Tier 2/3 for published content.
- Always show source attribution overlay in final 3 seconds.

### 6. Multilingual Parity
- Same hadith in 5 languages MUST produce same authenticity verdict.
- TTS audio length: variance ≤ 20% between languages (or trim/extend).
- Subtitle timing synced per language (Arabic RTL-aware).

### 7. Cost Management
- OpenAI Nova TTS is ~$0.015/1k chars. Cap at $0.50/reel.
- Claude API: cache verification responses for 24h (same hadith).
- Use prompt caching (Anthropic) for repeat translations.

---

## 🧰 STACK & FILES

### Core
- `app/api/generate-reel/route.ts` — main orchestrator
- `app/api/verify-hadith/route.ts` — proxies to hadithverifier.com
- `app/api/tts/route.ts` — TTS routing (OpenAI Nova vs native)
- `app/api/render-video/route.ts` — FFmpeg pipeline
- `lib/tts-router.ts` — language → voice provider selection
- `lib/ffmpeg-pipeline.ts` — server-side video composition

### Components
- `components/ReelPreview.tsx` — live preview before publish
- `components/HadithEditor.tsx` — manual fine-tuning
- `components/LanguageSelector.tsx`
- `components/PublishPanel.tsx` — IG/TikTok/YouTube buttons

### Tests
- `tests/playwright/` — Playwright E2E
  - `authenticity-gate.spec.ts` — blocks weak hadiths
  - `tts-router.spec.ts` — UZ→Nova, EN→native
  - `multilingual-parity.spec.ts` — 5 languages produce same verdict
  - `video-render.spec.ts` — output duration, file size
- Multi-agent suite:
  - `agents/base-agent.ts`, `language-agent.ts`, `verify-agent.ts`
  - `agents/docs-agent.ts`, `log-agent.ts`, `fix-agent.ts`

### CI
- `.github/workflows/ci.yml` — smart push gate (5 jobs)
- HR was the FIRST project to implement this pattern. Idris adopted it later.

### Documentation
- `AGENTS.md` — agent orchestration + session log
- `CHANGELOG.md` — version history
- `FIX_PATTERNS.md` — patterns P050-P080 (HR-specific)
- `QA_STANDARDS.md` — copied from engineering-standards repo
- sourcing-pipeline-design.md — content sourcing / library-population pipeline (Phase 0+)

---

## 📋 PRE-FLIGHT CHECKLIST (Run at START of every session)

```bash
# 1. Read constitution
cat CLAUDE.md QA_STANDARDS.md FIX_PATTERNS.md AGENTS.md

# 2. Check repo state
git status
git log --oneline -5

# 3. Check upstream HV API
curl -s https://hadithverifier.com/api/health | jq

# 4. Verify TTS providers
node -e "console.log(process.env.OPENAI_API_KEY ? 'Nova ready' : 'MISSING NOVA KEY')"

# 5. Run smoke test
npm run test:smoke
```

---

## 🔁 STANDARD WORKFLOWS

### Workflow A — Fix a TTS bug
1. Identify language affected
2. Check `lib/tts-router.ts` — is correct provider selected?
3. Search FIX_PATTERNS.md for P0XX matching symptom
4. Add Playwright test reproducing the bug
5. Apply fix
6. Run `npm test`
7. Update FIX_PATTERNS.md if novel pattern
8. Commit: `fix(tts): description [P0XX]`

### Workflow B — Add a new language
1. Add to `lib/languages.ts` config
2. Decide TTS provider (browser-native or Nova)
3. Add translation to `lib/i18n/<lang>.json`
4. Add to multilingual parity test
5. Manually verify Arabic transliteration if non-Latin script
6. Update `language-agent.ts` to include new language project

### Workflow C — Multilingual audit
```bash
# Trigger language-agent suite (manual dispatch only)
npm run test:multilingual
# OR via GitHub Actions: workflow_dispatch with run_multiagent=true
```

### Workflow D — Pre-publish verification
1. authenticity-gate must pass (Sahih/Hasan only)
2. TTS audio generated for all 5 languages
3. Video file: 15-60s, <50MB
4. Captions synced (verified by `caption-sync.spec.ts`)
5. Source attribution overlay present in last 3s

---

## 🐛 BUG LOG (auto-updated by Claude Code)

<!-- Claude Code: prepend new bug entries below this line -->

## REFERENCE: Key HR Patterns

### P071: UZ/TJ browser TTS missing
**Symptom:** speechSynthesis returns no voice for `uz-UZ` or `tg-*`
**Root cause:** Browser TTS engines lack Central Asian language support
**Fix:** Route UZ/TJ to OpenAI Nova API. Never fall back to Turkish — pronunciation diverges.
**File:** `lib/tts-router.ts`

### P052: FFmpeg silent crash on Vercel
**Symptom:** Video generation works locally, returns 500 on Vercel
**Root cause:** Vercel serverless function 50MB unzipped limit; ffmpeg-static is 70MB
**Fix:** Use Railway worker for FFmpeg, Vercel only for orchestration

### P063: IG API rate limit
**Symptom:** First 10 publishes work, 11th onwards fail silently
**Fix:** Add `INSTAGRAM_RATE_LIMIT_DAILY=200` env, queue overflow to next day

### P058: Caption sync drift on Arabic
**Symptom:** Arabic captions appear before audio (RTL timing offset)
**Fix:** Apply -0.3s offset for RTL languages in subtitle generation

### P074: Severity cache stale after HV API update
**Symptom:** Cached AUTHENTIC verdict served after hadithverifier flagged the hadith
**Fix:** Cache TTL 24h max. Invalidate on webhook from HV admin queue.

---

## 🌐 KEY URLS

- Repo: https://github.com/Farhod75/hadith-reels
- CI: https://github.com/Farhod75/hadith-reels/actions
- Upstream API: https://hadithverifier.com
- Sources: Sunnah.com (primary), Dorar.net, HadeethEnc.com
- TTS: OpenAI Nova (UZ/TJ), browser native (EN/AR/RU)

---

## 🛠️ AUTO-LOGGING PROTOCOL

When Claude Code starts work, it MUST:

1. Before code changes — append `[WIP]` to BUG LOG with timestamp
2. After tests pass — update to `[DONE]` with pattern ID
3. If novel pattern — append to FIX_PATTERNS.md (P050-P099 range for HR)
4. At session end — append to AGENTS.md session log
5. Commit format: `<type>: <description> [P0XX]`

---

## 🕋 PHILOSOPHY

Sadaqah jariyah. No ads. No tracking.
Every reel must be authentic — better to publish 1 verified Sahih hadith than 10 unverified posts.
Quality > speed. Trust nothing without HV verification.
