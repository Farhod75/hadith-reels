# CLAUDE.md
# Project constitution for hadith-reels
# Auto-loaded by Claude Code on every session
# Last updated: 2026-08-23

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

### Two SEPARATE hazards, verified 2026-08-23 — encoding, not reversion
These are distinct from the revert above and have their own signatures. Both
destroyed a working file during one session.

- **`>>` and `Out-File` default to UTF-16LE in Windows PowerShell 5.1.**
  Appending one canary line to `.githooks/pre-push` grew it 3410 → 3571 bytes;
  git reclassified the file as `Bin` (`1 file changed, 0 insertions, 0 deletions`)
  and `/bin/sh` could no longer execute it. This silently destroys hooks, `.py`,
  `.sh`, and any file that must be plain text.
- **`Out-File -Encoding utf8` writes UTF-8 WITH BOM.** Python rejects a leading
  U+FEFF: `SyntaxError: invalid non-printable character U+FEFF`. The `utf8NoBOM`
  option exists only in PowerShell 7+, not in 5.1.
- **Safe on this machine:** `Copy-Item` (byte copy), VS Code, and
  `[System.IO.File]::WriteAllText($path, $text)`. Two Python agents were
  installed via `Copy-Item` on 2026-08-23 and persisted and committed normally,
  so the revert above does not affect every write path.
- **Verify after writing — never assume:**
  `python -c "d=open('<path>','rb').read(); print(len(d), d.count(b'\x00'), d[:4])"`
  Want: expected byte count, 0 nulls, and a sane first four bytes.
- **To confirm something is IN git, ask git for the CONTENT, not for a status:**
  `git show HEAD:<path> | Select-String <token>`
  An empty `git status` means the working file matches HEAD — which is also
  exactly what you get when your fix was never written to disk at all. That
  misreading cost a full debugging cycle on 2026-08-23 (see P119 correction).
- **Downloads can silently not happen.** A `Copy-Item` from `~/Downloads` will
  fail loudly if the file is absent, but if an OLD file of the same name is
  there it will succeed and install the wrong content. Check `LastWriteTime`.

### Git hooks
`core.hooksPath` MUST be `.githooks`. Check with `git config core.hooksPath`.
If it is empty, Git reads `.git/hooks/` instead and the tracked hook does
nothing. This was the state until 2026-08-23 and it is invisible from the
outside: an older copy in `.git/hooks/` runs and prints the same banner, so the
hook looks alive while every edit to the tracked file has no effect.
Set it with: `git config core.hooksPath .githooks`

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
- Multi-language: EN, RU, UZ, TJ. **AR is formally OUT OF SCOPE (P118)** — a
  lane that cannot be human-reviewed must not be produced.
- TTS narration — **ElevenLabs `eleven_v3` for all four languages** (P102/P104
  retired OpenAI and browser speechSynthesis; see HARD RULE 2)
- Auto-generated visuals: Kling animated scenes (adults lane) or scene-baked
  mascot stills (kids lane). No copyrighted imagery.
- One-tap publish to social platforms
- Severity validation: NEVER publishes weak or fabricated hadiths

---

## 🚨 HARD RULES (NEVER VIOLATE)

### 1. Authenticity Gate (CRITICAL)
- EVERY hadith MUST be verified Sahih or Hasan before TTS generation.
- ALWAYS call hadithverifier.com API first → only proceed if severity = "AUTHENTIC".
- NEVER publish hadiths with severity HIGH/CRITICAL (weak/fabricated).
- Reference URL must resolve 200 OK + be in TRUSTED_DOMAINS.

### 2. TTS Voice Selection (P071 → superseded by P102 / P104 / P118)
- **All four languages route to ElevenLabs `eleven_v3`.** OpenAI Nova and browser
  speechSynthesis are RETIRED — P071's routing no longer applies.
- Voice matrix: EN adults James · RU adults Marat (`vQxSi2EuaRWwBw3nn6dK`) ·
  UZ adults Opa Johann · TJ adults Meisam. Kids voices differ per language and
  per boy/girl mascot — see `reel-tracker.md` for the shipped assignment.
