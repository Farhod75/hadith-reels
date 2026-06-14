## ════════════════════════════════════════════════════════
## PATTERN 46: HR ci.yml had language-speech real API step
## ════════════════════════════════════════════════════════
**ID:** P046
**Type:** CI architecture fix
**File:** hadith-reels/.github/workflows/ci.yml
**Commit:** fix: correct ci.yml — remove language-speech, add mocked E2E spec (P046)

**Symptom:** All HR CI runs #1-5 failed
**Root cause:** ci.yml step called tests/language-speech.spec.ts which
  calls real ElevenLabs API — non-deterministic, always flaky in CI.
  Also no spec file existed → "No tests found" error.
**Fix:** Remove language-speech step. Add tests/hadith-reels.spec.ts (mocked).
  Add playwright.config.ts. Install @playwright/test.
**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 47: Tab button locator breaks with emoji text
## ════════════════════════════════════════════════════════
**ID:** P047
**Type:** Test fix (locator resilience)
**File:** tests/hadith-reels.spec.ts
**Commit:** fix: resilient tab button locators for emoji text (P047)

**Symptom:** CI #7, #8 — "should show Browse hadiths tab" fails
  locator('button').filter({ hasText: /browse/i }) times out 5000ms
**Root cause:** Tab buttons render as "📚 Browse hadiths" — emoji creates
  a separate text node in headless Chromium. filter({ hasText }) and
  getByText() both fail to match because the emoji interrupts the string.
**Fix attempted:** Switch to locator('button').filter() — still failed.
**Better fix (P048):** Don't test tab labels at all — test functionality.
**Status:** SUPERSEDED by P048

## ════════════════════════════════════════════════════════
## PATTERN 48: Never test emoji tab labels — test functionality
## ════════════════════════════════════════════════════════
**ID:** P048
**Type:** Test architecture fix (test what matters)
**File:** tests/hadith-reels.spec.ts
**Commit:** fix: test tab functionality not emoji label text (P048)

**Symptom:** CI #7, #8 — same Browse tab test fails despite different locators
**Root cause:** The test was asserting UI LABEL TEXT ("Browse hadiths")
  not the FUNCTIONALITY (hadiths actually load and display).
  Emoji characters in tab labels are non-deterministic in headless CI.
  This is a test DESIGN problem, not a locator problem.

**Rule (ISTQB CT-AI — test what matters):**
  NEVER write tests that assert UI label text containing emojis.
  ALWAYS test the functional outcome instead:
  - Tab loads → test that content appears, not that tab label is visible
  - Button exists → test what happens when clicked, not button text

**Fix pattern:**
```ts
// WRONG — fragile emoji label test:
await expect(page.locator('button').filter({ hasText: /browse/i })).toBeVisible()

// RIGHT — test functional outcome:
await page.waitForSelector('text=/Fasting is a shield/i', { timeout: 10000 })
await expect(page.getByText(/Fasting is a shield/i).first()).toBeVisible()

// RIGHT — click tab via evaluate() for emoji buttons:
await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.textContent?.toLowerCase().includes('watch'))
  btn?.click()
})
```

**Watch tab navigation:** Use page.evaluate() to find button by
  partial textContent — bypasses emoji rendering issues entirely.

**Scoped to header:** For lang buttons (EN/UZ/AR/RU/TJ) — scope to
  header element to avoid false matches in hadith content:
  page.locator('header').locator('button', { hasText: 'EN' })

**Status:** FIXED — CI #9 ✅

## ════════════════════════════════════════════════════════
## PATTERN 49: Dual Seerah sources for UZ/TJ/RU vs AR/EN
## ════════════════════════════════════════════════════════
**ID:** P049
**Type:** Feature enhancement (content quality)
**File:** app/api/generate-reel/route.ts
**Commit:** feat: dual seerah sources — Uswa al-Hasana for UZ/TJ/RU (P049)

**Why:**
  Ar-Raheeq Al-Makhtum is the authoritative English/Arabic Seerah but
  its style is scholarly and historical. For Uzbek, Tajik and Russian
  audiences, Uswa al-Hasana (Усваи Хасана) — the Turkish multi-volume
  Seerah translated into Russian/Uzbek — is more culturally appropriate:
  - Emotional and devotional tone
  - Strong emphasis on love for the Prophet ﷺ
  - Better for social media engagement in Central Asian/Russian audience
  - Already familiar to Uzbek and Tajik Muslim communities

**Implementation:**
  getSeerahSource(lang) returns source name + description + attribution:
  - AR/EN → Ar-Raheeq Al-Makhtum (Safiur Rahman al-Mubarakpuri)
  - UZ/TJ/RU → Uswa al-Hasana (Усваи Хасана)

**Status:** IMPLEMENTED

## ════════════════════════════════════════════════════════
## PATTERN 50: TJ (Tajik) — no text_tajik column in DB
## ════════════════════════════════════════════════════════
**ID:** P050
**Type:** Language handling clarification
**File:** app/api/reels/route.ts
**Commit:** fix: TJ display uses Russian fallback, narration in Tajik (P050)

**Symptom:** When TJ selected, hadiths show Russian text — looks like a bug
**Explanation — NOT a bug:**
  hadith_library has: text_arabic, text_english, text_uzbek, text_russian
  NO text_tajik column exists. Russian text is the correct fallback for TJ.
**Status:** DOCUMENTED — working as designed

## ════════════════════════════════════════════════════════
## PATTERN 54: @remotion/renderer native binaries break Next.js build
## ════════════════════════════════════════════════════════
**ID:** P054
**Type:** Build fix (native module externalization)
**Files:** next.config.js, app/api/render-reel/route.ts
**Commit:** fix: externalize Remotion from Next.js build — native binaries (P054)

**Symptom:** CI #18 fails — "Module not found: @remotion/compositor-win32-x64-msvc"
**Root cause:** Remotion uses platform-specific native binaries. Next.js webpack
  tries to bundle ALL platforms. Linux CI runner fails on Windows binary.
**Fix:** Externalize all Remotion packages in next.config.js. Detect VERCEL
  env in render-reel route → return 501 with local render instructions.