- **P118:** RU adults shipped twice narrated by Adam (American English) under an
  `Abrar` label. Verify the voice ID, never the label.
- NEVER fall back to "tr-TR" Turkish for UZ — pronunciation diverges enough to confuse listeners.
- **ﷺ glyph handling is PER-LANGUAGE, measured 2026-08-16:** EN, UZ and TJ all
  voice the raw glyph correctly. **RU does not** — expand it to
  «да благословит его Аллах и приветствует» before TTS, and expand «(р.а.)» to
  «да будет доволен им Аллах». No `cleanForTTS` change is needed for the other three.

### 3. Video Generation
- Use FFmpeg server-side, NEVER client-side WebCodecs (too inconsistent across iOS/Android).
- Background: Kling scenes or mascot stills, NO copyrighted imagery.
- Duration: 15s minimum, 60s maximum for Shorts/Reels compatibility.
- Always include `alhamdulillah` ending fade.

### 4. CI Smart Push Gate (HR pattern — applies to all projects)
- TypeScript check on every push.
- **Python check on every push where a `.py` changed (P119)** — `ast.parse` on each
  changed file, then the offline `scripts/lib` pytest suite. Before P119 there was
  no Python category at all: `.py` fell through to `npx tsc --noEmit`, which cannot
  read Python, and pushed green. All four agents were unprotected.
- Playwright tests block deploy if red.
- log-agent generates `bug-queue.json` artifact after every run.
- docs-agent auto-commits CHANGELOG.md on every push.
- language-agent (multilingual) runs manual dispatch only — expensive.

### 5. Source Authority
- Tier 1 only for reels: Sunnah.com, Dorar.net, HadeethEnc.com
- NEVER cite Tier 2/3 for published content.
- Always show source attribution overlay in final 3 seconds.

### 6. Multilingual Parity
- Same hadith in 4 languages MUST produce same authenticity verdict.
- TTS audio length: variance ≤ 20% between languages (or trim/extend).
  **Known breach:** the #527 adults set ran EN 66.4s / UZ 51.6s / RU 44.7s /
  TJ 39.8s — a 67% spread, with EN the outlier. Uzbek runs structurally longer
  than EN/RU/TJ because reported speech takes explicit «деди»/«дедим» tags.
- Subtitle timing synced per language. Subtitles are generated for EN/RU only
  (P078: Whisper returns Latin transliteration for UZ/TJ).

### 7. Cost Management
- ElevenLabs `eleven_v3` — cap at $0.50/reel of narration.
- Kling `v2.1/master` image-to-video is the expensive step: 4 scenes per hadith,
  reused across all four language reels. Never regenerate scenes per language.
- Claude API: cache verification responses for 24h (same hadith).
- Use prompt caching (Anthropic) for repeat translations.
- **Current API model string: `claude-sonnet-5`.** `claude-sonnet-4-5` and
  `claude-sonnet-4-6` are gone; `scripts/translate-tajik.ts` still hardcodes
  `claude-sonnet-4-5` and will fail if run — TODO.

---

## 🧰 STACK & FILES

### Core
- `app/api/generate-reel/route.ts` — main orchestrator
- `app/api/verify-hadith/route.ts` — proxies to hadithverifier.com
- `app/api/tts/route.ts` — TTS routing; writes narration straight into the work
  tree at `out/work/{style}/{slug}/{lang}/` (P106)
- `app/api/render-video/route.ts` — FFmpeg pipeline
- `lib/tts-router.ts` — language → voice provider selection
- `lib/ffmpeg-pipeline.ts` — server-side video composition