**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 62: $env:BASE_URL session variable overrides playwright config
## ════════════════════════════════════════════════════════
**ID:** P062
**Type:** Test environment bug (session variable pollution)
**File:** tests/hadith-reels.spec.ts, playwright.config.ts
**Commit:** fix: Watch tab click via evaluate() for emoji button — P048 (P063)
**Date:** May 13 2026 — HR CI #24

**Symptom:**
  All 25 tests failing locally. Playwright opens hadithverifier.com (production)
  instead of localhost:3002. h1 shows "Hadith Verifier" not "Hadith Reels".
  Tests time out immediately trying to find elements that don't exist on HV.

**Root cause:**
  $env:BASE_URL was set to "https://hadithverifier.com" in the PowerShell
  session from a previous HV audit test run:
    $env:BASE_URL="https://hadithverifier.com"  ← set earlier, never cleared
  playwright.config.ts reads: process.env.BASE_URL || 'http://localhost:3002'
  Since BASE_URL was set → Playwright used hadithverifier.com for all tests.
  This affected ALL test runs in the same terminal session.

**Fix:**
  Clear the env var before running HR tests:
    $env:BASE_URL = ""
  Confirm it's cleared:
    echo $env:BASE_URL  ← should print nothing

**Rule going forward:**
  ALWAYS clear $env:BASE_URL before switching between HV and HR test runs.
  Add to pre-push hook: explicit BASE_URL=http://localhost:3002 passed to
  Playwright so session variables cannot override it.

**Prevention:**
  Pre-push hook now passes BASE_URL explicitly:
    BASE_URL=http://localhost:3002 npx playwright test ...
  This makes the hook immune to session variable pollution.

**Status:** FIXED — CI #24 ✅

## ════════════════════════════════════════════════════════
## PATTERN 63: Watch tab emoji button — all locator strategies fail
## ════════════════════════════════════════════════════════
**ID:** P063
**Type:** Test fix (emoji button click)
**File:** tests/hadith-reels.spec.ts
**Commit:** fix: Watch tab click via evaluate() for emoji button — P048 (P063)
**Date:** May 13 2026 — HR CI #24

**Symptom:**
  Watch tab tests timeout on button click. Tried all strategies:
  1. page.locator('button').filter({ hasText: /Watch reels/i }) → timeout
  2. page.getByRole('button', { name: /Watch reels/i }) → timeout
  3. page.getByText('🎬 Watch reels', { exact: true }) → timeout
  All fail because emoji "🎬" creates separate text node in headless Chromium.

**Root cause:**
  Button renders as: <button>🎬<!-- --> <!-- -->Watch reels</button>
  The emoji + HTML comment nodes + space break ALL Playwright text matchers.
  This is the same root cause as P047/P048 — emoji text nodes are
  non-deterministic in headless Chromium.

**Fix — page.evaluate() only reliable approach:**
```ts
await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.textContent?.toLowerCase().includes('watch'))
  btn?.click()
})
```
  evaluate() runs in browser context → accesses raw textContent →
  emoji rendering doesn't affect textContent string matching.

**Rule (extends P048):**
  For ANY button containing emoji + text: ALWAYS use page.evaluate()
  Never use: getByText(), getByRole(), filter({ hasText }) for emoji buttons.

**Status:** FIXED — CI #24 ✅ — 25/25 tests passing

## ════════════════════════════════════════════════════════
## PATTERN 64: Admin page Telegram button hidden — wrong step
## ════════════════════════════════════════════════════════
**ID:** P064
**Type:** UX clarification (not a bug)
**File:** app/admin/page.tsx
**Date:** May 13 2026

**Symptom:**
  "Post to Telegram" button appears to redirect to telegram.org home page.
  User unable to find the API-based post button.

**Root cause — two separate Telegram elements on Step 3:**
  1. "Telegram Channel / Open ↗" — link button → opens t.me/SahihHadithReels
     in browser. If channel doesn't exist in Telegram app → redirects to home.
  2. "✈️ Post to Telegram channel" — actual API button → calls /api/telegram/post

  User was clicking element #1 (the link), not element #2 (the API button).
  Element #2 is in a separate "📤 Publish to Telegram" section, below the
  platform links, and requires scrolling on smaller screens.

**Fix applied:**
  No code change needed. User workflow clarified:
  Step 3 → scroll down past Instagram/TikTok/YouTube/Telegram links
  → find "📤 Publish to Telegram" section → click "✈️ Post to Telegram channel"

**Future improvement:**
  Rename "Telegram Channel / Open ↗" to "Open @SahihHadithReels" to avoid
  confusion with the API post button.

**Status:** DOCUMENTED — working as designed

## ════════════════════════════════════════════════════════
## PATTERN 65: Vercel served cached old admin page after new commit
## ════════════════════════════════════════════════════════
**ID:** P065
**Type:** Deployment issue (Vercel build cache)
**File:** app/admin/page.tsx
**Date:** May 13 2026

**Symptom:**
  New app/admin/page.tsx with "✈️ Post to Telegram channel" button committed
  in feat: admin studio full pipeline (commit 3fb5f53). Vercel showed ✅ Ready.
  But admin page still showed old UI — "Auto-posting via Buffer API coming Phase 3"
  instead of the new Telegram post button.

**Root cause:**
  Vercel build cache served the old compiled page.tsx even after new commit.
  The /api/telegram/post route deployed correctly (returned 400 on test) but
  the admin page component was cached.

**Fix:**
  Force redeploy with empty commit:
    git commit --allow-empty -m "chore: trigger Vercel redeploy for admin page update"
    git push origin main
  After redeploy: hard refresh browser (Ctrl+Shift+R) to clear client cache.

**Rule going forward:**
  After deploying UI component changes, always verify in production with
  hard refresh. If UI doesn't match code → force empty commit redeploy.
  Check /api/ routes separately from UI components — they may deploy at
  different times from the same commit.

**Status:** FIXED — admin page now shows correct UI with Telegram post button

## ════════════════════════════════════════════════════════
## MILESTONE: Telegram channel @SahihHadithReels launched
## ════════════════════════════════════════════════════════
**Date:** May 13 2026
**HR CI:** #24 ✅ green
**HV CI:** #150 ✅ green

**What was accomplished:**
- Telegram channel @SahihHadithReels created
- Bot @hadith_verifier_alert_bot added as admin
- Vercel env vars added: TELEGRAM_ALERT_BOT_TOKEN, TELEGRAM_CHANNEL_CHAT_ID
- app/admin/page.tsx updated with full Telegram post pipeline
- app/api/telegram/post/route.ts deployed and working
- First text post sent successfully (Russian hadith)
- Background images downloaded for Remotion compositions:
  public/backgrounds/kaaba.jpg, madinah.jpg, desert.jpg, stars.jpg, mosque.jpg
- First MP4 rendered locally: out/adults.mp4 (5.7 MB, h264)
- 25 Playwright tests passing ✅
- HR CI #24 green ✅

**Next phase:**
- P066: Automated multi-language reel pipeline (4 langs × 2 styles)
- Background images committed to repo
- Remotion render with audio narration (ElevenLabs)
- AI video tools evaluation (Runway ML API)

## ════════════════════════════════════════════════════════
## PATTERN 67: @fal-ai/client SDK breaks Turbopack CI build
## ════════════════════════════════════════════════════════
**ID:** P067
**Type:** Build fix (SDK → direct REST API)
**Files:** app/api/generate-video/route.ts, next.config.js
**Commit:** fix: fal.ai direct REST API + CSP headers (P067)
**Date:** May 13 2026 — HR CI #30

**Symptom:** CI build fails — "Cannot find module '@fal-ai/client'"
  Even with serverExternalPackages and dynamic import — Turbopack
  still tries to resolve the module at build time in CI Ubuntu runner.

**Fix:** Remove @fal-ai/client SDK entirely. Use direct fetch() calls
  to fal.ai REST API: queue.fal.run
  No imports = no bundling issues. Works in CI and locally.

**Also:** Added fal.ai domains to CSP connect-src in next.config.js:
  https://queue.fal.run https://v3b.fal.media

**Voice updates:**
  EN adults: James — EkK5I93UQWFDigLMpZcX (husky, bold, narration)
  EN kids:   Danielle — FVQMzxJGPUBtfz1Azdoy (gentle, engaging)

**Rule going forward:**
  Never import heavy SDK packages in Next.js API routes.
  Always prefer direct fetch() to REST APIs — no bundling issues,
  smaller bundle, works in all environments.

**Status:** FIXED — CI #30 ✅
## ════════════════════════════════════════════════════════
## PATTERN 68: hadithreels.com domain registered + connected
## ════════════════════════════════════════════════════════
**ID:** P068
**Type:** Infrastructure + deployment
**Files:** next.config.js, scripts/merge-reel.js, HV app/page.tsx
**Date:** May 13 2026 — HR CI #32, HV CI #151

**What was done:**
- Registered hadithreels.com on Namecheap — $11.48/yr
- Connected to Vercel via ns1/ns2.vercel-dns.com nameservers
- Both hadithreels.com and www.hadithreels.com → Valid Configuration
- Updated CSP connect-src to include hadithreels.com
- Updated merge-reel.js watermark from vercel.app to hadithreels.com
- Updated HV cross-link banner from hadith-reels.vercel.app to hadithreels.com

**Rule going forward:**
  Always use hadithreels.com in all references.
  Never use hadith-reels.vercel.app in user-facing content.

**Status:** FIXED — both CIs green ✅

## ════════════════════════════════════════════════════════
## PATTERN 69: Complete reel production template finalized
## ════════════════════════════════════════════════════════
**ID:** P069
**Type:** Feature complete — production template
**Date:** May 13 2026

**Final reel template:**
- fal.ai Kling video (10sec, looped via -stream_loop -1)
- ElevenLabs James voice narration (EN adults)
- Whisper SRT subtitles (small model, 35 char width)
- Background nasheed at volume=0.25
- Hadith transliteration drawtext at top (fontsize=36)
- Source reference drawtext at bottom (fontsize=16)
- Output: h264 MP4, ~7.5MB, 34sec

**FFmpeg filter chain:**
  [narration][music]amix → volume 1.0 narration + 0.25 music
  subtitles SRT → MarginV=80
  drawtext hadith name → y=40
  drawtext source → y=h-30

**Voice matrix confirmed:**
  EN adults: James EkK5I93UQWFDigLMpZcX
  EN kids:   Danielle FVQMzxJGPUBtfz1Azdoy

**Background assets:**
  out/backgrounds/mosque.mp4 — intro scene
  out/backgrounds/nasheed-bg-1.mp3 — background music

**Status:** PRODUCTION READY ✅

## ════════════════════════════════════════════════════════
## PATTERN 70: TTS text cleaning + UZ/TJ kids voice fix
## ════════════════════════════════════════════════════════
**ID:** P070
**Type:** Feature fix (TTS quality)
**Files:** app/api/tts/route.ts, app/admin/page.tsx
**Commit:** fix: TTS text cleaning Prophet name + Danielle for UZ/TJ kids (P070)
**Date:** May 14 2026 — HR CI #37

**Fixes:**
1. Prophet ﷺ symbol not pronounced by ElevenLabs
   → cleanForTTS() replaces ﷺ, p.b.u.h, (pbuh), (saw) with
     "peace be upon him" (EN) or "صلى الله عليه وسلم" (AR)
2. UZ kids voice was Abrar Sabbah (harsh, rude accent)
   → Changed to Danielle FVQMzxJGPUBtfz1Azdoy (gentle, warm)
3. TJ kids voice also updated to Danielle
4. Back button added to Step 3 Preview
   → setStep('pick') + setGenerated(null) resets without page refresh

**Voice matrix final:**
  EN adults: James    EkK5I93UQWFDigLMpZcX
  EN kids:   Danielle FVQMzxJGPUBtfz1Azdoy
  UZ adults: Abrar    ErXwobaYiN019PkySvjV
  UZ kids:   Danielle FVQMzxJGPUBtfz1Azdoy
  RU adults: Abrar    ErXwobaYiN019PkySvjV
  RU kids:   Abrar    ErXwobaYiN019PkySvjV
  AR adults: Hijazi   pNInz6obpgDQGcFmaJgB
  TJ adults: Abrar    ErXwobaYiN019PkySvjV
  TJ kids:   Danielle FVQMzxJGPUBtfz1Azdoy