### Agents (Python, `scripts/`)
- `lint-content.py` — pre-TTS checks on GENERATED reel text (Workflow E)
- `stt-validate.py` — SRT vs source narration diff (Workflow F)
- `audit-assets.py` + `assets/asset-registry.json` — lane gate, BLOCKS renders (Workflow G)
- `audit-library.py` — per-language integrity checks on the DB rows (Workflow H)
- `translate-candidates.py` — Stage 2 of the sourcing pipeline (Workflow I)
- `source-candidates.py`, `upload-candidates.py`, `promote-candidates.py` — Stages 0/1/5
- `scripts/lib/` — sourcing modules + 49 offline pytest tests (no network)
- `scripts/lib/uzbek-translit.ts` — Cyrillic↔Latin, tested for okina vs tutuq.
  **Do not port to Python.** A second implementation drifts, and okina rules are
  exactly where drift corrupts silently.

### Components
- `components/ReelPreview.tsx` — live preview before publish
- `components/HadithEditor.tsx` — manual fine-tuning
- `components/LanguageSelector.tsx`
- `components/PublishPanel.tsx` — IG/TikTok/YouTube buttons

### Tests
- `tests/playwright/` — Playwright E2E
  - `authenticity-gate.spec.ts` — blocks weak hadiths
  - `tts-router.spec.ts` — routing per language
  - `multilingual-parity.spec.ts` — 4 languages produce same verdict
  - `video-render.spec.ts` — output duration, file size
- Multi-agent suite:
  - `agents/base-agent.ts`, `language-agent.ts`, `verify-agent.ts`
  - `agents/docs-agent.ts`, `log-agent.ts`, `fix-agent.ts`

### CI
- `.github/workflows/ci.yml` — smart push gate (5 jobs)
- `.githooks/pre-push` — local smart scanner. Requires `core.hooksPath=.githooks`.
- HR was the FIRST project to implement this pattern. Idris adopted it later.

### Documentation
- `AGENTS.md` — agent orchestration + session log
- `CHANGELOG.md` — version history
- `fix_patterns.md` — patterns P046–P119 (HR-specific). **P-numbers are ONE
  GLOBAL SEQUENCE shared with HV** — the same P-number is the same fix in both
  repos. Never renumber per project. Verify the frontier in BOTH repos before
  assigning: `git grep -n "^\*\*ID:\*\* P1[01][0-9]" fix_patterns.md`
- `QA_STANDARDS.md` — copied from engineering-standards repo
- `sourcing-pipeline-design.md` — content sourcing / library-population pipeline.
  Written 2026-06-14 and NOT updated since; read it as a proposal to validate,
  not a current spec.
- `reel-tracker.md` — every reel shipped, with the defects found in each

---

## 📋 PRE-FLIGHT CHECKLIST (Run at START of every session)

```bash
# 1. Read constitution
cat CLAUDE.md QA_STANDARDS.md fix_patterns.md AGENTS.md

# 2. Check repo state
git status
git log --oneline -5

# 3. Confirm the hook is actually wired
git config core.hooksPath          # must print .githooks

# 4. Check upstream HV API
curl -s https://hadithverifier.com/api/health | jq

# 5. Run smoke test
npm run test:smoke
```

---

## 🔁 STANDARD WORKFLOWS

### Workflow A — Fix a TTS bug
1. Identify language affected
2. Check `lib/tts-router.ts` — is correct provider selected?
3. Search fix_patterns.md for P0XX matching symptom
4. Add Playwright test reproducing the bug
5. Apply fix
6. Run `npm test`
7. Update fix_patterns.md if novel pattern
8. Commit: `fix(tts): description [P0XX]`

### Workflow B — Add a new language
1. Add to `lib/languages.ts` config
2. Decide TTS voice (ElevenLabs voice ID — verify the ID, not the label)
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
2. TTS audio generated for all 4 languages
3. Video file: 15-60s, <50MB
4. Captions synced (verified by `caption-sync.spec.ts`)
5. Source attribution overlay present in last 3s

### Workflow E — Lint generated reel text before TTS
1. Generate story/moral/seerah in the admin
2. Save the S:/M:/H:/C: blocks to `draft.txt` (gitignored)
3. Pull the matn: `select text_<lang> from hadith_library where ...`
4. Run: `python scripts\lint-content.py draft.txt --lang <lang> --matn "<matn>"`
5. Read every FAIL and WARN — they are heuristics, not verdicts
6. Fix in the admin, re-lint, then generate TTS
7. **Re-sync `draft.txt` after ANY edit made in the admin.** Workflow F compares
   the SRT against this file; a stale draft produces false mismatches and, worse,
   means the text that actually shipped was never linted in its final form.