**Status:** FIXED — CI #37 ✅

## ════════════════════════════════════════════════════════
## PATTERN 71: OpenAI Nova TTS for UZ/TJ Cyrillic
## ════════════════════════════════════════════════════════
**ID:** P071
**Type:** Feature — dual TTS provider routing
**File:** app/api/tts/route.ts
**Date:** May 14 2026 — HR CI #41

**Problem:** ElevenLabs Abrar voice has harsh accent for UZ/TJ
  Cyrillic text. Prophet ﷺ read as "p.b.u.h" in English.

**Fix:**
  1. Route UZ/TJ to OpenAI TTS (Nova/Onyx voices)
     - Nova for kids (warm, friendly)
     - Onyx for adults (deep, authoritative)
  2. cleanForTTS() replaces ﷺ with language-specific phrase:
     - UZ: Саллаллоҳу алайҳи васаллам
     - TJ: Салаллоҳу алайҳи васаллам
     - RU: Да благословит его Аллах и приветствует
     - AR: صلى الله عليه وسلم
     - EN: peace be upon him

**Provider routing:**
  UZ → OpenAI Nova/Onyx
  TJ → OpenAI Nova/Onyx
  EN → ElevenLabs James/Danielle
  AR → ElevenLabs Hijazi/Abu Salem
  RU → ElevenLabs Abrar

**Status:** FIXED — CI #41 ✅# HR Fix Patterns — append P072 through P075 to existing hr-fix-patterns.md

Append these entries at the END of the existing `hr-fix-patterns.md` file.
Do NOT replace the file — only append.

---

## P072 — `.env.local` dotenv comment-character silent truncation

**Symptom:** Admin login returns 401 "Invalid password"; OpenAI TTS route returns auth error despite key being "set". Byte inspection of `.env.local` shows correct value, but `process.env.<KEY>.length` at runtime is shorter than expected.

**Root cause:** dotenv parser treats unquoted `#` as start-of-comment. Everything from `#` to end-of-line is discarded silently. Affects any value containing `#` — common in passwords, some API keys, complex secrets.

**Example:** `ADMIN_PASSWORD=HR@Admin#Farhod75` was parsed as `HR@Admin` (8 bytes), truncating `#Farhod75` as comment.

**Fix:** Wrap the value in double quotes:
```
ADMIN_PASSWORD="HR@Admin#Farhod75"
```

**Detection:** Add temporary logging in the consuming route to print `process.env.<KEY>.length` and `Buffer.from(value).join(',')`. Compare to expected bytes. If env length < file length and the difference aligns with a `#` in the value, this is the bug.

**Prevention:** Default to quoting all `.env.local` values whose plain contents include any of: `#`, `$`, `'`, `"`, leading/trailing space, backtick. Or quote everything by convention.

**Related:** Browser-extension hydration mismatch (this same session), tsconfig.json BOM corruption.

**Status:** FIXED — May 15, 2026

---

## P073 — Browser-extension hydration warning on `<html>` and form elements

**Symptom:** Console floods with "A tree hydrated but some attributes of the server rendered HTML didn't match the client properties" error. References to `katalonextensionid`, `toscacontainsshadowdom`, `fdprocessedid` in the React stack.

**Root cause:** Browser extensions (Katalon Recorder, Tricentis Tosca, password managers) inject attributes into the DOM before React hydrates. These are SDET tooling extensions installed for QA work that pollute admin pages.

**Fix:** Add `suppressHydrationWarning` to four elements:
- `<html lang="en" suppressHydrationWarning>` in `app/layout.tsx`
- `<body className={inter.className} suppressHydrationWarning>` in `app/layout.tsx`
- `<input type="password" suppressHydrationWarning />` in `app/admin/page.tsx`
- `<button onClick={handleLogin} suppressHydrationWarning>Enter Studio</button>` in `app/admin/page.tsx`

`suppressHydrationWarning` only suppresses one level deep — it doesn't hide real bugs nested inside.

**Verification:** After fix, the hydration warning block disappears from Console. Viewport/themeColor warnings remain (unrelated, separate issue).

**Caveat — file delivery:** During this fix, partial code snippets with `...` placeholders were used in instructions and they got copy-pasted literally into JSX, breaking the build. Lesson: NEVER use `...` placeholder in delivered artifacts. See AGENTS_ADDENDUM.md File Delivery Protocol.

**Status:** FIXED — May 15, 2026

---

## P074 — OpenAI `tts-1` Russian-Cyrillic phonetic bias for UZ/TJ narration

**Symptom:** OpenAI Nova/Onyx narrating Uzbek or Tajik Cyrillic text pronounces letters using Russian phonetic patterns:
- `ҳ` (aspirated h, like Arabic ح) → reads as Russian `х`
- `қ` (deep uvular k, like Arabic ق) → reads as Russian `к`
- `ў` (Uzbek o-with-breve) → mispronounced
- `ғ` (voiced uvular g) → mispronounced
- `ж` (Uzbek "j" in "judge") → reads as Russian "zh" / "dzh"

Native speakers immediately identify the narration as non-native.

**Root cause:** OpenAI `tts-1` model has strong Russian-Cyrillic phonetic prior. Cannot be overridden by text alone. OpenAI TTS does not support SSML `<phoneme>` tags.

**Fix:** Migrate from `tts-1` to `gpt-4o-mini-tts` model + use the `instructions` parameter (which `tts-1` does not support) for per-language phonetic guidance.

Implementation in `app/api/tts/route.ts`:

1. Add `TTS_INSTRUCTIONS` constant keyed by `${lang}.${style}` with explicit phonetic instructions per language pair (uz.kids, uz.adults, tj.kids, tj.adults).
2. Change OpenAI request body:
   - `model: 'tts-1'` → `model: 'gpt-4o-mini-tts'`
   - Add `instructions: TTS_INSTRUCTIONS[langKey][style]`

Example UZ kids instruction (with concrete examples for stubborn letters):
```
"Speak as a native Uzbek (O'zbek) speaker reading to children. Use warm, gentle, joyful tone. Pronounce these Uzbek Cyrillic letters precisely: ҳ as aspirated h (like in 'house', not Russian х); қ as deep uvular k from back of throat (like Arabic ق, not Russian к) — pronounce қ consistently strong whether at start, middle, or end of word; ў as 'o' sound in 'go'; ғ as voiced uvular g (like Arabic غ); ж as English 'j' in 'judge' or 'jim' (single soft J sound, NOT 'dzh' with hard D onset, NOT French 'zh'). Example pronunciations: жилмайиб = 'JIL-mai-ib' (start with soft English J, no D); иссиқ = 'is-SEEQ' (strong throat-back Q at end, NOT soft K); қуёшдек = 'qu-yosh-DEK' (strong Q at start). Place word stress on the final syllable per Uzbek convention. Do not use Russian phonetic patterns."
```

**Effectiveness:** Significant improvement but NOT perfect. Approximately 80-90% of letters now correct. Persistent issues observed:
- Final-position қ in some words (иссиқ) still occasionally weak
- ж in некоторых positions still sometimes hard "dzh"

**v2 plan (post-Hajj):** Voice cloning via ElevenLabs Professional Voice Clone using native speaker recordings — this is the permanent fix. Phonetic substitution via PPD (Supabase table) as backup. See `hr-ppd-spec.md` for design.

**Reference research:** Speechmatics semantic word error rate paper — Whisper-class WER misses meaning-altering pronunciations. v2 validation should use semantic similarity (embedding-based), not just Levenshtein.

**Status:** PARTIALLY FIXED — May 15, 2026; permanent fix queued for post-Hajj (06/06+)

---

## P075 — Missing `text_tajik` column in `hadith_library` table

**Symptom:** TJ language tab on hadithreels.com displays Russian text instead of Tajik. Listen button narrates in Russian. Affects all 70 hadiths.

**Root cause:** Original Supabase schema had `text_arabic`, `text_english`, `text_uzbek`, `text_russian` but NO `text_tajik` column. Route `app/api/reels/route.ts` documented this as P050 with explicit RU fallback. Library appeared functional but was misleading users.

**Fix — three parts:**

**Part 1 — Schema:**
```sql
ALTER TABLE hadith_library ADD COLUMN text_tajik TEXT;
```

**Part 2 — Data:** Use Claude API (Sonnet 4.5) to translate `text_uzbek` → `text_tajik` for all 70 rows. Pipeline:
- `scripts/translate-tajik.ts` — generates `out/tajik-translations.json` for human review
- Human spot-checks JSON, edits any rows
- `scripts/apply-tajik-translations.ts --apply` — writes verified translations to Supabase

See `hr-tj-translation-process.md` for full process documentation.

**Part 3 — Route:** Update `app/api/reels/route.ts`:
- Add `text_tajik` to SELECT clause
- Add TJ branch: `lang === 'tj' ? (h.text_tajik || h.text_russian || h.text_english) : ...`
- `display_lang` now returns `'tj'` if `text_tajik` exists, `'ru_fallback'` only if missing

Update `app/page.tsx` Hadith interface:
- Add `text_tajik?: string`

**Verification SQL:**
```sql
SELECT hadith_number, LEFT(text_tajik, 60) AS tj_preview
FROM hadith_library WHERE text_tajik IS NOT NULL LIMIT 10;
```