8. A clean run means these five checks passed. It does NOT mean the text is
   correct — read it yourself. Human review is still the gate.

### Workflow F — Validate subtitles at the render gate
1. `render-reel.ps1` pauses at "REVIEW SUBTITLES before they are burned"
2. In a second terminal, run:
   `python scripts\stt-validate.py --srt "<srt>" --source draft.txt --lang <lang> --narration "<mp3>"`
3. `draft.txt` must hold the SAME language's S:/M: blocks as the SRT — a
   mismatch shows as ~0.01 similarity
4. Fix every HIGH in VS Code, save, then press ENTER at the gate
5. Type Cyrillic corrections on a Cyrillic layout — Latin homoglyphs are
   invisible on screen and the check exists because they shipped once
6. **Run this AT the gate, not after the render.** Running it afterwards means a
   defect is already burned into the MP4 and the reel must be re-rendered.
7. Warn-only. A clean run means these checks passed, not that the subtitles are
   correct — read them

### Workflow G — Adding an asset to the library
1. Put the file in `out/backgrounds/`, `assets/mascot/`, or
   `out/backgrounds/new/normalized/`
2. LISTEN to it or VIEW it. A search term is not a verification.
3. Add an entry to `assets/asset-registry.json`: classification, lanes,
   `verified: true`, and why
4. `python scripts\audit-assets.py --audit` — should report zero unregistered
5. An asset absent from the registry will BLOCK the render, by design

### Workflow H — Audit the library before a sourcing batch
1. `python scripts\audit-library.py` — all rows in `hadith_library`
2. Or one row: `--row 527`  ·  candidates: `--table hadith_candidates`
3. Read every HIGH — those are defects in the SOURCE ROW, and every reel
   made from that row inherits them
4. HIGH: Tajik column is a Russian copy (P050) · Latin homoglyph inside a
   Cyrillic word (R027) · grade outside sahih/hasan
5. WARN: wrong okina in Uzbek (R024) · Latin/Cyrillic mixed between the two
   Uzbek columns (R036) · missing or homepage-only source URL
6. INFO: empty language fields (which rows cannot make a 4-language set) ·
   long Tajik text with no Tajik-specific letters
7. Read-only — it never edits. Fix in Supabase, re-run
8. `--strict` exits 1 on any HIGH, for use as a gate later
9. Run it after ANY manual DB edit. lint-content.py cannot see these defects:
   it reads generated reel text, and the generator paraphrases, so the DB
   sentence never appears verbatim in draft.txt

### Workflow I — Stage 2: translate sourced candidates
1. Candidates must be at `status='deduped'` with `text_arabic` present
2. Dry run first: `python scripts\translate-candidates.py --limit 10`
3. Read `out\candidate-translations.json` — the full text, not the previews
4. Check against the Arabic: did anything get ADDED? A clause, an attribution,
   a ranking, a comparison. The matn is the only thing the translation may say
5. Any `[UNCERTAIN: ...]` marker is the model abstaining — that field needs a
   human, not a retry
6. `--commit` writes and sets `status='translated'`
7. `text_uzbek_latin` stays empty — derive it from the canonical Cyrillic with
   `scripts/lib/uzbek-translit.ts` (`deriveBothScripts`), which is tested for
   okina vs tutuq. Do not transliterate by hand
8. ALWAYS from `text_arabic`. Never from another language column — P075 built
   the current Tajik by translating text_uzbek, and «Неки» for «Некӣ» (R037)
   is what that produces

### Workflow J — Produce an animated adults reel (scene lane)
1. Verify the DB row first: grade, all four language texts, diacritics
2. Generate text in the admin → `draft.txt` → Workflow E
3. TTS per language — the route writes into the work tree (P106); nothing to download
4. Four NEW Kling scenes per hadith, MODE B (no figures), drawn from settings the
   matn implies — never from imagery it does not contain (P111 rule 14):
   `.\scripts\generate-image.ps1 -Name "<slug>-<scene>" -Count 3 -Prompt "..."`
   review the stills, then
   `.\scripts\generate-scene.ps1 -Name "<slug>-<scene>" -Image "out\refs\<pick>.jpg" -Duration 10 -Prompt "<MOTION only>"`
5. **Move the clips:** `generate-scene.ps1` writes to `out\backgrounds\new\`, but
   `render-reel.ps1 -Scenes` reads from `out\backgrounds\new\normalized\`. This
   undocumented manual step has blocked three separate sets (June #1520,
   8/11 #1, 8/16 #527). `Move-Item out\backgrounds\new\<slug>-*.mp4 out\backgrounds\new\normalized\`
6. **Kling can exceed the hook's 8-minute poll deadline** (one #527 scene took
   505s against a 480s limit). The job usually COMPLETES server-side — recover it
   rather than paying twice:
   `Invoke-RestMethod -Uri "https://queue.fal.run/fal-ai/kling-video/requests/<id>" -Headers @{Authorization="Key $key"}`
   then download `$r.video.url`.
7. `.\render-reel.ps1 -Style adults -Lang <lang> -Slug <slug> -Scenes a.mp4,b.mp4,c.mp4,d.mp4 -Open`
8. Reuse the same four scenes for all four languages — never regenerate per language
9. Update `reel-tracker.md` after the COMPLETE set ships, not per reel

---

## 🐛 BUG LOG (auto-updated by Claude Code)

<!-- Claude Code: prepend new bug entries below this line -->

## REFERENCE: Key HR Patterns

### P119: Pre-push hook blind to Python, and pointed at nothing
**Symptom:** 404 lines of new Python pushed with `Doc=3` and a TypeScript check
**Root cause:** no `.py` category, so it fell through to `tsc`; and `core.hooksPath`
was unset, so the tracked hook never ran at all
**Fix:** `PY_PATTERNS` + `ast.parse` + pytest branch; `git config core.hooksPath .githooks`
**Lesson:** a gate is not proven by passing — it is proven by failing on demand

### P111 / P115 / P116: the model finds the adjacent exit
**Pattern:** forbid invented FACT and it invents COMPARISON; forbid comparison and
it invents SOURCE; forbid source and it invents IMPORTANCE. Length pressure is
fabrication pressure. Ask what remains sayable that is not checkable against the matn.

### P071: UZ/TJ browser TTS missing — SUPERSEDED
**Was:** route UZ/TJ to OpenAI Nova. **Now:** all languages use ElevenLabs
`eleven_v3` (P102/P104). Kept here because the routing note misled a later session.

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

### P079: admin story field not editable — STILL OPEN
Generated titles cannot be corrected in place. Workaround: fix in the caption.
Bit the TJ #527 reel, where the generated title was ungrammatical.

---

## 🌐 KEY URLS

- Repo: https://github.com/Farhod75/hadith-reels
- CI: https://github.com/Farhod75/hadith-reels/actions
- Upstream API: https://hadithverifier.com
- Sources: Sunnah.com (primary), Dorar.net, HadeethEnc.com
- Sunnah.com API access request: github.com/sunnah-com/api/issues/3675 (open)
- TTS: ElevenLabs `eleven_v3`, all four languages

---

## 🛠️ AUTO-LOGGING PROTOCOL

When Claude Code starts work, it MUST:

1. Before code changes — append `[WIP]` to BUG LOG with timestamp
2. After tests pass — update to `[DONE]` with pattern ID
3. If novel pattern — append to fix_patterns.md (ONE global P-sequence with HV —
   verify the frontier in BOTH repos before assigning)
4. At session end — append to AGENTS.md session log
5. Commit format: `<type>: <description> [P0XX]`

---

## 🕋 PHILOSOPHY

Sadaqah jariyah. No ads. No tracking.
Every reel must be authentic — better to publish 1 verified Sahih hadith than 10 unverified posts.
Quality > speed. Trust nothing without HV verification.