**Caveat:** Translations are AI-generated from Uzbek source. Native Tajik speaker review desirable for v2. Quality observed as good — proper Tajik grammar (Persian-derived constructions like "то ҳангоме ки"), not transliterated Uzbek. One minor edit applied in JSON review (`то он ҳангоме ки` → `то ҳангоме ки` in hadith #13).

**Status:** FIXED locally — May 15, 2026; pending Vercel deploy.

---

End of P072-P075 appendix.
# Append to fix_patterns.md (HR — hadith-reels)

## ════════════════════════════════════════════════════════
## PATTERN 78: Whisper STT produces Latin transliteration for UZ/TJ — q→k drift
## ════════════════════════════════════════════════════════
**ID:** P078
**Type:** Pipeline limitation + workaround
**Project:** hadith-reels (also affects hadith-verifier — see HV P078)
**Files affected:**
  - reel-creation-pipeline.md (subtitle generation step)
  - remotion/HadithReel.tsx (subtitle rendering — bypassed for v2)
  - out/adults-tj-umra-reel-v2.mp4 (first reel shipped without subtitles)
**First observed:** May 15, 2026 — TJ adults reel render (Bukhari #1773 Umrah)
**Discovered during:** Pre-Hajj reel production session

**Symptom:**
  When generating .srt subtitle files from ElevenLabs-narrated UZ/TJ audio via
  Whisper STT (OpenAI Whisper API or local whisper-large-v3):
  1. Whisper transcribes Cyrillic audio output as Latin transliteration
     - "Расул" → "Rasul"
     - "Паёмбар" → "Payambar"
     - "Аллоҳ" → "Alloh"
  2. Compounded by Q→K consonant drift in transliteration:
     - "қабул" → "kabul" (should be "qabul")
     - "Ҳаққ" → "Hakk" (should be "Haqq")
     - "Қуръон" → "Kuran" (should be "Quran" or "Qur'on")
  3. Output is unreadable to native Tajik/Uzbek Cyrillic readers
  4. Hardcoding these subtitles onto the reel made it look broken

**Root cause:**
  Whisper's training corpus for Tajik (TJ) and Uzbek (UZ) is dominated by
  Latin-script transliteration sources, not Cyrillic. The model has stronger
  priors for Latin output even when the audio phonetics map cleanly to Cyrillic
  characters. Additionally, Whisper's tokenizer treats /q/ and /k/ as
  near-equivalent in Turkic phonetic contexts, causing systematic drift on
  uvular/velar distinctions that ARE phonemic in TJ/UZ.

**Workaround (current — v2 shipped this way):**
  Ship UZ/TJ reels WITHOUT burned-in subtitles. The audio narration alone
  conveys the message. Caption text in the post description carries the
  written Cyrillic version for accessibility.

  Implementation in v2 render:
  - HadithReel.tsx `subtitleText` prop set to empty string
  - Subtitle scene block conditionally skipped if subtitleText is empty
  - Reel duration redistributed: longer story/moral scene fade times

**Permanent fix options (deferred to post-Hajj):**

  Option A — Latin→Cyrillic conversion script (RECOMMENDED, fastest):
    1. Run Whisper as normal, get Latin .srt
    2. Pipe through a deterministic Latin→Cyrillic mapper:
       - "Rasul" → "Расул"
       - "kabul" → "қабул" (handle q→k reversal via context)
       - "Alloh" → "Аллоҳ"
    3. Use existing Uzbek Latin/Cyrillic conversion libraries:
       - npm: uzbek-latin-cyrillic
       - python: uzbek-translit
    4. For TJ: hand-built mapping table (no mature library exists)
    5. Add post-processing step to reel-creation-pipeline.md after STT

  Option B — Replace Whisper with Claude STT prompt:
    1. Send audio to Claude Sonnet with explicit instruction:
       "Transcribe this Tajik audio in Tajik Cyrillic script only.
        Use Cyrillic characters Ҳ, Ҷ, Қ, Ғ, Ӯ where appropriate.
        Do NOT use Latin transliteration."
    2. Claude has better script-following behavior on instruction.
    3. Cost: higher than Whisper, slower, but accurate.

  Option C — Generate .srt from Claude-generated story text directly:
    1. Skip STT entirely
    2. Use the story/moral text from /api/generate-reel as subtitle source
       (it IS already in Cyrillic — that's what we narrated FROM)
    3. Time-align by splitting on sentence boundaries proportional to audio
       duration (or use forced alignment via aeneas/Montreal Forced Aligner)
    4. This is technically the cleanest solution — bypasses STT entirely.
    5. RECOMMENDED for production pipeline.

**Prevention / detection:**
  Before next post-Hajj reel production, add CI check:
  - Lint subtitle .srt files for Latin characters in UZ/TJ outputs
  - Fail render if subtitleText contains [a-zA-Z] for lang in ['uz','tj']
  - Add to hr-render-reel-route.ts: validateSubtitleScript(text, lang)

**Status:** WORKAROUND IN PLACE (no subtitles for UZ/TJ).
  Permanent fix: Option C scheduled for post-Hajj (target 06/06/2026).
  Tracked in: hr-CLAUDE-append-3.md Phase 2 deliverables.

**Reels shipped under this workaround:**
  - out/adults-tj-umra-reel-v2.mp4 (Bukhari #1773, posted to @SahihHadithReels May 15)
  - Future TJ/UZ reels until Option C ships

## ════════════════════════════════════════════════════════
## PATTERN 79: Admin story/moral text not editable before TTS generation
## ════════════════════════════════════════════════════════
**ID:** P079
**Type:** UX gap (admin workflow)
**Project:** hadith-reels
**File affected:** app/admin/page.tsx (or wherever admin Step 2 renders)
**First observed:** May 16, 2026 — RU adults reel (Bukhari #1520, hajj-women)
**Discovered during:** Pre-Hajj reel production session

**Symptom:**
  Claude's generated story for RU adults reel contained grammatical error:
    "Послание к Аллаха" (Message to Allah — wrong)
  Should have been:
    "Посланник Аллаха" (the Messenger of Allah — correct)

  Error was present in:
  1. Generated story text shown in admin Step 2
  2. Story narration MP3 (ElevenLabs read the wrong text)
  3. Whisper-generated SRT (faithfully transcribed the wrong audio)
  4. Auto-generated caption (also used Claude's wrong text)

  Forced full regenerate workflow — re-generate story, re-download both MP3s,
  re-run concat, re-run Whisper, re-run final ffmpeg merge. ~10 min lost.

**Root cause:**
  In hr-admin-page.tsx Step 2 render, story and moral text are displayed via:
    <p className="text-amber-100 text-sm leading-relaxed" dir="auto">
      {generated.story}
    </p>
  This is a read-only paragraph. The user cannot click and edit the text
  before clicking "Generate Story narration".

  Result: any Claude generation error forces a full regenerate cycle, which:
  - Spends additional Anthropic API credits (story + moral regenerated)
  - Spends additional ElevenLabs credits (new MP3s)
  - Adds production time
  - Risks Claude making a different error in the new generation (P060)

**Workaround (current):**
  Click 🔄 Regenerate button in admin. Iterate 2-3 times if needed.
  Claude is non-deterministic — different output each run, sometimes worse,
  sometimes better. No guarantee of correct output on first retry.

**Permanent fix (target: post-Hajj):**

  Replace the read-only `<p>` elements with editable `<textarea>` elements
  bound to `setGenerated()` state. Approximate code change:

  ```tsx
  // BEFORE (read-only):
  <p className="text-amber-100 text-sm leading-relaxed" dir="auto">
    {generated.story}
  </p>

  // AFTER (editable):
  <textarea
    value={generated.story}
    onChange={e => setGenerated({ ...generated, story: e.target.value })}
    className="w-full bg-amber-950/30 text-amber-100 text-sm leading-relaxed
               border border-amber-800/50 rounded-lg p-2 resize-none min-h-[120px]"
    dir="auto"
  />
  ```

  Apply same pattern to:
  - generated.story (amber section)
  - generated.moral (emerald section)
  - generated.seerah_context (blue section, if present)

  Estimated effort: ~10 lines of code, 1 commit, fully backward compatible.

**Prevention / detection (post-fix):**
  Add UI affordance: highlight box border on textarea focus to signal
  "this is editable — please proofread before generating audio".

  Add a "Verified" checkbox the user must tick before "Generate Story narration"
  button is enabled. Forces explicit human review step.

**Test pattern (when fix lands):**
  Add to tests/hadith-reels.spec.ts:
  ```typescript
  test('admin Step 2 story is editable before TTS', async ({ page }) => {
    // ... navigate to admin, generate ...
    const storyTextarea = page.locator('textarea[data-test="story-edit"]')
    await expect(storyTextarea).toBeVisible()
    await storyTextarea.fill('Edited story text')
    // Verify the edit propagates to the generate audio request
  })
  ```

**Related patterns:**
  P060 — AI quality tests non-deterministic (same root: Claude varies between runs)
  P061 — TTS route contract (downstream of story text)
  P078 — Whisper STT limitations (separate issue, but same workflow stage)

**Status:** FIXED — CI #51 (c81d313), 2026-06-10.
  Story/moral/seerah render as editable <textarea> bound to generated state via
  updateField(); edits flow straight into TTS (no regenerate cycle needed).
  Also fixed: undeclared genError state (pre-existing build error surfaced while
  type-checking this change).
  Verified: manual admin test (RU reel) — edited text narrated correctly; tsc clean.
  Original workaround (regenerate until correct) no longer required.

  ================================================================

**ID:** P081
**Type:** Tooling bug (render automation)
**Project:** hadith-reels
**File affected:** render-reel.ps1 (Step 5 Whisper call)
**First observed:** Jun 11, 2026 — RU adults animated reel (Bukhari #1520)
**Discovered during:** render-reel.ps1 end-to-end testing (animated pipeline)
**Symptom:**
  The script's Whisper subtitle call failed with:
    "whisper.exe : usage: ... error: --max_line_width requires --word_timestamps True."
  Whisper printed its usage banner and produced NO .srt, so render-reel.ps1
  fail-loud guard halted at Step 5. The same command worked manually only when
  --word_timestamps True was also present.
**Root cause:**
  An earlier edit removed --word_timestamps (it had been suspected as the cause of
  a different failure) but LEFT --max_line_width 35 in the call. Whisper rejects
  --max_line_width unless --word_timestamps True is also supplied — they are a pair.
  The orphaned flag caused the usage error.
**Fix:**
  Dropped --max_line_width entirely. Segment-level SRT (Whisper default, no
  word-timestamps) reads BETTER in reels (whole phrases vs word-by-word flashing)
  and is faster/more reliable. Final call:
    & whisper "$narr" --model small --language $Lang --output_format srt --output_dir "out"
  Also: route Whisper directly (not through the Out-Null helper) so it writes the
  SRT, and skip-if-SRT-exists to avoid re-transcribing.
**Lesson:**
  Whisper CLI flags have dependencies (--max_line_width / --max_line_count /
  --max_words_per_line all require --word_timestamps True). Run native tools the
  EXACT way that worked manually; don't half-remove paired flags.

================================================================

**ID:** P082
**Type:** Tooling bug (video stitch — framerate mismatch)
**Project:** hadith-reels
**File affected:** render-reel.ps1 (Step 6 ordered-scene stitch, -Scenes mode)
**First observed:** Jun 11, 2026 — RU adults animated reel (Bukhari #1520, 4-scene)
**Discovered during:** Pillar 2 animated-reel assembly
**Symptom:**
  In the 4-scene animated reel (pilgrim → dua → Kaaba → path), the PATH scene
  flashed by in ~1 second instead of its full ~5 seconds, while the other three
  scenes played correctly. ffprobe confirmed the path clip was genuinely 5.04s /
  121 frames — so the clip was fine, but it disappeared in the stitched output.
**Root cause:**
  The path clip was 24 fps (Kling image-to-video / FLUX-still origin), while the
  other clips and the stitch target were 30 fps. The concat demuxer concatenates
  streams using the first stream's timebase; a 24fps clip dropped into a 30fps
  timeline gets wrong presentation timestamps and is compressed/flashed.
  (Sibling of the resolution-mismatch trap: image-to-video preserves the source
  still's aspect/fps, which often differs from the reel's 1080x1920 @ 30fps.)
**Fix:**
  In render-reel.ps1's animated (-Scenes) branch, NORMALIZE EACH clip to identical
  1080x1920 @ 30fps BEFORE concatenating, then concat the uniform temps with -c copy:
    ffmpeg -i clip -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -c:v libx264 -pix_fmt yuv420p -r 30 -an tmp
  Now any stray fps/resolution can't flash-by or distort. (Manual one-off fix for the
  affected clip: same -vf with fps=30 re-normalize.)
**Lesson:**
  Never -c copy concat clips from mixed sources (Kling t2v, Kling i2v, real footage,
  FLUX stills) — they differ in fps AND resolution. Always normalize each to a uniform
  spec first. Resolution guard alone is insufficient; framerate matters equally.

  ================================================================

**ID:** P083
**Type:** Tooling bug (render automation — PowerShell native stderr)
**Project:** hadith-reels
**File affected:** render-reel.ps1 (Step 5 Whisper call)
**First observed:** Jun 13, 2026 — EN adults animated reel (Bukhari #1520)
**Discovered during:** Producing the EN 1520 reel (first subtitled reel since the script's Whisper path)
**Symptom:**
  render-reel.ps1 halted at Step 5 with:
    "whisper.exe : ...UserWarning: FP16 is not supported on CPU; using FP32 instead
     ... NativeCommandError"
  No SRT produced; script died before the Test-Path $srt check. Running whisper
  manually produced a perfect SRT — so Whisper worked; only the script halted.
**Root cause:**
  The script sets `$ErrorActionPreference = 'Stop'` globally (line 45). The Whisper
  call (unlike ffmpeg, which goes through the Run() helper) was invoked directly:
    & whisper ... 2>&1 | ForEach-Object {...}
  Whisper writes a HARMLESS "FP16 not supported on CPU" warning to stderr. Under
  'Stop', that merged stderr line is treated as a TERMINATING error, killing the
  script before the SRT existence check. (Only triggers when Whisper actually runs —
  i.e. en/ru/ar; uz/tj auto-skip subs per P078, so they never hit it.)
**Fix:**
  Wrap the Whisper call in the same 'Continue' pattern as Run():
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & whisper ... 2>&1 | ForEach-Object {...}
    $ErrorActionPreference = $prevEAP
    if (-not (Test-Path $srt)) { Die ... }
  Now Whisper's FP16 warning prints harmlessly and the render continues; real
  failures still caught by the Test-Path check. Fixed CI/commit 2c47759.
**Lesson:**
  Native tools (whisper, ffmpeg) write normal/warning output to stderr. Under
  $ErrorActionPreference='Stop', ANY direct native call can be killed by a stderr
  line. Route ALL native calls through a 'Continue'-wrapped helper, not just ffmpeg.

  ## ════════════════════════════════════════════════════════
## PATTERN 84: Admin TTS request omits `style` → kids use adults (male) voice
## ════════════════════════════════════════════════════════
**ID:** P084
**Type:** Bug fix (request payload / voice routing)
**Files:** app/admin/page.tsx
**Commit:** fix: admin TTS request missing style param — kids used adults voice (P084)

**Symptom:**
  Kids reels were narrated with a MALE voice in every language, despite the
  voice matrix specifying Danielle (EN/UZ/TJ kids). Generating EN/Kids audio
  produced James/Adam (adults), not Danielle.

**Root cause:**
  AudioSection in the admin page calls /api/tts but only sends { text, lang }:
      body: JSON.stringify({ text: text.slice(0, 800), lang })
  The TTS route defaults `style = 'adults'` when none is sent, so EVERY kids
  generation silently routed to the adults voice. The VOICE_MAP and .env.local
  were correct all along — the request simply never asked for the kids voice.
  `style` was already available as a prop in AudioSection; it just wasn't in
  the body. This affected ALL kids languages, not only EN.

**Fix (one line):**
  app/admin/page.tsx — add `style` to the TTS request body:
      body: JSON.stringify({ text: text.slice(0, 800), lang, style })

**Verification:**
  Restart dev server → admin Kids/EN → generate 6009 TTS → female (Danielle).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 85: RU kids narration used male voice (ElevenLabs Abrar)
## ════════════════════════════════════════════════════════
**ID:** P085
**Type:** Enhancement / voice routing (TTS provider branch)
**Files:** app/api/tts/route.ts
**Commit:** feat: route RU kids TTS to OpenAI Nova (female) (P085)

**Symptom:**
  RU kids reels narrated with a male voice. RU (both styles) routed through
  ElevenLabs to ELEVENLABS_VOICE_ABRAR (Antoni, male); no female kids option.

**Root cause:**
  The OpenAI branch (Nova female for kids) only fired for uz/tj. RU always
  used the ElevenLabs path, which had a single male voice for both styles.

**Fix — two edits (RU adults untouched):**
  1. Add a 'ru.kids' entry to TTS_INSTRUCTIONS (warm Russian children's tone).
  2. Extend the OpenAI condition:
       const useOpenAI = ['uz','tj'].includes(langKey)
         || (langKey === 'ru' && style === 'kids')
     The OpenAI branch already selects 'nova' when style === 'kids'.

**Why safe:**
  RU adults still misses the useOpenAI condition -> stays on ElevenLabs/Abrar
  exactly as before. Only RU+kids flips to OpenAI Nova.

**Verification:**
  Admin Kids/RU -> generate 6009 -> female (Nova). Confirmed 2026-06-13.

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 86: Pre-push hook ran full E2E on API-only / doc pushes
## ════════════════════════════════════════════════════════
**ID:** P086
**Type:** CI/tooling fix (smart pre-push hook)
**Files:** .git/hooks/pre-push  (NOT version-controlled — see note)
**Commit:** docs: P086 — pre-push E2E gate (server guard + API/UI split)

**Symptom:**
  Pushing only app/api/tts/route.ts + fix_patterns.md triggered the FULL
  25-test Playwright browser suite. With the dev server not running, all 25
  failed with net::ERR_ABORTED and blocked the push. A stale .next also
  produced phantom tsc errors in .next/dev/types/validator.ts.

**Root cause:**
  1. E2E gate fired on (HAS_API + HAS_UI) > 0 — so any API change pulled in
     the entire browser suite, ignoring the hook's own classification.
  2. Hook assumed a dev server was already live on :3002; if not, every test
     ERR_ABORTED instead of skipping.

**Fix:**
  - Probe http://localhost:3002 (curl) before E2E; if unreachable, SKIP with a
    clear message instead of failing 25 tests.
  - Scope by change type: UI change → full suite; API-only → smoke tests only
    (npx playwright test --grep "smoke tests").
  - Separate, observed today: a stale .next caused phantom tsc errors in
    generated validator.ts — fixed by `Remove-Item -Recurse -Force .next`
    (build cache, gitignored, regenerated by next dev).

**Note (carry-over):**
  .git/hooks/pre-push is NOT version-controlled — fix is local only. Board
  item: move hook to a tracked scripts/pre-push.sh so it survives re-clone.

**Status:** FIXED (local hook)

## ════════════════════════════════════════════════════════
## PATTERN 87: UZ kids TTS mispronounced ҳ / ж / ғ (Nova phonetics)
## ════════════════════════════════════════════════════════
**ID:** P087
**Type:** Enhancement (OpenAI Nova phonetic instructions, P073 family)
**Files:** app/api/tts/route.ts
**Commit:** feat: strengthen uz.kids ҳ/ж/ғ pronunciation for Nova (P087)

**Symptom (UZ kids, OpenAI Nova):**
  - ҳ dropped/softened to an s-like sound: меҳрибон → "месрибон"
  - ж read as Russian/French "zh" instead of English J: жонзот, муҳтож
  - plain г occasionally hardened toward throaty ғ: сувга

**Fix — strengthened the 'uz.kids' instructions string:**
  - ҳ: ALWAYS audible breathy H, never dropped/softened to s, never Russian х.
  - ж: soft English J (judge), never zh, including word-final ж.
  - Added explicit examples: меҳрибон=meh-hree-BON, жонзот=JON-zot,
    муҳтож=muh-TOJ, сувга=suv-GA (plain g, not ғ).

**Residual + workaround:**
  Nova still mispronounced ҳ specifically on sentence-INITIAL capitalized
  "Меҳрибон" while reading lowercase "меҳрибонлик" correctly. Instructions
  can't reliably fix one stochastic position → reword so the word sits
  lowercase mid-sentence (content-side fix, not prompt-side).

**Status:** FIXED (instructions) + documented workaround
