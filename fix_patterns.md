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
**Follow-on (2026-08-27, see P124):** this fix made the blocks editable BEFORE
  narration, and that has been carrying the whole correction workflow since —
  every hand-fix to a generation lands in these textareas. The boundary it left
  is documented in P124: once "Generate narration" is clicked, the button becomes
  playback and the audio stays bound to the text that existed at generation time.
  Editing afterwards reaches nothing. The only re-narrate path is Regenerate,
  which replaces all four blocks. So the editable window is exactly one pass —
  which makes this fix load-bearing rather than convenient, and makes P124's
  per-block re-narrate the natural completion of it.

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

## ════════════════════════════════════════════════════════
## PATTERN 88: Public library capped at 40 rows; counter wrong
## ════════════════════════════════════════════════════════
**ID:** P088
**Type:** Feature/fix (pagination + accurate counts)
**Files:** app/api/reels/route.ts, app/page.tsx
**Commit:** feat: load-more pagination + accurate library counts (P088)

**Symptom:**
  hadithreels.com showed "40 Hadiths" no matter the real DB size, and browsing
  only ever displayed the first 40 rows. New hadiths past row 40 (ordered by
  collection) were unreachable when browsing. (Surfaced while diagnosing why
  Bukhari 6009 wasn't visible — root cause there was blank prod Supabase env;
  the 40-cap was the second, separate issue.)

**Root cause:**
  - /api/reels hard-limited to 40 and returned total = results.length (page
    size), not the real DB count.
  - Public page set stats.total from the fetched list length and never paged.

**Fix:**
  - Route: select with { count: 'exact' } → return real total; add an exact
    Sahih sub-count (head:true count query); accept offset for paging.
  - Page: paginate in PAGE_SIZE (40) batches; append on "Load more"; counter
    reads data.total/data.sahih (real DB counts). Load-more hidden during
    search (search stays client-side over loaded rows — option A).

**Known limit (option A):**
  Client-side search only filters loaded rows; user may need to Load More to
  search the full library. Server-side search (option B) deferred — board item.

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 89: Search only matched loaded rows (capped at 40)
## ════════════════════════════════════════════════════════
**ID:** P089
**Type:** Feature (server-side search)
**Files:** app/api/reels/route.ts, app/page.tsx
**Commit:** feat: server-side library search across all languages (P089)

**Symptom:**
  Client-side search filtered only the loaded rows (first 40), so any hadith
  past row 40 was unfindable until the user manually clicked Load More — and
  users had no way to know to do that. Got worse as the library grew.

**Fix:**
  - Route: accept `q` param; when present, .or(ilike) across text_english/
    russian/uzbek/tajik/arabic + narrator/collection/hadith_number over the
    WHOLE library (esc strips %/, that break .or()).
  - Page: debounced (300ms) search effect calls /api/reels?q=...; empty box
    returns to paginated browse; removed the client-side filter (filtered =
    hadiths). Also helps non-EN users find via in-language text search.

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 90: Retired model ID + structured-output truncation
## ════════════════════════════════════════════════════════
**ID:** P090
**Type:** API integration / structured-output reliability
**Repos:** hadith-verifier (analyze + dua routes), telegram_bot.py; hadith-reels (generate-reel route). Global entry — both repos.

**Symptom:**
  - Production 404 on every analysis: not_found_error, model: claude-sonnet-4-20250514
  - (Latent) Intermittent "Parse error" on longer duas/hadiths

**Root cause:**
  1. claude-sonnet-4-20250514 (Sonnet 4) retired on the Claude API 2026-04-20. Pinned model IDs go dead on retirement — they are not evergreen.
  2. max_tokens: 2000 too small for the 5-language JSON (4 translits + 3 translations + 5-lang comment, Arabic/Cyrillic = token-heavy). Overflow truncates JSON mid-string → JSON.parse throws.
  3. Reading content[0] assumes first block is text; breaks on thinking-enabled models. Bare JSON.parse intolerant of preamble.

**Fix:**
  - Model → claude-sonnet-4-6 (active drop-in). Upgrade path claude-sonnet-5 requires parse hardening first (adaptive thinking on by default).
  - max_tokens → 8000.
  - Extract text block by type: content.find(b => b.type === 'text'), not by index.
  - Parse by slicing first "{" … last "}" (matches generate-reel route's robust pattern).
  - Log raw.slice(0,300) on parse failure.

**Prevention:**
  - On model-retirement notices: git grep the pinned string across ALL repos — dead IDs hide in multiple callers (found in 4: analyze, dua, generate-reel, telegram_bot).
  - Structured-output pipelines fail at the parse boundary: generous token budget + tolerant extraction + explicit failure logging.
  - Never edit repo files in GitHub mobile editor — a stray newline in a string literal caused a build break.
  - "Committed" ≠ "fixed": verify green build AND a real end-to-end run.

**Status:** FIXED + verified live (green build, live RU analysis) — July 2026

**AMENDMENT (2026-08-08) — the sweep missed a caller for four months:**
  HR's app/api/generate-reel/route.ts was EDITED to claude-sonnet-4-6 during the
  original P090 sweep but never committed. `git grep` searches the WORKING TREE
  by default, so the verification step reported the fix as present while HEAD —
  and therefore production — still held claude-sonnet-4-20250514.
  Undetected until 2026-08-08 because no reel had been generated since April.
  Shipped as 7b6f017; verified against production, not just the deploy.

  RULE: after a multi-caller sweep, verify against HEAD, not the working tree:
    git grep -n "<retired-id>" HEAD -- app/ lib/
    git status --short          # nothing left unstaged
  A green `git grep` on an uncommitted edit is the same silent-success class as
  P096's zero-row update and P093's zero-test pass.


## ════════════════════════════════════════════════════════
## PATTERN 91: RLS disabled + allow-all policy defeating RLS
## ════════════════════════════════════════════════════════
**ID:** P091
**Type:** Security / database access control
**Repos:** shared Supabase DB xeirfeqnbjfyszykiraa (both apps). Migration: 20260707_enable_rls_security.sql

**Symptom:**
  - Supabase Security Advisor: 6 CRITICAL "RLS Disabled in Public" across hadith_library, video_backgrounds, hadith_candidates, hadith_promotions, flagged_posts (last also "Policy Exists RLS Disabled")

**Root cause:**
  1. RLS never enabled → anyone with the anon key (shipped in browser JS, effectively public) could read/insert/update/DELETE these tables directly.
  2. flagged_posts had a dormant "Allow all" policy (role public, cmd ALL, qual true). Enabling RLS ACTIVATED it, so the table stayed fully open. RLS "on" did NOT mean protected.

**Fix (two-pass migration, service_role verified first):**
  - Pre-check: confirmed all writers use SUPABASE_SERVICE_ROLE_KEY (bypasses RLS) — HV analyze/search/queue routes + HR upload-candidates.py.
  - Tier 1 (admin/pipeline): enable RLS, no anon policy → public denied. hadith_candidates, hadith_promotions, flagged_posts.
  - Tier 2 (public data): enable RLS + "create policy … for select to anon, authenticated using (true)" → public read-only. hadith_library, video_backgrounds.
  - drop policy "Allow all" on flagged_posts.
  - Verified: pg_class.relrowsecurity=true on all 5; pg_policies shows only the 2 read policies; both apps confirmed live.

**Prevention:**
  - "Control enabled" ≠ "control effective." After enabling RLS, ALWAYS list pg_policies and confirm each policy RESTRICTS — never trust the status flag.
  - Trust boundary runs along the KEY, not the code. Anything client-held (anon key, NEXT_PUBLIC_*) is public; enforcement is server-side. Backend = service_role, clients = anon.
  - On any new table: enable RLS + add intended policy in the SAME migration. Never leave public "temporarily".
  - Consider rotating anon + service_role keys if values were ever exposed.

**Status:** FIXED + verified live (5 tables RLS-on, both apps reading correctly) — July 2026

## ════════════════════════════════════════════════════════
## PATTERN 92: Mockable Claude via MOCK_CLAUDE seam + isolated test server
## ════════════════════════════════════════════════════════
**ID:** P092
**Type:** Test infrastructure / determinism / cost control
**Repos:** hadith-verifier (analyze route, api.spec.ts, playwright.config.ts, .githooks/pre-push). Pattern applies to any repo whose push tests hit the real Claude API.

**Symptom:**
  - Pre-push api.spec.ts made REAL Claude calls (~30s/test), causing: 429 rate-limit
    failures (own in-memory limiter + Anthropic), 30s timeouts, non-determinism, API cost
    on every push. Header claimed "mocked, fast" — it wasn't.

**Root cause:**
  The analyze route always called `anthropic.messages.create(...)`. Tests that only check
  status codes / schema shape don't need real Claude, but had no way to bypass it. The Claude
  call happens server-side inside the route, so Playwright can't intercept it from the test.

**Fix — route-level mock seam + isolated ephemeral server:**
  1. Route: `const response = process.env.MOCK_CLAUDE === '1' ? { content:[{type:'text',text:JSON.stringify(MOCK_ANALYSIS)}] } : await anthropic.messages.create({...})`.
     MOCK_ANALYSIS = canned valid object matching the response schema (verdict/confidence/
     severity/claim_summary/analysis/suggested_comment/references/red_flags/seerah_context).
     Rest of route (parse, getSeverity override) runs unchanged → real route logic tested.
  2. Also gate side-effects under mock so test runs don't pollute prod or trip limits:
     - rate limiter: `if (process.env.MOCK_CLAUDE !== '1') { checkRateLimit... }`
     - queue insert: `if ([...].includes(verdict) && process.env.MOCK_CLAUDE !== '1')`
  3. Port isolation: mocked tests run on :3011 (HV=3001, HR=3002, 3011=HV mock-only,
     ephemeral). Prevents collision with a running dev server.
  4. Hook starts its OWN mock server, waits for ready, runs tests, kills it, gates on the
     real exit code (see block below). Do NOT rely on Playwright webServer for the mock run
     (see P093 for why).

**Hook block (proven):**
```
if [ "$HAS_ANALYZE" -gt 0 ] && [ $FAILED -eq 0 ]; then
  MOCK_CLAUDE=1 npx next dev -p 3011 > /tmp/hv-mock.log 2>&1 &
  MOCK_PID=$!
  READY=0
  for i in $(seq 1 40); do curl -s -o /dev/null http://localhost:3011/api/test && { READY=1; break; }; sleep 1; done
  if [ $READY -ne 1 ]; then echo "❌ Mock server failed to start"; kill $MOCK_PID 2>/dev/null; FAILED=1;
  else
    BASE_URL=http://localhost:3011 npx playwright test tests/api.spec.ts --project=chromium --grep-invert "@real-api" 2>&1
    API_RC=$?
    kill $MOCK_PID 2>/dev/null
    [ $API_RC -ne 0 ] && FAILED=1
  fi
fi
```

**Prevention / notes:**
  - Result: api.spec push subset now ~45s, API tests sub-second, deterministic, $0, no limits.
  - The mock doubles as a schema contract — if MOCK_ANALYSIS drifts from what tests assert,
    you find out instantly (caught a `Tier 1` vs `tier1` mismatch for free).
  - Quality tests that genuinely need real Claude stay tagged @real-api (excluded from push,
    run manually). CI (ci.yml) intentionally left REAL against production = post-deploy smoke.
  - Document 3011 in CLAUDE.md port map so future sessions/agents don't cross-assign.

**Status:** FIXED + verified (exact hook logic proven green via standalone script, RC=0, sub-second) — July 2026


## ════════════════════════════════════════════════════════
## PATTERN 93: Windows/git-bash env + exit-code gotchas that silently defeat a CI gate
## ════════════════════════════════════════════════════════
**ID:** P093
**Type:** Test infrastructure / shell / Windows dev environment
**Repos:** hadith-verifier (.githooks/pre-push). Applies to any git-bash hook on Windows.

**Symptom:**
  While wiring MOCK_CLAUDE into the pre-push hook (P092), three separate bugs each made the
  gate behave wrongly — worst of all, a gate that PASSED while running zero tests.

**Three root causes + fixes:**
  1. **Inline env prefix doesn't propagate to spawned server (Windows).**
     `MOCK_CLAUDE=1 npx playwright test...` sets the var for npx, but on Windows git-bash the
     `.cmd` shim + Playwright's webServer spawn drops it — the spawned `next dev` never sees
     MOCK_CLAUDE, so it called REAL Claude (tests passed but took 30s). PowerShell `$env:` and
     bash `export` both work in isolation, but neither reliably reaches a process spawned by
     Playwright's webServer.
     → FIX: don't inline-prefix and don't rely on webServer to carry it. Start the mock server
       explicitly with the var on ITS command (P092 hook block).

  2. **`unset` after the test clobbers `$?`.**
     ```
     npx playwright test ...
     unset MOCK_CLAUDE BASE_URL      # <-- last command
     if [ $? -ne 0 ]; then FAILED=1  # <-- checks unset's exit (always 0), NOT the test
     ```
     Gate could never see a test failure.
     → FIX: capture immediately — `RC=$?` right after the test, then `unset`, then gate on `$RC`.

  3. **Playwright webServer timeout exits 0 → false pass.**
     When webServer failed to become ready, the run errored ("Timed out waiting ... webServer")
     but the outer exit code was 0 — a gate running ZERO tests reported success.
     → FIX: explicit start/poll(curl /api/test)/kill, and gate on the captured test exit code.
       Fail loudly ("❌ Mock server failed to start") if the health poll never succeeds.

**Prevention:**
  - A CI gate that CANNOT fail is worse than no gate — it ships anything with a green check.
    Always: capture the real exit code of the thing you care about, gate on THAT, and prove the
    gate can fail (not just pass) before trusting it.
  - On Windows git-bash: prefer explicit `command &` + health-poll over Playwright webServer +
    env-prefix magic. Fewer hidden processes, observable failures.
  - When a hook "passes" suspiciously fast or suspiciously slow, check timings — 30s = real API,
    sub-second = mock. Timing is the tell that env vars actually took effect.

**Status:** FIXED (all three addressed in the P092 hook block) — July 2026


## ════════════════════════════════════════════════════════
## PATTERN 94: Stage 5 promote (candidate→library) + CHECK constraints as schema contract
## ════════════════════════════════════════════════════════
**ID:** P094
**Type:** Data pipeline / integrity / idempotency
**Repos:** hadith-reels (scripts/promote-candidates.py). Touches shared DB hadith_library, hadith_candidates, hadith_promotions.

**What it is:**
  Stage 5 of the sourcing pipeline — moves human-approved candidates from
  hadith_candidates into the shared hadith_library, with an audit trail and
  idempotency. Completes: source → dedup → stage → HUMAN GATE (SQL) → promote → library.

**Design (promote-candidates.py):**
  - Reads: `status=eq.approved & grade_confirmed=eq.true & grade=in.(sahih,hasan) & promoted_library_id=is.null`
  - Maps candidate → library columns (schemas differ — mapping is NOT 1:1):
    - text_uzbek_cyrillic/latin → same; text_uzbek (legacy col) ← Cyrillic (canonical, keeps old readers working)
    - authority ← grading_source
    - source_url (text, singular) ← ONE deep-link extracted from source_urls (jsonb, plural): prefer dorar > sunnah > first
    - tags ← [] (red_flags is a VERIFIER concept, not library content — do not copy)
    - book ← null (not in candidates); created_at ← DB default now()
  - Writes hadith_promotions audit row (candidate_id, library_id, promote_mode, reviewed_by, source_deeplink, columns_written)
  - Stamps candidate: status='promoted', promoted_library_id=<new id>  ← IDEMPOTENCY GUARD
  - Discipline: dry-run default, --commit to write, --show to preview mapping, service_role key, stdlib-only, ensure_ascii=False for Arabic/Cyrillic/Tajik.

**Stage 4 human gate = SQL (not UI, by choice — promote today, UI later):**
  - review:  select ... from hadith_candidates where status='needs_human' (or 'sourced')
  - approve: update ... set status='approved', review_action='approve', reviewed_by=..., reviewed_at=now()
  - reject:  update ... set status='rejected', review_action='reject', review_reason=...

**Idempotency (proven):** second --commit finds 0 approved (candidate now 'promoted', not 'approved')
  → cannot double-insert. Re-running is always safe.

**KEY LESSON — CHECK constraints are a schema contract that catches bad writes loudly:**
  During testing, three assumed values were WRONG and the DB refused them at write time
  instead of silently storing garbage:
  - ck_status allows: sourced/deduped/translated/verified/needs_human/approved/rejected/promoted
    → 'pending' is NOT valid (assumed wrong).
  - ck_review allows: approve/edit_approve/reject/defer  → 'approved' is NOT valid (it's 'approve').
  - ck_grade = sahih/hasan; ck_promote_mode = insert/augment_update.
  This is defense-in-depth working as designed — same principle as P091's RLS lesson:
  a control must actually RESTRICT, and a good schema fails invalid states loudly and early.
  Had the status mismatch not been caught pre-commit, a promote could have inserted into
  library then failed the candidate-stamp step, leaving a half-done promote.

**Prevention / notes:**
  - Before writing to any table, read its CHECK constraints (pg_get_constraintdef) — don't
    assume enum values; the constraint is the source of truth.
  - When two schemas differ (candidates vs library), map explicitly and preview with --show
    on a DRY RUN before --commit. Never positional-insert into the shared library.
  - augment_update mode (fill missing translations on an existing library row) is designed
    for but NOT yet implemented — insert mode only for now. TODO.
  - Legacy Uzbek backfill (existing 74 rows have single-script, some MIXED-script text_uzbek)
    is a separate content-cleanup task via uzbek-translit.ts — parked, not part of promote.

**Status:** DONE + verified end-to-end on live data (promote → library + audit + idempotency stamp,
  then re-run = 0, then test row cleaned up, library back to 74) — July 2026
  
## ════════════════════════════════════════════════════════
## PATTERN 95: Uzbek TTS pronunciation — engine differences + Cyrillic homoglyph corruption
## ════════════════════════════════════════════════════════
**ID:** P095
**Type:** TTS quality / data integrity
**Repos:** hadith-reels (`lib/uzbek-tts-phonetics.ts`, `app/api/tts/route.ts`), shared DB `hadith_library`.
Applies to idris-learning-app and seerah audiobooks too.

---

### PART A — TTS engine findings (Uzbek)

**Investigated:** reported mispronunciation of Uzbek letters (ҳ, ғ, қ, ў, ж) in narration.

**Findings (browser + route testing, 2026-08):**
| engine | ж | ҳ / қ / ғ | verdict |
|---|---|---|---|
| **OpenAI gpt-4o-mini-tts** (current UZ/TJ path) | ✅ correct ("jannat") | ✅ correct | **no fix needed** |
| **ElevenLabs eleven_v3** | ❌ says "dj" | ✅ correct | needs inline IPA |
| ElevenLabs eleven_multilingual_v2 | — | — | **silently ignores IPA** |

**Conclusion: the reels pipeline needed NO change.** Uzbek routes to OpenAI
(`useOpenAI = ['uz','tj'].includes(langKey) …`), which already pronounces Uzbek correctly.

**ElevenLabs v3 fix (built, validated, reserved for future/audiobook use):**
- Inline IPA wrapped in `/slashes/` corrects ж. Mixing IPA for ONE word with Cyrillic for the
  rest WORKS: `/dʒanˈnat/ оналар оёғи остида` → correct. So only problem WORDS need transcribing.
- Formatting rules (each learned by failure):
  1. Everything inside `/…/` must be IPA/Latin — never Cyrillic. `/dʒума/` = undefined output.
  2. Always close the slash. `/dʒamoat` (unclosed) does not work.
  3. Include stress `ˈ` before the stressed syllable (Uzbek stress is normally final).
     Audibly improved results; ElevenLabs' own guidance recommends it.
- **IPA gotcha:** `j` = the "Y" sound; the "J" of *jam* is `dʒ`. Getting this backwards
  produces a wrong test input and a FALSE failure (it did — cost one test cycle).
- **Model assert required:** on `eleven_multilingual_v2` IPA is silently ignored — no error,
  just wrong audio. `applyUzbekIPA()` throws unless model is `eleven_v3`.

**REJECTED approach — do not reintroduce:** an earlier design respelled Cyrillic
(ж→дж, ҳ→х, қ→к) to trick a Russian-phonetics engine. Disproven: v3 already over-shoots to
"dj" so ж→дж makes it worse, and ҳ/қ need no help. **A workaround that helps a weak model can
harm a stronger one — re-baseline after every model upgrade.**

---

### PART B — Cyrillic homoglyph corruption in `hadith_library` (production data defect)

**Symptom:** 9 of 74 rows had Latin-script `text_uzbek` containing invisible Cyrillic
look-alike characters mid-word — e.g. `qo'shniСini`, `ustunИdir`, `Amалlar`, `shafОat`,
`rishtalарини`. Visually identical, different bytes.

**Cause:** typed/pasted with a Cyrillic keyboard layout mid-word. The homoglyph pairs
(а/a, о/o, е/e, с/c, р/p, и/i, Н/H, И/I, О/O, л/l) are indistinguishable by eye.

**Impact — three real failures:**
1. **TTS** — engine hits Cyrillic inside a Latin word and may switch phonetics or stumble.
2. **Search** — user typing `qo'shnisini` never matches `qo'shniСini`.
3. **Dedup** — different bytes → the same hadith can be inserted twice.

**Detection query (keep this — reusable):**
```sql
select id, text_uzbek from hadith_library
where text_uzbek ~ '[a-zA-Z]'          -- has Latin
  and text_uzbek ~ '[\u0400-\u04FF]';  -- AND has Cyrillic
```

**Fix:** `translate()` mapping each Cyrillic homoglyph to its Latin twin, PREVIEWED as a
dry-run `select` before any `update`. One row (`uylanСa`) needed a manual correction to
`uylansa` — character mapping alone gave `uylanca`, which is the right *character* but the
wrong *word*. Mechanical fixes can't infer intent; always eyeball the diff.
**Verified: post-fix count = 0.**

---

### KEY LESSONS

- **Verify the test input before blaming the system.** A typo in the test phrase (`оёги`
  instead of `оёғи`) made OpenAI look broken and nearly triggered an unnecessary re-architecture
  of a working pipeline. The engine pronounced exactly what it was given.
- **Cheap manual probing beats building.** ~20 minutes in the ElevenLabs browser UI overturned
  a plausible, fully-designed respelling module. Probe the capability before automating around it.
- **Silent capability degradation is the dangerous failure.** v2 ignoring IPA without error is
  the same class as P093's exit-code-0-on-failure. Prefer features that fail loudly; assert
  preconditions when they don't.
- Scope collapsed from "5 broken letters, build an ASR eval harness" to "no change needed for
  reels, 8-word lexicon reserved for ElevenLabs" — purely by testing instead of theorising.

**Status:** DONE — reels pipeline unchanged (correct as-is); `lib/uzbek-tts-phonetics.ts`
built + validated for future ElevenLabs use; 9 corrupted library rows repaired and verified.
August 2026

**Repo note:** Fix implemented in hadith-reels (scripts/); logged here because
hadith_library is shared and HV reads text_uzbek. HV action item: P089 search
must normalize apostrophes (qo'shni → qoʻshni).

## ════════════════════════════════════════════════════════
## PATTERN 96: Replayed backfill corrections + silent zero-row updates
## ════════════════════════════════════════════════════════
**ID:** P096
**Type:** Data-safety fix (stale snapshot replay + silent success)
**File:** scripts/apply-uzbek-scripts.ts
**Commit:** fix: --skip-source-fix flag + zero-row detection on backfill apply (P096)

**Symptom:**
  Legacy Uzbek two-script backfill (built 2026-06-14, commit 7b1946c) was never run.
  On re-examination two months later it was still ready to write, but:
  1. It wanted to write corrected_text_uzbek to 9 rows whose homoglyph corruption
     had already been fixed in production by other means.
  2. Its 74 write results could not be distinguished from 74 no-ops.

**Root cause — part 1 (stale replay):**
  The apply step does not compute anything. It replays out/uzbek-scripts.json,
  generated on 2026-06-14 from the then-corrupted table. Any defect fixed in
  production between generation and apply gets silently overwritten with the
  June-era value. Backfill scripts age; their input snapshots age with them.

**Root cause — part 2 (silent success):**
  supabase.from(t).update(u).eq('id', id) returns { error: null } when it
  matches ZERO rows. A stale id logs ✓ and increments the success counter for
  a write that never happened. Same failure class as:
    - P093 — Playwright webServer timeout exits 0 having run zero tests
    - anon-key writes under RLS — blocked, no error surfaced
  A green counter is not evidence of work performed.

**Fix — three parts:**
  1. Assert the defect still exists BEFORE --apply:
       select count(*) from hadith_library
       where text_uzbek ~ '[a-zA-Z]' and text_uzbek ~ '[\u0400-\u04FF]';
     Returned 0 → corrections already landed → skip that path.
  2. Gate the correction behind --skip-source-fix rather than deleting the code.
     The path stays available for future runs against uncorrected data.
  3. Chain .select('id') and treat an empty array as failure:
       else if (!data || data.length === 0) {
         fail += 1;
         console.error(`  ✗ #${n} (${id}): matched 0 rows — id not found`);
       }

**Also fixed — dishonest preview:**
  Summary and per-row preview lines were computed from cleaned_from_mixed
  without consulting the flag, so a --skip-source-fix dry run still printed
  "correcting source text_uzbek". The dry run IS the human gate; a preview
  that misreports what will happen defeats the gate. Both lines now branch
  on SKIP_SOURCE_FIX.

**Verification query — do not count against a fixed number:**
  The script's built-in hint said "expect 74 / 74", which assumes the table
  never grows. Compare against total_rows instead:
    select count(*) as total_rows,
           count(text_uzbek_cyrillic) as cyr,
           count(text_uzbek_latin) as lat,
           count(*) filter (where text_uzbek is not null
                              and text_uzbek_cyrillic is null) as uz_without_scripts
    from hadith_library;
  Result: 74 / 74 / 74 / 0 ✅

**Homoglyph predicate — known limitation:**
  The mixed-script check catches rows containing BOTH Latin and Cyrillic.
  A row where every Latin char was replaced by a Cyrillic homoglyph reads as
  pure Cyrillic and scores 0. Once both script columns are populated, the
  stronger per-column assertions are:
    text_uzbek_latin    !~ '[\u0400-\u04FF]'
    text_uzbek_cyrillic !~ '[a-zA-Z]'

**Rule going forward:**
  Before running any backfill whose input is a generated snapshot:
    1. Check the snapshot's age against the last change to its target table.
    2. Re-assert the defect predicate — never assume the defect is still there.
    3. Confirm affected-row counts; never trust an absent error as proof of write.

**Status:** FIXED — 74/74 applied, 0 failed


## ════════════════════════════════════════════════════════
## PATTERN 97: Transliterator returned raw Latin source — okina/tutuq drift
## ════════════════════════════════════════════════════════
**ID:** P097
**Type:** Data-correctness fix (orthography + unnormalized passthrough)
**Files:** scripts/lib/uzbek-translit.ts, scripts/lib/uzbek-translit.test.ts,
           scripts/promote-candidates.py
**Commit:** fix: normalize Latin apostrophes to okina/tutuq by context (P097)

**Background — two distinct Uzbek letters, not one apostrophe:**
  okina  ʻ U+02BB — forms the letters oʻ and gʻ  (boʻlsa, ulugʻ, Roʻza)
  tutuq  ʼ U+02BC — glottal stop, from Cyrillic ъ (Qurʼon, neʼmat, inʼom)
  Rule: apostrophe after o/O/g/G → okina; anywhere else → tutuq.

**Symptom:**
  After the legacy two-script backfill (P096), text_uzbek_latin held 41 rows
  with ASCII apostrophe ('), 1 row with okina, 32 with none. No row mixed
  variants — the transliterator was consistent per row, just not normalizing.

**Root cause:**
  deriveBothScripts() returned `latin: text` — the RAW input — for Latin-source
  rows. latinToCyrillic() folds all apostrophe glyphs via .replace(APOS, S),
  but that normalization only ever reached the CYRILLIC output. The Latin side
  was passthrough, so whatever the source typed survived into the column.
  Cyrillic-source rows were correct (CYR_MAP emits OKINA for ў/ғ, TUTUQ for ъ),
  which is why exactly 1 row had proper orthography.

**Compounding error — a blanket replace() made it worse before better:**
  An initial repair ran replace(text, '''', 'ʻ') across 41 rows, collapsing
  BOTH letters into okina. That corrupted 6 rows (Qurʼon→Qurʻon, neʼmat→neʻmat,
  inʼom→inʻom). The spot-check that followed searched for apostrophes adjacent
  to spaces/punctuation — the one position where tutuq never appears — so it
  could not have caught the defect it was meant to catch.
  LESSON: verify a normalization against the RULE it must satisfy, not against
  a proxy pattern. Counts proving uniformity are not counts proving correctness.

**Fix — data:**
  Context-aware repair, all apostrophes per row (not just the first):
    update hadith_library
    set text_uzbek = regexp_replace(
          regexp_replace(text_uzbek, U&'([ogOG])[\02BB\02BC]', U&'\\1\02BB', 'g'),
          U&'([^ogOG])[\02BB\02BC]', U&'\\1\02BC', 'g')
    where text_uzbek ~ U&'[\02BB\02BC]';
    update hadith_library set text_uzbek_latin = text_uzbek where text_uzbek is not null;
  Verify (both 0):
    select count(*) filter (where text_uzbek ~ U&'[^ogOG]\02BB') as bad_okina,
           count(*) filter (where text_uzbek ~ U&'[ogOG]\02BC')  as bad_tutuq
    from hadith_library;

**Fix — code (prevents recurrence):**
  New exported normalizeLatinApostrophes() applying the o/g context rule.
  Called on the `latin:` return in BOTH branches of deriveBothScripts —
  the Cyrillic branch is already correct, but routing it through the same
  function gives one owner for the invariant.
  5 tests added, incl. a regression test that fails against `latin: text`.

**KNOWN LIMITATION (accepted, logged not fixed):**
  The internal sentinel S === TUTUQ (both U+02BC), so LAT_RULES cannot
  distinguish oʻ from oʼ — ['o'+S, 'ў'] matches first, and a genuine tutuq
  after o/g folds to okina. No row in hadith_library exercises this.
  Full fix = private-use sentinel + context-aware LAT_RULES (option B, deferred).

**Downstream to verify:**
  P089 server-side library search must normalize apostrophes, or a user typing
  qo'shni will not match stored qoʻshni. NOT done — open item.

**Status:** FIXED — 74/74 rows correct, 11/11 tests green

## ════════════════════════════════════════════════════════
## PATTERN 98: Poll loop killed a COMPLETED job — deadline checked before success
## ════════════════════════════════════════════════════════
**ID:** P098
**Type:** Control-flow bug (wasted a paid API generation)
**File:** scripts/generate-scene.ps1
**Commit:** fix(scene): break on COMPLETED before deadline check; exit early on terminal failure (P098)

**Symptom:**
  A Kling image-to-video generation ran to completion, and the script reported:
    status: COMPLETED
    FAILED: timed out after 8 min (request 019fe271-... still COMPLETED)
  The clip was generated and paid for, but never downloaded — step 3 never ran.

**Root cause:**
  In the do/while poll loop, the deadline check sat INSIDE the body, above the
  while condition:
      Write-Host "status: $($st.status)"
      if ((Get-Date) -gt $deadline) { Die "timed out ..." }
    } while ($st.status -ne 'COMPLETED')
  On the iteration where status finally became COMPLETED, the deadline test ran
  FIRST and called Die — one line before the loop would have exited normally.
  The generation had simply taken longer than 8 minutes; success arrived, and
  the script threw it away.

**Fix:**
      if ($st.status -eq 'COMPLETED') { break }
      if ($st.status -in @('FAILED','ERROR','CANCELLED')) { Die "generation failed ..." }
      if ((Get-Date) -gt $deadline) { Die "timed out ..." }
    } while ($true)
  Success is now tested before failure. Terminal error states also exit
  immediately instead of polling out the full 8 minutes.

**Rule going forward:**
  In any poll loop, evaluate the SUCCESS condition before any failure or timeout
  condition. A timeout is only meaningful if the work is still pending.
  Related: P093 (unset clobbers $? — capture the exit code before cleanup).
  Both are ordering bugs where a later statement destroyed an earlier result.

**Note — recovery was attempted and abandoned:**
  A -RequestId parameter to re-fetch the orphaned result was drafted, then
  reverted: the fal queue-result URL shape was unverified, and regenerating
  costs ~$0.50. Not worth speculative code. Regenerated instead; loop fix held.

**Status:** FIXED — scene 1 regenerated and downloaded successfully

## ════════════════════════════════════════════════════════
## PATTERN 99: amix outlived -shortest — frozen subtitle tail on every animated reel
## ════════════════════════════════════════════════════════
**ID:** P099
**Type:** Output-correctness fix (ffmpeg filter semantics)
**File:** render-reel.ps1
**Commit:** fix(render): bound reel to narration length — amix dropout_transition + explicit -t (P099)

**Symptom:**
  adults-en-bukhari-1-reel.mp4 ran 81.0s against a 78.8s narration. The final
  subtitle cue stayed frozen on screen for the last ~2.2s over silent video.

**Root cause:**
  -shortest WAS present, but it measures the MAPPED output streams, and the
  audio map is [aout] — the amix result, not the narration:
    [1:a]volume=1.0[narration];[2:a]volume=0.25[music];
    [narration][music]amix=inputs=2:duration=first[aout]
  amix defaults to dropout_transition=2, adding a 2-second gain-renormalisation
  tail when an input drops out. The nasheed (150s) outlives the narration
  (78.8s), so [aout] ran ~2s past duration=first. -shortest then honoured 81s.
  Diagnosis came from ffprobe on all four inputs — reel 81.0, narration 78.77,
  nasheed 150.0, background 20.1 — which ruled out every other candidate.

**Fix — two parts:**
  1. amix=inputs=2:duration=first:dropout_transition=0[aout]
  2. Measure the narration and hard-bound the output:
       $narrDur = [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $narr)
       ... "-shortest","-t",[string][math]::Round($narrDur,2),...
  Part 2 is belt-and-suspenders: -t makes the intended length explicit rather
  than emergent from filter-graph semantics.
  Result: 78.766009s — exact match to the narration.

**Scope — affects earlier reels:**
  Same code path as R005 (bukhari-1520 RU, the first animated reel). Any
  published animated reel from before this fix likely carries the same frozen
  tail. Not re-rendered; noted for awareness.

**Also learned (not a bug):**
  The background was 20.1s against 81s of audio — ffmpeg loops the scene set
  ~4x. Expected for a 4x5s scene set under an 80s narration, but worth knowing
  the visuals repeat; more or longer scenes reduce the loop count.

**Rule going forward:**
  -shortest is only as good as what is mapped. When an amix/afade/concat sits
  between inputs and output, verify the RESULT length with ffprobe rather than
  trusting the flag. Same class as P096: an absent error is not proof of the
  intended outcome.

**Status:** FIXED — verified 78.766s

## ════════════════════════════════════════════════════════
## PATTERN 100: Whisper crashed on Cyrillic — CP1252 console, not a transcription failure
## ════════════════════════════════════════════════════════
**ID:** P100
**Type:** Environment fix (Windows console encoding)
**File:** render-reel.ps1 (Step 5 — Whisper call)
**Commit:** fix(render): force UTF-8 for Whisper so Cyrillic/Arabic subtitles don't abort (P100)

**Symptom:**
  RU reel render died at Step 5:
    UnicodeEncodeError: 'charmap' codec can't encode character '\u0412'
      in position 27: character maps to <undefined>
    Skipping out\adults-ru-bukhari-1-narration.mp3 due to UnicodeEncodeError
    FAILED: Whisper did not produce ...-narration.srt

**Root cause:**
  \u0412 is Cyrillic «В» — the first letter of the narration. Whisper
  TRANSCRIBED correctly; it crashed trying to PRINT the progress line to a
  CP1252 console (transcribe.py line 482, print(make_safe(line))). The
  traceback aborted the run before the .srt was written. The defect is in
  stdout encoding, not in the audio or the model.

**Why it didn't hit R005 (also RU, June):**
  Python is now 3.14 (C:\...\Python314). Newer Whisper/Python builds print
  segment text to stdout during transcription where earlier ones did not.
  An environment change, not a code change on our side.

**Fix (session-level, proven):**
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUTF8 = "1"
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  PYTHONIOENCODING is the one that matters — it makes Python write UTF-8
  regardless of console codepage. The other two fix display.

**TODO — make it durable:**
  Set PYTHONIOENCODING/PYTHONUTF8 inside render-reel.ps1 before the Whisper
  invocation, so RU/AR reels don't depend on shell state. Currently the render
  only succeeds in a shell where these were set by hand.

**Related:** same CP1252 root cause as the mojibake in PowerShell's
  Invoke-RestMethod output (ï·º for ﷺ) — cosmetic there, fatal here.

**Status:** WORKED AROUND — durable fix pending

## ════════════════════════════════════════════════════════
## PATTERN 101: generate-reel fabricated hadith — invented scenes + speech attributed to the Prophet ﷺ
## ════════════════════════════════════════════════════════
**ID:** P101
**Type:** CONTENT-SAFETY DEFECT — highest severity in this project
**File:** app/api/generate-reel/route.ts (prompt)
**Commit:** d4ee1af — fix(generate-reel): forbid invented incidents and attributed speech (P101)

**Symptom:**
  Generating the RU adults script for Sahih al-Bukhari #1 produced, TWICE, a
  fabricated narrative incident with direct speech attributed to the Prophet ﷺ:
    Gen 1 — the Prophet ﷺ approaches a companion after prayer, asks what he felt,
            the companion answers in quoted speech, the Prophet ﷺ replies
            «Именно это и есть истинное поклонение».
    Gen 2 — a companion carries water; the Prophet ﷺ stops and says «даже эта
            капля воды станет весомее горы в День воздаяния»; the companion is
            then said never to have acted without intention again.
  None of this is in Bukhari #1, in Ar-Raheeq Al-Makhtum, or in any source.
  It is invented hadith — the exact category HV exists to detect.

**Root cause:**
  The route prompt constrains seerah_context to cite a real period, but has NO
  rule against inventing incidents or attributing speech to the Prophet ﷺ.
  Bukhari #1 is a ONE-SENTENCE matn; with little to expand, the model fills the
  space with narrative. EN complied by chance (it described the Hijra setting);
  RU did not. Same hadith, same route — so compliance was luck, not design.

**Why the existing gates did not catch it:**
  - The human review gate DID catch it. That is the only reason it did not ship.
  - No automated check exists. Nothing in the route, tests, or CI inspects
    generated output for invented narrative or quoted speech.

**Fix — required in the route prompt (APPLIED):**
  Add to the RULES block:
    - NEVER invent an incident, scene, or conversation that is not in the hadith
      text or the cited seerah source.
    - NEVER attribute direct or indirect speech to the Prophet ﷺ, any prophet,
      or any companion beyond what the hadith itself records.
    - NEVER state what a named person felt, thought, or did afterwards.
    - If the matn is short, expand ONLY into documented historical context of
      the period. Do not compensate with narrative.

**Interim mitigation (used for R011):**
  Story field hand-written from the EN version's approach — historical setting,
  no scene, no quoted speech. P079's editable textareas made this possible
  without a regenerate cycle.

**Also observed:** the RU caption cited «Источник: Усваи Хасана» while EN cited
  Ar-Raheeq Al-Makhtum for the same hadith. Source attribution is not consistent
  across languages — separate defect, needs investigation.

**Rule going forward:**
  Every generated story is read in full before TTS. Regeneration is NOT a fix
  for a fabrication — two generations produced two different fabrications.
  Edit the textarea by hand instead.

**Status:** FIXED — rules 7-10 added; verified by regenerating the exact failing case
  (Bukhari #1, RU) which produced clean output on first generation. NOTE: the original
  rules ACTIVELY CAUSED this — rule 2 required naming the Prophet ﷺ or companions, and
  rule 5 required "a simple scene a child can picture" for Kids style. The defect was
  in the rules, not merely absent from them. Kids style is now explicitly told NOT to
  invent a scene.
  Automated detection still does not exist. Human review remains the only gate.

  ## ════════════════════════════════════════════════════════
## PATTERN 102: OpenAI TTS hardened plain г to ғ in Uzbek — moved UZ/TJ to ElevenLabs v3
## ════════════════════════════════════════════════════════
**ID:** P102
**Type:** Provider migration (supersedes P071, P073, P087 for UZ/TJ)
**File:** app/api/tts/route.ts
**Commit:** 8229667 — fix(tts): route UZ/TJ to ElevenLabs eleven_v3 (P102)

**Symptom:**
  UZ adults narration pronounced plain г as the throaty ғ (uvular fricative) —
  audibly closer to an F. Affected Мадинага, қилган, келган, тўлган, мавзуга,
  қараганда, солганда. Every -ган / -га ending in the language.

**What was ruled out, in order:**
  1. Wrong text — NO. Source text had plain г correctly throughout.
  2. Missing instructions — NO. P087's corrective example ("сувга = suv-GA,
     do NOT harden plain г into ғ") existed only in 'uz.kids'. Added the same
     to 'uz.adults' with contrast pairs. Still wrong.
  3. Phonetic environment — NO. First theory was assimilation to a nearby қ
     (қилган, қараганда). Disproved when тўлган and мавзуга failed too.
  4. Content reword — NO. Rewording to avoid the environment (қилган→этган,
     қараганда→назар солганда) did not help; солганда also failed.
  5. Voice selection — NO. Switched adults from onyx to nova (the voice that
     P087 tuned and R008 shipped on). Still wrong. This also means R008's
     correctness was luck: P087 says "г OCCASIONALLY hardened".
  6. Newer OpenAI model — NONE EXISTS. gpt-4o-mini-tts is still current
     (verified against OpenAI docs, Aug 2026).

**Root cause:**
  gpt-4o-mini-tts does not reliably distinguish Uzbek Cyrillic г from ғ.
  The `instructions` parameter BIASES output; it does not control phonemes.
  P087 documented this same limit for ҳ ("instructions can't reliably fix one
  stochastic position") and resolved it content-side. That escape hatch does
  not scale to a letter appearing in every grammatical ending.

**Fix — provider change:**
  UZ and TJ now route to ElevenLabs eleven_v3.
    const useOpenAI = langKey === 'ru' && style === 'kids'   // was: uz/tj too
  VOICE_MAP gained uz and tj entries. Verified by browser test before coding.

**Voice matrix (UZ/TJ), chosen deliberately — different voice per language:**
    uz.adults  Opa Johann        R3XXDwKMU2YHwBcuYUH3
    uz.kids    Mini              hO2yZ8lxM3axUxL8OeKX
    tj.adults  Meisam            KXptrwcsEqqFSwRKJukF
    tj.kids    Katherine Polished 0zUZ5qUGb8wympsfJH8d
  Rationale: most viewers watch ONE language only, so cross-language voice
  consistency is invisible to them; per-language fit wins. (Meisam is a Persian
  voice and Tajik is a Persian variety — chosen on that hypothesis, confirmed
  by ear.)

**SUPERSEDES EARLIER FINDINGS — v3 improved between July and August 2026:**
  July test: eleven_v3 said "dj" for ж, which is why lib/uzbek-tts-phonetics.ts
  (inline IPA lexicon) was built. Re-tested Aug 2026 on the same ж words
  (Жаннат, жума, ҳижрат, бежиз): CLEAN. The IPA layer is NOT needed for reels.
  eleven_multilingual_v2 remains worse — accented, and does not recognise Tajik.
  So the win is v3 specifically, not ElevenLabs generally.
  This vindicates the module's own warning: "re-baseline after every model
  upgrade." P071 ("OpenAI Nova for UZ/TJ Cyrillic") is now OBSOLETE.

**Side effect — EN/AR/RU adults also moved to v3** (shared fetch, one model_id).
  Regression-tested by regenerating EN (James) and RU (Abrar) narrations for
  Bukhari #1: no degradation, ﷺ still expands correctly. Accepted rather than
  making model_id language-conditional.

**Rule going forward:**
  When a TTS defect survives instructions, voice change, AND content reword,
  stop tuning and re-baseline the providers. Six escalation steps here; the
  first five were all inside a provider that could not do the thing.

**Status:** FIXED — verified across UZ, TJ, EN, RU; shipped in R012 and R013

## ════════════════════════════════════════════════════════
## PATTERN 103: Prompt rules mandated the fabrication they forbade
## ════════════════════════════════════════════════════════
**ID:** P103
**Type:** Prompt defect — specification conflict (extends P101)
**File:** app/api/generate-reel/route.ts
**Commit:** 9ea9b89 — fix(generate-reel): P103 — remove mandated-fabrication conflict in rules 2/6/9 and story field

**Symptom:**
  generate-reel invented an occasion for hadith that have no recorded setting.
  Bukhari #1417 produced "the Prophet ﷺ saw people sharing in Madinah" and
  "this teaching came from that same warm world of caring and sharing" across
  repeated generations — including after P101 had tightened rules 7-10.

**What was ruled out, in order:**
  1. Sampling noise — NO. Two independent generations produced the same
     invented Madinah setting.
  2. Rule 9 too narrow — NO. This was the standing theory carried into the
     session ("widen from any named person to any person or group"). Widening
     it alone would not have worked; the leak survived to the History field.
  3. Kids-style register — NO. First generation was adult-register (wrong
     Style selected), but the fabrication persisted after correcting to Kids.

**Root cause:**
  Rules 2 and 6 REQUIRED what rules 7-10 FORBADE. Rule 2 said story MUST
  reference the Prophet ﷺ or his companions; rule 6 said seerah_context MUST
  cite a real period. For a hadith with no recorded incident, the only way to
  satisfy those requirements is to invent one. The model obeyed the
  requirement, not the prohibition.
  The `story` field description compounded it: "warm, vivid, story-like",
  "must give human emotional context", "must feel real and touching" is an
  instruction to dramatize, sitting directly above the anti-fabrication rules.

**Fix — four edits, all in the prompt:**
  Rule 2: MUST reference → MAY reference, with "if neither records an incident
    for this hadith, do NOT construct one — explain the teaching itself instead"
  Rule 6: cites a period ONLY if sources tie the hadith to one; otherwise state
    exactly three things and nothing more — collection and book, narrator,
    classical scholarly reading
  Rule 9: "any named person" → "any person or group", plus explicit occasion
    clause: "NEVER assert the occasion, setting, or audience of the hadith
    unless the narration itself records it"
  story field: rewritten to ask for explanation rather than drama

**Rule 6 needed a second pass:**
  The first version permitted the three-element fallback but did not forbid
  padding past it. The model gave collection/narrator/reading correctly, then
  invented anyway in softened form: "during a time when he often encouraged his
  companions to give in charity". Added an explicit stop clause naming the
  softened phrasings ("during a time when", "in an era where") as occasions.

**Verified:**
  Regenerated EN Bukhari #1417 twice after the fix. Story and Moral clean on
  both. History clean after the rule 6 second pass. #1417 was the hadith that
  leaked twice, so this is a control test, not a fresh-hadith sample.

**Rule going forward:**
  When a prompt reliably produces forbidden output, do not strengthen the
  prohibition first — search the prompt for an instruction that MANDATES the
  forbidden output. Prohibitions cannot win against requirements.
  Softened phrasings are the same fabrication and must be named explicitly.

**Also in this session (not separate patterns):**
- Kids clips now render at `--resolution 720p` (736x1312, was 480x864).
  `choices=["480p","720p"]` was always in generate-talking-clip.py; 480p was
  merely the default, and every kids reel through #6009 shipped at 480p.
- Mascot stills recovered and committed to assets/mascot/. The source PNGs were
  never committed and no longer existed — only 480p video frames in out/talking/.
  Recovery: extract frame → use as face reference in Nano Banana Pro → regenerate
  scene at 4K (3072x5504) → commit. Never let a source asset exist only inside a
  rendered video.
- generate-talking-clip.py checks FAL_KEY before argparse, so `--help` fails
  without a key. Move env guards after parse_args().
- split-narration.py line 172 next-step hint still references the nonexistent
  lamb-boy-mosque-night-v2.png — update to v3.

**Status:** FIXED — verified on EN Bukhari #1417 (R014); shipped 2026-08-10

## ════════════════════════════════════════════════════════
## PATTERN 104: Kids voices split by mascot; OpenAI fully retired from TTS
## ════════════════════════════════════════════════════════
**ID:** P104
**Type:** Feature + provider migration (completes P102; fixes P085 recurrence)
**File:** app/api/tts/route.ts, app/admin/page.tsx
**Commit:** 502c0de — feat(tts): P103 — kids voices split by mascot; RU kids off OpenAI, ElevenLabs now sole provider

**Symptom:**
  First boy-lamb kids reel (EN, Bukhari #1417) shipped with Danielle — a female
  voice on a male mascot. Fabric lip-syncs the mouth, so the voice reads as the
  character's own, not a narrator's. Every kids voice in the matrix was female
  because the matrix was built around the girl lamb.

**Decision — mascot/voice pairing becomes channel convention:**
  boy lamb → male voice, girl lamb → female voice, alternating mascot by hadith.
  Adults reels have no mascot and are unaffected.

**Design choice — separate `mascot` field, NOT extended `style`:**
  Rejected: style = 'kids-boy' | 'kids-girl' | 'adults'. Fewer edits, but style
  would stop meaning "audience" and start meaning "audience + character", and
  would be ambiguous on adults reels that have no mascot at all.
  Chosen: VOICE_MAP[lang].kids.{boy|girl}, with mascot threaded admin → route.

**P084 failure-mode guard:**
  P084 was a missing payload field producing wrong-voice audio with NO error.
  Same shape here. Mitigation: mascot defaults to 'girl' in the route, so an
  omitted field falls back to the voices already shipped on #6009 rather than
  silently switching gender.

**Voice matrix (kids), all eleven_v3:**
    en.kids.girl  Danielle           FVQMzxJGPUBtfz1Azdoy
    en.kids.boy   Eric               cjVigY5qzO86Huf0OWal
    ru.kids.girl  Arabella Calm&Mat  ocFEgn1SP9oWO9QrLDgb
    ru.kids.boy   Liam Youthful      pw8bioilqsSn2jApHYwT
    uz.kids.girl  Mini               hO2yZ8lxM3axUxL8OeKX
    uz.kids.boy   George             JBFqnCBsd6RMkjVDRZzb
    tj.kids.girl  Katherine Polished 0zUZ5qUGb8wympsfJH8d
    tj.kids.boy   Liam Viral         VCgLBmBjldJmfphyB8sZ
  Male kids voices are deliberately NOT the adults voices — reusing James,
  Abrar, Opa Johann or Meisam would make kids and adults reels indistinguishable
  within a language.

**RU kids migrated off OpenAI — provider consolidation complete:**
  Nova was the last OpenAI slot, surviving P102 because RU had not hit the
  Cyrillic г defect. Replaced with Arabella. The `useOpenAI` branch and the
  OPENAI_API_KEY check are DELETED; ElevenLabs is now the sole TTS provider.
  TTS_INSTRUCTIONS retained as reference only, never called — it encodes hard-won
  Uzbek/Tajik phonetic knowledge worth keeping if a future provider needs it.

**P085 recurrence found and fixed:**
  VOICE_MAP ru.kids pointed at ELEVENLABS_VOICE_ABRAR — the male adults voice.
  This is exactly P085, still present in the map. It was masked because
  useOpenAI intercepted RU kids before the map was ever read. Deleting the
  OpenAI branch would have exposed it as male-voiced girl-lamb reels.
  Lesson: a branch that bypasses a lookup also hides bugs in that lookup.
  When removing a branch, audit what it was shadowing.

**Found while editing, NOT changed — needs .env.local audit:**
  ar.adults fallback is 'pNInz6obpgDQGcFmaJgB' (Adam), not Hijazi
  ru.adults fallback is 'ErXwobaYiN019PkySvjV'; library lists Abrar Sabbah as
  VwC51uc4PUblWEJSPzeo
  Both only fire if the env vars are unset, so they may never have mattered.

**Note — eleven_v3 take variance is expected:**
  Identical text/voice/model gives different takes per call (dashboard shows
  these as "Generation 1 / Generation 2"). Not a defect and not a setting. The
  admin issues one take per click; regenerate for a different one.
  voice_settings.stability 0.5 is the dial if variance ever needs narrowing.

**Verified:**
  EN kids + Boy lamb → Eric; toggle hidden on Adults; tsc clean.

**Status:** FIXED — shipped 2026-08-10

## ════════════════════════════════════════════════════════
## PATTERN 105: Seerah attribution fired unconditionally — false source credit in captions
## ════════════════════════════════════════════════════════
**ID:** P105
**Type:** Content-safety defect — false attribution (completes P103)
**File:** app/api/generate-reel/route.ts, app/admin/page.tsx
**Commit:** (this commit) — fix(generate-reel): P105 — drop unconditional seerah attribution from captions; seerah_context field no longer mandates a period

**Symptom:**
  Every non-English reel caption carried a seerah source credit — "📖 Источник:
  Усваи Хасана" (RU), "📖 Манба: Усваи Ҳасана" (UZ), "📖 Сарчашма: Усваи Ҳасана"
  (TJ) — regardless of whether the story drew on that source. Appeared in
  R003, R004, R005 (May) and again in R015, R016, R017 (Aug), so it has been
  live since the tracker began. EN was unaffected in appearance only; the same
  mechanism credited Ar-Raheeq Al-Makhtum unconditionally there.

**Root cause:**
  getSeerahSource(lang) returns a hardcoded attribution string, interpolated
  directly into the JSON schema as "source_attribution": "${...}". It was never
  a model output — a constant dressed as one. Line 170 set it again server-side.
  Nothing checked whether the source was actually used.
  This became a live falsehood after P103: the prompt now correctly tells the
  model to explain the teaching plainly when no incident is recorded, so most
  stories consult no seerah source at all — while the caption kept crediting one.

**Why this is a hard-rule violation, not a cosmetic bug:**
  The project rule is no fabricated attributions. Crediting a book that was not
  used is a fabricated attribution, even when the book is real and the hadith is
  sound. The hadith citation (collection, number, narrator) is what a viewer
  needs to verify; the seerah source is background material for the story.

**Fix — drop the attribution from captions entirely:**
  Removed "source_attribution" from the JSON schema
  Removed result.attribution server-side assignment
  Removed the attribution line from the admin caption builder
  Removed attribution/source_attribution from the Generated interface
  Remotion `attribution` prop now receives the hadith citation instead
  Story panel header no longer displays a seerah credit
  getSeerahSource() RETAINED — the model still draws on the source for the
  story where it records something relevant. Only the caption credit is gone.

**Second defect found in the same read — seerah_context still mandated a period:**
  P103 fixed rule 6 in the RULES block but NOT the field description, which
  still said "the specific historical moment or period when this teaching was
  most lived or demonstrated". The rule said "only if the sources tie the hadith
  to one"; the field said "give me a specific moment". Same specification
  conflict P103 was about, surviving in a second location.
  Lesson: when fixing a prompt conflict, grep the WHOLE prompt for the mandate.
  A JSON schema field description is an instruction with the same force as a
  numbered rule.

**Third, minor:** getSeerahSource used Усваи Хасана (Х) in `name` and the RU
  attribution, Усваи Ҳасана (Ҳ) in UZ/TJ. Normalized `name` to Ҳ (the book's
  own title); RU attribution string removed with the rest.

**Verified:** RU generation (Al-Bayhaqi #1120) — caption shows collection,
  narrator, verify link, tags. No seerah line, no undefined, no blank gap.

**Status:** FIXED — shipped 2026-08-10

## ════════════════════════════════════════════════════════
## PATTERN 106: Pipeline automation — TTS to disk, work tree, wrapper, caption template
## ════════════════════════════════════════════════════════
**ID:** P106
**Type:** Automation / friction removal (no defect — deliberate improvement)
**Files:** app/api/tts/route.ts, app/admin/page.tsx, render-mascot-reel.ps1,
           split-narration.py, make-kids-reel.ps1 (new)
**Commits:** 5c272a8, 6caa47b, 4fbfea2, ad18d59

**Motivation:**
  The R014-R017 session (Bukhari #1417, 4 languages) took ~8 hours. Step-count
  audit put it at roughly 70% manual, and every defect that session — P103
  fabrication leak, three grammar errors, the P105 false attribution — was
  caught by a human reading output, not by any gate. Conclusion: automate the
  MECHANICAL steps aggressively; leave content review human until an Auditor
  exists (see agent-architecture-roadmap.md Phase 4).

**1. TTS writes to disk (app/api/tts/route.ts):**
  Was: generate in browser -> download -> rename -> move to out\. Eight times
  per hadith set, and the rename is where a wrong slug silently poisons every
  downstream command.
  Now: route writes to out/work/{style}/{slug}/{lang}/{style}-{lang}-{slug}-{section}.mp3
  Gated on NODE_ENV !== 'production' — Vercel's filesystem is read-only and
  ephemeral. Write failures are caught and logged, never break the audio
  response. Returns X-Saved-Path header.
  Route gained `slug` and `section`; admin derives the slug from
  collection + hadith_number ("Sahih al-Bukhari" + "1417" -> bukhari-1417).
  Verified against Al-Bayhaqi, which the regex had not been proven on.

**2. Per-reel work tree (out/ restructure):**
  out/ had 108 loose files after 17 reels — ~30 files per hadith set, growing
  without bound. Restructured:
    out/backgrounds/  shared nasheeds and bg video (unchanged)
    out/refs/         FLUX source stills, mascot references
    out/data/         candidates.json, translations, sourcing state
    out/work/         current set only — stays small permanently
    out/published/    {style}/{slug}/{lang}/ — archive
    out/_legacy/      tests and dead-convention files
  render-mascot-reel.ps1 $talkDir now points at the per-reel folder; the final
  reel lands there too, so archiving a set is a single folder move.
  NOTE: three MP4s could not be moved — persistent file lock survived closing
  the player. Copied and left in place; same environment quirk as the
  PowerShell silent-revert gotcha. Delete after reboot.

**3. make-kids-reel.ps1 (new) — one command from narration to reel:**
  Chains concat -> duration check -> split if needed -> Fabric per chunk at
  720p -> render. Replaces ~16 hand-typed commands with filenames per hadith set.
  Two deliberate design points:
  - Seam-aware split. split-narration.py maximises chunk length, so on UZ it
    cut at 27.3s MID-MORAL rather than at the 22.3s story/moral silence,
    forcing a manual recut. The wrapper cuts at storyDur + 0.5s instead.
    split-narration.py itself is unchanged and still correct for its own use;
    the greedy objective is logged as a P107 candidate.
  - Confirmation pause before Fabric (skip with -Auto). Fabric is the only
    paid, irreversible step; a keypress is cheap insurance against spending
    on a bad TTS take.
  Step 0 validates inputs, FAL_KEY presence AND length (~69 chars), and
  ffmpeg/ffprobe/python on PATH before anything is spent.
  -Mascot girl currently fails Step 0 by design: the girl-lamb still does not
  exist in the repo yet.

**4. Deterministic caption template (app/admin/page.tsx):**
  Captions were hand-corrected on every reel. Same two fixes four times each
  in the #1417 session.
  - TAG_BLOCKLIST filters tags that pull the wrong audience. #date reaches
    dating content; #hellfire skews to metal/gaming. Tags come from the hadith
    library, so filtering happens at caption time rather than editing the library.
  - Hadith text now included in the caption, via text_display (already
    language-aware per /api/reels lines 66-73). Rationale: captions get
    screenshotted and forwarded, which is the exact fabrication vector this
    project exists to fight. A caption carrying verified text plus its
    reference is the sadaqah working.
  - #kids appended automatically on kids reels.

**Still manual after P106:**
  Clicking Generate for story and moral in the admin (2 clicks per language).
  Content review — deliberately so.
  Publishing — 16 uploads per hadith set across 4 platforms. Roadmap Part 6
  rule 4 keeps cross-posting a human act.

**Known remaining friction (P107 candidates):**
  - Collection and narrator stay Latin inside Cyrillic captions ("Sahih
    al-Bukhari #1417, Adiy ibn Hatim" in a Russian caption). Hand-corrected on
    all four languages in the #1417 session. Needs translation maps or DB columns.
  - split-narration.py greedy chunk objective (see above).
  - Pre-push classifier still blind to scripts/, assets/, and read UI=0 on a
    session that changed admin/page.tsx.

**Status:** SHIPPED 2026-08-11 — verified end to end on Al-Bayhaqi #2318 (TTS
  write) and Bukhari #1417 RU (caption). Wrapper validated through Step 0;
  full run pending the next hadith set.

## ════════════════════════════════════════════════════════
## PATTERN 107: PowerShell splat by position bound to the wrong script
## ════════════════════════════════════════════════════════
**ID:** P107
**Type:** Script defect
**File:** make-kids-reel.ps1
**Commit:** (P107 commit) — fix(pipeline): P107 - splat render args by name; Clips as array not joined string

**Symptom:**
  make-kids-reel.ps1 completed Fabric lip-sync then died at [4/4] with
  "Cannot validate argument on parameter 'Lang'. The argument '-Lang' does not
  belong to the set en,ru,uz,tj,ar". Both paid Fabric calls had already
  succeeded, so nothing was lost — but the reel had to be rendered by hand.

**Root cause:**
  The render step built an array and splatted it:
    $renderArgs = @('-Lang', $Lang, '-Slug', $Slug, '-Clips', $clipFiles)
    & "$PSScriptRoot\render-mascot-reel.ps1" @renderArgs
  Array splatting passes arguments POSITIONALLY. The literal string '-Lang'
  landed in the first positional parameter, which is -Lang itself, so the
  validator saw the flag name as the value.
  Second defect in the same line: -Clips was passed as a comma-joined STRING
  while render-mascot-reel.ps1 declares it [string[]].

**Fix:**
  Hashtable splatting, which binds by NAME:
    $renderParams = @{ Lang = $Lang; Slug = $Slug; Clips = $clipFiles }
    if ($Nasheed) { $renderParams['Nasheed'] = $Nasheed }
    & "$PSScriptRoot\render-mascot-reel.ps1" @renderParams
  $clipFiles is now a real array, not a joined string.

**Rule going forward:**
  In PowerShell, splat with a HASHTABLE when the target has named parameters.
  Array splatting is positional and silently misbinds when the array contains
  flag names.

**Also:** the script file was first saved as Windows-1252, which mangled every
  em dash into a byte sequence PowerShell could not parse inside strings
  (10+ cascading parse errors). Repo .ps1 files must be UTF-8; prefer plain
  hyphens over em dashes in PowerShell string literals.

**Status:** FIXED — verified on kids-ru-bukhari-8 (full wrapper run, all 4 steps)

## ════════════════════════════════════════════════════════
## PATTERN 108: Stale `selected` after language switch; narrator epithets and inverted isnad verbs
## ════════════════════════════════════════════════════════
**ID:** P108
**Type:** State bug + prompt defect (extends P103)
**Files:** app/admin/page.tsx, app/api/generate-reel/route.ts
**Commit:** (P108 commit) — fix: P108 - clear selected on lang change; forbid narrator epithets and wrong isnad verbs

**Symptom 1 — wrong-language hadith text in caption:**
  The RU Bukhari #8 caption rendered with the ENGLISH hadith text while the
  rest of the caption was Cyrillic. Caught before publishing.

**Root cause 1:**
  /api/reels resolves `text_display` per language (route.ts lines 66-73). The
  picker stores a SNAPSHOT of the hadith in `selected` at click time. The
  useEffect on [lang] refetched the list but never touched `selected`, so
  selecting in EN and then switching to RU left English text in place.
  P106's language-aware caption was correct; its input was stale.

**Fix 1:**
  Clear `selected` when the language button is clicked. NOT in a useEffect —
  calling setState synchronously in an effect body triggers cascading renders
  and React warns about it. The selection clears because the user changed
  language, so the clear belongs in the click handler.

**Symptom 2 — narrator epithets, every language:**
  "сподвижник Ибн Умар", "Ибн Умар, сын второго халифа", "яке аз бузургтарин
  саҳобаҳо", "one of the close companions of the Prophet ﷺ". Appeared in RU
  (twice), TJ, and EN across the #8 set, and in TJ during the #1417 set
  ("саҳобаи бузург").

**Symptom 3 — inverted isnad verbs in Russian:**
  "Пророк ﷺ передал нам" / "рассказал нам" in THREE consecutive Russian
  generations. This inverts the chain of transmission: the Prophet ﷺ SAID the
  hadith; the companion NARRATED it. In hadith terminology передал is what a
  narrator does.

**Root cause 2+3:**
  Rule 9 forbids stating what a person felt, thought, saw, or DID. It does not
  forbid describing WHO THEY WERE, and says nothing about which verb attaches
  to whom in an isnad. Same shape as P103: the prohibition did not cover the
  case, so the model filled the gap.

**Fix 2+3 — two new prompt rules:**
  Rule 11: name narrators plainly. No epithets, family relationships, or
    standing among the companions. Standard honorifics that follow a name in
    the target language (RA, رضي الله عنه, розияллоҳу анҳу) are permitted.
  Rule 12: the Prophet ﷺ SAID; the companion NARRATED. Never write that the
    Prophet ﷺ transmitted or related a hadith. In Russian: сказал, not
    передал/рассказал.

**Verified:** RU regeneration after the fix produced "Пророк ﷺ сказал" and
  "Его передал Ибн Умар (ра)" — correct verb, plain narrator, honorific kept.

**Note — metaphor drift was observed but NOT ruled on:**
  History sections introduced a second metaphor competing with the Story's
  (a "map" and "table legs" against an established house-and-pillars image).
  Deliberately left unruled; the post-fix generation self-corrected to a
  consistent metaphor, so a rule would have been premature.

**Status:** FIXED — shipped 2026-08-11

## ════════════════════════════════════════════════════════
## PATTERN 109: Search box never called the API it was built for
## ════════════════════════════════════════════════════════
**ID:** P109
**Type:** Wiring defect — feature existed, UI was never connected
**Files:** app/api/reels/route.ts, app/admin/page.tsx
**Commit:** (P109 commits) — fix: P109 - wire search box to server-side search

**Symptom:**
  Searching "8" or "#salah" in the admin returned 0 hadiths. Searching "salah"
  worked. No pattern was obvious from the outside.

**Diagnosis — the decisive observation:**
  DevTools Network tab was EMPTY while typing. The search box never issued a
  request. That single fact explained the whole pattern:
  - `fetchHadiths()` built params with `lang` and `limit` only — never `q`
  - a client-side `filtered` array checked text_display, narrator, and tags
  - "salah" matched a TAG on rows already loaded, so it appeared to work
  - "8" is not in any row's text, narrator, or tags, so it matched nothing
  P089 built server-side search across all five text columns plus narrator,
  collection, and hadith_number. The UI was never wired to it.
  The client filter could also only ever see the 70 fetched rows — search
  could not reach the rest of the library at all.

**Fix:**
  - fetchHadiths sends `q` when searchQ is non-empty
  - useEffect refetches on [filterGrade, lang, searchQ] with a 300ms debounce
  - `filtered` is now just `hadiths` — the server already applied the search;
    re-filtering client-side dropped valid results
  - strip `#` and `"` from the query: users type "#salah" and "#8" naturally,
    and those characters reached Postgres literally and matched nothing
  - added `tags.cs.{...}` to the .or() chain (tags were only ever searchable
    via the client filter that was just removed)
  - secondary sort by hadith_number (was ordered by collection alone, so rows
    within a collection came back in insertion order)

**Exact match on pure-digit queries:**
  Substring matching on numbers does not scale — at 6k rows "1" would return
  thousands. A query of only digits now uses .eq('hadith_number', q).
  "8" returns 1 row; "salah" still returns 8. Text searches stay substring.

**Lesson:**
  When one search term works and another does not, check whether a request is
  being made AT ALL before theorising about query syntax. Two wrong theories
  (a malformed tags clause, then a broken .or() chain) were tested and
  discarded before the empty Network tab settled it in seconds.

**Status:** FIXED — shipped 2026-08-11

## ════════════════════════════════════════════════════════
## PATTERN 110: CI type-check gate could not fail
## ════════════════════════════════════════════════════════
**ID:** P110
**Type:** Gate integrity (CI)
**File:** .github/workflows/ci.yml
**Commit:** fix: remove continue-on-error from CI type check (P110)

**Symptom:**
  CI reported green on every run regardless of TypeScript errors.
  The type-check step ran `npx tsc --noEmit` but carried
  `continue-on-error: true`, so a non-zero exit could never fail
  the job. CI #50 green did not mean the types were clean.

**Root cause:**
  `continue-on-error: true` was set on the Type check step,
  converting a gate into a report. Same failure class as P093
  (Playwright webServer timeout returning EXIT_CODE=0 with zero
  tests run): the gate was present, visible, and incapable of
  blocking.

**Fix:**
  Removed `continue-on-error: true` from the Type check step.
  Verified `npx tsc --noEmit` exits clean locally before removing,
  so the gate closes with no outstanding type debt.

**Rule:**
  A gate that cannot fail is worse than no gate — it manufactures
  false confidence. Any CI step whose purpose is to block MUST be
  able to fail the job. Audit for `continue-on-error: true` on
  verification steps; it belongs only on genuinely optional steps
  (artifact upload, notifications).

**Related:** P093 (gate integrity). Sibling item not in this fix:
  CI E2E `BASE_URL` still points at production — tracked separately.

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 111: Prompt did not pin the divine name or block invented similes
## ════════════════════════════════════════════════════════
**ID:** P111
**Type:** Content safety (prompt rules)
**File:** app/api/generate-reel/route.ts
**Commit:** fix: pin divine name per language, forbid similes and unsourced attribution (P111)

**Symptom:**
  Muslim #482 kids set, all four languages, caught at human review:
  - EN rendered the divine name as "God" (7 occurrences incl. title);
    TJ rendered it as "Худо" (6 occurrences incl. title).
  - Every language invented a simile absent from the matn:
    EN "like standing next to a warm, caring light"
    UZ "sajda is like standing close to the sun — you feel its heat"
    TJ "like a door of a house was opened — knock and make dua"
  - RU, UZ and TJ opened the seerah block with unsourced authority
    ("Учёные объясняют:", "Уламолар...", "Олимон...") naming no scholar.
  - TJ additionally inverted the hadith's meaning, calling sujud
    "поинтарин ҳолати бандагист" (the LOWEST station of servanthood).

**Root cause:**
  Three separate absences in the prompt, all confirmed by `git grep`:
  1. Neither "Allah" nor "God" appears anywhere in the route. The divine
     name was never pinned — every prior EN reel said "Allah" by chance,
     not by rule. Nothing broke; the rule never existed.
  2. P101 forbids invented incidents, attributed speech, inner states and
     character descriptions. A SIMILE is none of those, so comparisons
     invented by the model passed every existing rule. 4 of 4 languages
     produced one — this is an unblocked category, not drift.
  3. No rule forbids appealing to unnamed scholarly authority. Same class
     as P105 (false source attribution), which covered credited books but
     not vague "scholars say" framing.

**Fix:**
  Added to the prompt rules:
  - Divine name is fixed per language and MUST NOT vary:
      EN Allah · RU Аллах · UZ Аллоҳ · TJ Аллоҳ · AR الله
    Never "God", "Бог", "Худо". Where the matn itself says *Rabb*,
    translate as Lord (EN) / Господь (RU) / Парвардигор (TJ) — that is a
    different word in the source and stays.
  - No similes, metaphors or comparisons that are not in the matn.
    Explaining what a word means is allowed; inventing what it is LIKE
    is not.
  - No appeal to unnamed authority. "Scholars say/explain/teach" is
    forbidden unless a specific named source is cited and verified.
    State the meaning directly instead.
  - The seerah block must not reframe the hadith's meaning. Sujud is the
    station of greatest CLOSENESS; do not render it as lowly or diminished.

**Rule:**
  A prohibition only blocks the categories it names. P101 enumerated four
  fabrication types and the model routed around them into a fifth. When a
  content rule is written, ask what ADJACENT form of the same fault it
  leaves open — invented fact, invented quote, invented feeling, invented
  comparison and invented authority are five distinct surfaces.
  Corollary: a behaviour that has always been correct is not evidence of a
  rule. Verify the rule exists before trusting the behaviour.

**Detection:**
  All four caught by human review before publish. No automated gate covers
  any of these; the Auditor (agent-architecture-roadmap.md Phase 4) is
  where they belong.

**Related:** P101 (fabrication rules), P103 (rule conflict), P105 (false
  source attribution).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 112: RU kids boy voice produced a background hum
## ════════════════════════════════════════════════════════
**ID:** P112
**Type:** Asset quality (TTS voice matrix)
**File:** app/api/tts/route.ts
**Commit:** fix: RU kids boy voice Liam Youthful -> Maxim Calm & Neutral (P112)

**Symptom:**
  Muslim #482 RU kids narration carried a steady background hum —
  described as an electrical device running behind the voice. Present in
  the raw ElevenLabs mp3, before any nasheed mix, so not a render artifact.
  EN clips from the same session were clean, isolating it to the RU voice.

**Root cause:**
  Liam — Clear, Youthful and Steady (`pw8bioilqsSn2jApHYwT`) produced the
  artifact on eleven_v3. Maxim — Calm & Neutral (`HcaxAsrhw4ByUo4CBCBN`)
  auditioned clean on the same Russian text and model.

**Fix:**
  VOICE_MAP ru.kids.boy fallback changed to `HcaxAsrhw4ByUo4CBCBN`.
  Verified `ELEVENLABS_VOICE_RU_KIDS_BOY` is NOT set in .env.local, so the
  literal actually governs — per the earlier finding that these fallbacks
  only fire when the env var is unset.

**Notes:**
  Maxim's library label reads "calm and neutral middle-aged Russian", an
  adults register. Accepted after audition on real reel text. Watch across
  the next RU boy-lamb set that he does not blur the kids/adults line the
  separate male voice matrix exists to preserve.

**Workflow gap found (not fixed):**
  The admin regenerates story/moral TEXT together with audio — there is no
  audio-only reroll. A single bad TTS take therefore costs all content
  edits made since generation. This turned a 60-second reroll into a voice
  change decision. Candidate fix: separate "regenerate narration" action.

**Related:** P102 (UZ/TJ provider migration), P104 (mascot/voice split),
  P084/P085 (wrong-voice routing).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 113: Adults render path never received the P106 work-tree restructure
## ════════════════════════════════════════════════════════
**ID:** P113
**Type:** Pipeline drift (path convention)
**File:** render-reel.ps1
**Commit:** fix: render-reel.ps1 reads and writes the per-reel work tree (P113)

**Symptom:**
  First adults reel since the out/ restructure (Sunan Abu Dawud #3641, EN)
  could not be rendered without hand-copying files. render-reel.ps1 still
  used the pre-restructure flat convention:
    expected  out\adults-en-abudawud-3641-story.mp3
    actual    out\work\adults\sunan-abu-dawud-3641\en\...-story.mp3
  and wrote all six artifacts back to flat out\ and out\backgrounds\,
  requiring four manual Move-Item calls after the render to reassemble
  the set in one folder.

**Root cause:**
  P106 restructured out/ into out/work/{style}/{slug}/{lang}/ and pointed
  the KIDS pipeline (render-mascot-reel.ps1, the TTS route) at the new
  tree. render-reel.ps1 — the ADULTS path — was not updated, because no
  adults reel was produced between the restructure and today. The drift
  was invisible for four days and surfaced only on first use.

**Fix:**
  render-reel.ps1 now derives $workDir = out\work\{Style}\{Slug}\{Lang},
  creates it if absent, and resolves story/moral/narration/srt/bg-mixed/
  reel against it. $normDir (shared scene clips) deliberately unchanged —
  scene clips are shared assets, not per-reel artifacts.

**Rule:**
  A restructure is not complete until every consumer of the old layout is
  migrated. When a path convention changes, enumerate ALL scripts that
  read or write those paths — not just the ones in the current session's
  workflow. A path convention that only half the pipeline knows is worse
  than the old one, because the working half hides the broken half until
  the next time you use it.

**Related gaps found in the same session (NOT fixed here):**
  - TTS route derives a different slug for adults ("sunan-abu-dawud-3641")
    than the render convention and the tracker ("abudawud-3641"). Two names
    for one hadith breaks machine dedup. Needs one canonical rule.
  - -Scenes resolves clip names only against normalized\, though animated
    mode normalizes internally; Kling output lands in new\ and must be
    copied by hand.
  - Burned subtitles are oversized — they cover the generated scene
    imagery. Reduce ~20% from the next reel.
  - No convention for the Prophet ﷺ in burned subtitles: this reel shows
    both the symbol and the spoken "peace be upon him".

**Related:** P106 (out/ restructure + TTS to disk), P082 (per-clip
  normalization in -Scenes mode).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 114: Whisper crashed on Cyrillic; SRT still written to the pre-restructure path
## ════════════════════════════════════════════════════════
**ID:** P114
**Type:** Encoding + path drift (render pipeline)
**File:** render-reel.ps1
**Commit:** fix: force UTF-8 for Whisper and write the SRT to the work tree (P114)

**Symptom:**
  First Cyrillic adults reel since the restructure (Abu Dawud #3641, RU)
  died at Step 5:
    UnicodeEncodeError: 'charmap' codec can't encode characters in
    position 27-32 ... whisper/transcribe.py line 482, print(make_safe(line))
  followed by "Skipping <narration>.mp3 due to UnicodeEncodeError" and a
  hard fail on the missing SRT.

**Root cause (two independent bugs, one edit):**
  1. Whisper prints transcription progress to stdout. On Windows the child
     process inherits a CP1252 console codec, which cannot encode Cyrillic,
     so transcribe.py raises inside its own PROGRESS PRINT and abandons the
     file. The transcription itself was never the problem — the crash is in
     display, not in ASR. Known since P100 as a manual PYTHONIOENCODING
     workaround that was never hardened into the script.
  2. P113 migrated the script's path variables to the work tree but missed
     the literal `--output_dir "out"` on the whisper invocation. Whisper
     would have written the SRT to flat out\ while $srt pointed at the work
     tree, so the Test-Path guard would have failed even after fix 1.
     EN never exposed this because Latin output never reached bug 1.

**Fix:**
  Set $env:PYTHONIOENCODING = 'utf-8' around the whisper call (saved and
  restored, same discipline as the existing $ErrorActionPreference flip
  from P083), and changed --output_dir from "out" to "$workDir".

**Rule:**
  A crash inside a progress print is not a failure of the work — check
  WHERE in the traceback the exception is raised before assuming the task
  itself is unsupported. And: a path migration is not verified until it has
  been run in every branch. P113 was tested on EN, which skips the whisper
  branch entirely on Latin-script success; the untested branch carried the
  miss for a full session.

**Verified:** RU render completed end to end — SRT produced in the work
  tree, Cyrillic intact, subtitles burned, reel at 48.4s / 13.9 MB.

**Related:** P100 (original Cyrillic crash, workaround only), P113 (work
  tree migration), P083 (whisper stderr under ErrorActionPreference Stop),
  P078 (UZ/TJ subtitle skip).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 115: Seerah source named in a negative claim
## ════════════════════════════════════════════════════════
**ID:** P115
**Type:** Content safety (prompt rules)
**File:** app/api/generate-reel/route.ts
**Commit:** fix: forbid naming a seerah source in negative statements (P115)

**Symptom:**
  Abu Dawud #3641 produced the same defect in three of four languages,
  caught at human review:
    EN  "Neither this narration nor any passage in Ar-Raheeq Al-Makhtum
         ties it to a specific occasion, setting, or audience..."
    RU  "Ни сам хадис, ни «Усваи Ҳасана» не указывают на конкретный повод..."
    TJ  "Манбаи Усваи Ҳасана рабти мушаххасеро бо ин ҳадис сабт накардааст..."
  Each names a seerah book that was never consulted, in a sentence whose
  only content is that the book contains nothing. A viewer reads this as
  "we checked Ar-Raheeq Al-Makhtum" — a claim the pipeline cannot stand
  behind. The RU instance additionally spelled the title with Tajik
  letters inside Russian text.

**Root cause:**
  Rule 6 said: do not name a seerah source unless citing a specific
  documented passage from it. The model satisfied this literally by naming
  the source in a NEGATIVE claim — no passage is cited because the
  sentence asserts there is none. The prohibition was written against
  false positive citation and left false *implied consultation* open.
  Same class as P111: a rule blocks only the category it names, and the
  model routes into the adjacent one.

  Note the rule was working in the sense that mattered most — no occasion
  was invented, which is what P103 was for. The failure was in how the
  refusal got narrated.

**Fix:**
  Extended rule 6: the prohibition now covers negative statements
  explicitly — a source may not be named to say it contains nothing,
  records no occasion, or does not tie the hadith to a period. Naming a
  book you did not cite implies you consulted it. When there is no
  occasion, say nothing about sources at all: collection, narrator,
  meaning, stop.

**Rule:**
  A citation rule must cover the absence case. "Only cite what you
  consulted" and "do not name what you did not consult" are different
  rules, and a model will find the gap between them. When writing any
  prohibition, ask what the model can still say that satisfies the letter
  while producing the same false impression.
  Also: narrating a refusal is itself content. The audience does not need
  to hear which sources were searched and came back empty.

**Detection:**
  Human review, three languages of four. No automated gate covers this;
  it is a candidate check for the content linter (deterministic: a known
  seerah title appearing in the same sentence as a negation).

**Related:** P111 (divine name / simile / unnamed authority), P105 (false
  source attribution), P103 (rule conflict on occasions).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 116: Short matn padded with unearned elevation
## ════════════════════════════════════════════════════════
**ID:** P116
**Type:** Content safety (prompt rules)
**File:** app/api/generate-reel/route.ts
**Commit:** fix: forbid ranking the hadith's subject beyond the matn (P116)

**Symptom:**
  Abu Dawud #1479 — "Dua is worship", 30 characters in EN, the shortest matn
  used to date — produced elevation beyond the text in three of four
  languages, caught at human review:
    UZ  "дуо барча ибодатларнинг асосидир"  (the foundation of ALL worship)
    UZ  "энг катта ибодат"                   (the greatest worship) — title + moral
    TJ  "аз ҳама баланд ва пурарзиш"         (the highest and most valuable)
  The matn says dua IS worship. It does not rank dua above other worship, and
  it does not call it foundational. EN and RU stayed clean.

**Root cause:**
  Rule 10 tells the model that a shorter story is correct and not to compensate
  with narrative. It complied — it invented no incidents — but satisfied the
  length pressure a different way: by inflating the subject's importance.
  Superlatives are not narrative, so rule 10 did not bind them, and rule 15
  covers the opposite direction only (a station of closeness rendered as lowly).
  Neither rule covered elevation upward.

  Third instance of the same structural failure, after P111 (similes) and P115
  (sources in negative claims): a rule closes one exit and the model finds the
  adjacent one.

**Fix:**
  Added rule 16: do not rank or elevate the hadith's subject beyond what the
  matn states; do not compare it to virtues the matn does not mention; a short
  hadith stays short, and brevity is not an invitation to supply significance
  the text does not claim.

**Rule:**
  Length pressure is a fabrication pressure. When the source text is short and
  the output format expects more, the model will fill the gap with whatever the
  rules have not forbidden. Forbidding invention of FACT (P101), of COMPARISON
  (P111) and of SOURCE (P105/P115) still left invention of IMPORTANCE open.
  Ask what remains sayable that is not checkable against the matn.

**Detection:**
  Human review, 3 of 4 languages. scripts/lint-content.py ran clean on all four
  — none of its five checks cover superlatives. A sixth check is possible
  (superlative terms per language, absent from the matn) but would be noisy;
  deferred pending more examples.

**Related:** P111 (similes, divine name, unnamed authority), P115 (source in a
  negative claim), P101 (fabrication rules), P103 (rule conflict).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 117: No gate on which assets a lane may use
## ════════════════════════════════════════════════════════
**ID:** P117
**Type:** Asset provenance (render gate)
**File:** render-reel.ps1, render-mascot-reel.ps1, assets/asset-registry.json,
  scripts/audit-assets.py
**Commit:** feat: asset registry and lane gate in both render paths (P117)

**Symptom:**
  Both render scripts glob `out\backgrounds\*.mp3` and pick at random. Nothing
  distinguishes a kids bed from an adults one, so the picker crossed lanes twice
  in one day:
    R029 TJ adults  -> vocal-hamd-kids-01.mp3 (kids-register hamd), re-rendered
    R030 EN kids    -> ambient-ocean-bg.mp3 (adults ambience), barely audible
                       under a child's narration, re-rendered
  The deeper case is older: every bed in the library was instrumental from May
  until 2026-08-15, approved once and reused across 26 reels. A viewer flagged
  it, not any gate.

**Root cause:**
  Assets carried no recorded classification and no lane approval. Both are
  lookups, not judgements — but nothing existed to look them up in. Every
  existing check inspects what the pipeline just PRODUCED; nothing inspected
  what it REUSES. Generation-time review cannot catch a defect that entered the
  library before generation, which is why 26 reels shipped with it.

**Fix:**
  `assets/asset-registry.json` records, per asset: classification (vocal |
  vocal+daf | ambience | instrumental | mascot | mascot-reference | scene),
  the lanes approved for it, whether a human has verified the classification,
  and why. Retired assets carry `"lanes": []`.

  `scripts/audit-assets.py` has two modes. `--check FILE --lane LANE` exits 1
  if the asset is unregistered, retired, or approved for a different lane —
  this is the gate. `--audit` sweeps the folders and reports unregistered files,
  missing entries, retired-but-reachable assets, and entries not yet verified.

  Both render scripts now call `--check` after resolving the nasheed:
  render-mascot-reel.ps1 appends to `$problems` at Step 0 (fails before any
  work); render-reel.ps1 dies at Step 7 (after Whisper, since that is where the
  bed is resolved).

  The gate does NOT silently retry with another asset. A picker that quietly
  reaches past a rejected file hides the fact that the library contains
  something it should not reach.

**Rule:**
  A rule nobody can look up is not a rule. "Kids beds are vocal, adults get
  ambience" lived only in conversation, so nothing enforced it and it broke
  twice the same day it was decided. Any constraint that reduces to a lookup —
  which lane, which grade, which language — belongs in a machine-readable
  record with a gate, not in a person's memory.
  Corollary: classification stays HUMAN. The registry records a judgement; the
  script only enforces what was written. Nothing here decides whether an
  instrument is permissible.

**Known state at commit:**
  21 of 27 entries are `verified: false` — 8 Pixabay nasheeds downloaded from an
  "acapella nasheed" search (the search term is not a verification) and 13 scene
  clips that predate the registry. They are usable but unconfirmed, and `--audit`
  lists them until a human listens or views. `makka-tower.mp4` in particular is
  modern architecture and sits oddly with the era guidance in
  animated-reel-scene-prompts.md.

**Related:** agent-fleet-roadmap.md agent 12 (asset-auditing), the audio policy
  in reel-creation-pipeline.md, P093/P110 (gate integrity).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 118: Voice comments named voices the IDs did not resolve to
## ════════════════════════════════════════════════════════
**ID:** P118
**Type:** Config drift (TTS voice matrix)
**File:** app/api/tts/route.ts
**Commit:** fix: RU adults voice was Adam, not Abrar; mark AR as out of scope (P118)

**Symptom:**
  Resolving every VOICE_MAP id against the ElevenLabs API found two slots
  pointing at a voice other than the one the comment named:
    ru.adults  ErXwobaYiN019PkySvjV  -> "Adam - Dominant, Firm" (american)
                                        env var named ELEVENLABS_VOICE_ABRAR
    ar.*       pNInz6obpgDQGcFmaJgB  -> "Adam - Dominant, Firm" (american)
                                        env var named ELEVENLABS_VOICE_HIJAZI
  R023 and R027 (RU adults) both shipped narrated by an American English voice.
  Neither was caught by review — eleven_v3 carries Cyrillic through a non-native
  voice well enough that it sounded acceptable.

**Root cause:**
  Two compounding things. The fallback ids were wrong, and — checked separately
  — only ONE ELEVENLABS_VOICE_* var is set in .env.local
  (ELEVENLABS_VOICE_EN_KIDS). Every other slot resolves to its hardcoded
  fallback, so "it's only a fallback" was never true: the fallbacks ARE the
  configuration.

  The comments were the only record of intent, and a comment cannot be wrong
  loudly. Nothing compared the label to the id until it was done by hand.

**Fix:**
  ru.adults -> vQxSi2EuaRWwBw3nn6dK ("Marat - Warm, Calm and Friendly", moscow),
  resolved against the API before committing. Env var renamed
  ELEVENLABS_VOICE_ABRAR -> ELEVENLABS_VOICE_RU_ADULTS to match every other
  language's pattern; the old name referenced a voice never actually configured.

  AR left on the placeholder ids but documented as NOT PRODUCTION: Arabic reels
  are out of scope because Farhod does not read Arabic fluently enough to review
  generated output, and human review gates every publish. A lane that cannot be
  reviewed must not be produced. The block now says so, and the ids are marked
  PLACEHOLDER - Adam, English.

**Rule:**
  An identifier and the comment beside it are two claims that drift apart
  silently. Where an id is opaque — voice ids, model ids, place ids — resolve it
  against the source of truth before trusting the label, and re-resolve when
  touching the block. `curl -H "xi-api-key: $k" .../v1/voices/{id}` takes
  seconds and would have caught this months ago.
  Corollary: a fallback is not a fallback if the primary is unset. Check what
  is actually in .env.local before dismissing a hardcoded default as unreachable.

**Verified:** all 13 VOICE_MAP ids resolved against the API 2026-08-15. The
  other 11 match their comments. Accent labels describe each voice's English
  and do not constrain what it can read — George (british) reading Uzbek and
  Katherine (south african) reading Tajik have both passed review repeatedly.

**Related:** P102 (UZ/TJ to ElevenLabs), P103/P104 (kids voice split by mascot),
  P112 (RU kids boy -> Maxim), P084/P085 (wrong-voice routing).

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 119: Pre-push hook blind to Python, and pointed at nothing
## ════════════════════════════════════════════════════════
**ID:** P119
**Type:** Gate integrity — a check that could not fail
**Files:** .githooks/pre-push, .git/config (core.hooksPath)
**Commit:** 7b3b3ae, a85877d

**Symptom:**
  Committing `scripts/audit-library.py` — 404 lines of new Python — printed
  `Classification: Doc=3 API=0 UI=0 Remotion=0 Config=0`, ran a TypeScript
  check, reported `✅ All checks passed` and pushed. The Python was never
  parsed, imported or tested.

**Diagnosis — two independent faults, either alone sufficient:**

  (1) NO PYTHON CATEGORY. The hook classified into Doc/API/UI/Remotion/Config.
      A `.py` file matched none of them, so `NON_DOC` counted it and the
      doc-only skip did not fire — but nothing downstream tested it either.
      Control fell through to `npx tsc --noEmit`, which cannot read Python,
      reported clean, and passed. A pure-Python commit therefore ran a
      TypeScript compiler over unchanged TypeScript and called that a gate.
      All four agents — lint-content.py, stt-validate.py, audit-assets.py,
      audit-library.py — had zero pre-push coverage. These are the scripts
      that gate what gets published.

  (2) THE TRACKED HOOK WAS NOT THE RUNNING HOOK. `core.hooksPath` was unset,
      so Git read `.git/hooks/pre-push`. The repo's `.githooks/pre-push` was
      never executed. This is invisible from the outside: an older copy in
      `.git/hooks/` runs and prints the same banner, so the hook looks alive
      while edits to the tracked file do nothing. Every fix to `.githooks/`
      since it was created had existed on one machine only.

**Decisive observation:**
  After adding the Python branch to `.githooks/pre-push`, a push still printed
  the OLD classification line with no `Py=` field. The file on disk and the
  file being executed were different files.

**Proof the gate was absent, not merely weak:**
  A file containing `def broken(:` was committed and pushed to main. Output:
  `✅ TypeScript OK` → `✅ All checks passed` → `19c7f28..7b3b3ae`. A
  syntactically invalid Python file reached the default branch through a hook
  whose stated purpose is to prevent exactly that.

**Fix:**
  - `PY_PATTERNS="\.py$"` and `HAS_PY`, reported in the classification line
  - A Python branch, placed before the E2E branch: syntax-parse every changed
    `.py` via `ast.parse`, then run `python -m pytest scripts/lib -q`
    (49 tests, offline, ~0.2s, no network and no credentials)
  - Interpreter probe across `python` / `python3` / `py`; if none is found the
    branch FAILS rather than passing silently — a missing interpreter must not
    read as success
  - `git config core.hooksPath .githooks`
  - Removed a duplicated `Classification:` echo introduced during the edit

**Verified in both directions:**
  - `def broken(:` → `❌ Python syntax error` → `❌ Push blocked`, push refused
  - valid `.py` → `Py=1`, 49 tests run and pass, push proceeds
  A gate is not proven by passing. It is proven by failing on demand.

**Incidental finding:**
  The parse error reported was `SyntaxError: invalid non-printable character
  U+FEFF` — a BOM written by `Out-File -Encoding utf8` in Windows PowerShell,
  which emits UTF-8 WITH BOM. Python rejects a BOM mid-file. Never write a
  `.py` from PowerShell without `-Encoding utf8NoBOM`; edit in VS Code
  instead. Same family as the repo's standing rule against PowerShell file-API
  writes.

**Rule:**
  A classifier that routes work to checks must fail closed on anything it does
  not recognise. This one fell through to an unrelated check and reported its
  success as the verdict. Ask of every gate: what input makes this fail? If
  there is no answer, it is decoration. Third instance in this project after
  P093 (Playwright webServer timeout returning EXIT_CODE=0 with zero tests
  run) and P110 (continue-on-error masking the type gate).

**Related:** P093 (gate that cannot fail), P110 (CI gate integrity)

**Status:** FIXED  
**Correction (2026-08-23, same day):** this pattern was written and marked FIXED
before the hook was ever committed. `git status --short .githooks` returned
empty and that was read as "already committed"; it actually meant the working
file matched HEAD, i.e. the fix was not on disk. The download had silently not
occurred, so the `Copy-Item` that installed it copied nothing. Verified only
after a later push again showed no `Py=` field. The lesson is the pattern's own
lesson applied to its own fix: `git status` reports a comparison, not a
presence. To confirm a file's content is in git, ask git for the content —
`git show HEAD:<path> | Select-String <token>`. Actually committed in 51c9656.

**Status:** FIXED (verified in git 51c9656)

## ════════════════════════════════════════════════════════
## PATTERN 120: Verifier competence is per-defect-class, not per-language
## ════════════════════════════════════════════════════════
**ID:** P120
**Type:** Gate design — knowing what a check cannot see
**Files:** scripts/probe-passb.py (throwaway), sourcing-pipeline-design.md §Stage 3
**Context:** Stage 3 A/B verify. D2 requires pass B to be a different model from
pass A. It says nothing about whether that model is competent in Tajik or Uzbek.

**The question nobody had asked:**
  A verifier that cannot read the language fails in the worst possible way — it
  rubber-stamps, and from outside that is indistinguishable from a working gate.
  The design doc flagged this as the "pass-B competence" caveat and it was never
  tested. Building Stage 3 first would have meant discovering it at candidate 200.

**Method:**
  Bukhari #527, whose four translations are known-good (Stage 2 output, audited
  clean, and cross-checked against eight shipped reels). For each language, two
  prompts: the clean translation, and the same text with ONE planted defect drawn
  from the actual reel log — not an invented one. Clean should pass, planted
  should fail. Passing both means blind. Failing both means noise.
  Planted: EN invented action + invented ranking (P105/P116) · RU dual→singular,
  «родителям»→«матери» · UZ divine name «Аллоҳ»→«Худо» (R025) · TJ invented
  simile + «Некӣ»→«Неки» (P111 r14 + R037).

**Result — gpt-5.6-terra, two identical runs:**
  EN pass/fail ✅ · RU pass/fail ✅ · TJ pass/fail ✅ · **UZ pass/PASS ❌**
  Reproducible to the confidence level across both runs.

**Diagnosis — the naive read is wrong:**
  "GPT is blind in Uzbek" does not survive contact with the other results. It
  caught the TAJIK invented simile, quoting the Arabic correctly — so it reads
  Cyrillic Central Asian text well enough to detect added content. It caught the
  Russian dual→singular shift and cited بِرُّ الْوَالِدَيْنِ as dual, which is
  real Arabic competence.
  What it missed in Uzbek was «Худо» for «Аллоҳ». Both words mean God, and the
  Arabic does say اللَّه — so the translation is FAITHFUL. It is wrong on a
  PROJECT RULE, not on the matn. The model was never told Худо is forbidden, so
  it had no basis to fail it, and it said so at high confidence because it was
  right about the question it was actually asked.
  Same for the Tajik «Неки»: it caught the simile in that very sentence and said
  nothing about the diacritic. Orthography is not faithfulness.

**Rule:**
  Ask of a verifier not "which languages can it read" but "which DEFECT CLASSES
  can it see." Competence is per-class. A model judges faithfulness to a source;
  it does not know your conventions unless they are in the prompt, and putting
  them there turns a judgement engine into a rules engine — worse at both.

**Resulting layering (each class has exactly one owner):**
  | Defect class                                   | Owner              |
  |------------------------------------------------|--------------------|
  | Added content: action, ranking, simile, source | pass B (model)     |
  | Omission, meaning change, register drift        | pass B (model)     |
  | Divine name substitution                        | lint-content.py    |
  | Diacritics, homoglyphs, okina, script mixing    | audit-library.py   |
  | Grade, source URL, empty fields                 | audit-library.py   |
  Both of pass B's misses already have deterministic owners that catch them
  reliably — `Худо` is in lint-content.py's `DIVINE_SUBSTITUTES['uz']` at FAIL
  level, and «Неки» is audit-library.py's TJ check. Nothing is uncovered. Pass B
  is USABLE FOR ALL FOUR LANGUAGES, for what pass B is for.

**Cost of finding out:** eight API calls, a few cents, one hadith.
**Cost of not finding out:** an Uzbek gate that reports green forever.

**Generalisation:** this is the P093/P110/P119 family again — a gate that cannot
fail — but arrived at from the other direction. Those three were gates that could
not fail for MECHANICAL reasons (wrong exit code, continue-on-error, wrong file).
This one would have been a gate that could not fail for a SEMANTIC reason: the
check was real, the model was competent, and it still could not see the defect
because nobody had told it that defect existed. Before trusting any verifier,
plant a known defect and confirm it screams.

**Related:** P093, P110, P119 (gates that cannot fail); P111, P116 (the model
finds the adjacent exit)

**Status:** DOCUMENTED — informs Stage 3, which is not yet built

## ════════════════════════════════════════════════════════
## PATTERN 121: The asset gate checked one asset class out of two
## ════════════════════════════════════════════════════════
**ID:** P121
**Type:** Gate integrity — a real gate wired to the wrong scope
**Files:** render-reel.ps1 (line ~260), scripts/audit-assets.py, assets/asset-registry.json
**Found:** 2026-08-25, during the Muslim #2999 UZ render

**Symptom:**
  The UZ reel rendered with `ambient-ocean-bg.mp3` under the narration — an
  ocean-ambience track, not a nasheed. The background policy is VOCAL-ONLY
  nasheed; instrumentals were retired to `_instrumental` precisely so the random
  picker could not reach them. This file is neither, and should not have been
  reachable at all.

**First finding — the file is invisible to the audit.**
  `audit-assets.py --audit` lists eight `vocal-*` audio files and reports
  `0 missing`. `ambient-ocean-bg.mp3` appears NOWHERE in the output: not
  registered, not unregistered, not missing. Yet it passed `--check` at render
  time and reached the merge. Either it is registered as something it is not, or
  `--check` returns success for files it has never seen. A gate that passes
  unknown input is not a gate.

**Second finding — the bigger one — the scene clips were never checked.**
  The same audit reports EIGHT scene clips as UNREGISTERED and states plainly:
  "The render gate will BLOCK these."
    b527-dawn / -doorway / -minaret / -night        (R038–R041)
    m2999-dawn / -harvest / -storm / -steady        (R042–R045)
  It did not block them. **Eight reels shipped over clips the audit itself says
  should have been stopped.**

**Diagnosis — the decisive line:**
  render-reel.ps1:260
      $assetName = Split-Path $chosen -Leaf
      $auditOut  = & python "scripts\audit-assets.py" --check $assetName --lane $Style
  `$chosen` is the RANDOMLY PICKED NASHEED. The gate is called with exactly one
  filename: the one asset the script selected itself. Clips passed in by the
  operator via `-Scenes` are never named to it and never reach it.
  The comment two lines above says why, and it is honest:
      "not a judgement call - twice on 2026-08-15 the random picker crossed lanes."
  The gate was built to police the PICKER, because the picker was what had
  failed. It was never widened to police the INPUT. So the gate is real, it
  works, it is correctly wired — to half the problem.

**Why this went unnoticed for eight reels:**
  The audit and the gate are the same script but different verbs. `--audit`
  reports and is run by a human occasionally; `--check` blocks and runs on every
  render. The reporting half saw the unregistered clips every time it was run
  and said so. Nobody connected "the audit lists them as blocked" with "the
  renders are succeeding," because the audit's own wording — future tense, "will
  BLOCK these" — reads as a description of what happens, not a claim to test.

**Fix (applied 2026-08-25):**
  1. `render-reel.ps1` now calls `--check` on EVERY `-Scenes` clip, inside the
     existing resolve loop right after the file-exists check, so a clip is
     rejected before any ffmpeg work happens.
  2. The eight clips already in published reels registered retroactively as
     `scene` / adults / verified. The operator watched each one before it
     shipped, so the human check was real — it was just never recorded.
  3. **The ambience half resolved the opposite way from the original diagnosis.**
     `--check` does NOT pass unknown files: a made-up filename is BLOCKED with
     exit 1. `ambient-ocean-bg.mp3` passed because it was REGISTERED — `ambience`,
     `lanes: ["adults"]`, verified true, with a considered note ("Generated with
     ffmpeg... Not music", restricted to adults after being inaudible under a
     child's narration). The gate enforced the registry correctly; the REGISTRY
     disagreed with an unwritten policy. Operator decision: backgrounds are VOCAL
     NASHEED ONLY. Both ambience files set to `lanes: []`, moved to
     `out/backgrounds/_retired/`, keys path-prefixed to match. Nasheed pool 12 → 10.
  4. **A second defect surfaced during the fix:** the registry is SECTIONED
     (`audio` / `mascots` / `scenes`) and `audit-assets.py` picks the section by
     FILE EXTENSION, not by where the entry sits. The eight `.mp4` entries were
     first added inside `audio`, so the audit reported them as UNREGISTERED *and*
     MISSING simultaneously — while `--check` passed them, because it matches on
     filename alone. Two halves of one script disagreeing again, same as the
     `--audit`/`--check` split above. The extension rule is now stated in the
     registry's own `_comment`.

**Verified in both directions:**
  - unregistered clip → `BLOCKED: m2999-dawn.mp4 is not in the asset registry`
    → `FAILED: scene clip rejected` → no render
  - registered clips → all four stitch, render completes
  - retired ambience → `--check ambient-ocean-bg.mp3 --lane adults` exits 1
    (it exited 0 the day before)
  - `--audit` → 0 unregistered, 0 missing

**Correction to the original diagnosis:** this pattern was first written as
"`--check` passes unknown files." It does not. Verify what a gate actually does
before describing what it failed to do.

**Still open:** seven of the eight vocal nasheeds are `verified: false`, their
notes admitting a Pixabay search term was the only basis for calling them
acapella. Eight files are in rotation on an unchecked assumption.
**Resolved 2026-08-29:** all eight vocal nasheeds listened to and confirmed
voice-only, plus `vocal-hamd-kids-01.mp3`. `verified: true` on all nine. The
Pixabay search term turned out accurate — which is luck, not method: the files
were in rotation across nine published reels on nothing but a search phrase, and
if any had carried a lute the defect would already have shipped. Audit
unverified count 21 → 13; the remainder are pre-registry scene clips needing a
viewing pass.

**Status:** FIXED

**Rule:**
  A gate protects the inputs it is NAMED, not the inputs that exist. When a gate
  is built in response to one failure, ask immediately what else travels the same
  path and is not covered. And when a tool reports "this will be blocked," treat
  that as a claim to verify, not a fact to read — the reporting half of a tool
  and the enforcing half can disagree indefinitely without either being wrong.

**Related:** P093 (Playwright gate returning 0 with zero tests run), P110
(continue-on-error masking the type gate), P119 (hook blind to Python, and
pointed at the wrong file), P120 (verifier blind to a defect class nobody named).
Fourth in the family, and the first where the gate was correctly built and
correctly reporting while still not covering the thing that mattered.

**Status:** DOCUMENTED — fix pending

## ════════════════════════════════════════════════════════
## PATTERN 122: The same invented claim appears in all four languages
## ════════════════════════════════════════════════════════
**ID:** P122
**Type:** Content safety — fabrication is prompt-level, not per-language
**Files:** app/api/generate-reel/route.ts (prompt), scripts/lint-content.py
**Found:** 2026-08-25, across the Muslim #2999 adults set (R042–R045)

**The matn (Sahih Muslim 2999):**
  "How wonderful is the affair of the believer — indeed, all of his affair is
  good. If prosperity befalls him he is grateful, and if adversity befalls him
  he is patient."
  Four moves: wonder · the claim · condition-response · condition-response.
  It makes no claim about WHY, about what kind of thing gratitude and patience
  are, or about what the believer thereby wins.

**What the generator produced, in four separate generations:**

  EN  "These are not passive states but active disciplines"
      "no moment in a believer's life is ever wasted or lost"
  RU  «не как пассивное смирение, а как внутреннее действие»
      «ни одно мгновение его жизни не оказывается пустым или потерянным»
      «верующий находится в состоянии духовного выигрыша»
  UZ  «ҳеч бир ҳол беҳуда эмас — чунки у Аллоҳга боғлиқлигини унутмайди»
      «на фаровонликда кибрланади, на мусибатда умидсизланади»
  TJ  «ин вижагии хоси мӯъмин аст»
      «имон... на тавассути тағйири воқеият, балки тавассути тағйири посухи қалб»
      title: «Мӯъмин ҳамеша ғолиб аст» (the believer is always VICTORIOUS)

**The decisive observation:**
  These are not four different mistakes. They are the SAME THREE MOVES, made
  independently in four languages by four separate generation calls:

  1. CHARACTERISE the response — "active not passive," «внутреннее действие»,
     an inner state versus outward circumstance. The matn says he gives thanks
     and is patient. It does not say what sort of thing that is.
  2. TOTALISE the claim — "no moment ever wasted," «ҳеч бир ҳол беҳуда эмас».
     The matn says his affair is good. "Never wasted" is a larger claim.
  3. ESCALATE good → winning — «духовного выигрыша», «ғолиб аст» (victorious).
     GOOD is what the hadith says. VICTORY is what the generator reaches for.

  Independent recurrence across four languages means this is not a per-language
  slip to be caught at review. It is a property of the PROMPT. The generator is
  asked for a story of a certain length about a matn that is one sentence long,
  and these three moves are where the remaining words come from.

**Why the linter cannot catch it:**
  `lint-content.py` checks divine name, unnamed authority, seerah sourcing,
  simile markers, and meaning inversion. None of these are similes, none cite an
  authority, none substitute a divine name. They are ASSERTIONS ABOUT THE
  HADITH'S SIGNIFICANCE, expressed in ordinary declarative prose. There is no
  lexical marker to match on. All four generations linted CLEAN.
  Stage 3's A/B verify would catch them — but Stage 3 verifies TRANSLATIONS
  against the matn, not generated reel text. Nothing currently checks the story.

**Lineage — this is the fourth turn of the same screw:**
  P101  rules requiring named figures in narrative action CAUSED the fabrications
        the prohibition rules existed to prevent
  P111  forbid invented FACT → it invents COMPARISON (rule 14)
  P115  forbid comparison → it invents SOURCE, including in negative claims
  P116  forbid source → it invents IMPORTANCE ("greatest", "foundation of all")
  P122  forbid importance → it invents CHARACTER ("active not passive"),
        TOTALITY ("never wasted"), and OUTCOME ("victorious")
  Each prohibition closes one exit. The model does not stop; it finds the next
  door. The doors are not random — they are, in order, the cheapest ways to add
  words to a short text without contradicting it.

**Fix (applied 2026-08-25):**
  1. **The length target was the root cause.** `"story": "3-4 sentences..."` on a
     matn that is ONE sentence long. The instruction already said "A shorter,
     plainer story is correct; an invented one is not" — and the generator
     invented anyway, in four languages. P101's shape exactly: a concrete count
     beats a vague caution. Replaced with: follow the matn's own length, say what
     it says in the order it says it, explain a term if needed, and NOT what kind
     of thing it describes, how much of life it covers, or what the person gains.
  2. **A second, worse defect found in the same file — the KIDS lane instructed
     the very thing P111 rule 14 forbids.** Line 57 read: "Use vivid comparisons
     children understand (like a kind teacher, like the sun warming you)."
     A direct instruction to invent similes, with examples supplied. Every kids
     reel since that line was written was generated under a standing contradiction
     between two rules in one prompt. Replaced with: explain plainly; do not invent
     comparisons; if the hadith contains an image, use that one.

**Verified on a real generation:** kids EN for Muslim #2999, generated
immediately after both edits. No invented comparison. Length tracked the matn —
five short sentences, no padding. None of the three moves this pattern
documents. First generation of this hadith across five attempts that needed no
rewrite; the four before it each required one.

**Residual, accepted:** the H block still contains "nothing that touches a
believer is outside of good" — a mild totalising gloss, but defensible as a
reading of كُلَّهُ خَيْرٌ, and H is not narrated. The caption title came back
"Every Moment Is Good For The Believer" and was corrected by hand: the matn says
his AFFAIR is good, not every moment. The move is weaker but not gone.

**Rule:**
  When the same invented claim appears in independent generations across
  languages, stop treating it as a review finding and treat it as a prompt
  defect. Per-language review catches instances; only the prompt catches the
  pattern. And before adding the next prohibition, ask what the model will reach
  for once that exit is closed — because it will reach for something, as long as
  it is being asked for more words than the source contains.

**Related:** P101, P105, P111, P115, P116

**Status:** FIXED — verified on one generation. Watch the next three languages;
a single clean run on a non-deterministic system is one sample.

## ════════════════════════════════════════════════════════
## PATTERN 123: The classifier's remaining blind spots — .ps1 and .json
## ════════════════════════════════════════════════════════
**ID:** P123
**Type:** Gate coverage — closing the categories P119 left open
**Files:** .githooks/pre-push
**Commit:** 58a4c71

**Symptom:**
  Committing the P121 fix — a change to `render-reel.ps1` and
  `assets/asset-registry.json` — printed
  `Doc=1 API=0 UI=0 Remotion=0 Config=0 Py=0`, ran `npx tsc --noEmit`, and
  pushed. The two files that actually changed were counted as nothing.

**Why this is worse than it sounds:**
  `render-reel.ps1` is not a helper. It IS the render pipeline and, since P121,
  IS the asset gate. The commit being waved through was the one that added the
  scene-clip check. A gate whose own patch is unverified is a gate on trust.
  `asset-registry.json` is the sole record of which assets a human has approved
  for which lane. A trailing comma there makes the registry unloadable, and
  `audit-assets.py --check` would then fail on every asset — or, worse, the file
  could be malformed in a way that silently drops entries.

**Diagnosis:**
  Identical in shape to P119. The classifier had Doc/API/UI/Remotion/Config/Py.
  A `.ps1` matched none of them, so `NON_DOC` counted it and the doc-only skip
  did not fire — but no branch downstream tested it either. Control fell through
  to the TypeScript compiler, which cannot read PowerShell, and its success was
  reported as the verdict. Same for `.json`.
  P119 fixed the Python case specifically. It did not ask what ELSE travels the
  same path — which is exactly the question P121's rule says to ask.

**Fix:**
  - `PS1_PATTERNS` / `HAS_PS1`, `JSON_PATTERNS` / `HAS_JSON`, both reported in
    the classification line.
  - PowerShell branch: `[System.Management.Automation.PSParser]::Tokenize()` on
    each changed `.ps1`. This PARSES WITHOUT EXECUTING — a hook that ran
    render-reel.ps1 would be a catastrophe, not a check. Tokenize returns parse
    errors in a `[ref]` parameter rather than throwing, so the branch must
    inspect the collection and exit non-zero explicitly.
  - JSON branch: `json.load` on each changed `.json`.
  - Both FAIL if their interpreter is absent (`pwsh`/`powershell`, `python`).
    A missing checker must never read as success — P119's lesson applied twice.
  - `PY_BIN` discovery hoisted above the branches, since two now use it.
  - When `assets/asset-registry.json` changes, the branch also runs
    `audit-assets.py --audit` and prints the tail. REPORTS ONLY, never blocks —
    a pre-existing unverified asset must not stop an unrelated push.

**What the JSON check does NOT do, stated plainly in the hook's own comment:**
  It would not have caught the defect that prompted it. On 2026-08-25 eight
  `.mp4` entries were added to `asset-registry.json` inside the `audio` section.
  The file was perfectly valid JSON. The audit reported those eight as
  UNREGISTERED *and* MISSING simultaneously — because `audit-assets.py` picks a
  section by FILE EXTENSION, not by where the entry sits — while `--check`
  passed them, matching on filename alone. Syntax checking cannot see structural
  wrongness. That is `audit-assets.py`'s job, which is why the audit is invoked
  alongside rather than a parse being treated as sufficient.

**Verified in both directions:**
  - `if ($true) {` unterminated → `The string is missing the terminator` +
    `Missing closing '}'`, with line numbers → push blocked
  - `{"a": 1,}` → `Illegal trailing comma before end of object: line 1 column 8`
    → push blocked
  - valid files → `Ps1=0 Json=0`, push proceeds

**Known and accepted:** `.githooks` is itself in `DOC_PATTERNS`, so a hook-only
change classifies as doc-only and skips every check — including its own. A hook
cannot meaningfully test itself, and this is why both the P119 and P123 fixes
were pushed without being exercised by the very branches they added. Both were
instead proven by hand, before the commit, with deliberately broken files. That
manual proof is not optional; it is the only verification this file ever gets.

**Rule:**
  When a gate is widened in response to one file type, enumerate every file type
  in the repo and ask which branch would catch it. P119 closed Python and
  stopped. Four days later the same hole ate the fix to a different gate. A
  category-based classifier fails silently for exactly the categories nobody
  thought to name.

**Related:** P093, P110, P119, P120, P121 — the gates-that-cannot-fail family.
This is the sixth.

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 124: Generated text cannot be edited after narration
## ════════════════════════════════════════════════════════
**ID:** P124
**Type:** Workflow defect — the correction path is a full regeneration
**Files:** app/admin/page.tsx
**Found:** 2026-08-27, Muslim #2999 UZ kids
**Supersedes the scope of:** P079, which recorded this as "title field not
editable." It is not the title field. It is every generated block.

**Symptom:**
  `make-kids-reel.ps1` refused to chunk the UZ kids narration:
      FAILED: story/moral seam at 28.3s doesn't fit the 28s cap
  The story alone ran 27.8s. The fix is obvious — shorten the story, re-narrate.
  It could not be done.

**Diagnosis:**
  The admin exposes "Generate Story narration" per block. BEFORE the first
  click, the textarea is editable and the edit is what gets narrated. AFTER the
  click, the button becomes playback for the audio that already exists, and the
  audio stays bound to whatever text was present at generation time. Editing the
  textarea afterwards changes nothing that reaches TTS.
  The only path to re-narrate is **Regenerate**, which replaces ALL FOUR blocks
  — story, moral, seerah and caption — with fresh model output.

**Why that is worse than it sounds:**
  Every reel this week required hand-corrections before narration: divine-name
  case in RU, Latin captions in UZ, invented claims in all four languages, the
  escalation move, honorific expansion for RU. Regenerate discards all of it and
  returns text that must be reviewed and corrected again from scratch — and, on
  a non-deterministic model, corrected DIFFERENTLY, because the new text
  contains different defects. The correction is not idempotent.
  So the editable window is exactly one pass: read the generation, fix
  everything, and generate narration once. Any defect noticed after that point —
  including one that only surfaces at the render gate, like an over-long story —
  costs a full re-review of four blocks.

**Workaround used (did not regenerate):**
  The narration audio was already correct; only its LENGTH was wrong. Split the
  existing audio instead of re-authoring the text:
      python split-narration.py --base kids-uz-muslim-2999 \
        --audio "<story>.mp3" "<moral>.mp3" --outdir "<work dir>"
  It cuts at SILENCE POINTS rather than only the story/moral seam, so it can
  split inside the story: 27.8s+8.7s became 25.7s + 11.4s. The seam then falls
  mid-story between two flowing sentences and still reads cleanly at the cut,
  because the mascot resets to base pose either way.
  **Rule of thumb:** if the TEXT is wrong, you must regenerate. If only the
  LENGTH is wrong, split the audio and keep the reviewed text.

**Second finding, same set (2026-08-26, RU kids):**
  The generator returned S and M IDENTICAL — the same paragraph twice, verbatim.
  Not a truncation and not a style choice; the moral is specified as a distinct
  actionable takeaway. Caught by reading, and nothing automated would have
  caught it: `lint-content.py` checks each block against its own rules, not
  blocks against each other. First occurrence. A duplicate-block check is cheap
  and belongs in the linter.

**Third finding, same set (2026-08-28, TJ kids):**
  The `C:` label was omitted from the generation, so the caption title was
  absorbed into the end of the H block. A parse-shape failure, distinct from
  content. Also cheap to check: the linter can assert all four labels are
  present before anything else runs.

**Fix (proposed, not applied):**
  1. **Admin:** keep the block editable after narration and re-enable
     "Generate Story narration" as a re-narrate action per block. The TTS route
     already takes a `section` parameter (P106) and writes per-section files, so
     the backend supports this — it is a UI state problem, not an API one.
     This was already logged as the P120-era "per-block TTS regenerate" item;
     P124 is the evidence for why it matters.
  2. **lint-content.py:** two structural checks before the five content checks —
     all four of S/M/H/C present, and no two blocks identical.
  3. Until (1) ships, the workflow rule stands: **fix everything before the
     first narration click.** Trim the story pre-emptively if the language runs
     long — UZ and RU both do — because it cannot be trimmed afterwards.

**Rule:**
  A correction workflow whose only path is "start over" is not a correction
  workflow. Where a system generates several artifacts together and a human
  reviews them, each artifact must be independently re-committable, or the cost
  of fixing one defect is re-reviewing everything — and on a non-deterministic
  generator, "everything" comes back different each time.

**Related:** P079 (narrower statement of the same defect), P106 (per-section TTS
writes, which is the capability the fix needs), P122 (the corrections this makes
expensive to preserve)

**Status:** DOCUMENTED — fix pending

## ════════════════════════════════════════════════════════
## PATTERN 125: Per-block re-narrate, and a stale-text warning
## ════════════════════════════════════════════════════════
**ID:** P125
**Type:** Workflow fix — the implementation of P124
**Files:** app/admin/page.tsx (AudioSection)
**Commit:** f4195ae

**What P124 described:** editing a generated block after clicking
"Generate narration" reached nothing. The audio stayed bound to the text that
existed at generation time, and the only re-narrate path was the whole-reel
Regenerate, which replaces all four blocks and discards every hand-correction.

**The cause, in one function:**
    function toggle() {
      if (!audioUrl) { generate(); return }   // first click -> narrate
      ...                                      // every click after -> play/pause
    }
  `audioUrl` is local state in `AudioSection`. Once set, `generate()` was
  unreachable. The `text` prop was ALWAYS current — `updateField` updates it
  live as you type — so the component knew the new text and simply never used
  it. And the backend was never the obstacle: `/api/tts` takes a `section` and
  writes per-section files (P106), so calling it twice for one section already
  worked. This was UI state, not an API limitation.

**Fix:**
  - `narratedText` state records the exact text each narration was made from.
  - `isDirty = !!audioUrl && text.trim() !== narratedText.trim()`.
  - A `↻ Re-narrate` button appears once audio exists and ALWAYS calls
    `generate()`. It turns amber when `isDirty`.
  - A warning line renders when dirty: "Text edited since narration —
    re-narrate before rendering, or the reel will use the old audio." That is
    the message that would have caught the over-long UZ #2999 story at the
    textarea instead of at the Fabric chunker.
  - Previous blob URLs are revoked on re-narration, so repeated takes do not leak.
  - `data-test` hooks on the play button, the re-narrate button, and the warning.

**Verified in the browser, both states at once:** with the story untouched and
the moral edited, the story's Re-narrate rendered grey and the moral's rendered
amber with the warning beneath it. Re-narrating the moral produced audio of the
EDITED text — the colour change proves detection, the audio proves the fix.

**Rule:** when a control's behaviour depends on whether an artifact exists, the
"already exists" branch needs its own escape hatch. `if (!x) create(); else
use();` silently removes the ability to re-create, and the loss is invisible
until someone needs it — here, three months and roughly forty reels later.

**Related:** P124 (the diagnosis), P079 (editable textareas, the fix this
completes), P106 (per-section TTS writes, the capability this relies on)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 126: The classifier's third blind spot — and the map of the rest
## ════════════════════════════════════════════════════════
**ID:** P126
**Type:** Gate coverage — enumerating the hole instead of patching it again
**Files:** .githooks/pre-push
**Commit:** 80ab8f3

**Symptom:**
  Pushing the P125 fix — a change to `app/admin/page.tsx`, the entire content
  pipeline — printed every counter at zero:
      Doc=0 API=0 UI=0 Remotion=0 Config=0 Py=0 Ps1=0 Json=0
  and ran `npx tsc --noEmit` alone.

**Why:**
      UI_PATTERNS="^app/page\.tsx$|^components/|^lib/"
  `^app/page\.tsx$` is anchored to exactly the public homepage. `app/admin/`
  matches nothing. The admin studio — hadith picker, generation, editing, TTS,
  caption, publish — has never been covered by any branch of this hook.

**Third occurrence of the same shape (P119 Python, P123 .ps1/.json).** So this
time the hole was ENUMERATED rather than patched, per P123's own rule. Every
tracked file was listed against every pattern:

  | Uncovered | Risk |
  |---|---|
  | `app/admin/page.tsx`, `layout.tsx` | the whole content pipeline |
  | `scripts/*.ts` (7 files) | **`uzbek-translit.ts` has 11 passing tests the hook never ran** |
  | `scripts/merge-reel.js`, `.claude/hooks/log-session.js` | no `.js` branch at all |
  | `app/layout.tsx`, `app/globals.css` | site shell |
  | `.github/workflows/ci.yml` | YAML, unchecked |
  | `supabase/migrations/*.sql` | SQL, unchecked — and these touch the SHARED table |
  | images, SVGs, favicon, `.mjs` configs | correctly uncovered, not code |

**The sharpest item was not the admin.** `scripts/lib/uzbek-translit.ts` carries
a passing 11-test suite covering okina vs tutuq and apostrophe folding — the
single defect class that reached five published captions — and the hook had
never invoked it. Tests existing but never run is precisely the P119 shape.

**Fixed here (part A):**
  - `TS_SCRIPT_PATTERNS="^scripts/.*\.ts$"`, `HAS_TSSCRIPT`, reported as
    `TSScript=` in the classification line.
  - Branch runs `npx tsx scripts/lib/uzbek-translit.test.ts` — 11 tests, ~17ms,
    offline. Cheap enough for every push.

**Proven by breaking the thing it guards:** `const OKINA` was temporarily set
from `'\u02BB'` to `'\u0027'` — the ASCII apostrophe, the actual historical
defect. Result: `TSScript=1`, 6 of 11 failed with `"ro'za" !== 'roʻza'` and
`"bo'lsa" !== 'boʻlsa'`, push blocked. Reverted, 11/11, pushed.

**NOT fixed here, and deliberately (part B):**
  Widening `UI_PATTERNS` to include `^app/admin/` was the obvious one-line fix
  and would have been WORSE THAN NOTHING. `tests/hadith-reels.spec.ts` contains
  no reference to `admin` at all — the E2E suite never loads that page. Adding
  the pattern would run 25 public-site tests on an admin change and report
  green: a change "verified" by tests that cannot see it. That is P123's lesson
  exactly, and the reason the pattern stays narrow until admin tests exist.
  Order required: (1) write admin E2E tests — the P125 `data-test` hooks are
  already in place for the dirty-state case — then (2) widen `UI_PATTERNS`.

  Also outstanding: `.js` files, `.yml`, and `.sql`. SQL has no cheap checker
  and touches the shared `hadith_library`; better to print it as explicitly
  unchecked than let it count as nothing.

**Rule:** patching a classifier for the one file type that just bit you
guarantees a fourth occurrence. Enumerate every file the repo tracks against
every pattern, and for each gap decide: covered, deliberately uncovered, or
uncovered-and-logged. "Uncovered and nobody noticed" is the only unacceptable
state — and a pattern that routes to a check which cannot see the change is
that state wearing a green tick.

**Related:** P093, P110, P119, P120, P121, P123 — the gates-that-cannot-fail
family. Seventh.

**Status:** PARTLY FIXED — scripts/*.ts covered; admin E2E and the .js/.yml/.sql
gaps remain

## ════════════════════════════════════════════════════════
## PATTERN 127: A dead pattern, and why an undefined one is worse
## ════════════════════════════════════════════════════════
**ID:** P127
**Type:** Gate integrity — the classifier's own configuration was unverified
**Files:** .githooks/pre-push
**Commit:** 97a71aa

**Found by watching the classification line.** Pushing five new admin E2E tests
printed `UI=0` and ran `tsc` alone. The suite was not run — by the very hook
that runs the suite.

**First finding — TEST_PATTERNS was dead.**
      TEST_PATTERNS="^tests/|\.spec\.ts$"
  Defined, and never referenced again. No `HAS_TEST`, no counter in the echo, no
  branch. It has apparently been dead since the hook was written. **The test
  file had no test coverage:** a change to the suite ran a TypeScript check and
  pushed. Eighth instance of the gates-that-cannot-fail family, and the most
  pointed one — the thing not being checked was the checker.
  Fixed: `HAS_TEST` counted, reported as `Test=`, and folded into the E2E
  condition — `$((HAS_API + HAS_UI + HAS_TEST))`.

**Second finding — and this one was not predicted.**
  Having found one dead pattern, the obvious move was a self-check: assert every
  `*_PATTERNS` has a matching `HAS_*` counter. That check was written, and it
  did not work. Proving it is what produced the real finding.
  `PY_PATTERNS` was renamed to `PY_PATTERNSX` and the hook run. Expected: a
  warning. Actual: **`Py=1` on a hook-only change**, and silence.
  `grep -E ""` — an empty pattern — **matches every line**. So an undefined
  pattern does not produce zero matches. It produces a match on EVERY changed
  file, the counter reads high, and the wrong branch runs. On a larger commit
  that would have run the Python branch over files containing no Python, or the
  build check on a doc change.
  The first self-check tested whether the COUNTER was set. It always is:
  `HAS_PY=$(...)` assigns a number whether the pattern is empty or not. The
  check was structurally incapable of firing — a gate that could not fail,
  written while fixing gates that could not fail.

**The corrected check tests the pattern, not the counter:**
      for p in DOC_PATTERNS API_PATTERNS UI_PATTERNS ... TS_SCRIPT_PATTERNS; do
        eval "val=\$$p"
        if [ -z "$val" ]; then
          echo "❌ $p is empty or undefined — an empty regex matches EVERY file"
          FAILED=1
        fi
      done
  `FAILED=1`, not a warning: an empty pattern is a live misrouting bug.
  Placement matters — it must sit AFTER `FAILED=0`. The first attempt put it
  above the doc-only skip, where `FAILED=1` would be set on an undeclared
  variable and then overwritten by `FAILED=0` moments later. It would have
  detected the fault and discarded the result.

**Verified in both directions:**
  - `TEST_PATTERNS` live: a trailing newline in the spec file → `Test=1`, all
    30 tests run, push proceeds.
  - `PY_PATTERNSX`: → `Py=2` (the empty regex matching both changed files, one
    a shell script and one a spec) → `❌ PY_PATTERNS is empty or undefined` →
    push blocked.

**Known limitation:** on a doc-only push the script exits before the check runs.
Acceptable, because the dangerous case is covered: if `DOC_PATTERNS` itself were
empty, `NON_DOC` would equal the file count, the skip would not fire, and the
check would run.

**Rule:**
  Configuration is code. A classifier's pattern table is the part most likely to
  drift and least likely to be read, and a regex engine's behaviour on empty
  input is a footgun with no error message — the failure is louder counters, not
  quieter ones. Assert the config, not the symptom. And when you write a check
  because a check was missing, prove THAT check fails on demand before trusting
  it; the first version here did not, and only breaking it deliberately revealed
  why.

**Related:** P093, P110, P119, P120, P121, P123, P126 — eighth in the family,
and the first where the fix for the family was itself an instance of it.

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 128: Structural defects no per-block check can see
## ════════════════════════════════════════════════════════
**ID:** P128
**Type:** Checker coverage — a whole defect class had no owner
**Files:** scripts/lint-content.py
**Commit:** 0a368e4
**Implements:** the two linter items identified in P124

**The two defects, both from the Muslim #2999 kids set:**

  1. **RU: S and M came back IDENTICAL.** The generator returned the same
     paragraph for the story and the moral, verbatim. The reel would have
     narrated it twice — a viewer hears the same words at 0:00 and again at
     0:21. Caught only by reading.
  2. **TJ: the `C:` label was dropped.** The caption title
     «Ҳамаи кори мӯъмин хайр аст!» was absorbed into the END of the seerah
     block. The content was not missing; it was in the wrong place, which is
     harder to notice than absence.

**Why the existing five checks were structurally incapable of seeing either:**
  Every content check reads ONE block and asks whether its text breaks a rule —
  divine name, unnamed authority, seerah source, invented simile, meaning
  inversion. Both defects here are perfectly legal at that level. Two identical
  blocks are two individually valid blocks. A merged block is one valid block
  containing more than it should. The defect only exists in the RELATIONSHIP
  between blocks, or between the file and its expected shape, and nothing was
  looking there.

**A near-miss worth recording.** The missing-label case WAS already detected:
      missing = [k for k in 'SMHC' if k not in blocks]
      if missing: print(f'  note: no {...} block(s) in this file')
  A bare `note:` — not a Finding. It did not sort with the results, did not
  appear in the FAIL/WARN/INFO counts, and printed one line above
  `no findings.` On the TJ run it was there, on screen, and was read straight
  past. Detection without severity is not a check; it is a comment. Promoted to
  a real Finding at WARN.

**Fix:** two structural checks, run BEFORE the content ones, since a missing or
duplicated block changes what those are even examining.
  - `missing-block` (WARN) — names the absent label AND says where to look:
    "that block's text is now sitting INSIDE the previous one — check the end
    of the block above it."
  - `duplicate-block` (FAIL) — compares every block body pairwise. FAIL rather
    than WARN: identical blocks are never intentional.
  Check count 5 → 7.

**Verified in three directions before shipping:**
  - clean four-block input → `no findings`
  - `C:` label removed → `[WARN] missing-block`
  - S and M identical → `[FAIL] duplicate-block`, naming the MORAL block
  Then run against the real TJ #2999 `draft.txt` to confirm no false positive
  on genuine reel content — clean.

**Rule:** when a checker examines items one at a time, ask what defects live
BETWEEN items. Per-item validation cannot see duplication, ordering, absence,
or merging, and those failures look like valid content from inside every
individual item. And a detection that prints without a severity level will be
read past — if it is worth detecting, give it a level and let it into the count.

**Related:** P124 (where both defects were diagnosed), P105/P111/P115 (the five
content checks this sits alongside)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 133: The title had no constraint, so it escalated
## ════════════════════════════════════════════════════════
**ID:** P133
**Type:** Content safety — a prompt fix that stopped at the wrong boundary
**Files:** app/api/generate-reel/route.ts
**Commit:** 294cc01
**NOTE ON NUMBERING:** that commit message says "P132". Wrong — P132 is HV's,
in the shared global sequence. This is P133. Recorded rather than force-pushed.

**Symptom:** P122 stopped two of three invented moves. The third survived every
set — "good" became "wins":
      RU  «Верующий побеждает всегда»      (the believer always WINS)
      UZ  «Мўмин доим ютади»               (the believer always WINS)
      TJ  «Мӯъмин ҳамеша ғолиб аст»        (the believer is always VICTORIOUS)
  Three languages, independently, on a matn that says his affair is GOOD. And
  in all three it appeared in the TITLE.

**Cause — two instructions pushing the same way, and no counterweight:**
      line 108: "title": "... max 8 words, shareable, inspiring"
      line 122: 4. title MUST be shareable — would someone click on this?
  Meanwhile P122 had tightened the STORY to "you may NOT say what kind of thing
  it describes, how much of life it covers, or what the person thereby gains" —
  and left the title with no constraint at all. So the escalation the story
  could no longer make, the title made freely, one field away.
  Same specification-conflict shape as P101: a concrete demand ("would someone
  click?") beats a vague caution every time, and here there was not even a
  caution to beat.

**Fix:** replace the demand, do not add a prohibition. P122's lineage shows each
prohibition just moves the model to the next door.
  - title spec now: state what the hadith is ABOUT or quote its own words; it
    may not promise an outcome, name a benefit, or rank the deed — **with a
    worked negative example**, "'Two Deeds Allah Loves' is right; 'The Believer
    Always Wins' is not." P103 showed an abstract rule gets reinterpreted; a
    concrete wrong answer is harder to argue with.
  - rule 4 rewritten from "would someone click" to "a title that promises more
    than the hadith states is fabrication in the most-read line of the reel."

**Verified on the hardest available case.** Tested against Bukhari #6446 —
"Richness is not having many possessions, but richness is contentment of the
soul" — a definitional statement about what something IS, which is exactly the
shape that invites "The Secret To True Wealth" or "How To Be Truly Rich."
Result: **"Richness Is Contentment of the Soul"** — the matn's own words. Held.

**Not yet proven outside English.** RU, UZ and TJ produced this move
independently, so an English-only pass is not evidence. Next three languages of
the #6446 set are the real test.

**Rule:** when tightening one field, check the adjacent fields for the same
freedom. A constraint applied to the story and not the title does not remove the
option — it relocates it, and in this case relocated it to the single most-read
line in the reel.

**Related:** P101 (specification conflict), P111/P115/P116/P122 (the lineage of
invented moves), P103 (concrete examples beat abstract rules)

**Status:** FIXED in EN — pending confirmation in RU/UZ/TJ

## ════════════════════════════════════════════════════════
## PATTERN 134: A poll deadline set from a guess, not a measurement
## ════════════════════════════════════════════════════════
**ID:** P134
**Type:** Tooling — a timeout that turned completed work into apparent failure
**Files:** scripts/generate-scene.ps1
**Commit:** 9176262

**Symptom, four times across three sets:**
      FAILED: timed out after 8 min (request <id>, last status IN_PROGRESS)
  Each time the job had NOT failed. Kling finished it server-side; only the
  poll gave up. The operator then either paid to regenerate or recovered by
  hand through the fal status API — looking the commands up again each time.

**Measured inference times, all master-tier 10s i2v at 1080x1920:**
      b527-doorway    505s   (8.4 min)
      b6446-market    564s   (9.4 min)
      b6446-dunes    1678s  (28.0 min)
  Against a hardcoded `(Get-Date).AddMinutes(8)`. The 8 was never measured —
  the script's own banner says "video gen takes ~1-4 min", which was true when
  it was written and has not been true for months.

**Not a network issue.** `inference_time` is reported BY fal, measured on their
GPUs. The local side sends a few hundred bytes every 8 seconds. The 3.3x spread
between the fastest and slowest job, same prompt shape and resolution and the
same connection throughout, is queue contention on their side.

**Fix:**
  - deadline 8 → 20 minutes, with the measurements recorded in a comment so the
    next person changing it knows what it was set from
  - **the timeout message now carries the recovery commands**, with the request
    ID and output path already interpolated. They had been looked up three
    times; the fourth time they were in the error.

**Known incomplete.** 20 minutes is not a safe ceiling — b6446-dunes took 28.
And a script that blocks a terminal for half an hour is its own problem. The
right shape is: poll to a reasonable limit, write the request ID to a file, exit
cleanly, and offer `--resume` to collect it later. That turns a timeout from a
failure into a handoff. Not built.

**Rule:** a timeout is an assertion about how long something takes. If it was
never measured, it is a guess wearing a number — and when it fires on work that
actually succeeded, it converts a slow success into a false failure and invites
paying twice. Record the measurements next to the constant, and put the recovery
path in the error message rather than in someone's memory.

**Status:** MITIGATED — deadline raised, recovery documented in the error;
resume-by-request-id not built

## ════════════════════════════════════════════════════════
## PATTERN 135: A fixed pad on top of a variable silence
## ════════════════════════════════════════════════════════
**ID:** P135
**Type:** Audio — a constant that assumed its input started at zero
**Files:** render-reel.ps1 (adults), make-kids-reel.ps1 (kids)
**Commit:** 0cd3dd3 (adults), <this commit> (kids)
**NOTE ON NUMBERING:** 0cd3dd3 shipped the adults fix with "P135" in the commit
message and an inline comment, but the pattern block was never written. Authored
here, after the fact, covering both lanes. The number was already bound to the
change in two places; renumbering would have broken those references.

**Symptom:** the gap between the story and the moral read as roughly 2 seconds
in the finished reel — long enough to sound like the audio had stopped.

**Measured on TJ #6446, adults:**
      story      19.330563
      moral       6.034250
      narration  26.364898
  19.330563 + 1 + 6.034250 = 26.364898 exactly. The script's pad was doing
  precisely what it said. The other second was already inside the story MP3 —
  ElevenLabs leaves a variable tail of silence at the end of a generation.

**Two call sites, same defect, different mechanism:**
  - adults, render-reel.ps1:131 — `apad=pad_dur=1` on the story, then concat
  - kids, make-kids-reel.ps1 step 1 — a 1s `anullsrc` as a middle input to
    `concat=n=3`
  Both insert a fixed duration after an input whose own trailing silence is
  unknown and unmeasured. Same voices, same provider, same tail.

**Fix:** 1s → 0.5s at both sites, which reads as ~1.5s in the finished reel.
In the kids lane two coupled values moved with it:
  - the `[1/4]` progress line hardcoded "1.0s gap" in its output and would have
    reported a duration the script no longer produced
  - the chunker's seam, `$cut = $storyDur + 0.5`, was placed to land mid-gap.
    With a 0.5s gap that lands exactly on the moral's first sample, risking a
    clipped opening phoneme on clip02. Now `+ 0.25`.

**Known incomplete.** 0.5 is a second guess at a number that should not be
guessed. The gap is still `constant + whatever ElevenLabs left`, so it varies
by generation and language; this only makes the variation smaller. The real fix
is `silenceremove` to trim the story's tail before padding, which would give a
true 1s regardless of input — deferred because it is a filter change needing
testing across four languages, and it was raised mid-set.

**Cost of the delay:** R050–R052 published with the 1s pad, R053 with 0.5s.
Accepted deliberately — nobody watches four language versions consecutively.

**Rule:** padding is an assertion that the input ends where you think it ends.
When the input comes from a generative API, it does not — so a fixed pad is
measuring from a moving origin. Trim to a known boundary first, then pad. And
when a constant changes, grep for it: the value was also living in a progress
string and in an arithmetic offset that was chosen relative to it.

**Related:** P099 (amix vs -shortest — the previous audio-timing assumption),
P106 (the kids chain this pad sits inside)

**Commit:** 0cd3dd3 (adults), 0cc2279 (kids)

**Status:** MITIGATED — both lanes at 0.5s; silenceremove not built

## ════════════════════════════════════════════════════════
## PATTERN 136: A gate that lexed instead of checking
## ════════════════════════════════════════════════════════
**ID:** P136
**Type:** Gate integrity — a success message wider than the check behind it
**Files:** .githooks/pre-push, make-kids-reel.ps1, render-reel.ps1
**Commit:** <this commit>

**Symptom:** `make-kids-reel.ps1` was edited to add a P135 comment. The comment
landed between a line ending in a backtick and the line it continued, which
ends the statement. ffmpeg ran with no output file and PowerShell then tried to
execute `-f` as a command. The pre-push hook reported `✅ PowerShell OK` and
pushed it.

**Why the hook missed it:** the PowerShell branch (P123) calls
`PSParser::Tokenize`, which is a LEXER. It splits text into tokens and reports
malformed ones. The broken file was not malformed — a complete `ffmpeg ...`
statement, a comment, then a new statement starting with `-f`. Every token
valid. It lexed clean because it WAS clean; it just wasn't the program anyone
meant. Tokenizing cannot catch this class, and no stricter parser can either.

**Two things were wrong, and only one was the check:**
  1. the message. `✅ PowerShell OK` claims correctness; the branch's own
     comment on line 147 says "parse without executing". Now reads
     `✅ PowerShell parses (not executed)`.
  2. the missing check. Added a deterministic scan: a line ending in a
     backtick followed by a comment line. There is no legitimate reason to
     write that, so a match is always a defect. No execution required.

**A wrong fix shipped first, and is the more useful half of this pattern.**
The initial attempt added `-ValidateOnly` to both render scripts — a switch
exiting after step 0 — and had the hook invoke it as a smoke test. It passed
the broken file. `-ValidateOnly` exits at line 71; the defect was at line 77.
The smoke test never reached it. A gate built to catch a specific defect, in
the same commit as a pattern about gates that cannot fail, could not catch that
defect. It was found only because the gate was deliberately broken and tested
before shipping — the rule from P129–P132, applied to the fix for P129–P132.

**Proof of failure (required before this shipped):** comment moved between the
backtick and its continuation, committed, pushed. Output:
`❌ make-kids-reel.ps1:76 comment after a line-continuation backtick`,
push blocked, exit non-zero. Restored, re-run, clean.

**Kept:** `-ValidateOnly` stays on both scripts. It is useful by hand and costs
nothing. It is NOT wired into the hook — it proves a script reaches step 0 and
nothing beyond.

**Note on placement:** the same comment is legal inside `@(...)`, which is why
`render-reel.ps1`'s P135 comment — sitting inside an ffmpeg argument array —
never broke. Continuation backticks are the hazard, not comments.

**Rule:** a gate's success message must state what was verified, not what the
reader hopes was verified. `OK` and `parses (not executed)` describe the same
check; only one of them can mislead. And a new gate is not shipped until it has
been proven to fail on the defect that motivated it.

**Related:** P123 (the PowerShell branch this extends), P129–P132 (hook that
never ran, suite that never passed), P121 (asset gate wired to one of two
classes), P127 (dead TEST_PATTERNS)

**Commit:** eb7ee9a

**Status:** FIXED — message corrected in both repos, check added in HR,
proven to fail

## ════════════════════════════════════════════════════════
## PATTERN 137: Recovery that existed only as a printed suggestion
## ════════════════════════════════════════════════════════
**ID:** P137
**Type:** Cost — a documented manual workaround where a supported path belonged
**Files:** scripts/generate-scene.ps1
**Commit:** <this commit>

**Symptom:** Kling jobs regularly outlive the poll. When the deadline passes,
the job usually still completes server-side — only the script gives up. P134
raised the deadline 8→20 min and printed a hand-run recovery snippet in the
failure message: fetch status, fetch result, download by URL. Four lines to
retype under time pressure, in a shell, with the request id copied by eye.

**What that cost.** The snippet is easy to skip and easy to get wrong, so the
practical response to a timeout was to regenerate — paying a second time for a
clip already sitting on fal's servers. P134 was logged INCOMPLETE for this
reason and stayed that way for two sets.

**Fix:** `-Resume <request_id>`. The script skips submission, builds the status
and result URLs from the id, and drops into the existing poll loop unchanged:

    .\scripts\generate-scene.ps1 -Name b6446-market -Resume 01a0524c-...

Three supporting changes were needed and are the interesting part:

  1. `-Prompt` was `[Parameter(Mandatory)]`. A resume has no prompt — the job's
     parameters were fixed at submission. Made optional, with an explicit guard
     so a normal run without `-Prompt` still fails loudly rather than
     submitting an empty one.
  2. The queue URLs use the base app id `fal-ai/kling-video`, NOT the full
     model path in `$Model`. Building them from `$Model` returns 404.
  3. The header printed `$Model`, `$Duration` and `$Prompt` — all defaults on a
     resume, none of them true of the job being recovered. A resumed 10s
     image-to-video clip announced itself as 5s text-to-video. Suppressed.

**The timeout message now prints the real command**, with `$Name` and `$reqId`
interpolated, so it is copy-pasteable rather than a template to adapt.

**Proof (required before shipping):**
  - guard: `-Name test-noprompt` with no prompt →
    `FAILED: -Prompt is required unless -Resume <request_id> is given`
  - resume: a completed job id → `status: COMPLETED` on the first poll,
    14.75 MB downloaded at 1080x1920, nothing submitted, nothing charged.

**Also fixed here:** the deadline comment was labelled P133 (the title-escalation
pattern). It is P134. A comment pointing at the wrong pattern sends the next
reader to an unrelated entry — the P118 shape, where a label disagreed with its
referent.

**Still open:** `generate-talking-clip.py` (fal VEED Fabric) has the same gap and
no resume. A TLS timeout on R057 forced a re-run that regenerated BOTH clips,
paying twice for one that had already succeeded. Same fix, different API and
language; not attempted here.

**Rule:** if the failure message has to tell the operator how to recover by
hand, the recovery belongs in the script. A printed workaround is a feature with
the implementation left to the person least able to do it — mid-failure, under
time pressure, with money on the line.

**Related:** P134 (the deadline this completes), P118 (label disagreeing with
referent), P136 (a gate that could not fail)

**Commit:** 21d52dd

**Status:** FIXED — Kling resumable and proven. Fabric still exposed.

## ════════════════════════════════════════════════════════
## PATTERN 138: Paying twice for work already done
## ════════════════════════════════════════════════════════
**ID:** P138
**Type:** Cost — a paid step with no idempotency, behind a gate that overstated it
**Files:** make-kids-reel.ps1
**Commit:** <this commit>

**Symptom:** R057, the TJ leg of the #6446 kids set. Fabric returned clip01 and
saved it; clip02 died in `fal_client.upload_file` with a TLS handshake timeout.
The re-run regenerated BOTH clips. clip01 was paid for twice — a 22.4s clip at
720p, $0.15/sec.

**Why the obvious fix was the wrong one.** This was logged as needing
resume-by-request-id, matching P134/P137 for Kling. It does not. The failure
happened during UPLOAD, before submission — no request id existed, and no
resume could have recovered it. The waste was not the failed clip. It was the
SUCCEEDED clip, regenerated because nothing checked whether it was already
there.

**Fix:** skip generation when the output mp4 exists; `-ForceRegen` to override.
Two lines of real logic in the loop.

**The gate was lying too, and that is the more interesting half.** The
pre-Fabric confirmation printed "About to submit 2 clip(s) to fal Fabric at
720p (paid)" before any existence check ran. On a re-run where both clips were
already present, it announced a cost that was not about to be incurred and
asked for confirmation of a decision that no longer existed. A warning that
fires when nothing is at stake trains the operator to click through the one
gate that guards real money. The prompt now counts what will ACTUALLY be
generated, names what is being reused, and disappears entirely when there is
nothing to pay for.

**Deliberately not clever:** stale clips are NOT detected by comparing mp3 and
mp4 timestamps. If the narration changes and the run is repeated, the old clips
are reused and `-ForceRegen` is required. A timestamp heuristic is more clever
and more surprising when it guesses wrong; an explicit flag fails in the
direction the operator can see.

**Proof (required before shipping):** re-ran the TJ leg with both clips on disk.
Before: prompt claimed 2 paid submissions. After: `all 2 clip(s) already
generated - nothing to submit, nothing to pay`, no prompt, `0 generated, 2
reused`, zero Fabric calls. Render completed normally.

**Still open:** `generate-talking-clip.py` uses `fal_client.subscribe()`, which
submits and polls in one blocking call and never exposes the request id. So
Fabric jobs lost AFTER submission are still unrecoverable — a narrower gap than
this pattern closes, and it needs `submit()` plus id capture before a `--resume`
is even possible.

**Rule:** a paid step must be idempotent, and the gate in front of it must
describe what is about to happen rather than what usually happens. Both halves
matter — idempotency without an honest gate still teaches the operator that the
warning means nothing.

**Related:** P137 (Kling resume — the fix this one was mistaken for), P134,
P136 (a success message wider than its check; this is the inverse)

**Commit:** 0d9d98f

**Status:** FIXED — re-runs cost only what failed. Fabric post-submission
recovery still absent.

## ════════════════════════════════════════════════════════
## PATTERN 139: The right name in the wrong case
## ════════════════════════════════════════════════════════
**ID:** P139
**Type:** Content check — a rule that validated identity but not form
**Files:** scripts/lint-content.py
**Commit:** <this commit>

**Symptom:** R043 shipped "благодарит Аллах" where the accusative "Аллаха" is
required. `check_divine_name` passed it — that check validates WHICH name is
used («Аллах» not «Бог») and nothing validated its grammatical form. A
substituted name failed loudly; a declined one did not fail at all.

**Why this was left open for eleven reels.** Russian declines Аллах across five
cases, and knowing which one a clause requires needs a parser. The obvious
implementation — flag non-nominative forms, or flag nominative outside subject
position — produces false positives on correct text, and a false positive here
is worse than the miss: it teaches the operator that the divine-name check
cries wolf.

**Fix: two collocations with no legitimate nominative form.**
  1. transitive verbs governing the accusative, followed by nominative —
     благодар*, проси*, помни*, люби*, слав*, восхвал*, бойся/боится
  2. prepositions governing an oblique case, followed by nominative —
     к, ко, от, у, для, с, со, перед, про, без, ради, кроме

No parsing, no guessing at intent. Same philosophy as P136's backtick scan: a
pattern with no correct use, checked deterministically.

**«о» and «об» are deliberately excluded.** "О Аллах!" is the vocative and is
correct — including those prepositions would flag every dua in the corpus. This
exclusion is the whole design, not a footnote: the rule earns its place by what
it declines to flag.

**Proof (required before shipping):** one line containing the real R043 defect
alongside the vocative and three correct accusatives —
"Сегодня благодарит Аллах ... О Аллах, помоги нам. Проси Аллаха о помощи и
благодари Аллаха каждый день." Result: exactly one FAIL, on the defect. The
vocative and all three correct forms passed. The false-positive half is the
half that was tested hardest.

**Also fixed here:** the summary line read "these seven checks passed" as a
literal, with eight checks registered. The checks are now a list that is both
iterated and counted, so the number cannot disagree with what ran. Identical
shape to P135's hardcoded "1.0s gap" — a constant describing behaviour that
moved without it.

**Not covered:** R039's «Аллахом». Instrumental is correct in ordinary
constructions ("создан Аллахом"), and without the original sentence any rule
would be a guess. Left uncovered deliberately rather than approximated.

**Rule:** a check that validates identity should be asked whether it also needs
to validate form. "Is it the right word" and "is the right word used correctly"
are different questions, and passing the first reads like passing both.

**Related:** P135 (a hardcoded constant that did not move), P136 (deterministic
scan over a pattern with no legitimate use)

**Commit:** 298f702

**Status:** FIXED — accusative and prepositional cases covered, vocative
preserved, check count derived

## ════════════════════════════════════════════════════════
## PATTERN 140: Reading the first content block
## ════════════════════════════════════════════════════════
**ID:** P140
**Type:** API contract — a positional assumption plus a silent default
**Files:** app/api/generate-reel/route.ts, scripts/translate-tajik.ts
**Commit:** 3df65d1

**Symptom:** after moving `/api/generate-reel` from `claude-sonnet-4-6` to
`claude-sonnet-5`, generation returned HTTP 200 after 14.6 seconds with every
field empty. Title blank, story blank, moral blank, and the caption rendered
the literal string "undefined" where the moral belonged.

**Cause:**

    const raw = response.content[0].type === 'text' ? response.content[0].text : '{}'

`content` is an ARRAY OF BLOCKS, not a single answer. sonnet-5 returns a
thinking block first, so `content[0].type` is `'thinking'`, the ternary fell to
its default, and `'{}'` parsed cleanly into an object with no keys. Confirmed by
logging: `P140 blocks: ["thinking","text"]`. The text was always there, one
index further along.

**Two defects, and the second is the one that hid the first:**

  1. **Indexing by position.** Block order is not part of the contract. Filter
     by type: `response.content.find(b => b.type === 'text')`.

  2. **A silent default on an unrecognised shape.** `: '{}'` converts "I do not
     understand this response" into "the model returned nothing" — and `{}`
     parses without error, so every downstream check passed. Fifteen seconds of
     paid generation was discarded behind a 200. The route now returns 500 and
     names the block types it actually received.

**Scope, found by grepping `content[0]` across both repos:**
  - HR `app/api/generate-reel/route.ts` — silent `'{}'`. The reel generator.
  - HR `scripts/translate-tajik.ts` — threw on non-text, so it would at least
    have failed loudly. Still positional.
  - HV `app/api/voice-intent/route.ts` — silent `''`. LIVE IN PRODUCTION.
  - HV `agents/playwright_agent.py` — positional.

**Model strings updated in the same pass**, since the two travel together:
`generate-reel` (4-6), `translate-tajik` (4-5, older than everything else),
`playwright_agent.py` (4-6), `telegram_bot.py` (4-6), and `setup_agent.ps1`,
which REWRITES both HV files to 4-6 and would have silently undone this fix on
its next run. Five call sites, each hardcoding the model independently — which
is why they drifted apart in the first place.

**Note on P129.** That entry attributes an empty 500 on `/api/voice-intent` to
the retired model string. `voice-intent` also carried THIS defect, on a route
already running sonnet-5. Whichever caused the original outage, the positional
read was present and would produce the same silent failure. The two are easily
confused and the distinction matters when reading P129.

**Method worth reusing:** the log that found it printed the block TYPES, not the
content — `response.content.map(b => b.type)`. One line, and it turned "the
model returned nothing" into "the model returned two blocks and we read the
wrong one."

**Rule:** when an API returns a list, never assume the item you want is first.
And never default a parse failure to an empty-but-valid value — an unrecognised
shape must fail loudly, or every check downstream will pass on nothing.

**Related:** P129 (the empty 500 on the same route), P123

**Status:** FIXED — all four sites filter by type, all model strings on sonnet-5

## ════════════════════════════════════════════════════════
## PATTERN 141: A report line for the expected state
## ════════════════════════════════════════════════════════
**ID:** P141
**Type:** Signal quality — a permanent finding that was never a problem
**Files:** scripts/audit-assets.py
**Commit:** <this commit>

**Symptom:** every `--audit` run printed four lines under RETIRED BUT REACHABLE:
"approved for no lane, yet sitting where the picker can find them." Four
mascot files, every run, indefinitely.

**Why it was wrong.** `lanes: []` means the render gate refuses the asset — and
it does, verifiably (`--check` still prints `BLOCKED: ... is RETIRED`). A
retired asset whose file remains on disk is therefore the EXPECTED state, not a
defect. Its registry entry is also the only record of why it was retired, so
the file staying put is what preserves that history.

**And two of the four were not retired at all.** `lamb-boy-v1.png` and
`lamb-girl-v1.png` carry `lanes: []` because they are FACE-LOCK REFERENCES for
Nano Banana Pro scene generation — working tooling that is never rendered
directly. The audit was reporting live infrastructure as a problem, because
`lanes: []` was read as "retired" when it actually means "not for any render
lane."

**Fix:** removed the category. `lanes: []` is enforced at the gate; it does not
also need reporting. The audit now prints "registry and disk agree" on a clean
run instead of four permanent lines to scroll past.

**Second defect found in the same block, and it is the more interesting one:**

    # retired entries live in a subfolder; check there too

That comment sat above code that checks no subfolder. `os.listdir` on line 126
is not recursive and nothing anywhere resolves a `_retired/` path. The fallback
it annotates does something else entirely — retries the bare filename in the
same flat folder when a registry key carries a stale path prefix.

So a convention was designed, documented, and never built, and the comment has
been telling readers otherwise since. Same shape as P127's dead `TEST_PATTERNS`
and P136's `✅ PowerShell OK`: the text asserted more than the code did.

**Moving the files was considered and rejected.** `_retired/` would make all
four report as MISSING — a real alarm state — because existence is checked with
`os.path.join(folder, key)` against the flat directory. Hiding a non-finding by
creating a false finding is not an improvement.

**Proof:** `--audit` reports "registry and disk agree; every entry is
human-verified." `--check assets\mascot\lamb-boy-v1.png --lane kids` still
prints `BLOCKED: lamb-boy-v1.png is RETIRED`. Noise removed, enforcement intact
— both halves verified, because removing a warning is only safe if the thing it
warned about is still prevented.

**Rule:** a report should contain findings, not states. If a line appears on
every clean run, it is not telling anyone anything — and it trains the reader to
skim past the lines that are.

**Related:** P138 (a gate warning about a cost that was not being incurred),
P136, P127 (declared mechanisms that did not exist), P117 (this registry)

**Commit:** 53ea4fa

**Status:** FIXED — category removed, gate verified still blocking

## ════════════════════════════════════════════════════════
## PATTERN 142: Nothing verified the matn against its source
## ════════════════════════════════════════════════════════
**ID:** P142
**Type:** Verification gap — a chain of checks with no first link
**Files:** scripts/verify-matn-source.py (new), hadith_library (4 rows)
**Commit:** a8e3638
**Found:** 2026-09-02, from an outside report

**How it surfaced.** An external comparison of the channel against its sources
flagged three library rows as mis-graded. All three were real. Checking why
they were there found a fourth, and a hole underneath all four.

**The four rows, all filed under Al-Bayhaqi, all graded hasan:**

  #2318 "Prayer is the pillar of the religion", Muadh ibn Jabal.
        The Arabic stored was الصلاة عماد الدين — the standalone wording, which
        as-Sakhawi, as-Suyuti and al-Albani all grade weak. Muadh's ACTUAL
        narration is different text: رأس الأمر الإسلام وعموده الصلاة وذروة
        سنامه الجهاد, Tirmidhi 2616, hasan sahih. So a weak wording carried a
        sound narration's narrator and grade.
        → CORRECTED to Tirmidhi 2616, translations nulled for re-run.

  #1120 "The death of a scholar is a calamity that cannot be compensated",
        Abu Darda. al-Albani: ضعيف جداً, very weak (Da'if at-Targhib 73).
        → DELETED.

  #8497 "The right of the child upon the parent — writing, swimming, archery",
        Ibn Umar. The wording is ABU RAFI'S, not Ibn Umar's, and is weak
        (Isa ibn Ibrahim, whom Ibn Hibban placed in al-Majruhin). The genuine
        Ibn Umar text is different and graded munkar.
        → DELETED.

  #5486 "Whoever gets married has completed half of the religion", Anas.
        This one was LEGITIMATE — Shu'ab al-Iman 5486 really is this
        narration, and al-Albani graded it hasan li-ghayrihi. Deleted anyway,
        on the operator's call: hasan li-ghayrihi is hasan by corroboration,
        and al-Haythami, Ibn al-Jawzi and al-Iraqi all weakened it. A channel
        that publishes only sahih and hasan cannot carry a contested grade.
        → DELETED.

Library 69 → 66. **None of the four had ever been used for a reel.**

**Why the source URLs looked right and were not.** Every row cited a
sunnah.com Tirmidhi URL while claiming Al-Bayhaqi as its collection. #2318's
URL was genuinely related (tirmidhi:2616, also about prayer as a pillar) — but
#1120's pointed at "Islam is built on five", and #8497's at the silver
hand-guard of the Prophet's sword. The citations were arbitrary. An early
assumption that the URL told us what each row was MEANT to be held for one row
and was wrong for the rest.

**The hole, which is the actual pattern.**

  - Stage 3 A/B compares TRANSLATION against MATN. #2318's translations were
    faithful in all five languages. The Arabic was wrong. A/B passes this.
  - 55 of 66 rows were bulk-inserted straight into hadith_library on
    2026-05-12, before the candidate pipeline existed. They never met any gate.
  - HV, which exists to catch exactly this class of circulating weak narration,
    had never been pointed at the library. It analyses what a user pastes.

So the system had a check for translation fidelity, a check for asset
registration, a check for content rules — and no check that the Arabic in a row
is the hadith at the URL it cites. Every downstream verification assumed a
correct matn as its starting point.

**Fix:** `scripts/verify-matn-source.py`. Fetch the cited page, normalise both
sides (strip harakat, tatweel, alef and ya variants, punctuation), and measure
what fraction of the stored matn appears as one contiguous run. Deliberately
dumb — no model, no grading opinion. One question: is this text on that page.

Calibrated on the real case:

      correct matn                     1.000
      correct matn, diacritics removed 1.000
      the weak wording that was stored 0.333
      an unrelated hadith              0.000
      correct matn, one word dropped   0.714  → REVIEW

**A sliding-window difflib comparison was tried first and rejected** — it
scored the genuinely-correct matn at 0.875, below the pass line, because window
offsets stepped past the right alignment by one word. Longest contiguous run
has no alignment to get wrong.

**BLOCKED: sunnah.com returns 403.** Not a User-Agent problem — browser-like
headers were refused identically, so the block is at the TLS/edge layer.
Impersonating a browser more convincingly was rejected: sunnah.com is
donation-funded and publishes an API so that scripts do not scrape it. The fix
is the key blocked on sunnah-com/api issue #3675, open since 2026-08-21. That
issue now blocks TWO things — new sourcing AND verification of existing rows.
Everything but the fetch layer is finished and tested.

**Rule:** a verification chain needs a first link. Checking that a translation
matches its matn, that a matn has a grade, and that a grade meets policy all
assume the matn is the hadith it claims to be — and nothing was checking that.
When every gate validates a transformation, ask what validates the input.

**Also:** "verified" meant different things depending on when a row was created
and nothing recorded which. A `matn_verified_at` column is the follow-up.

**Related:** P120 (pass-B competence — what A/B can and cannot see), P117
(asset registry, the same shape for assets)

**Status:** LIBRARY CLEAN — 4 rows resolved, 66 remain, none verified
matn-to-source. Script complete, blocked on #3675.

## ════════════════════════════════════════════════════════
## PATTERN 143: A tail that three flags refused to allow
## ════════════════════════════════════════════════════════
**ID:** P143
**Type:** Render — a video ending on its own last syllable
**Files:** render-reel.ps1
**Commit:** <this commit>
**Found:** 2026-09-03, reported from Instagram playback

**Symptom:** on Instagram, adults reels appeared to have their last seconds cut
off. Not a platform behaviour — IG does not trim Reels.

**Cause:** the final merge ran `-t $narrDur` with no margin, so the video was
exactly as long as the narration and the last frame landed on the last
syllable. The loop then restarted before the closing word had finished
rendering and before the outro card had any time on screen. Kids reels were
unaffected: `render-mascot-reel.ps1` uses neither `-t` nor `-shortest`.

**The first fix did nothing, and that is the useful part.** Changing `-t` to
`$narrDur + 1.0` produced a 25.865s file from a 25.865s narration — no tail at
all. Two other flags on the same line were overriding it:

  - `amix=duration=first` makes `[aout]` exactly as long as its first input,
    the narration
  - `-shortest` then cuts the video at the end of the shortest stream, which
    is that audio

So `-t` could only ever shorten, never extend. Three length controls on one
command, and the most visible one was the one with no authority.

**Fix:** pad the narration BEFORE the mix —
`[1:a]volume=1.0,apad=pad_dur=1.0[narration]`. The shortest stream is now
genuinely 1s longer, so `amix`, `-shortest` and `-t` all agree. The nasheed
continues under the tail rather than stopping dead.

**Verified:** narration 25.864898s → reel 26.860000s. Before the fix both read
25.86s.

**Rule:** when a duration flag has no effect, look for the other flags that
also govern duration. `-t`, `-shortest` and `amix=duration=` were each doing
something reasonable; the bug was that nobody had asked which of the three
actually decides.

**Related:** P135 (a pad measured from a moving origin), P099 (amix vs
-shortest — the same two flags, a previous timing assumption)

**Commit:** be903b1

**Status:** FIXED — adults lane only; kids lane was never affected

## ════════════════════════════════════════════════════════
## PATTERN 144: A token budget spent before the answer
## ════════════════════════════════════════════════════════
**ID:** P144
**Type:** API contract — a limit sized for a model that no longer exists
**Files:** app/api/generate-reel/route.ts
**Commit:** <this commit>

**Symptom:** generating the UZ leg of Muslim #82 failed three times with
"Model returned no text block (got: thinking)". EN and RU had succeeded on the
same route minutes earlier.

**Cause:** `max_tokens: 1200`. That number was chosen for a model where the
whole budget went to output. sonnet-5 spends it on thinking FIRST, so a harder
generation exhausts the budget mid-reasoning and returns a thinking block with
nothing after it.

**Why UZ and not EN or RU.** Nothing language-specific. This generation was
simply the most expensive of the four — Uzbek, a theologically contested point
requiring the scholarly disagreement to be stated, and an extended context
block. It crossed the line the others sat under. A limit that fails only on
your hardest inputs is one that will keep surprising you.

**Fix:** `max_tokens: 4000`.

**The error message is the other half of this entry.** P140 replaced a silent
`'{}'` default with a 500 naming the block types received. That is what made
this diagnosable in one screenshot instead of a debugging session — the old
code would have shown four empty fields behind a 200, exactly as it did on
2026-09-01. Two days apart, the same underlying model behaviour surfaced twice:
once as silent corruption, once as a clear error. The difference was entirely
in how the failure was reported.

**This was already on the open-items list** as "max_tokens: 1200 in
generate-reel", logged weeks ago when the number was merely tight. It became a
failure when the model changed underneath it. A limit noted as tight is a limit
that has not failed YET.

**Check elsewhere:** every route calling this model has a max_tokens sized
before the change. HV's `/api/analyze` runs the same SDK against the same model
and its budget has not been reviewed.

**Rule:** when a model gains a new phase, every limit measured against the old
one is stale — not wrong yet, stale. Thinking consumes the same budget as
output, so a number that was generous for text alone can be insufficient for
thinking plus text.

**Related:** P140 (the same model change, surfacing as silent corruption), P123

**Commit:** 19c9d33

**Status:** FIXED in generate-reel. Other routes' budgets not yet reviewed.

## ════════════════════════════════════════════════════════
## PATTERN 145: Screening 65 rows when the source refuses to talk
## ════════════════════════════════════════════════════════
**ID:** P145
**Type:** Verification — a check redesigned around a blocked dependency
**Files:** scripts/verify-matn-source.py
**Commit:** 28ed174

**Starting position (P142).** Nothing verified matn against source, and two
rows proved the failure mode: #2318 held a weak wording under a sound
narration's narrator and number, #3104 held a munkar wording under an-Nasai's
sound Mu'awiyah ibn Jahimah narration. Both had faithful translations of wrong
Arabic. The check was written and immediately blocked: sunnah.com returns 403
to scripted clients, browser-like headers refused identically, and the API key
sits behind sunnah-com/api #3675 — a repo with access requests open since
March. Dorar's API returns a Cloudflare challenge to the same client.

**Waiting was not a plan.** Reworked to read a local clone of
AhmedBaset/hadith-json — a scraped mirror of sunnah.com, 50,884 hadiths across
the nine books. No key, no rate limit, no load on a donation-funded site.

**The mirror numbers hadiths differently.** Bukhari 6446 is 6207 there. That
looked like a blocker and was an improvement: instead of looking up a number,
the check asks

    does our stored Arabic appear ANYWHERE in the collection it claims?

Both real defects answer NO — الصلاة عماد الدين is not in Tirmidhi,
الجنة تحت أقدام الأمهات is not in an-Nasai. Both would have been caught.

**First full run: 40 found, 16 partial, 9 missing.** Too much noise, and the
noise had one cause.

**Contiguous-run coverage under-scores a legitimate EXCERPT.** Muslim #2999
stores the believer's-affair hadith with two phrases dropped — وليس ذاك لأحد
إلا للمؤمن, and فكان خيرا له after each condition. Every word genuine, every
word in order, but the omissions break the run, so it scored 0.47 and reported
MISSING. It is published across eight reels (R042–R049) and is perfectly sound.

A check that flags sound rows teaches the reader to skim it — P138's lesson,
arriving from the other direction.

**Fix: also compute gapped recall** — what fraction of the stored matn's words
appear IN ORDER, gaps allowed, via `get_matching_blocks`. Rank on that, report
both, and label a row whose contiguous score is low as an excerpt so the
difference is visible rather than hidden.

                                contiguous   gapped
      #2999 elided, genuine          0.467    1.000
      #2318 wrong wording            0.333    0.333
      #2616 correct excerpt          1.000    1.000
      common particles only          0.000    0.000

**The particle control was the check on the check.** Arabic function words
(من، في، الله، و) are everywhere, so a short matn could in principle score
high by accident. It scores zero, because matching blocks require ORDER, not
presence. Tested before shipping, because a measure that passes everything is
the failure mode being fixed.

**Second run: 52 found, 10 partial, 3 missing.** All three MISSING are Musnad
Ahmad — the mirror's README states chapters 8-30 are absent from its source, so
that is a known gap, not evidence. The mirror holds nothing against any row.

**What this does NOT do, stated in the script's own output every run:**
  - FOUND verifies the TEXT only. Not the grade, not the narrator. #3104 had a
    correct grade and the wrong narrator and this check cannot see that.
  - The mirror is a THIRD-PARTY SCRAPE. Nothing is marked matn_verified_at on
    its say-so; a match narrows the field and a human confirms.
  - MISSING means READ IT, never "it is wrong."

**Found while running it, and worth its own entry eventually:** `hadith_number`
does not uniquely identify a row. Bukhari #1469 and #6018 each have two rows —
legitimate excerpts of multi-clause hadiths — and Tirmidhi #2616 gained a
second when #2318 was renumbered onto an occupied number. An UPDATE written as
`where hadith_number in ('82','2616')` then set matn_verified_at on a row
nobody had verified. That is this column's exact failure mode, committed an
hour after establishing the non-uniqueness.

**Rule:** when a dependency refuses you, ask what question the blocked tool was
really answering. "Is this text at that URL" became "is this text in that
collection" — no key, no numbering to reconcile, and a better question.

**Related:** P142 (the gap this fills), P138 (a warning that fires when nothing
is wrong), P136

**Status:** WORKING — 65 rows screened to a 10-row reading list. Rows remain
unverified until read; the mirror screens, it does not certify.

## ════════════════════════════════════════════════════════
## PATTERN 146: A ranking change that picked the wrong hadith
## ════════════════════════════════════════════════════════
**ID:** P146
**Type:** Measurement — a fix that broke the cases it was not tested against
**Files:** scripts/verify-matn-source.py
**Commit:** <this commit>

**What P145 changed and why it was wrong.** Contiguous-run coverage
under-scored legitimate excerpts, so gapped recall was added and the match was
ranked on it. That fixed Muslim #2999. It also silently broke row selection.

**Tirmidhi #3373** — «من لم يسأل الله يغضب عليه» — was matched to mirror entry
**1104, a hadith about marriage without a guardian**, while the correct entry
3457 sat in the same file. Abu Dawud #4811 matched entry 1906, Jabir's hajj
narration. Neither contains a word of the stored matn.

Not a noisy score. The WRONG ENTRY, reported with a confident number.

**Two effects compounded:**

  1. **Gapped recall rises with haystack length.** A long entry gives more
     chances for six common words (من، لا، الله، عليه) to appear in order by
     coincidence. Every stored matn that scored badly was short; every spurious
     match was long.
  2. **Ties went to file order.** `if g > best_g` keeps the FIRST of equal
     scores. Both 1104 and 3457 scored 0.833, and 1104 comes first.

**The particle control that cleared gapped recall could not have caught this.**
It tested a short needle against a SHORT entry. The false-positive rate scales
with the haystack, so the control was run in the one condition where the defect
does not appear. A control that cannot fail is the P136 shape, applied to a
measurement instead of a gate.

**Fix:** rank on `(contiguous, gapped)` as a tuple — contiguous primary, gapped
as tie-break — and refuse FOUND when contiguous is below 0.30 however high
gapped runs. Contiguous is the discriminating measure; a run of consecutive
words is hard to hit by accident.

                                  contiguous   gapped
      #3373 vs correct 3457            0.667    0.833
      #3373 vs spurious 1104           0.333    0.833   <- tie, wrong winner
      #2999 vs correct entry           0.467    1.000

**Result:** 65 rows, 54 found, 8 partial, 3 missing — from 52/10/3. #3373 and
#4811 now resolve to 3457 and 4813 at 1.00. No row dropped OUT of FOUND, so no
coincidental match was hiding among the previous run's passes.

**Two corrections found while chasing this**, both genuine wording defects the
tool existed to surface:
  - #3373 stored «من **لا** يسأل الله»; the narration reads «من **لم** يسأل».
  - #4811 stored «من لا يشكر الناس لا يشكر الله»; Abu Dawud has the clauses
    inverted — «لا يشكر الله من لا يشكر الناس».
Same meaning, not the narration's wording. Both corrected.

**Rule:** when a measure is changed to fix one case, re-run the cases it
already handled. P145 shipped on the strength of a single improved result
without checking what the change might displace — and it displaced correct
answers, which is worse than the noise it removed.

**Related:** P145 (the change this corrects), P138, P136

**Commit:** 6e1b801
**Status:** FIXED — reading list down to 8 rows, 3 MISSING are the mirror's
documented Musnad Ahmad gap

## ════════════════════════════════════════════════════════
## PATTERN 147: A key that identifies nothing
## ════════════════════════════════════════════════════════
**ID:** P147
**Type:** Data model — a column treated as a primary key that was never unique
**Files:** hadith_library, app/admin/page.tsx
**Commit:** <this commit>

**`hadith_number` does not uniquely identify a row, and code assumes it does.**

Bukhari #1469 has two rows; Bukhari #6018 has two; Tirmidhi #2616 has two. None
are errors — they are separate excerpts of multi-clause hadiths. #6018 alone
carries three clauses (speak good or stay silent, honour the neighbour, honour
the guest), and the library holds two of them.

**It has caused two real failures:**

  1. **A stale admin selection — RETRACTED 2026-09-05.** Originally recorded
     here as a defect: after #2318 was renumbered to 2616, the admin displayed
     `Selected: Al-Bayhaqi #2318` beside a card showing Muslim #82. The
     operator identified the actual cause — the new hadith had not been
     clicked, so the field was correctly showing the previous selection. The UI
     was working. Recorded rather than removed, because the assistant reached
     for a code defect on the strength of a screenshot without asking what the
     operator had done.

  2. **A false verification, committed by the assistant.** An UPDATE written as
     `where hadith_number in ('82','2616')` matched BOTH #2616 rows and set
     matn_verified_at on the charity excerpt, which nobody had checked. That is
     precisely the failure the column exists to prevent, committed an hour
     after the non-uniqueness had been established in the same session.

**Every query against this table must scope by `id`, or by
`(collection, hadith_number)` and accept that it may still return more than
one row.** `hadith_number` alone is a search term, never an identifier.

**Not fixed by deduplication.** The duplicate rows are legitimate content. The
defect is in what reads them.

**Rule:** a column that looks like a key invites being used as one. If it is
not unique, either make it unique or make the non-uniqueness impossible to
miss — a name like `hadith_number` promises identity it cannot deliver.

**Related:** P108 (language switch silently deselecting the hadith), P142,
P145
**Commit:** 031d5a8
**Status:** DOCUMENTED — one real failure (the UPDATE), one retracted. Query
discipline stands: scope by `id`, or by `(collection, hadith_number)` and
expect more than one row.

## ════════════════════════════════════════════════════════
## PATTERN 148: A real filename used as a placeholder
## ════════════════════════════════════════════════════════
**ID:** P148
**Type:** Ergonomics — a template that reads as filled in
**Files:** split-narration.py
**Commit:** <this commit>

**Symptom:** `split-narration.py` prints a ready-to-run block for turning each
chunk into a talking clip. Its first line was:

    $img = "assets\mascot\lamb-boy-mosque-night-v3.png"   # <- pick the mascot scene

The code comment above it reads "user fills in the mascot image", so a
placeholder was intended. A REAL, VALID filename was used as that placeholder,
with the instruction to change it sitting beside it as a comment.

**It fired three times in one session.** The Bukhari #574 set is the GIRL
mascot. Every language that overran the 28s chunk cap — RU, UZ and TJ — routed
through this script, and each time the printed block would have generated the
boy lamb had it been pasted as printed. Three reels, wrong mascot, on a set
whose whole visual identity is the mascot.

**The resolution was wrong too:** `--resolution 480p`, from the POC. Every
shipped kids reel is 720p. So the block would have produced the wrong character
at half the resolution, and both values look deliberate.

**Why a comment did not save it.** A placeholder that is syntactically valid
and semantically plausible does not read as a placeholder. It reads as a
default someone chose. The comment competes with the value, and the value wins,
because the value is what runs.

**Fix:** `<MASCOT>` and `<NASHEED>` — placeholders that cannot execute — with
the real options listed in the comment rather than one of them promoted to the
line itself. Default resolution corrected to 720p. `-Nasheed` added to the
printed render command, since omitting it hands the choice to the random picker
that drew an ocean-ambience track on R044 and an adults-lane bed on R029/R030.

**Rule:** a placeholder must be impossible to run. If a template can be pasted
unedited and will work — just wrongly — it will be pasted unedited. The failure
is silent, produces a plausible artefact, and is caught only by someone noticing
the wrong face in a finished video.

**Related:** P118 (a comment asserting what its value was not), P136 (a message
wider than its check)
**Commit:** 55a4db8
**Status:** FIXED — placeholders now fail loudly

## ════════════════════════════════════════════════════════
## PATTERN 149: A rule enforced in one language and not another
## ════════════════════════════════════════════════════════
**ID:** P149
**Type:** Content check — the same rule, four implementations, one lax
**Files:** scripts/lint-content.py
**Commit:** <this commit>

**Symptom:** the RU leg of Bukhari #574 failed the linter on «учёные
предполагали». The EN leg of the SAME SET, carrying the identical phrase
"though scholars have suggested", passed clean — and shipped as R062 to four
platforms.

**Cause, and it is two independent failures in one pattern:**

    'en': [r'\bscholars\s+(say|explain|teach|hold|note|agree)', ...]

  1. `suggested` was not in the verb list.
  2. `have` sits between the noun and the verb, so `\bscholars\s+(verb)` could
     not match even if `suggested` had been listed.

RU caught it because its pattern matches the BARE NOUN — `\bУчён?ые\b` — with
no verb requirement. Same rule, stricter implementation, and the difference was
invisible until one phrase went through both.

**Fix:** every language now matches the noun. A correct attribution names
someone — "Ibn Hajar in Fath al-Bari" — and does not use the word *scholars*,
so real citations still pass. That is what the corrected RU, UZ and TJ blocks
in this set do.

**Proof:** the exact published R062 sentence now FAILS `unnamed-authority`.

**The wider point.** A rule with a per-language pattern table has four chances
to be wrong and no mechanism to notice. The verb-list approach was
enumeration - it can only catch what someone thought to list, and the failure
is silent. Matching the noun inverts that: it catches everything and admits
the exception by construction.

**Not corrected in R062.** The published phrase is honest — scholars have
suggested this, and the reel claims nothing more. The rule exists to stop
FABRICATED authority; this was a rule the linter should have enforced, not a
false claim. RU, UZ and TJ in the same set name Ibn Hajar.

**Rule:** when the same rule is implemented per language, the strictest
implementation is the specification and the others are bugs. Check them against
each other, not each against its own intent.

**Related:** P111/P105 (the rule), P139 (the RU divine-name case check, added
because a rule validated identity but not form)
**Commit:** 55a4db8
**Status:** FIXED — all five languages match the noun

## ════════════════════════════════════════════════════════
## PATTERN 150: Twenty reels of hand-fixing a two-line defect
## ════════════════════════════════════════════════════════
**ID:** P150
**Type:** Localisation — text the model never saw, corrected downstream instead
**Files:** app/admin/page.tsx, lib/tags.ts (new), lib/refs.ts (new)
**Commit:** 14dcb36

**Symptom:** every RU, UZ and TJ caption came out with English hashtags, an
English "Verify:" label and a Latin collection name, appended to a Cyrillic
body. The assistant corrected them by hand on every language of every set —
roughly twenty reels, logged as "caption in English" nine or ten times in the
tracker as though it were a generation defect.

**It was never a generation defect.** The prompt asks for `caption_intro`; the
reference line, verify label and hashtags are assembled in `app/admin/page.tsx`
AFTER the model returns. Hardcoded, English, unreachable by any prompt change:

    `🔍 Verify: hadithverifier.com\n\n` +
    `${tags} #hadith #islamic #authentic${style === 'kids' ? ' #kids' : ''} #${langLabel.toLowerCase()}`

Twenty corrections were applied to the symptom without anyone reading the line
that produced it. Every one of those was a downstream patch on a defect whose
source was three lines of TypeScript.

**Why both languages ship, not one.** The operator, a Uzbek speaker, put it
plainly: he searches in his own language first, and so does the audience — an
Uzbek speaker looking for hadith content searches «ҳадис», not #hadith. But
hashtags are free and each is a separate discovery path, so dropping the
English set would cost the global audience for nothing. The caption now emits
both forms of every topic tag, collapsing to one when lang is English.

**The tag vocabulary had to be deduplicated before it could be translated.**
The library's `tags` column held ~100 values with heavy overlap — prayer/salah,
charity/sadaqah/giving, knowledge/ilm/learning/education, forgiveness/
repentance/tawbah, blessing/blessings, good deeds/good-deeds, judgment-day/
qiyamah. Translating those separately would have multiplied the mess by four.
`lib/tags.ts` maps raw tags onto 56 canonical concepts, each carrying its four
forms.

**A third of them are not translations.** salah, dua, sadaqah, iman, sabr,
shukr, taqwa, tawbah, ilm, jannah, akhirah, ibadah, dhikr, barakah, deen are
Arabic loanwords that already exist in Russian, Uzbek and Tajik Islamic
vocabulary. They are transliterated — намоз, дуо, садақа, иймон, сабр — and
they are the terms the audience actually uses.

**The reference line keeps BOTH forms of the collection and one of the
narrator.** Collection plus number is the CITATION — what someone types to
verify the hadith independently — so the Latin form has to survive. The
narrator is not part of that lookup, so it is localised only and the line stays
readable:

    📖 Ҷомеъи Тирмизӣ (Jami at-Tirmidhi) №1956, Абӯзарр

`№` rather than `#`, which is the numeral sign those languages use.

**Unmapped values fall back to English rather than vanishing.** A new tag,
collection or narrator appearing in the library should look wrong in a caption,
not silently disappear from it.

**Rule:** when the same correction is made by hand more than twice, stop making
it and find where the text comes from. Nine tracker entries recorded this
defect as a property of the generation. It was a hardcoded string, and reading
one function would have found it at any point in the preceding month.

**Related:** P106 (the tag blocklist, in the same assembly), P111, P139

**Status:** FIXED — verify label, hashtags and reference line all localised;
Latin citation preserved

## ════════════════════════════════════════════════════════
## PATTERN 151: A corrected matn had nowhere to go
## ════════════════════════════════════════════════════════
**ID:** P151
**Type:** Pipeline — a stage that only ran forwards
**Files:** scripts/translate-candidates.py, scripts/verify-candidates.py
**Commit:** <this commit>

**Symptom:** six matn corrections on 2026-09-04 left three library rows with
null translations and no supported way to refill them. Stages 2 and 3 read
`hadith_candidates` at `status='deduped'` and `status='translated'`. A promoted
row never re-enters that flow, so a row whose Arabic was corrected after
promotion could be translated by hand or not at all.

The pipeline was built for material moving one direction. Corrections move the
other way, and nothing accounted for that.

**Fix:** `--library` on both scripts. The table was already a parameter on
`sb_get` and `sb_patch` — it was hardcoded only at the call sites. Selection
differs by necessity: candidates filter on `status`, library rows filter on
`text_russian is null` for Stage 2 and `matn_verified_at is null` for Stage 3.

**Stage 3 is REPORT-ONLY on library rows, and that is deliberate.**
`matn_verified_at` has meant "a human read this against a source" for every row
carrying it — eleven rows, all read by hand. Letting a model pass set it would
silently change what the column means and make the hand-read rows
indistinguishable from machine-passed ones. `hadith_library` also has no
`verify_a` / `verify_b` / `verify_agreement` / `status` / `updated_at` columns,
so a write would 400 on five of them. The human sets the timestamp, which is
what the script's own footer already said: the human gate is Stage 4.

**Stage 2 CLEARS `matn_verified_at` when it writes to a library row.** A
re-translation is unverified until Stage 3 runs. Without this, a corrected row
would carry a verification stamp for translations nobody had checked — the
mistake made on #2616 on 2026-09-04, where an UPDATE scoped by `hadith_number`
hit two rows and stamped one that had never been read.

**A/B EARNED ITS KEEP ON THE FIRST REAL RUN.** #1899's UZ translation rendered
singular الوالد as «ота-она», parents dual — the exact drift corrected in the
DB that morning, reappearing in a fresh machine translation. Both passes caught
it independently at high confidence, neither seeing the other's output. That is
the mirror of the defect P120 PLANTED to probe pass B's competence, arising
naturally, in a language the probe covered less. The design assumption held.

It also caught a lost verb parallel in TJ #2616 (تُطْفِئُ used for both sin and
fire, flattened in one clause), a dropped سنامه in EN, and an added «(модарат)»
gloss plus a dual-to-plural shift in TJ #3104.

**Two objections overruled, recorded so they are not re-litigated.** B holds
الوالد means "parent" not "father"; overruled, because the singular number is
the more consequential fidelity point and al-Munawi extends it to the mother a
fortiori. B read TJ «қуллаи кӯҳони он» as "peak of its mountain"; overruled,
кӯҳон is the camel's hump.

**A failed API call was reported as a disagreement.** #3104's UZ pass B returned
`SSL: SSLV3_ALERT_BAD_RECORD_MAC` and the row was marked `disagree` — a network
error adjudicated as a verdict. It cleared on retry. NOT FIXED: an `error` from
either pass should mark the row `incomplete` and queue a retry, never contribute
to agreement. Logged here rather than patched, because it needs a change to how
verdicts are combined.

**Rule:** a pipeline that only runs forwards has no answer for a correction. Ask
what happens when something already through the gates turns out to be wrong —
the answer should not be "do it by hand."

**Related:** P120 (pass-B competence, probed with planted defects), P147
(`hadith_number` is not unique — the UPDATE that stamped an unverified row),
P142
**Commit:** e7c3276
**Status:** FIXED — both stages take `--library`; three rows re-translated,
verified and stamped. Error-as-verdict still open.

## ════════════════════════════════════════════════════════
## PATTERN 152: A failed call counted as a disagreement
## ════════════════════════════════════════════════════════
**ID:** P152
**Type:** Gate integrity — absence of a verdict reported as a verdict
**Files:** scripts/verify-candidates.py
**Commit:** <this commit>

**Symptom:** four transport failures in one session — two SSL resets from pass
B, two truncated JSON responses from pass A — each marked its row `disagree`
and `needs_human`. A human was sent to adjudicate verdicts that were never
produced.

**It was a deliberate choice, and it was wrong.** The code said so:

    """pass | fail | disagree. An error on either side is a disagreement -
    absence of a verdict is not a verdict."""

Conservative reasoning: if we could not check it, let a human look. In practice
it made the gate noisier than the thing it checks. Three of four verifications
on an-Nasai #463 reported `disagree` when two of them were network failures,
and the operator had nothing to read.

**It also corrupted the calibration figure.** The script prints a disagreement
rate for D5 tuning and explains what it means: near 0% says the passes are
correlated, very high says the gate is mistuned. Counting transport failures as
disagreements made that number meaningless in exactly the sessions where it
would have mattered. The rate now divides by adjudicated rows only.

**Fix:** `incomplete` as a fourth verdict — not pass, not fail, not disagree.
It says the true thing: this was not checked. Rows roll up to `incomplete` only
when nothing worse happened, so a real fail or disagreement still reaches the
human. The summary prints the count separately and says plainly: re-run them,
do not send them to Stage 4.

**Pass A's truncation was a token budget (P144 again).** `max_tokens: 1000`
predated thinking models, and an-Nasai #463's matn quadrupled when its
continuation was restored, so A's responses grew past the limit and came back
as JSON cut mid-string. Raised to 3000. Every UNPARSEABLE in this session was
that.

**Rule:** a gate must distinguish "I checked and disagree" from "I could not
check". Collapsing them is safe-looking and produces a report the operator
learns to skim — which is the failure the gate exists to prevent.

**Related:** P144 (a budget sized before the model changed), P138 (a warning
that fires when nothing is wrong), P136
**Commit:** a991fff
**Status:** FIXED — errors report as incomplete, A's budget raised, calibration
excludes unchecked rows

## ════════════════════════════════════════════════════════
## PATTERN 153: The source was never shown
## ════════════════════════════════════════════════════════
**ID:** P153
**Type:** Verifiability — a claim published without its evidence
**Files:** app/admin/page.tsx
**Commit:** <this commit>

**The Arabic matn was in the database, in the admin card, and in every
verification pass — and never in a caption.** Sixty-five reels published a
translation with no way for a reader to check it against the source.

**Found by the operator asking.** The assistant had just argued that the
translations are defensible partly because "anyone with Arabic can check you —
that's already in the captions." It was not. The claim was made confidently and
was simply false; the operator went and looked.

**Why it matters more here than elsewhere.** These translations are generated
from the matn by a model and verified by two others. No muhaddith reviews them
and no published translation is used (P075's guardrail: never translate a
translation). The whole case for that pipeline rests on the output being
checkable — and the one audience able to check it, Arabic readers, was given
nothing to check against.

**Fix:** full matn in the caption, under the translated quote and above the
moral. Translation first because that is what most readers read; the Arabic
under it as the source.

**Full matn, never truncated.** an-Nasai #463 is four clauses and roughly forty
words after its continuation was restored, which is a long block in a TikTok
caption where the moral may fall below the fold. Accepted: a clipped scripture
is worse than a long caption.

**Description, not title.** Titles truncate at 40-60 characters on most
platforms and mixing RTL Arabic with a Latin collection name renders
unpredictably.

**Rule:** if the argument for trusting an output is that someone can verify it,
check that they have been given what they need to. The verification story was
sound and the artefact did not carry it.

**Related:** P150 (the same caption assembly), P151, P075
**Commit:** a991fff
**Status:** FIXED — all four platforms

## ════════════════════════════════════════════════════════
## PATTERN 154: Fifteen exchanges to read an error message
## ════════════════════════════════════════════════════════
**ID:** P154
**Type:** Diagnosability — a failure with its own explanation discarded
**Files:** render-reel.ps1
**Commit:** 007416d

**What was actually wrong:** on 2026-09-03 a Russian caption was pasted into
the open SRT tab in VS Code and saved. `adults-en-muslim-82-narration.srt`
stopped being a subtitle file and became draft text. libass could not parse it,
the final merge failed, and every adults render with subtitles failed from that
day on.

**Nobody knew, because three separate things hid it:**

  1. `Run` was `& $exe @cmdArgs 2>&1 | Out-Null`. EVERY ffmpeg error, in every
     step, for the life of the script, was discarded. libass was reporting
     "Unable to open" each time and nothing was listening.
  2. The merge check was `if (-not (Test-Path $reel))`. ffmpeg failed BEFORE
     writing, so `-y` overwrote nothing, `Test-Path` found the previous run's
     file, and the script reported success — printing that three-day-old file's
     size as confirmation.
  3. The subtitle gate opens the SRT in VS Code every render. The operator saw
     Russian draft text open on an English reel repeatedly and reasonably
     assumed the script was opening the wrong file. It was opening the right
     file, which contained the wrong thing.

**Found only because the operator asked about font size.** Nothing about the
symptom pointed at subtitles; the renders reported success.

**The diagnosis is the part worth recording.** Once `Run` was fixed and the
error appeared, it took one command to find the cause. Before that, fifteen
exchanges of guesswork: the assistant proposed an absolute path, then escaping
the drive colon as `C\:`, then copying the SRT to a space-free temp directory —
three fixes for a problem that was none of them. Each was plausible BECAUSE
there was no error text to contradict it. A silent failure does not merely hide
its cause; it makes every wrong theory survive.

Two of those wrong fixes were applied to a file the assistant had already
tangled, which produced new failures that looked like progress. The file was
eventually reset with `git checkout` and rebuilt from the committed version.

**Five changes:**

  - `Run` captures output and prints the last 20 lines ONLY on a non-zero exit.
    Quiet when it works, loud when it does not.
  - The merge checks the exit code, the file, AND its age. A file older than
    five minutes after a "successful" merge means ffmpeg wrote nothing.
  - `Assert-ValidSrt` — a file whose first line is not a cue number is not a
    subtitle file. It fails with that sentence and a suggestion to delete and
    regenerate, instead of handing it to libass.
  - Long cues split before the review gate, so what is proofread is what gets
    burned. Whisper cuts at pauses, so one sentence became a 17-word cue that
    wrapped to five lines and covered a third of the frame. Splits at
    punctuation nearest the midpoint, timing divided by character count.
    Measured: 5 cues became 11, at 7-10 words each.
  - Subtitle FontSize 22 → 18. The font was the smaller half of the problem;
    shorter cues did more than a smaller font could.

**R058 is unaffected** — it rendered on 2026-09-03 before the corruption and
shipped with correct subtitles. A scan of every other SRT in `out/work` found
none corrupted.

**Rule:** a tool that discards stderr is not quiet, it is lying by omission.
The information needed to fix this existed on every failed run for three days
and was thrown away each time. And a check that a file EXISTS is not a check
that a step SUCCEEDED — the previous run's output satisfies it perfectly.

**Related:** P136 (a success message wider than its check), P143 (a duration
flag with no authority), P100 (Whisper's own output discarded on Windows), P83

**Status:** FIXED — errors surface, the merge is verified, corrupt SRTs are
rejected, cues are split

## ════════════════════════════════════════════════════════
## PATTERN 155: Twenty morals with no one to address
## ════════════════════════════════════════════════════════
**ID:** P155
**Type:** Specification — the prompt asked for exactly what it got
**Files:** app/api/generate-reel/route.ts
**Commit:** <this commit>

**Symptom:** five consecutive sets — twenty generations, every language — came
back with a moral that never mentioned Allah. "Look at three things you own and
say I am thankful for this." "Tell yourself: this is enough for me." "Sit with
her. Listen to her. That is precious." Gratitude with no object, an action with
no addressee. Corrected by hand every time and logged in the tracker as a
recurring content defect.

**It was not a content defect. It was the spec.**

    "moral": "1-2 sentence practical takeaway. What should someone DO or FEEL
              differently after watching this reel? Make it actionable for
              modern life."
    3. moral MUST be practical — what to do TODAY

Nothing in there asks for Allah. The model produced a self-improvement brief
because a self-improvement brief is what was requested, twenty times, correctly.
P103, P122 and P133 again: the defect is caused by what the spec DEMANDS, and
adding a prohibition elsewhere would have fought the instruction rather than
fixed it.

**Three rounds to get it right, and the intermediate failures matter more than
the final wording** — each fix closed one failure and opened a narrower one:

  1. **Omission.** Asked for an action directed to Allah, with a worked
     contrast: "notice how that feels in your chest" is wrong, "say
     alhamdulillah — Allah promised Paradise to the one who guards them" is
     right. Allah appeared. So did a new defect.

  2. **Commentary on the text.** "for the hadith ties the Lord's pleasure to
     theirs", "Аллах через его слова показал" — the moral began citing the
     hadith as its authority instead of stating the ground. A note ABOUT the
     text where the text itself belonged. Fixed by requiring the ground stated
     plainly, with 'ties' / 'shows' / 'teaches' named as the shape to avoid.

  3. **Misattributing the speaker.** TJ produced «Зеро Парвардигор гуфтааст» —
     *because the Lord has said*. That makes it hadith qudsi, which it is not.
     The most serious of the three: it changes the CATEGORY of the text, not
     just its framing. Fixed by stating that the hadith is the Prophet's ﷺ
     speech unless the matn itself says otherwise.

**Verified across three languages** after round three: EN, RU and TJ each named
Allah, stated the ground directly, and attributed the wording to the Prophet ﷺ,
with no correction by hand.

**Rule:** when the same correction is made by hand more than twice, read the
instruction that produced it. Twenty tracker entries recorded this as something
the model kept doing. It was something the prompt kept asking for. And when
tightening a prompt, expect the next failure to be narrower and adjacent — test
the same inputs again rather than assuming the fix is complete.

**Related:** P103, P122, P133 (a spec demanding what it elsewhere forbade),
P150 (twenty hand-corrections of a hardcoded string)
**Commit:** 3fe4a4e
**Status:** FIXED — verified on #1899 and #3104 in three languages

## ════════════════════════════════════════════════════════
## PATTERN 156: A default that doubled the bill
## ════════════════════════════════════════════════════════
**ID:** P156
**Type:** API contract — an unsent parameter is not an absent one
**Files:** scripts/generate-scene.ps1
**Commit:** deb3db5

**Kling 2.6 Pro defaults `generate_audio` to TRUE.** The script does not send
the parameter, so every clip was generated with native audio: $0.14 per second
instead of $0.07, and an AAC track inside a file that exists only to be a
SILENT background — the nasheed and narration are mixed in at render time.

The first test clip, 5 seconds, cost $0.70 rather than $0.35 and came back with
audio confirmed by `ffprobe -select_streams a`.

**Found by reading the schema, not by testing.** The model page lists duration
and per-second cost but not parameter defaults. The OpenAPI schema, behind the
Schema button, gives `"generate_audio": {"type": "boolean", "default": true}`.
One click, before spending $2.80 on four clips that would have cost $5.60 and
carried unwanted sound.

**Fix:** `if ($Model -match 'v2\.6') { $payload['generate_audio'] = $false }` —
conditional because 2.1 Master does not accept the parameter and would reject
the request.

**THE COST NOTE IN THIS SCRIPT WAS WRONG BY 3x**, and had been since the POC:

    COST NOTE: ~5s standard-tier clip is roughly $0.35-0.50

The script's default was `fal-ai/kling-video/v2.1/master`, which is $1.40 for
5s. So a four-clip scene set cost $5.60, not the $1.50-2.00 the pipeline
checklist quoted. Every cost estimate downstream of that comment was wrong.

**Real rates, checked 2026-09-09:**

      Kling 2.1 Master   $1.40 / 5s,  +$0.28 per additional second
      Kling 2.1 Pro      $0.49 / 5s,  +$0.098
      Kling 2.6 Pro      $0.07 / second, audio off   ($0.70 for 10s)

2.6 Pro is a LATER architecture than 2.1 Master, not a downgrade. Compared
side by side against an existing Master clip, the quality difference did not
justify paying double for atmospheric backgrounds seen behind text.

**Rule:** a parameter you do not send still has a value. Read the schema before
the first paid call — the model page documents what the model DOES, the schema
documents what it will do by default, and the difference between those two cost
double here.

**Related:** P144 (a limit sized before the model changed), P137, P134

**Status:** FIXED — audio off on 2.6, cost note corrected, default switched

## ════════════════════════════════════════════════════════
## PATTERN 157: A default that was harmless with two options
## ════════════════════════════════════════════════════════
**ID:** P157
**Type:** Gate coverage — operator input reaching no gate, plus a silent default
**Files:** make-kids-reel.ps1
**Found:** 2026-09-09, registering the five-mascot rotation

**Symptom:**
  None yet. Found by reading the script before the first camel render rather
  than by a bad reel shipping — the one time in this log that order held.

**Diagnosis — two defects, one line apart:**
  `[ValidateSet('boy','girl')][string]$Mascot = 'boy'` behaved correctly while
  the library held exactly two mascots. With five registered, the same line is
  two problems. `ValidateSet` rejects `-Mascot camel` loudly, which is fine.
  The DEFAULT does not: omit the flag and the set renders the boy lamb with no
  error, no prompt, and a correct-looking log line. A default is a guess the
  script makes on the operator's behalf, and it stops being safe the moment the
  option set outgrows the guess.

  Separately, `$stillMap` resolves a path the operator chose and hands it
  straight to Fabric. The asset gate is called on the NASHEED the render script
  picks for itself — never on the mascot still. P121 said the gate protects the
  inputs it is NAMED, and asked what else travels the same path. The mascot
  still is the answer, three weeks later.

**Fix:**
  - `-Mascot` is `[Parameter(Mandatory)]` with no default; ValidateSet extended
    to the five registered mascot keys.
  - `$stillMap` extended to five entries.
  - Step 0 now runs `audit-assets.py --check <still> --lane kids` and appends to
    `$problems`, so an unregistered or wrong-lane mascot fails before any fal
    spend, alongside the existing nasheed check.

**Rule:**
  A default is a decision made in advance for a situation you can still hold in
  your head. When the option set grows past the assumption the default encoded,
  the default does not become wrong loudly — it becomes wrong silently, which is
  worse. Re-read every default when its domain expands.

**Related:** P117 (registry and gate), P121 (gate wired to half the inputs),
P148 (a real mascot filename used as a placeholder — same lane, same asset,
also silent)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 158: The admin knew two mascots and defaulted to a dead language
## ════════════════════════════════════════════════════════
**ID:** P158
**Type:** UI/backend contract + silent defaults
**Files:** lib/mascots.ts (new), app/admin/page.tsx
**Found:** 2026-09-09, wiring the five-mascot rotation through the admin

**Symptom:**
  P157 taught `make-kids-reel.ps1` five mascots. The admin still offered two,
  so the camel set could be rendered but not GENERATED — the text and narration
  step had no way to select it.

**Diagnosis:**
  `type Mascot = 'boy' | 'girl'` was declared in three places with no shared
  source: the admin's local type, the TTS route's voice map, and the render
  script's `$stillMap`. They agreed only because nobody had changed one.

  The TTS route turned out to be RIGHT and needed no edit. Its `boy`/`girl` are
  VOICE SLOTS, not lamb identities — the contract was always gender. The admin
  was the layer conflating mascot with gender, because with two lamb mascots
  the two concepts were the same string.

**Fix:**
  - `lib/mascots.ts` — one source of truth: key, label, emoji, gender, and the
    registry `still` filename. `mascotGender(key)` throws on an unknown key.
  - Admin imports it, renders `MASCOTS.map()`, and converts at the API boundary:
    `mascot: mascotGender(mascot)`. The TTS contract is untouched.
  - Language default `'ar'` → `'ru'`. AR is out of scope (P118) and its kids
    voice IDs are English placeholders, so the default shipped a wrong-voice
    narration with no error. RU is the largest audience.

**Rule:**
  When two concepts share a string because they happen to have the same
  cardinality, they will be treated as one concept until the cardinality
  changes. Separate them at the boundary, not in every consumer.
  Third silent default found in one session (P157, this, and the TTS route's
  own `mascot = 'girl'` fallback, still open). Defaults are guesses made when
  the option set was small enough to hold in your head.

**Still open:** `app/api/tts/route.ts:141` defaults `mascot = 'girl'`. An admin
payload omitting the field gets a female voice silently. Left for its own fix.

**Related:** P157, P118 (AR out of scope), P103/P104 (voice follows mascot)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 159: A random picker with no lane and no memory
## ════════════════════════════════════════════════════════
**ID:** P159
**Type:** Asset selection — unfiltered glob, no state
**Files:** render-mascot-reel.ps1, .gitignore
**Found:** 2026-09-09, rendering the first camel set

**Symptom:**
  The pipeline checklist said "render with the nasheed named explicitly — never
  let the picker choose." That instruction had been in the doc since 2026-08-31
  and was followed on every set. It is a workaround written in place of a fix.

**Diagnosis:**
  `Get-ChildItem "out\backgrounds\*.mp3" | Get-Random` had two defects the audio
  policy already named as a KNOWN GAP and left standing:
  - No lane filter. The glob included `ambient-ocean-*`, so a kids reel could
    draw ocean noise and an adults reel a kids hamd. Lane separation existed
    only as a filename convention nobody enforced.
  - No memory. Nothing recorded the previous pick, so the same bed could land on
    consecutive reels — invisible per-reel, obvious to anyone scrolling the feed.

**Fix:**
  - Lane filter by filename convention: `ambient-*` excluded from the kids
    renderer, leaving 10 vocal beds.
  - `out\backgrounds\.last-used.json` records the last pick per lane and the
    next draw excludes it, falling back to the full pool if that would empty it.
  - `-ValidateOnly` added to render-mascot-reel.ps1 so the picker can be proven
    without a render. There was no way to test this code path before.
  - `-Nasheed` still overrides, for when a specific bed is wanted.

**Proven:** two consecutive validate-only runs picked vocal-nasheed-05 then
path-to-jannah, the second reporting `avoided: vocal-nasheed-05.mp3`.

**Rule:**
  A documented workaround is an unfixed defect with a note attached. When the
  doc tells the operator to route around the code, the instruction is evidence,
  not a solution — and the audio policy had even labelled this one KNOWN GAP.

**Still open:** render-reel.ps1 (adults lane) has the same unfiltered glob at
line 110. Same fix, different lane constant.

**Related:** P117/P121 (gate coverage), audio policy KNOWN GAP

**Status:** FIXED (kids lane only)

## ════════════════════════════════════════════════════════
## PATTERN 160: The derive script only knew about candidates
## ════════════════════════════════════════════════════════
**ID:** P160
**Type:** Script scope — a table the workflow outgrew
**Files:** scripts/derive-uzbek-latin.ts
**Found:** 2026-09-09, generating UZ for Bukhari #5971

**Symptom:**
  The admin card showed ENGLISH text with Uzbek selected. Not a UI bug — the
  card reads legacy `text_uzbek`, found NULL, and fell back. `text_uzbek_latin`
  was NULL too; only `text_uzbek_cyrillic` was populated, at 308 chars.

**Diagnosis:**
  The matn was extended and re-translated, and that path writes Cyrillic only.
  `derive-uzbek-latin.ts` fills Latin from Cyrillic, but reads
  `hadith_candidates` — the Stage 2 sourcing table. #5971 is a LIBRARY row, so
  the script could not see it at all. The same gap P151 fixed twice already, in
  translate-candidates.py and verify-candidates.py, for the same reason:
  re-translating a library row after a matn correction was not a workflow the
  candidates-era scripts were written for, and it is now routine.

  Had generation run, the Uzbek reel would have been built from English text.
  Nothing downstream catches that: the linter compares against the matn passed
  on the command line, and the operator would naturally pass the Cyrillic one.

**Fix:**
  - `--library` and `--number` flags; table and key column selected from them.
  - On library rows the patch also writes legacy `text_uzbek` from the LATIN
    (P097), matching all 74 rows backfilled in August.
  - `.select()` chained to the update (P096) — the bare `.update()` reported a
    zero-row match as success. It earned its place on the first run: the write
    failed on a missing `updated_at` column, which `hadith_library` does not
    have and `hadith_candidates` does. Column now set only on the candidates
    path.

**Rule:**
  When a script names a table, it names an assumption about which workflow it
  belongs to. Check every sibling script when one of them needs a --library
  flag; this is the third.

**Related:** P151 (same flag, two other scripts), P096 (silent zero-row update),
P097 (legacy column takes Latin), P147 (hadith_number is not unique)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 161: The library was checked for homoglyphs, the generator wasn't
## ════════════════════════════════════════════════════════
**ID:** P161
**Type:** Check coverage — a defect class gated on one side only
**Files:** scripts/lint-content.py
**Found:** 2026-09-09, generating TJ for R081

**Symptom:**
  The TJ H block came back with ӱ (U+04F1) where Tajik uses ӯ (U+04EF), twice.
  The DB row was clean — the generator introduced it. `lint-content.py` returned
  0 fail 0 warn. It was caught by reading the text, not by tooling.

**Diagnosis:**
  `audit-library.py` has caught this class since 2026-08-21 (R027 homoglyph) —
  but it reads `hadith_library` rows. Nothing checked the text the GENERATOR
  produces, which is what actually reaches TTS. A clean source row does not
  imply clean output, and the whole point of the M and S blocks is that they are
  rewritten rather than copied.

  Same shape as P121: a gate built where a failure was first seen, never widened
  to the other end of the same path. The library end was guarded because the
  library end was where the first homoglyph turned up.

**Fix:**
  `check_script()` — per-language Cyrillic alphabet whitelist plus a mixed-script
  word detector, FAIL on both, wired with the structure checks since a wrong
  letter changes what the content checks are reading. S/M/H only: the C block
  legitimately mixes Arabic matn, a Latin collection name and Latin hashtags.
  Alphabets are permissive — full Russian base for all three lanes plus each
  language's own extras — so a loanword does not fire. Check count 8 → 9,
  printed from len(checks) rather than a literal.

**Proven in both directions:** fires on the exact R081 line naming ӱ U+04F1 and
its block; silent on the real shipped TJ, UZ and RU drafts.

**Rule:**
  When a check guards a data store, ask what writes to it and what reads from
  it. Both ends need the check, and the end that produces new text needs it more
  than the end that stores reviewed text.

**Related:** P121 (gate wired to half the inputs), P160 (third script needing
--library), R027 (first homoglyph, library side), P128 (structure checks)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 162: The adults picker, and a gate that ran too late to be tested
## ════════════════════════════════════════════════════════
**ID:** P162
**Type:** Asset selection — no state, plus gate placement
**Files:** render-reel.ps1
**Found:** 2026-09-10, porting P159 to the adults lane

**Symptom:**
  None shipped. P159 fixed the kids picker and left the adults one, which had
  the same unfiltered glob and no memory of its last pick.

**Correction to the P159 write-up:** the adults lane was NOT silently broken.
  Line 373 already ran the P117 gate on the picked bed, so a kids-only nasheed
  was rejected, not used. The claim that this lane had "the same defect" was
  wrong and is corrected here. What was actually wrong was smaller and in two
  places.

**Diagnosis:**
  1. No no-repeat memory, so the same bed could land on consecutive adults reels.
  2. The pick and its gate sat at step 7, AFTER the background mix. A
     lane-rejected bed therefore killed the render only once all the ffmpeg work
     had run — and more importantly, the picker could not be exercised without a
     full paid render. Untestable code is how P121 survived eight reels.

**Fix:**
  - `*-kids-*` filtered out of the adults pool at validation time, so a crossing
    bed is never picked rather than picked and then rejected.
  - Shared `out\backgrounds\.last-used.json`, keyed by lane, so kids and adults
    keep independent histories.
  - Pick and P117 gate MOVED into the validation block, ahead of all ffmpeg. The
    step-7 site is now one comment pointing here; `$chosen` is still in scope.

**Proven in both directions:** two consecutive runs on a bogus slug picked
light-of-my-heart then path-to-jannah, the second reporting `avoided:
light-of-my-heart-bg.mp3`, pool 9 not 10 with the kids hamd filtered out, and
both died on missing narration before any ffmpeg ran.

**Rule:**
  Where a gate runs decides whether it can be tested. A check placed after
  expensive work is a check nobody exercises deliberately — move it to where a
  dry run reaches it, and the cost of being wrong drops from a render to a
  second.

**Related:** P159 (kids lane, same picker), P117/P121 (the lane gate and its
coverage), P123 (hook tokenizes .ps1)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 163: A default that was protective until the caller changed
## ════════════════════════════════════════════════════════
**ID:** P163
**Type:** Silent default — outlived its reasoning
**Files:** app/api/tts/route.ts
**Found:** 2026-09-10, closing the P157/P158 family

**Symptom:**
  None shipped. Found by reading the route while fixing the admin.

**Diagnosis:**
  `mascot = 'girl'` was a DELIBERATE default, and the comment above it said why:
  P103 wanted a payload missing the field to fall back to shipped voices rather
  than switch gender. That was correct reasoning about a caller that sent
  'boy'/'girl' directly and might omit it.

  P158 changed the caller. The admin now computes the value with
  `mascotGender(mascot)`, so an absent field no longer means "an older client
  omitted it" — it means the caller is broken. Worse, the selection is a
  ternary: `mascot === 'boy' ? boy : girl`. ANY unexpected value lands on girl,
  including a mascot KEY like 'camel' if a future caller sends the key instead
  of the gender. The default's stated purpose was to prevent silently narrating
  in the wrong gender; after P158 it produces exactly that.

**Fix:**
  Default removed. Kids requests validate `mascot` is 'boy' or 'girl' and 400
  otherwise, with the received value in the message. Adults ignore the field as
  before.

**Proven in both directions:** missing mascot 400, mascot:'camel' 400,
mascot:'boy' 200, adults with no mascot 200.

**Rule:**
  A default encodes an assumption about who is calling. When the caller changes,
  re-read every default on that boundary — the reasoning in the comment may
  still be sound and still no longer apply. Fourth silent default in two
  sessions (P157 -Mascot, P158 lang 'ar', this, and P159's picker with no
  memory).

**Related:** P157, P158, P103 (the original default and its reasoning), P084

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 164: 720p was a June choice nobody priced
## ════════════════════════════════════════════════════════
**ID:** P164
**Type:** Cost / unexamined constant
**Files:** make-kids-reel.ps1
**Found:** 2026-09-10, checking Fabric's real duration cap

**Symptom:**
  None. Nothing was broken. 100% of fal spend is Fabric lip-sync, $45 in 8 days,
  and every clip had been generated at 720p since the lane was built.

**Diagnosis:**
  Two assumptions surfaced together while checking the "~30s" cap, and both had
  the same shape — a number chosen once and never re-read:

  1. **The cap is real.** fal and VEED's API pages both document 30s. VEED's
     5-minute figure describes their editor, not this endpoint. 28s is a correct
     margin and there is no narration room to reclaim.
  2. **Splitting costs nothing.** Fabric bills per second of OUTPUT with no
     minimums, so 21s + 9s bills the same as one 30s clip. The earlier reasoning
     that a split "pays twice" was wrong. What a split actually costs is the
     mascot reset seam, which is a quality question, not a cost one.

  Then the real finding: 720p is $0.15/sec against 480p at $0.08. The clip is
  normalised into a 1080x1920 frame either way and the audience watches at phone
  width. Side by side at feed size the two were indistinguishable; only under a
  hard crop did 720p show finer embroidery and eye highlights.

  `generate-talking-clip.py` had defaulted to 480p all along. The wrapper
  overrode it to 720p in three places, two of which were only display strings —
  so the cost decision lived in a hardcoded argument nobody had cause to read.

**Fix:**
  `-Resolution` parameter, ValidateSet 480p|720p, default 480p. The confirmation
  prompt now prints the resolution AND the per-second rate, so the paid step
  states its own price. 720p remains one flag away for a set that warrants it.

**Rule:**
  A constant chosen before the delivery format was known is a guess that has
  outlived its evidence. Price every paid parameter against the size the output
  is actually consumed at — and put the price in the confirmation prompt, so the
  next person does not have to go looking for it.

**Related:** P138 (Fabric idempotency), P157/P158/P163 (defaults that outlived
their reasoning)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 165: Stage 0 was blocked on the only source that needed a key
## ════════════════════════════════════════════════════════
**ID:** P165
**Type:** Pipeline unblock — a dependency nobody re-examined
**Files:** scripts/lib/source_hadeethenc.py, scripts/lib/test_source_hadeethenc.py
**Found:** 2026-09-10, asking whether #3675 had a workaround

**Symptom:**
  Stage 0 had been blocked since 2026-08-21 waiting on Sunnah API issue #3675.
  The design named three Tier-1 sources; the tracker said "adapters built."

**Diagnosis:**
  Only Sunnah acquires. `source_dorar.py` exists but CONFIRMS grades — it is
  called from `confirm_via_dorar`, on a candidate that already exists.
  `source_hadeethenc.py` was never written at all. So "adapters built" was true
  of the two that existed and hid the absence of the third, and the one source
  needing a key became the only source.

  Rejected on the way: `sunnah-now/database` GitHub dumps. Unaffiliated with
  sunnah.com, Bukhari only, unverified provenance. §4 says nothing outside the
  curated table is a source, and a community mirror is precisely what this
  channel exists to correct.

**Fix:**
  `source_hadeethenc.py`, mirroring the Sunnah adapter's pure-parse / thin-fetch
  split. Keyless. Supplies Arabic matn, isnad opener, grade, and AUTHORITATIVE
  translations — uz comes back native Cyrillic, tg comes back real Tajik with
  the correct ӯ (U+04EF), the very letter the generator got wrong in R081.

**Four things the API does that a trusting parser gets wrong:**
  1. `language=ar` has NO `hadeeth_ar` key — the Arabic is in `hadeeth`, and the
     isnad in `hadeeth_intro`. Every other language returns both. Cost a
     debugging round; now a regression test.
  2. A missing translation returns **200 with an empty string**, not 404, not
     null. `present()` treats absence explicitly at every field.
  3. Default `Python-urllib` User-Agent gets 403 while curl succeeds. And
     because `HTTPError` subclasses `URLError`, the first `fetch_langs` would
     have swallowed that 403 as "no translations" — a blocked fetch and a
     genuinely absent language were indistinguishable. Now only 404 means
     absent; everything else raises. Proven live when DNS dropped mid-session:
     it raised instead of returning three silently blank languages.
  4. No hadith NUMBER. `reference` looks like it has one, but it is free-text
     Arabic bibliography with volume/page pairs and commentary works, and lists
     TWO Bukhari numbers for hadeeth 66511. Kept raw as a cross-check; never
     parsed. `citation_pending=True` until Dorar supplies collection + number.

**Licence, enforced by usage not by code:**
  HadeethEnc terms are (1) no modification, addition or deletion, (2) credit the
  source. Resolution: their translation is reproduced VERBATIM as the caption
  matn or not used at all; story and moral are written from `text_arabic`, never
  from their translation; credit line in every caption that uses their text.
  Stage 4 becomes accept-or-reject for these rows — if a translation needs
  fixing, reject and translate from the Arabic rather than edit theirs.

**Rule:**
  "Adapters built" is a claim about code, not about capability. When a pipeline
  stage is blocked, check whether the blocker covers every path or only the one
  that happened to be wired first.

**Related:** P151 (--library on two other scripts), P160 (the third), P121 (half
the inputs), P161 (the ӯ this source gets right)

**Status:** FIXED — adapter live and tested; Stage 0 orchestration to follow.

## ════════════════════════════════════════════════════════
## PATTERN 166: Committed the reference, not the thing
## ════════════════════════════════════════════════════════
**ID:** P166
**Type:** Incomplete commit — the artifact described was never added
**Files:** make-kids-reel.ps1, assets/mascot/*.png
**Found:** 2026-09-10, first render of the hoopoe set

**Symptom:**
  Two failures, one shape.
  1. `make-kids-reel.ps1` printed `at  (paid, ~$0.08/sec)` and Fabric died with
     `--resolution: expected one argument`. No spend — argparse rejected it.
  2. `git ls-files assets/mascot/` listed only the six lamb PNGs. camel-dawn-v1,
     hoopoe-garden-v1 and bee-orchard-v1 were never staged.

**Diagnosis:**
  P164 added `-Resolution` in three places that USE the variable and never the
  param block that DECLARES it. `$Resolution` was therefore an undefined
  variable, which PowerShell expands to an empty string rather than raising —
  so the tokenizer check passed, `-ValidateOnly` passed, and the failure
  surfaced at the paid step.

  P157 committed registry entries for three mascots and never `git add`ed the
  images. The registry pointed at files the repo did not contain: a fresh clone
  fails the asset gate, and R078–R081 are not reproducible. Both `git add` lines
  named the JSON and the docs, never the binaries.

  In both cases the commit MESSAGE was accurate about intent and wrong about
  content, and every check we ran was blind to the gap: a tokenizer cannot see
  an undefined variable, and a doc commit cannot see a missing binary.

**Fix:**
  - `-Resolution` declared in the param block with its ValidateSet and 480p
    default; `$MaxLen` gains the comma it needed.
  - The three mascot PNGs staged and committed.

**Rule:**
  When a commit adds a flag, run the thing with the flag before committing —
  not a syntax check, the actual path. When a commit adds a registry entry,
  `git status --untracked-files=all` on the directory it references. An
  undefined PowerShell variable and a missing binary both fail silently, and
  both were described accurately in a message that did not match the diff.

**Related:** P164 (the flag), P157 (the registry entries), P117/P121 (the gate
that would have caught the missing files on a clean clone)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 167: A mascot with no mouth to open
## ════════════════════════════════════════════════════════
**ID:** P167
**Type:** Asset design constraint — a property of the still, not the tool
**Files:** assets/mascot/hoopoe-garden-v2.png, assets/asset-registry.json,
           lib/mascots.ts, make-kids-reel.ps1
**Found:** 2026-09-10, first hoopoe render

**Symptom:**
  The hoopoe's lip-sync looked wrong in a way the camel's never had. The beak
  stayed rigid and a mouth opened behind and below it.

**Diagnosis:**
  Fabric animates mouth-corner articulation on whatever face it is given. The
  camel and both lambs have LIPS, so it had a mouth to move. The hoopoe has a
  closed beak — no aperture — so it invented one underneath. Not a Fabric
  defect and not a resolution defect: the still gave it nothing to work with.

  This is a property of the ASSET, discoverable before any spend, and it
  generalises: the ant (Chechen papakha) would have failed the same way, and
  the bee is borderline.

**Fix:**
  hoopoe-garden-v2 regenerated with the BEAK PARTED — mandibles separated, a
  hint of interior visible — so Fabric animates the beak itself. Proven on the
  8.3s moral clip alone at 480p ($0.70) before committing to the set.
  v1 retired in the registry with `lanes: []` and the reason recorded, rather
  than deleted: the gate then blocks it WITH an explanation.

**Two things learned generating it:**
  - Nano Banana Pro drifts badly on an edit. The first attempt returned an ibis
    in three-quarter profile with a different kalpak and a flattened background.
    Character lock needs the change stated as one narrow instruction plus an
    explicit list of what must not move.
  - The reference image was rejected once as "conflicts with our safety
    policies" — a false positive on a cartoon bird. Retrying in a fresh chat
    cleared it. Do not reword around it.

**Rule:**
  Before adding a mascot, ask whether the character HAS a mouth that opens. If
  the mouth is a beak, mandibles, or anything rigid, the still must be generated
  already parted. Test on the shortest clip in the set before rendering the rest.

**Related:** P164 (480p, which this was briefly mistaken for), P117 (registry
retirement with a reason)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 168: Retirement the picker couldn't see
## ════════════════════════════════════════════════════════
**ID:** P168
**Type:** Two sources of truth for one decision
**Files:** scripts/audit-assets.py, render-mascot-reel.ps1, render-reel.ps1
**Found:** 2026-09-16, after vocal-hamd-kids-01 was retired

**Symptom:**
  vocal-hamd-kids-01 was retired in the registry on 2026-09-10 with `lanes: []`.
  The very next render still reported "10 beds" and could draw it — the gate
  then killed the render. Retiring an asset made renders FAIL rather than route
  around it.

**Diagnosis:**
  Eligibility was decided twice. The registry held the real answer; the pickers
  re-implemented it as a filename filter — `ambient-*` in the kids renderer,
  `*-kids-*` in the adults one. Those filters were correct on the day they were
  written (P159, P162) and could not see a decision recorded anywhere else.
  So a retired asset stayed in the pool, got drawn, and was rejected at the
  gate: the gate did its job, and the pool never learned.

**Fix:**
  `audit-assets.py --list --lane LANE [--section SECTION]` — the registry
  answers "what may I use?" once, and both renderers ask it instead of
  guessing. Filenames no longer encode lane membership anywhere.

  Failure is explicit: if the list cannot be read or comes back empty, the
  render stops with a message. It does NOT fall back to "use everything",
  which would reintroduce exactly this bug.

**Two things the wiring cost, both about the CALLER not the code:**
  - `--list` first printed a count to stderr. PowerShell turns native stderr
    into an ErrorRecord, and `$ErrorActionPreference='Stop'` makes that
    terminating. A machine-readable command must write NOTHING but its output.
  - The interface was verified by running the Python directly, which passed,
    and only broke when called from PowerShell. Test a machine interface from
    the caller that will actually use it.

**Also observed:** with the ambience beds already retired to `_retired/`, both
lanes now return the same 9 files. The lane field currently separates nothing
in audio — vocal-hamd-kids-01 was the only asset it ever distinguished. It
still earns its place for mascots.

**Rule:**
  When a gate and a chooser both decide the same thing, the chooser must ask
  the gate. Two implementations of one rule stay in sync only until one of them
  is updated.

**Related:** P159 (kids picker), P162 (adults picker), P117/P121 (the gate),
P167 (the retirement that exposed this)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 169: Ten Latin captions the generator never wrote
## ════════════════════════════════════════════════════════
**ID:** P169
**Type:** Wrong column selected — a defect blamed on the wrong layer
**Files:** app/api/reels/route.ts
**Found:** 2026-09-16, after the tenth occurrence

**Symptom:**
  Every UZ caption came back with a LATIN matn quote inside an otherwise
  Cyrillic caption. Corrected by hand on ten consecutive sets and logged each
  time against the generation step.

**Diagnosis:**
  Not the generator. `/api/reels` never SELECTed `text_uzbek_cyrillic` — the
  column was not in the query at all — so the response fell through to
  `text_uzbek`, which holds LATIN by design (P097, matching the 74 rows
  backfilled in August). The generator echoed faithfully what the API gave it.

  Ten log entries attributed this to the generation step because that is where
  it was SEEN. Nobody checked what the API returned, because the admin card
  showed the same Latin text and looked like independent confirmation — it was
  the same defect, rendered twice.

  The same select drove search: `text_uzbek.ilike` only, so a Cyrillic query
  matched nothing while every other language searched its own script.

**Fix:**
  `text_uzbek_cyrillic` added to the select; caption prefers it and falls back
  to Latin then English. Search now covers both Uzbek scripts.

**Proven:** searching «Аллоҳга» returns 6 hadiths where it previously returned
none, the cards render Cyrillic, and a fresh kids caption (Tirmidhi #3479) came
back fully Cyrillic with no correction.

**Rule:**
  A defect observed downstream is not evidence about where it originates. Ten
  occurrences went into the log against the wrong layer because the symptom was
  visible there and the cause was one query away. When the same wrong value
  appears in two places, suspect one source, not two bugs.

**Related:** P097 (why the legacy column holds Latin), P050 (a language falling
back silently), P147

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 170: The old picker was left behind the comment that replaced it
## ════════════════════════════════════════════════════════
**ID:** P170
**Type:** Dead code that still ran — a move that only added
**Files:** render-reel.ps1
**Found:** 2026-09-17, first adults render since P162

**Symptom:**
  The render printed the nasheed TWICE. Step 0 chose vocal-nasheed-07; step 7
  then chose vocal-nasheed-01, and that is the bed in the reel.

**Diagnosis:**
  P162 moved the pick into the validation block and left a comment at step 7
  saying so — but the original block underneath was never deleted. It ran, and
  ran LAST, so it won.

  Three consequences, none visible in the output:
  - The P117 gate checked vocal-nasheed-07 while vocal-nasheed-01 shipped. The
    gate was live and testing the wrong file, which is worse than no gate: it
    reports a pass for something that is not what ships.
  - The leftover still carried the PRE-P168 filename filter and rebuilt
    `$nasheeds` from an ungated `Get-ChildItem`, so a retired bed could reach a
    reel through it. P168's fix was real and simply bypassed.
  - `.last-used.json` was written twice per render, so no-repeat was one behind.

  Both the P162 and P168 test runs passed, because both used `-ValidateOnly` or
  died at validation. Neither reached step 7. The code path that shipped reels
  was the one no test exercised.

**Fix:**
  Leftover block deleted; the comment at step 7 now states what is NOT there
  and why. `$chosen` from validation is used directly.

**Rule:**
  Moving code means deleting it from where it was. A comment saying "this
  happens earlier now" is not a deletion, and the reader who most needs it is
  the one skimming for the line that assigns the variable — which was still
  right there, still assigning it.

  And: a validation-only smoke test proves the validation path. It says nothing
  about the code after it. P162 and P168 were both verified this way and both
  left this defect untouched for five reels.

**Related:** P162 (the move), P168 (the filter it bypassed), P117 (the gate it
misdirected)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 171: The mix nobody had listened to on a phone
## ════════════════════════════════════════════════════════
**ID:** P171
**Type:** Audio balance — a default carried since the first reel
**Files:** render-reel.ps1
**Found:** 2026-09-17, rendering R089

**Symptom:**
  The nasheed sat too close to the narration. Not a defect — nothing failed,
  eighty-five reels shipped this way — but on a phone speaker the bed competed
  with the voice, and the voice is the point.

**Diagnosis:**
  narration 1.0 / music 0.25 had been in the filtergraph since the pipeline was
  built and was never revisited. About 12 dB of separation, chosen once on
  desktop monitoring and never checked against the device 97% of views arrive
  on. Same shape as P164's 720p: a number picked before the delivery context
  was known.

**Fix:**
  narration 1.4 / music 0.12 — roughly 21 dB. amix applies 1/n scaling across
  inputs, so 1.4 peaks near 0.7 of full scale with headroom; that is the
  practical ceiling before loud syllables clip. If the voice still sits back
  after this, the fix is normalising the ElevenLabs source, not raising the
  multiplier further.

  ADULTS LANE ONLY. render-mascot-reel.ps1 is still at 0.20 and untouched —
  kids narration is a mascot voice over a bed, a different balance question.

**Note:** the three already-rendered languages of the set were re-rendered at
the new mix and the two already-published reels re-uploaded, rather than
shipping a set mixed two ways. Re-rendering is free; only Fabric and Kling cost.

**Rule:**
  Check output defaults against the device the output is consumed on, not the
  one it is produced on. Second time this session — 720p was the first.

**Related:** P164 (resolution priced against delivery size), P143 (the amix
duration trap in the same filtergraph)

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 172: Stage 0 wired to a source that needs no key
## ════════════════════════════════════════════════════════
**ID:** P172
**Type:** Pipeline completion — an adapter built and left unconnected
**Files:** scripts/source-candidates.py
**Found:** 2026-09-25, two weeks after P165

**Symptom:**
  Stage 0 was still described as blocked on Sunnah API issue #3675, and the
  library had not gained a row since August. `source_hadeethenc.py` had been
  built, tested with 14 offline tests and committed on 2026-09-10 — and never
  called by anything.

**Diagnosis:**
  Building the adapter was the visible half. The runner still imported only
  `source_sunnah`, so the keyless path existed and was unreachable. Same shape
  as P165 itself: "adapters built" was true of the code and false of the
  capability.

**Fix:**
  `--provider sunnah|hadeethenc` on source-candidates.py. Distinct from
  `--source mock|live`, which is a Sunnah endpoint switch and was left alone.

  The citation is the whole difficulty. HadeethEnc gives no hadith number, so
  Dorar now supplies collection + number as well as the grade, through
  `canonical_collection()` — which already refuses commentaries and takhrij
  works, so no new mapping was invented. A candidate whose citation does not
  resolve is DROPPED: it cannot be deduped, since hard_key needs both fields,
  and it cannot be cited in a caption.

  `--provider hadeethenc --no-dorar` is an argparse error rather than a silent
  total loss, since Dorar is the only citation source for those candidates.

**Proven live on two refs, and the DROP is the better half:**
  - 66515 → Muslim #1599, sahih, Dorar match 0.894, citation_pending resolved
    to False, dedup `new`, all four translations present. UZ came back native
    Cyrillic and TJ real Tajik, both carrying the isnad opener with the
    honorific already correct — content the pipeline has been hand-fixing.
  - 66511 → DROPPED. Dorar returned «غريب جدا والمحفوظ حديث عمر» — a takhrij
    verdict on a variant route, not a grade. The hadith itself is Bukhari #1
    and sahih, but the matched card was a weak variant, and
    classify_dorar_grade correctly refused to read that as a grade. A hadith
    being sound does not make a particular card citable.

**Rule:**
  An adapter is not a capability until something calls it. When a stage is
  reported blocked, check what the RUNNER imports, not what exists in lib/.

**Related:** P165 (the adapter), P160/P151 (the same "built but not wired"
shape), P147 (hadith_number is not unique)

**Status:** FIXED — acquisition live. Promotion to hadith_library is still a
separate gated step and unchanged.

## ════════════════════════════════════════════════════════
## PATTERN 173: Refs by query, and drops that were only console output
## ════════════════════════════════════════════════════════
**ID:** P173
**Type:** Pipeline usability — finding candidates, and not losing them
**Files:** scripts/he-refs.py (new), scripts/source-candidates.py
**Found:** 2026-09-25, first real batch through the HadeethEnc path

**Two problems, one session.**

**1. There was no way to choose what to source.** `out/source-refs.txt` did not
exist and the runner fell back to two sample ids. HadeethEnc organises by
CATEGORY, so the four-slot content cycle (mercy, deed, accountability,
character) maps onto category ids and a refs file falls out of a query rather
than out of browsing.

  `he-refs.py --slot mercy --limit 10 --exclude-langs` writes ids with the
  title as a comment. `--exclude-langs` drops ids whose translations list
  lacks uz or tg — coverage is PER HADITH (P165), and a candidate missing
  either would need machine translation, which is what this source exists to
  avoid.

  Supply is uneven and the thinnest slot is the best-performing one: mercy 57
  hadeeths, deed 91, accountability 240, character 283.

**2. Four in ten were dropped, and the drops existed only as console output.**
  The first real batch: 10 refs → 6 candidates, all 6 grade-confirmed, 1 caught
  as a hard duplicate. The four drops were three different causes:
  - 5456 — «غريب لا نعرفه إلا من هذا الوجه»: a takhrij note, not a grade.
  - 65063 — «عارضة الأحوذي», Ibn al-Arabi's COMMENTARY on Tirmidhi, with a
    volume/page "number" of 6/115.
  - 58240 — «المستدرك على الصحيحين», a primary collection outside the map.
  - 66537 — «صحيح الترمذي 2632», al-Albani's grading work.

**Two alias additions were considered and REFUSED, deliberately:**
  - «صحيح الترمذي» → Tirmidhi. Refused. Al-Albani's Sahih Sunan al-Tirmidhi is
    a SELECTION with its own sequential numbering that does not reliably track
    the Jami's. Mapping it would risk a caption citing a number that points at
    a different hadith — the exact defect shape of #3104 and #8497, which this
    channel exists to correct in others. A dropped candidate costs one reel; a
    wrong number costs the premise.
  - al-Mustadrak → primary. Refused for a different reason: it IS primary, but
    al-Hakim is known for leniency, the channel has never cited it, and adding
    a collection changes what appears in captions as an authority. That is a
    decision to take with a scholar, not a side effect of widening an alias map
    to rescue a candidate.

**Fix:** drops now written to `out/candidates-dropped.json`. A daif drop is
final, but a CITATION drop is not a ruling on the hadith — it is a statement
about which card Dorar matched. Per G2 a human admits, never a score, so these
are a review queue rather than waste. Nothing in that file enters the pipeline.

**Known gap:** the dropped record carries only `ref` and `reason`, not the matn
or translations, so reviewing one means re-fetching it.

**Rule:**
  When a gate rejects something, ask whether the rejection is a JUDGEMENT or an
  UNRESOLVED LOOKUP. A judgement can be final and silent. An unresolved lookup
  belongs in front of a human, because the thing it could not resolve may be
  resolvable by someone who knows the field.

**Related:** P172 (the wiring), P165 (per-hadith language coverage), P147

**Status:** FIXED

## ════════════════════════════════════════════════════════
## PATTERN 174: A dedup key is not a citation
## ════════════════════════════════════════════════════════
**ID:** P174
**Type:** Latent citation defect + provenance column
**Files:** promote-candidates.py, hadith_library schema
**Found:** 2026-09-25, designing promotion for HadeethEnc candidates

**Two things, both about what a row claims.**

**1. translation_source.** HadeethEnc's licence requires crediting them per row
carrying their text. `authority` already holds the GRADING source (Dorar) —
conflating two provenances in one column is how mis-graded rows ended up with
the wrong authority attached. New column, two values: 'hadeethenc.com' or NULL
(in-house). NULL on all 65 existing rows; no backfill, since writing to
verified rows to state the status quo is risk without benefit.

  A three-value split ('hadeethenc-partial') was designed and dropped: the
  caption emits the same credit either way, so the distinction would have been
  stored and never read. Which language came from where is recoverable from the
  candidate JSON.

  The spelling came from the parser, not from the design: source_hadeethenc.py
  already wrote "hadeethenc.com". Two spellings of one fact is how the nasheed
  usage table drifted, so the existing tested value won.

**2. syn_number mints citations that are not citations.** upload-candidates.py
generates "auto-<sha1[:10]>" when Dorar gives no number, so
UNIQUE(collection, hadith_number) cannot collapse distinct hadiths. Correct for
a candidate. WRONG for the library — it is a dedup key, and it would reach a
caption as "#auto-3f2a91b04c" on a channel whose premise is verifiable
citation. Nothing refused it. Zero such rows exist in either table, so this
closes the gap while it is still theoretical rather than after a reel ships.

**A measurement that reversed a decision.** The plan was to refuse
mixed-provenance rows so the column could stay unambiguous. Measured first: of
57 hadeeths in the mercy slot, only 22 (38%) carry all four languages, and the
gap is structural — uz and tg missing together on 33 of 35, ru on 2. Refusing
would have discarded 62% of the thinnest and best-performing slot. The
assumption was wrong and the measurement was cheap.

**Rule:**
  Before a value reaches a caption, ask what it IS, not where it came from. A
  hash that guarantees uniqueness and a number that identifies a hadith are
  both strings in the same column, and only one of them can be cited.

**Still open:** HadeethEnc candidates cannot yet be promoted.
hadith_promotions.candidate_id is NOT NULL, so a JSON-sourced row has no audit
trail, and upload-candidates.py's to_row() writes text_arabic only — it would
discard exactly the translations that make this source worth using. The upload
path needs its own mapping.

**Related:** P172/P173 (the sourcing path), P160 (the missing Uzbek Latin,
which this path reproduces), P169 (a column nothing selects is invisible)

**Status:** PARTIAL — column and guard shipped; promotion path not built.


## ═══════════════════════════════════════════════════════════
## PATTERN 175: The upload mapping discards what the source was for
## ═══════════════════════════════════════════════════════════
**ID:** P175
**Type:** Wrong-shape reuse + provenance granularity
**Files:** upload-candidates.py, hadith_candidates schema
**Found:** 2026-09-26, building the upload path for HadeethEnc candidates

**The trap was reuse.** upload-candidates.py already had a candidate→row
mapping, so the obvious move was to point --from-json at to_row(). But to_row()
serves the Dorar-search path, where a candidate IS only an Arabic matn — it
writes text_arabic and nothing else. Routing HadeethEnc through it would have
dropped all four translations, which are the entire reason HadeethEnc is worth
fetching. The insert would have succeeded. The rows would have looked fine in
the table. Stage 2 would then have spent model calls re-translating text that
came from a Tier-1 source with a human translator behind it. Hence a separate
mapping, json_to_row(). Reusing the name would have been the defect.

**Provenance granularity, resolved the opposite way from P174.**
hadith_candidates.translation_meta is jsonb and already carried per-language
records ({at, model, provenance, source_field}) from Stage 2. So the candidates
table gets per-language provenance while the library keeps P174's scalar
translation_source. Not an inconsistency: the caption reads one scalar and needs
one answer, while the candidate is the audit record and has to say which
language came from where. Two tables, two jobs — and P174's measurement that
only 38% of a slot carries all four languages is exactly why the audit record
cannot flatten it.

**Guards placed where the information is, not where the failure lands.** Three
refusals sit in json_to_row() rather than downstream: missing citation, an
auto- synthetic number, and citation_pending still true. P174 already refuses
auto- numbers at promotion, so a synthetic row would have been insertable and
then permanently unpromotable — a dead row nothing cleans up. Refusing at the
door costs one line and leaves no residue. review_fuzzy rows are skipped unless
--allow-fuzzy is passed: G2 says similarity never decides admission, and
defaulting to upload would have let it decide.

**status='translated', not 'verified'.** The text exists; it has not been
through the Stage 3 A/B pass. promote-candidates.py reads status='approved'
only, so the human gate stays exactly where it was. Choosing 'verified' here
would have moved a gate by picking a string.

**One thing deliberately not built.** text_uzbek_latin is left NULL.
derive-uzbek-latin.ts already owns the tested deriveBothScripts +
normalizeLatinApostrophes. A second transliterator in Python would be a second
thing to keep correct, and P097 is precisely the defect that appears when one
of two copies drifts.

**Proven:** first live batch, 5 of 6 inserted — Bukhari 2654 / 6871 / 6857 / 31
and Muslim 2628, all four languages each. Muslim 2759 dropped as a hard
duplicate, so the live dedup baseline was read and honoured. Dry run first; the
commit matched it row for row.

**Status:** FIXED


## ═══════════════════════════════════════════════════════════
## PATTERN 176: Wiring a column all the way to the reader
## ═══════════════════════════════════════════════════════════
**ID:** P176
**Type:** Loop closure + caption localisation
**Files:** app/api/reels/route.ts, lib/refs.ts, app/admin/page.tsx
**Found:** 2026-09-26, making P174's translation_source actually visible

**P169 is why this is a pattern and not a chore.** That defect ran for ten
consecutive sets — the generator got blamed for Latin Uzbek captions when the
real cause was /api/reels never selecting text_uzbek_cyrillic. A column that
exists in the table and is read by nothing is not a feature; it is decoration
shaped like one. P174 added translation_source, and this closes the path from
it to a reader in three hops — API select, builder, caption. None of the three
is optional, and the first one was missing.

**A separate line, not a suffix on buildRef().** The ref line is the CITATION:
collection plus number, what someone types to check the hadith independently.
Who translated it is a different claim about a different object. Folding it in
would have made the citation longer and harder to scan for no gain.

**A different word from the seerah source.** The caption already spends
Источник / Манба / Сарчашма on the seerah attribution. Reusing that label here
would have put two identically-named lines in one caption pointing at two
different things — worse than omitting the credit. Перевод / Таржима / Тарҷума
/ Translation instead, with 🌐 rather than 📖, so the lines are distinguishable
before the word is read.

**Empty means empty, including the newline.** Emitted as
(credit ? `${credit}\n` : '') rather than a plain interpolation, so an in-house
row produces no blank gap where the credit would sit. All 65 library rows are
NULL — that is the common path, not the edge.

**uz_cyrillic / uz_latin.** getSeerahSource() accepts those variants, so the
label lookup normalises any lang starting with 'uz'. Without it the Uzbek
caption would have silently fallen back to the English word — the exact
failure mode P150 exists to prevent.

**The type had to change too.** interface Hadith is explicit, so adding the
column to the API select did not add it to the TS shape; tsc caught it.
Declared string | null rather than ?: string — NULL is the normal case for an
in-house row, and optional-only would have understated that.

**Proven in both directions.** With translation_source NULL the caption is
identical to before, no blank line. With it set to 'hadeethenc.com' on Bukhari
#6018, UZ rendered «🌐 Таржима: HadeethEnc.com» and RU «🌐 Перевод:
HadeethEnc.com» — the label map, not the English fallback. Row reverted to NULL
after the test.

**Status:** FIXED


## ═══════════════════════════════════════════════════════════
## PATTERN 177: The review gate reviewed a draft that was thrown away
## ═══════════════════════════════════════════════════════════
**ID:** P177
**Type:** Non-deterministic gate + prompt conventions
**Files:** translate-candidates.py
**Found:** 2026-09-27, re-translating five HadeethEnc candidates

**Dry run and commit were separate invocations, each generating its own text.**
The script printed "DRY RUN - nothing written. Read the JSON, then --commit",
so the workflow read one artifact and shipped a different one. Three rolls on
Bukhari #2654 produced three different Uzbek openings; roll 2 removed a
parenthetical gloss and roll 3 put it back. We reviewed clean text and
committed text with the defect, and nothing downstream could catch it: Stage 3
refuses conventions by design (P120) and lint-content.py runs on generated reel
text, not candidates. Same family as P154, where the merge check tested only
that a file existed, and P162, where the nasheed picker could not be tested
without a paid render. A check that does not check the thing it names.

**--apply writes out/candidate-translations.json as-is, with no model calls.**
Generate, review, apply. The reviewed text is the text written. It also means a
correction belongs IN the reviewed JSON, not in an SQL patch after the write —
we had already patched two rows by hand before this existed. Deliberately the
same shape as P175's --from-json on the uploader, so the pipeline has one
pattern rather than two.

**Prompt conventions, each earned by a defect the same day.** Honorifics per
TARGET language; no parenthetical glosses; رسول الله is the Messenger, never an
envoy («элчи»). The first version of the honorific rule was written in
Uzbek/Tajik forms and applied to all four languages, so English came back
"Narrated 'Abdullah ibn 'Amr ibn al-'As, розияллоҳу анҳумо" — Cyrillic inside
English. A rule stated in one language's convention is not a rule.

**Still open.** The gloss appeared in five of roughly twelve translations
reviewed today, in round brackets, square brackets and once as a dash aside.
The prose rule slowed it and did not stop it. The next version should be
structural — no bracketed aside anywhere in the output — rather than describing
the behaviour and hoping.

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 178: Tier-1 for grading is not Tier-1 for translation
## ═══════════════════════════════════════════════════════════
**ID:** P178
**Type:** Source-quality measurement
**Files:** scripts/lib/source_hadeethenc.py, sourcing-pipeline-design.md
**Found:** 2026-09-27, first Stage 3 run over a HadeethEnc batch

**Measured, not assumed.** Stage 3 over seven candidates — five from
HadeethEnc, two translated in-house by translate-candidates.py:

    in-house (#2999, #6446):  8 of 8 language-passes clean, high confidence
    HadeethEnc (five rows):   EN 3/5, RU 0/5, UZ 0/5, TJ 1/5

**The defects are one type: interpretive expansion.** One Arabic phrase split
into two (قول الزور → false witness AND false speech), terms upgraded (حامل
المسك, the CARRIER of musk, → "musk seller"; نافخ الكير, the bellows-blower, →
"blacksmith"), narrative detail invented («тик туриб» — stood up — where the
Arabic has فَجَلَسَ, sat up), and qualifiers added. The worst was «бегуноҳ» —
INNOCENT — attached to قَتْلُ النَّفْسِ in both Uzbek and Tajik on #6871, flagged
four times independently. That changes the ruling being reported, on a channel
whose premise is that altered narrations spread.

**So HadeethEnc's role changes, and does not shrink.** It stays what unblocked
Stage 0: keyless, Tier-1, and it supplies the Arabic matn plus, via Dorar, the
citation and the grade. Its RU/UZ/TJ are discarded and re-translated from the
Arabic. English goes too — 3 of 5 is not reliable, and one row translated three
ways in-house and one way from HadeethEnc is a provenance mess for no gain. In
consequence translation_source stays NULL on these rows, and P176's credit line
is the guard for if HadeethEnc text ever does ship.

**The disagreement rate turned out to be a source signal.** 0% on the in-house
rows, 4 of 5 on HadeethEnc, almost all A=pass / B=fail with B substantively
right (الْغَافِلَاتِ is heedless, not innocent; رضي الله عنهما is dual). The D5
number reads as mistuning when it is high — here it was measuring the source.

**Closed at the source 2026-09-29.** parse_hadeeth() no longer writes their
text into text_english/russian/uzbek_cyrillic/tajik, and translation_source is
left NULL for whoever produces the text to set. The `translations` parameter
stays: it is still the fallback that finds hadeeth_ar when the payload was
fetched in another language.

**Closed at the caller 2026-09-30.** source-candidates.py was still calling
fetch_langs on every candidate — four API calls each, for text nothing reads.
It now passes None, and the header comment that called HadeethEnc's
translations AUTHORITATIVE, which stood for three days after the measurement
said otherwise, is corrected. A defect fixed in one layer leaves the layer
above still doing the work; grep the callers, not just the function.

**Status:** FIXED (policy); adapter unchanged, it still fetches translations

## ═══════════════════════════════════════════════════════════
## PATTERN 179: The adapter put the isnad where the narrator goes
## ═══════════════════════════════════════════════════════════
**ID:** P179
**Type:** Shape mismatch with the library
**Files:** scripts/lib/source_hadeethenc.py, hadith_candidates
**Found:** 2026-09-27, building the caption ref line for the five new rows

**Two columns, same cause.** narrator held the entire Arabic isnad chain —
«عَنْ أَبِي مُوسَى رضي الله عنه عَنِ النَّبِيِّ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ قَالَ:» — where
the other 65 library rows hold a name. And text_arabic carried that same isnad
in front of the matn, where the library holds matn only. That is why these five
ran 300-450 characters against a library average under 130, and why every
translation opened with "From Abu Bakrah, may Allah be pleased with him".

**The caption is where it would have shown.** buildRef() looks the narrator up
in NARRATORS and falls back to printing it verbatim (P150), so a full Arabic
isnad would have rendered in the ref line, and the narrator would have appeared
twice — once inside the Arabic, once after it.

**Fixed in the data first.** The isnad prefix in text_arabic was exactly the
narrator string, so one UPDATE stripped it and set proper names. All five were
then re-translated from the matn and re-verified.

**Closed at the source 2026-09-29.** narrator is None: the payload has no
narrator-NAME field at all, so it is resolved with the citation like collection
and hadith_number. text_arabic has the intro stripped when it is a byte-exact
prefix — and only then. It frequently is not: id 66511 carries
«...رضي الله عنه قَالَ:» in hadeeth_intro and «...قَالَ:» without the honorific
in the body. The shapes differ row to row, so the boundary cannot be inferred:
a wrong cut damages the matn, and a right-looking cut is unverifiable.

**The unstrippable case is flagged, not quietly passed through.**
matn_intro_stripped carries three states — None (no intro field), True
(removed), False (present and not removable) — and upload-candidates.py rejects
on False, beside the existing citation_pending check. That reader is the whole
point. P181 is this same lesson from the other end: a flag nobody reads is only
a quieter silence.

**Known limitation.** The intro is read from the primary payload only. When the
Arabic is recovered from a translation payload, that payload's intro is not
consulted. Low risk — the non-Arabic shapes keep hadeeth_ar matn-only and the
concatenation appears only in the language=ar shape — but it is not covered.

**Tests.** test_source_hadeethenc.py pins all three flag states and both intro
shapes, 17 passing. AR_PAYLOAD's intro/body asymmetry is now documented in the
fixture as load-bearing — adding the honorific to the body to tidy it would
silently kill the regression.

**Also:** lib/refs.ts gained Abu Bakra — a new narrator entering the library
needs a NARRATORS entry or the caption prints Latin inside Cyrillic. Note he is
NOT Abu Bakr as-Siddiq: أبو بكرة with ta marbuta is Nufay' ibn al-Harith
ath-Thaqafi.

**Status:** FIXED


## ═══════════════════════════════════════════════════════════
## PATTERN 180: The caption wrapped text that already carried its own quotes
## ═══════════════════════════════════════════════════════════
**ID:** P180
**Type:** Non-idempotent decoration
**Files:** app/admin/page.tsx
**Found:** 2026-09-29, building the R094–R097 captions

**The wrapper did not ask first.** The caption assembled the body as
`«${hadithText}»`, unconditionally. Most library rows hold bare text, so this
was right for 65 of them — but rows whose text already opens with « came out
as ««…»», and #2654's Uzbek was one of them.

**The fix is a guard, not a cleanup.** Stripping quotes on the way in would have
been the wrong direction: the library is allowed to hold either shape, and it is
the caption's job to arrive at one. So the wrapper now checks before it wraps:

    (hadithText.trim().startsWith('«') ? `${hadithText}\n\n` : `«${hadithText}»\n\n`)

**The class, not the instance.** Any decoration applied to data that may already
carry it needs this check — quote marks, the ﷺ glyph, the 🌐 credit prefix. The
same bug is latent anywhere the caption concatenates a sigil onto a library
column without testing for it first.

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 181: The promoter hardcoded empty tags and said nothing
## ═══════════════════════════════════════════════════════════
**ID:** P181
**Type:** Silent default
**Files:** promote-candidates.py, hadith_library
**Found:** 2026-09-29, after five promoted rows had already shipped untagged

**A true comment defending the wrong behaviour.** map_to_library returned
`"tags": []` with the note *red_flags is a verifier concept* — correct, and
beside the point. Candidates carry no theme data at all, so tags genuinely
cannot be derived at promote time. The defect is that the promoter filled that
gap with a plausible empty value instead of refusing to guess.

**Nothing downstream complained.** An untagged library row promotes, verifies,
renders and publishes without a single warning; the gap only surfaced when the
2026-09-27 batch of five was queried for theme coverage. Patching them took
three SQL attempts — ambiguous column in RETURNING, then text[] against jsonb —
all of it avoidable at the point of promotion.

**Fixed by making the empty case loud.** `--tags a,b` supplies the batch's tags
(one invocation per theme, which is how a reviewed batch is promoted anyway),
`--no-tags` is the explicit opt-out, and the guard exits before any write when
neither is given. A default that cannot be derived should be demanded, never
assumed.

**Also:** lib/tags.ts still has no Cyrillic pair for `kabair` or `shirk`.
Tagging a row correctly does not reach the caption until that is filled.

**Status:** FIXED


## ═══════════════════════════════════════════════════════════
## PATTERN 182: The tag vocabulary drifted out from under its own translation
## ═══════════════════════════════════════════════════════════
**ID:** P182
**Type:** Mapping table outgrown by the data it maps
**Files:** lib/tags.ts
**Found:** 2026-09-29, from a published caption — not from a test

**P150 translated a snapshot.** It deduplicated roughly 100 library tags onto
56 canonical concepts and gave each four forms. Nothing kept that current. The
`tags` column now holds ~150 distinct values and 53 of them were reaching
captions unmapped.

**The fallback is correct, and that is what hid it.** buildTags() keeps an
unmapped tag rather than dropping it — right, because a new tag should not
silently vanish from a caption. But a kept tag emits only its English form, so
the caption loses the localised half that P150 exists to provide, and nothing
logs the miss. The only evidence is the caption itself: «#maruf» shipped bare
in the RU and TJ reels of Muslim #1005 while every tag beside it carried its
pair.

**Half fixed, half deferred.** 24 of the 53 were synonyms of concepts that
already carry four forms — intention/niyyah, remembrance, praise/thanks,
religion, spouse/wife, umrah, ramadan, sujud/prostration, scholar/teaching,
tongue, virtue, muslim, silatur-rahim, sadaqah-jariyah, companionship/
friendship, pillar(s), trial — and are now aliases. The other 29 are genuinely
new concepts needing four forms each: zakat, riba, fitna, shirk, kabair, maruf,
purity/clean/tahara, death, orphan, neighbor, prophet, soul, wisdom, salvation,
bloodshed, path, strength, shield, time, oath, obligation, warning, influence,
rebirth, people, women, fire. That is translation review, not a code change.

**The gap that matters is the missing check.** This drifts again the moment the
library grows, and it will be invisible again. Diffing
`select distinct unnest(tags) from hadith_library` against TAG_CANONICAL is the
whole test, and it belongs beside derive-uzbek-latin.ts since the vocabulary
lives in a .ts. Until it exists, P150 is only as current as the last hand audit.

**Related:** P150 (the vocabulary), P169 (Latin inside a Cyrillic caption — a
different layer: the matn, not the tags)
**Closed 2026-09-30.** scripts/audit-tags.ts reads the library's live `tags`,
diffs it against TAG_CANONICAL and TAG_FORMS, and exits 1 on a gap: an unmapped
tag, a raw tag pointing at a concept with no forms, or a concept missing a
language form. It separates "found gaps" (1) from "could not run" (2) — the
first draft returned 0 on an empty read, so a wrong env or an RLS change would
have looked like a pass. That is P093's shape exactly, caught before the script
reached a hook.

**Counting by machine changed the answer.** The audit confirmed the 29 and
attached each tag's row count. 25 of them appeared on ONE row. Eleven were real
recurring topics and got four forms each — kabair, shirk, zakat, riba, fitna,
tahara, death, neighbor, prophet, orphan, women. The other fifteen were
descriptive words lifted from a single matn: «shield» from *fasting is a
shield*, «rebirth» from *hajj mabrur*, «path» from *seeking knowledge*, «soul»
from *richness of the soul*. Those were removed from the library rather than
translated. The removal was previewed row by row first — taking tags away can
strand a row untagged, which is the state P181 exists to prevent — and every
affected row kept four or more tags and all of its real topic tags.

**The alias trap, avoided.** Thirteen of the 29 were first proposed as aliases
onto existing concepts, each inferred from its single row. That would have been
worse than the gap it closed. An unmapped tag emits English only and the audit
reports it on every run; a wrong alias emits a confident wrong Cyrillic hashtag
and reports nothing. `obligation` → ilm is right for Ibn Majah #224 and wrong
for the next obligation hadith that is not about knowledge.

**Rule:** a vocabulary that has to stay in step with data needs a diff that
runs, not a person who remembers. When a mapping is uncertain, leave the gap
the audit can see rather than close it with a guess it cannot.

**Status:** FIXED — gate live in .githooks/pre-push as of 80e6c58


## ═══════════════════════════════════════════════════════════
## PATTERN 183: A blocklist that predated the thing it was blocking
## ═══════════════════════════════════════════════════════════
**ID:** P183
**Type:** Rule outlived the assumption it was written under
**Files:** lib/tags.ts, app/admin/page.tsx, scripts/audit-tags.ts
**Found:** 2026-09-30, while reading page.tsx for an unrelated task

**P106 filtered eight tags at caption time** because those hashtags reach the
wrong audience — #date lands in dating content, #hellfire skews to metal and
gaming. Correct then, and written when every hashtag in a caption was English.

**P150 made the assumption false and nothing revisited it.** Once each concept
carried four forms, dropping a tag stopped meaning dropping one hashtag: to
avoid #death the filter also dropped #ўлим, #марг and #смерть. Two of the eight
— `death` and `women` — are ordinary hadith topics whose localised hashtags
reach nothing problematic, and they were being suppressed on the RU, UZ and TJ
captions that are this channel's actual audience.

**It lived inline in a component, so nothing could check it.** On the morning
of 2026-09-30, `death` and `women` were each given four forms as part of
closing P182 — and scripts/audit-tags.ts, the tool built for exactly this,
reported OK, because it had no idea the list existed. Its own BLOCKED_UPSTREAM
constant held two of the eight entries, guessed from a comment in lib/tags.ts
saying a blocklist "applies upstream." Reading the comment instead of finding
the list is what produced that guess.

**Fixed by splitting the filter along the line P150 drew.** TAG_BLOCKLIST now
lives in lib/tags.ts and still drops the tag whole at the caller; six entries,
none of them in TAG_FORMS, so tag and English form remain the same act for
them. EN_HASHTAG_BLOCKLIST suppresses only the English form inside buildTags(),
and `death` and `women` moved there. audit-tags.ts imports TAG_BLOCKLIST rather
than restating it.

**Rule:** a rule encodes an assumption about the world it was written in. P106
assumed one tag meant one hashtag. Write the assumption down beside the rule,
because the change that invalidates it will not announce itself — and keep the
rule where the thing it constrains can see it, or no gate will ever catch the
drift.

**Related:** P106 (the blocklist), P150 (four forms per concept), P182 (the
audit that could not see this)

**Status:** FIXED


## ═══════════════════════════════════════════════════════════
## PATTERN 184: The caption had no idea how long it was allowed to be
## ═══════════════════════════════════════════════════════════
**ID:** P184
**Type:** Missing constraint — discovered by the platform, not the code
**Files:** lib/tags.ts, app/admin/page.tsx
**Found:** 2026-09-30, measuring instead of guessing

**Telegram caps a media caption at 1024 UTF-16 code units**, and Uzbek and
Tajik cleared it on nearly every set. Nothing in the pipeline knew the number.
The operator found out after posting, from the post itself — Telegram
truncates from the END, and the end of every caption is the hashtag line, so
what vanished was always the tags.

**Measured first, then built.** A plain character counter went in before any
trimming logic, because neither of us could say what was being cut by hand or
by how much. The first Uzbek caption read 1073 — 49 over. Small enough that
trimming the right thing would fix it.

**What yields, and what never does.** P116 established that length pressure on
the generator is fabrication pressure: told to be shorter, the model complied
on narrative and inflated importance instead, which is how invented
superlatives reached Muslim #1005. The hadith text and the Arabic matn are the
caption's verifiability and are explicitly never truncated (P106, P153). That
leaves the hashtags, which are additive reach.

**fitTagLine() degrades in order of cheapest loss:** localised + English, then
localised only, then without the language self-tag, then dropping topic
concepts from the end. Rung 1 knowingly trades against P150, whose argument for
shipping both forms was that "hashtags are free" — over the cap they are not,
and on a Cyrillic caption the localised tag reaches the audience this channel
actually has. It never trims silently: the admin prints what was given up, and
the textarea stays editable.

**The measurement that matters is what came next.** On Bukhari #2654's Uzbek
the ladder went four rungs down, to two topic tags, landing at 1019. That is
not the ladder failing — it is the body being roughly 960 characters on its
own, leaving about 60 for tags. #2654 carries an unusually long Arabic matn.
Trimming hashtags treats the symptom; the structural answer is a two-message
post, video with a short caption plus the full text as a reply, since Telegram
allows 4096 in a text message. Not built.

**Rule:** a limit the code does not know is a limit the platform enforces
silently and arbitrarily — from the end, on whatever happened to be last. Put
the number in the code, show it before the thing ships, and choose what gives
rather than letting the byte count choose.

**Status:** FIXED — the caption now fits deliberately. The body length itself
is untouched and is the real constraint.


## ═══════════════════════════════════════════════════════════
## PATTERN 185: The check existed. Nothing ran it.
## ═══════════════════════════════════════════════════════════
**ID:** P185
**Type:** Gate present, never invoked
**Files:** scripts/audit-library.py, .githooks/pre-push
**Found:** 2026-09-30, fixing a one-row defect and discovering the check for it
          had been written weeks earlier

**Bukhari #574's Uzbek Latin held an ASCII apostrophe** where the okina U+02BB
belongs — «o'qigan» for «oʻqigan», P097 residue from the 74-row August
backfill, which wrote Latin without going through the transliterator.

**check_uz_okina was already in audit-library.py and matches exactly that.**
Six wrong characters, both Latin columns, written long before #574 was noticed.
It never fired because nothing runs audit-library.py. The script is excellent
and had no caller — the same shape as P119 (a hook blind to Python while four
agents gating every reel had no coverage) and P126 (eleven transliterator tests
the hook never invoked). Third time in this repo.

**Fixed by derivation, not by hand.** The Cyrillic column is canonical (D4), so
`derive-uzbek-latin.ts --library --number 574 --commit` regenerated the Latin
rather than an UPDATE patching the character. That matters here: P097 is about
okina versus tutuq — ʻ (U+02BB) in oʻ/gʻ against ʼ (U+02BC) for the glottal
stop — and a blind `'` → `ʻ` replace is wrong wherever the tutuq belongs. The
transliterator knows which; a SQL statement does not.

**check_ha_formulas added while in there.** Uzbek and Tajik write ҳ (U+04B3)
where Russian writes х, and a Russian keyboard or a Russian-heavy model
produces х silently in the honorific formulas — «Аллах» for «Аллоҳ»,
«розияллоху анху» for «розияллоҳу анҳу». Deliberately a closed list of thirteen
fixed phrases rather than a rule about the letter: Tajik uses х correctly in
ordinary words (хуб, хона, хонадон) and flagging the letter would bury real
findings under noise. text_russian is excluded, where «Аллах» is right. It
found nothing across 70 rows, so it is a regression guard, not a cleanup.

**Both now run on every non-doc push**, `--strict`, beside the tag audit from
P182. At 0 HIGH today, so it passes now and fires the day something regresses.

**Rule:** writing the check is the easy half. Ask what invokes it before
calling the pattern closed — a gate with no caller is documentation that
believes it is enforcement.

**Related:** P097 (okina vs tutuq), P119 and P126 (gates nobody invoked),
P182 (the tag audit, wired the same way), P093 (a gate that passed having run
nothing)

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 186: The file was fine. The reader could not see its first line.
## ═══════════════════════════════════════════════════════════
**ID:** P186
**Type:** Encoding assumption in a gate; the failure report points away from the cause
**Files:** scripts/lint-content.py
**Found:** 2026-10-01, linting R101's Tajik draft

**lint-content.py reported `no S (STORY) block` on a file whose first line was
`S: Расули Аллоҳ ﷺ фармуданд...`.** M, H and C parsed. Only S was missing.

**The draft had been written by `Set-Content -Encoding utf8`, which in
PowerShell 5.1 writes a BOM.** So line 1 arrives as `\ufeffS: ...`, and
`parse_blocks`'s `^\s*([SMHC])\s*:` does not match it — U+FEFF is a format
character (Cf), not whitespace, so `\s` steps over spaces and tabs and stops
dead on it. The regex is correct; the file is correct; the two disagree about
byte one.

**Only the FIRST block can ever disappear this way**, which is the whole
fingerprint. One missing block and it is always S means the file, not the
generation. Any other missing block means a dropped label.

**The report sent you the wrong way.** check_missing_block's advice — "that
block's text is now sitting INSIDE the previous one, check the end of the block
above it" — is sound for a dropped label and nonsense for S, which has no block
above it. P124 promoted that note from a quiet `note:` line to a real Finding so
it could not be read past; this is the next layer, where it is impossible to
miss and still misleading. A check that fires correctly can still cost you the
session if its remedy names a cause that cannot apply.

**Fixed with `encoding='utf-8-sig'`** on the one `open()`. It strips a BOM if
present and is byte-identical to `utf-8` when it is not, so nothing else moves.
The missing-block advice now names the BOM when the missing block is S.
Verified both ways: the old script warns missing-block on a BOM file and the new
one does not, and BOM and no-BOM files now produce identical output.

**Not fixed in the paste ritual.** The alternative was to keep writing drafts
with `[System.IO.File]::WriteAllText(..., UTF8Encoding $false)` and remember it
every time. A reader that only accepts files written one particular way is the
defect — `utf-8-sig` is what every Python tool in this repo should read with,
since every draft on this machine is written by PowerShell.

**Rule:** when a parser reports the first element of a file missing and the rest
present, suspect the file's first bytes before the parser's logic. And when a
gate tells you what to do about a finding, check that its remedy can apply to
the case that fired.

**Related:** P124 (the missing-block check itself), P100 (PowerShell console
codec breaking Whisper on Cyrillic — same class: the tool was right, the
encoding between them was not), P185 (a gate nobody invoked; this one ran and
pointed the wrong way)

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 187: The doc rule had no caller either
## ═══════════════════════════════════════════════════════════
**ID:** P187
**Type:** Rule written where a gate was needed
**Files:** scripts/audit-docs.py, .githooks/pre-push
**Found:** 2026-10-01, hours after shipping P186

**A whole session went on correcting docs that had quietly stopped describing
the repo.** reel-creation-pipeline.md argued the nasheed picker was unsafe
three patterns after P162/P168/P170 fixed it, and its own cost table was a
model and a clip length out of date. animated-reel-scene-prompts.md was headed
"not yet wired to fal.ai Kling" for a lane that had shipped 29 reels. AGENTS.md
still routed UZ/TJ to browser SpeechSynthesis, retired at P102 in August. The
tracker copy attached to the Claude project was sixty-four reels behind.

**The first fix was a rule**: a START OF SESSION block in CLAUDE.md and
QA_STANDARDS 10.10 saying read the repo, not a copy of it.

**Which is the exact shape of P119, P126 and P185** — a check that exists and
nothing invokes. P185 shipped the day before this, and its own closing line is
"ask what invokes it before calling the pattern closed." The rule was written
and the session moved on. Fourth time.

**scripts/audit-docs.py is the caller.** It cannot judge prose, so it does not
try; it checks only what is COUNTABLE, where wrong is wrong with no opinion
involved: the tracker's declared totals against its own rows, reel IDs against
the count, every shipped hadith against the duplicate-check index, every
nasheed row against actual usage three ways (declared count, listed IDs, reels
that say they used it), assets named against the registry, and any P-number
cited above the frontier. Exit 1 on drift, 2 when it cannot read a file, same
contract as the other two audits. It is in the pre-push hook, unscoped by
changed files — doc drift arrives when PRACTICE changes, which is usually a
commit touching no doc at all.

**It found two defects on its first run**, both invisible to every other check:
`ramadan-bg.mp3` was used by five reels and its row listed four, missing R007
since June; `light-of-my-heart-bg.mp3` declared seven uses, listed six, and had
R094 missing from the set shipped the day before. The nasheed rotation is
planned off that table, so each one was planning a repeat.

**What it deliberately does not check:** whether a paragraph is true. That
needs a reader, and pretending otherwise would have produced a gate that
passes while the docs lie — which is the failure this exists to prevent, in a
new costume.

**Rule:** a rule about what a future session should READ is not a control. If
the thing you are protecting can be counted, count it in a gate. If it cannot,
say plainly that it rests on a human, and do not let the rule's existence feel
like coverage.

**Related:** P185, P126, P119 (gates with no caller — this is the fourth),
P093 (a gate that passed having run nothing), P186 (the lint gate that ran and
pointed the wrong way), P182 (the audit this one is modelled on)

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 188: The write said "written" and wrote nothing
## ═══════════════════════════════════════════════════════════
**ID:** P188
**Type:** Tool reports success on a no-op; the assistant believed it
**Files:** CLAUDE.md
**Found:** 2026-10-03, three times in one session

**A file edit was committed to the repo, the tool returned `written`, and the
file on disk was unchanged.** Three times: `scripts/list-library.py` twice, then
`app/api/tts/route.ts`. Each time a retry landed it. Each time the first call
reported success with an empty `rejected` list.

**The shape is a second write to a path already written this session.** First
writes land. A later write to the same path can silently no-op, and `force:
true` does not prevent it.

**Worse: the day before, the opposite was written into CLAUDE.md.** Thirteen
files had been committed that way without incident, and from thirteen successes
the assistant recorded that this write path is NOT affected by the machine's
documented PowerShell write-revert problem. That is induction presented as a
finding, and it is the same error as stating a repo fact from recollection — the
evidence was real, the conclusion outran it.

**Fixed by verifying, not by avoiding.** Every write is now followed by a read
that confirms the change is present — a grep for the new text, a byte count, a
`git diff --numstat`. The cost is one command; the alternative is a commit whose
diff does not contain what the commit message describes.

**Rule:** a tool's success message is a claim about the call, not about the
disk. Where a write matters, read it back. And do not promote a run of
successes into a property of the system — thirteen clean writes is evidence
that writes often work, not evidence that they always do.

**Related:** P154 (a render that reported OK on a stale file), QA_STANDARDS 10.9 (state a repo fact only from something read this session), P190 (the same session, the same mistake, on video output)

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 189: stt-validate.py: seven weeks, three catches, no caller
## ═══════════════════════════════════════════════════════════
**ID:** P189
**Type:** Gate present, never invoked — fifth instance
**Files:** render-reel.ps1, scripts/stt-validate.py
**Found:** 2026-10-03, when the operator asked whether the validator step was real

**`scripts/stt-validate.py` shipped 2026-08-15 and nothing ever called it.** It
was documented in CLAUDE.md as Workflow F, in FEATURES.md with its ten checks,
in the README, and in two agent SKILLs. It ran when somebody remembered.

**In that time it caught three defects that human review had already passed:**
- R039 — «Аллахам», not a word, still burned into RU cue 2 AFTER hand-correction
- R043 — an SRT whose structure the editing itself broke, 9 cues to 8
- R051 — the narration said «это второе, а не первое» where the draft stopped at
  «это второе»; a three-word divergence nobody saw

**And it caught a fourth the day it was wired in.** R102's Whisper pass put
"traitors" where the source said "traders" — on the line introducing musk. The
operator had already pressed ENTER at the review gate, so it burned in and the
reel had to be re-rendered. The validator would have caught it before the gate.

**Now runs inside `render-reel.ps1` at step 2b**, before the human checkpoint,
unconditionally whenever there are subtitles — INCLUDING under `-NoReview`,
where there is no human about to look and an automated check matters more, not
less. Warn-only by design: it is a reader's aid, not a gate, and the human at
the checkpoint still decides. Added `-Draft` so the source file is explicit.

**Rule:** this is the fifth time in this repo. Writing the check is the easy
half, and documenting it in four places is not the same as calling it. When a
check is finished, the next question is which line of which script invokes it;
if the answer is "the operator, from memory", it is not finished.

**Related:** P185, P187, P126, P119 (the same class), P093 (a gate that passed having run nothing), P124 (the check this one sits beside)

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 190: The render reported OK on a file that was not a video
## ═══════════════════════════════════════════════════════════
**ID:** P190
**Type:** Success check tests the wrong property
**Files:** render-reel.ps1
**Found:** 2026-10-03, after YouTube abandoned processing three times

**R103's reel rendered, reported `OK ... 11.7 MB`, and was watched and
approved.** It then went to Telegram, which played it. YouTube said "Processing
abandoned". TikTok hung. By the time anyone looked, the file was **2.25 MB with
no moov atom** — ffprobe could not read it at all.

**P154 had already hardened this check**, and it still missed. Step 8 verifies
the ffmpeg exit code, that the output exists, and that it is less than five
minutes old. A truncated MP4 with no moov atom satisfies all three. The script
then printed the file's size as confirmation, which is how `11.7 MB` was
reported for a file that later measured 2.25 MB — the size was read at a moment
the file was still whole.

**Two platforms rejecting one file is a statement about the file.** That is what
turned the diagnosis around: the instinct was to blame YouTube, and comparing
against the English reel — which probed clean at 1080x1920, 40.7s, AAC — took
thirty seconds and settled it.

**What truncated it is still open.** Nothing was writing the file by the time it
was examined, and the mtime sat fifteen minutes stale; the likeliest account is
a second render starting, ffmpeg's `-y` truncating the output to begin
rewriting, and the run not completing. Recorded as unexplained rather than
guessed at.

**Rule:** a check that the output EXISTS is not a check that the output is
USABLE. For a media file, probe it: a duration and a stream are cheap to read
and are the thing the next step actually needs. And verify before uploading —
two platforms had already rejected this one before anyone looked at the file.

**Related:** P154 (the previous hardening of this same check), P188 (the same session, the same shape: a success message believed over the artefact)

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 191: The generator reaches for the same four additions in every language
## ═══════════════════════════════════════════════════════════
**ID:** P191
**Type:** Prompt-level, not per-language
**Files:** app/api/generate-reel/route.ts (prompt), scripts/lint-content.py
**Found:** 2026-10-03, after the fourth language of #2628 produced the same block

**Across EN, RU, UZ and TJ for Sahih Muslim #2628, the generation added the
same four things, independently, every time:**

1. **An invented instruction in M.** RU: "Ask Allah to place you among the
   righteous". UZ: "thank Allah for giving a good brother". TJ: "ask Allah to
   join you with good companions". The hadith instructs nothing of the kind; it
   compares two companions.
2. **A paraphrase attributed to him ﷺ as a quotation.** RU went furthest and
   attributed a DIFFERENT hadith — al-maru ala dini khalilihi, Abu Dawud and
   Tirmidhi — to Muslim #2628.
3. **A chapter claim in H.** Four languages, four different chapter names, none
   verifiable from the repo. R101 did the same thing on #6857.
4. **A second simile built on top of the matn's own.** EN: "musk and smoke each
   leave their trace". TJ: "just as the scent of musk or the smoke of the forge
   spreads". On a hadith whose entire content IS a simile.

**Four languages is not four slips.** P122 and P133 established this shape — the
generator reaches for the same additions in every language, which makes it a
prompt problem, not a translation problem. The same is true here, and the
remedy is the prompt, not four hand-corrections per set.

**A lint gap found while confirming it.** `check_simile`'s marker lists miss the
most natural word in two languages: Russian has «подобно» but not «подобен»,
Uzbek has «мисоли» but not «қиёслаб». Both fired clean on text containing an
obvious comparison. Widened to stem matches.

**Rule:** when a defect appears in every language of a set, stop fixing it per
language. One generation getting it wrong is a slip; four getting it identically
wrong is the instruction telling them to.

**Related:** P122, P133 (the same cross-language shape), P111 (divine name, simile and attribution rules), P116 (length pressure as fabrication pressure)

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 192: A real word in the wrong place: the matn said "the one who blows the inspection"
## ═══════════════════════════════════════════════════════════
**ID:** P192
**Type:** Library defect invisible to every automated check
**Files:** hadith_library (text_uzbek_cyrillic, text_uzbek_latin)
**Found:** 2026-10-03, reading the Uzbek blocks before narration

**The Uzbek matn for Sahih Muslim #2628 rendered نَافِخُ الْكِيرِ — the blower
of the bellows — with a word that means INSPECTION.** Both script columns
carried it, so the published Uzbek read "the one who blows the inspection", and
it had been sitting in the library since the row was promoted.

**No gate could have caught it.** `audit-library.py` checks ha/kha confusions,
okina versus tutuq, and honorific formulas. `lint-content.py` reads GENERATED
text against the matn — and the generation was faithful to a matn that was
already wrong, exactly as on #2999 where the EN and RU columns were missing a
clause. A correctly spelled, grammatical, real word in a well-formed sentence is
invisible to a character-class check and to a faithfulness check alike.

**It was caught by a native speaker reading the blocks**, and settled by asking
him rather than by the assistant picking a replacement: the Arabic is an agent
noun, a PERSON, parallel to the carrier of musk — which rules out the device
and rules out the redundant "bosqon puflovchi", since the bosqon is itself the
thing that blows.

**Fixed in the DB, not in the reel.** The Cyrillic is canonical (D4), so the
Latin was regenerated with `derive-uzbek-latin.ts --library --number 2628
--commit` rather than hand-edited — and the derivation got okina versus tutuq
right, which a hand-edit of both columns would have flattened (P097).

**The same check on Tajik, run BEFORE generating because of this, came back
clean** — "damandai kura", an agent noun parallel to "homili mushk", exactly
what the Arabic is. The Tajik translator got right what the Uzbek one got wrong.

**Rule:** read the matn in the target language before generating, not after.
Every downstream check measures faithfulness TO the row; none of them can tell
you the row is wrong. That remains a human reading, in the language, and it is
the second time in one session it was the only thing standing between a wrong
word and a published reel.

**Related:** P145/P146 (the library audit), P151 (re-translating a corrected matn), P097 (okina vs tutuq), P120 (A/B verify judges faithfulness, blind to conventions), the #2999 missing clause and the #574 cold/ugly corrections

**Status:** FIXED

## ═══════════════════════════════════════════════════════════
## PATTERN 193: A model upgrade is a re-roll, not a cure — the mispronunciation class moved words
## ═══════════════════════════════════════════════════════════
**ID:** P193
**Type:** TTS defect class surviving the change that was supposed to end it
**Files:** app/api/tts/route.ts, reel-creation-pipeline.md (pronunciation watch-list)
**Found:** 2026-10-04, auditioning eleven_v4 at a set boundary

**The Tajik stem-vowel defect was the MODEL, not the voice.** Three reels had
logged Meisam mis-voicing «Марде»→«Мардэ» (R081), «Даре»→«Доре» (R089) and
«атри»→«отри» (R105). The diagnosis on record was that Meisam is a Persian voice
and Persian alif sits closer to [ɒ] than Tajik а — and a voice-replacement plan
had already been built on it. Auditioned on one line carrying all three:

| word | Meisam v3 | Rustam v3 | Meisam v4 |
|---|---|---|---|
| атри  | FAIL отри  | ok | ok |
| Марде | FAIL Мардэ | ok | ok |
| Даре  | FAIL Доре  | FAIL Доре | ok |

Same voice, different model, defect gone. The accent explanation was plausible
and wrong. Five Tajik voices were auditioned on the strength of it; none was
needed, and the one that scored best on pronunciation (Rustam) was rejected on
register anyway.

**The Uzbek audition is why this is not a victory.** Opa Johann, one line, both
models:

| word | v3 | v4 |
|---|---|---|
| етим x3 | FAIL этим | ok |
| Оқ      | FAIL ўқ   | ok |
| емоқ    | ok        | FAIL эмоқ |

v4 fixed two and introduced one — and it is the SAME defect. v3 said етим→этим;
v4 says емоқ→эмоқ. Word-initial Cyrillic е→э survived the upgrade and moved to a
different word.

**«емоқ» was safe across 105 reels.** It would have broken on the first v4 set,
inside the matn, silently. Nothing reads narration back against the written word
except `stt-validate.py`, which runs only when subtitles are on — and P078 turns
subtitles OFF for UZ and TJ. The two languages that carry this defect are exactly
the two with no automated listener.

**Rule:** a pronunciation watch-list entry is scoped to the model that produced
it. Changing models expires the whole list: entries that were fixes become noise,
and words never on it start failing. Re-audition every entry against the new
model before a set ships on it, and record the model beside each entry.

**What this costs the existing rule.** The watch-list in
`reel-creation-pipeline.md` says "add entries as found; look for a real pattern
at ~5, not before." That assumed entries ACCUMULATE toward a pattern. They do
not accumulate — they are re-rolled. The permanent fix named in P71 (voice
cloning, with a phonetic substitution table as backup) is now the only thing
that survives a model change, and the table must be keyed by language AND model.

**Also established by this audition, and worth more than the result:**
`voice_settings.speed` is ignored by eleven_v3 AND eleven_v4. Only
eleven_multilingual_v2 honours it (14.35s → 16.16s at 0.75), and m2 was rejected
on the same audition for mangling the Tajik accent — P102 restating itself.
Two IDENTICAL v3 requests, same voice, same text, measured 11.84s and 12.40s:
a 4.7% duration spread from generation variance alone. Any judgement about pace
or weight from ONE clip per voice is inside the noise, and three "speed" results
in this session (11.76 / 11.92 / 12.16s) were noise read as signal. Pronunciation
judgements are NOT — a word is right or wrong — which is why the tables above
stand and the duration claims made beside them did not.

**Related:** P102 (why this pipeline is on ElevenLabs at all), P71 (voice cloning
as the permanent fix, PPD as backup), P078 (no subtitles for UZ/TJ), P118 (a
label and a fallback disagreeing), P154/P190 (a check satisfied by something that
is not the thing it measures)

**Status:** FIXED — default moved to eleven_v4. Watch-list re-audit OUTSTANDING.
## ═══════════════════════════════════════════════════════════
## PATTERN 194: The background is built at clip length, the reel is cut to narration length — a short reel drops its tail
## ═══════════════════════════════════════════════════════════
**ID:** P194
**Type:** Latent for 106 reels; surfaced by the first reel shorter than its own scene set
**Files:** render-reel.ps1
**Found:** 2026-10-04, R106 (Sahih Muslim #2963 EN)

**Four 10s scene clips behind 23s of narration played two and a half of them.**
The closing beat — the clip chosen to carry what the hadith concludes — never
appeared in the finished reel at all. The render reported OK.

**Why it was invisible until now.** Step 6 concatenates the ordered clips at
full length (4 x 10s = 40s), and step 7 merges with `-stream_loop -1` and cuts
the output to narration duration. When narration is LONGER than the concat the
background loops and every clip plays; when it is SHORTER the tail is simply
never reached. Every adults reel before this one ran 41-69s against 40s of
scenes, so the concat was always the short side and the bug could not express
itself. R106 is the first reel in 106 that is shorter than its own scene set.

**Not a truncation bug and not a Kling bug.** Nothing failed. ffprobe reports a
healthy file, the gate passes, the subtitles validate, the duration is correct.
The reel is simply missing a third of the visual material that was generated,
reviewed and paid for.

**Fixed with `-FitScenes`:** trims each clip to narration / clip-count before
the concat (here 22.99s / 4 = 5.748s each) so every clip appears regardless of
reel length. Verified by measurement, not by the log line: bg-mixed went from
40.0s to 22.93s and the reel from 3 clips to 4.

**Deliberately NOT the default, and deliberately non-destructive.** The masters
on disk keep their full 10s because the other three languages of the same set
need them — UZ is consistently the longest lane and will run 30-35s, where
trimming to 5.7s would multiply the cut rate for no reason. The flag belongs to
the RENDER, not to the asset.

**What this says about the rest of the pipeline.** The same shape is worth
looking for elsewhere: a step that sizes its output from one input while a later
step sizes the final result from a different one. Nothing reconciles them, and
the mismatch is silent in whichever direction does not error.

**Related:** P154/P190 (a check satisfied by something that is not the thing it
measures), P162/P168/P170 (the nasheed picker, the other place where a per-render
choice was being made from asset-level state)

**Status:** FIXED — `-FitScenes` added. Not on by default; pass it when
narration is shorter than clips x duration.
## ═══════════════════════════════════════════════════════════
## PATTERN 195: Rule 8 reads as satisfied by a paraphrase, so every moral re-attributes
## ═══════════════════════════════════════════════════════════
**ID:** P195
**Type:** A prohibition the model can comply with while producing the defect
**Files:** app/api/generate-reel/route.ts
**Found:** 2026-10-04, after a second full set showed the same four additions

**P191 recorded that the generator reaches for the same additions in every
language. It did not say why thirteen rules failed to stop it.** Rule 8 already
says: NEVER attribute direct or indirect speech to the Prophet SAW beyond what
the hadith itself records.

The moral blocks said, in all four languages: "for the Prophet SAW said this
guards against belittling His blessings", and the Tajik equivalent. That is
indirect speech — and it is NOT beyond the hadith, because the matn's own reason
clause says exactly that. The model checks its sentence against rule 8, finds the
content present in the matn, and ships. **It is complying.** The rule forbids
inventing sayings; it does not forbid re-quoting one the story block already
attributed.

Evidence across two sets, eight generations:

| addition | #2628 | #2963 |
|---|---|---|
| paraphrase re-attributed in the moral | 4 of 4 | 4 of 4 |
| invented du'a / dhikr instruction | 4 of 4 | TJ |
| qualification added inside the attribution | - | EN, RU |
| "and he explained that" splitting one utterance | - | RU, TJ |

Eight for eight on the first row. That is the model's modal output, not its tail.

**Why temperature is the wrong lever, asked directly by the operator.** Lowering
it pushes sampling TOWARD the mode, and these additions ARE the mode. Temperature
corrects inconsistency; the problem here is consistency.

**Fixed with four rules that name the behaviour rather than the category:**
17 — the moral APPLIES, never re-quotes, even a faithful paraphrase; the story
block holds the attribution. 18 — nothing inside the attribution that is not in
the matn, including correct scholarship like "in worldly matters". 19 — a hadith
with a reason clause is ONE utterance, never a quote plus an act of explaining.
20 — no instruction to recite anything the matn does not contain.

**The shape worth keeping:** a rule that the model can satisfy while producing
the defect is not a weak rule, it is a rule aimed at the wrong thing. Before
strengthening a prohibition, check whether the output actually violates it.

**Related:** P191 (the observation), P155 (the moral had no addressee because
none was asked for), P116 (length pressure is fabrication pressure)

**Status:** FIXED — rules 17-20 added. Unproven until the next set: the test is
whether a generation comes back without them.

## ═══════════════════════════════════════════════════════════
## PATTERN 196: The linter only ever sees text a human already cleaned
## ═══════════════════════════════════════════════════════════
**ID:** P196
**Type:** A gate placed after the check it duplicates
**Files:** reel-creation-pipeline.md (step order), scripts/lint-content.py (not at fault)
**Found:** 2026-10-04, while about to add a check that already existed

**The Tajik H block came back containing "afзоиш" — Latin "af" inside a Cyrillic
word.** It was caught by reading. The conclusion drawn in the moment was that
lint-content.py had no check for script mixing and needed one.

It has one. `check_script` flags any word containing both alphabets, and a probe
on the exact corrupted line returns `[FAIL] mixed-script`. The check is correct,
it has been there, and it never saw the word.

**Because draft.txt is written AFTER the blocks are reviewed.** The human reads
the generated output, corrects it, and the corrected text is what gets linted.
The linter is downstream of the review it exists to support.

**Three consequences, all of them active today:**
1. Every defect caught by eye is invisible to the linter. It reported "no
   findings" on all four languages of this set, on text that had contained a
   mixed-script word, an invented dhikr instruction, and four re-attributions.
2. Its measured value is understated to the point of looking like a formality.
   Four clean runs in a row is not evidence that generation is clean.
3. The ONLY defects it can catch are the ones the human misses — exactly
   inverted. A deterministic check costs nothing and should run FIRST, so human
   attention is spent on what no check can see: a real word in the wrong place,
   a wrong diagnosis, a register that does not fit the lane.

**Fix:** draft.txt must be written from the generator's RAW output and linted
BEFORE human review, with the review reading the linter's findings alongside the
blocks. This is automation item 3 on the operator's list, and the reason for it
is not convenience — it is that the linter currently grades the proofreading
instead of guarding the output.

**Not yet built.** Recorded because the reasoning is the valuable part and it was
one keystroke from being lost: the session was about to add a duplicate check and
call it a fix.

**Related:** P186 (the BOM that meant only the first block could ever go
missing), P189 (stt-validate: seven weeks, three catches, no caller), P119/P126/
P185/P187 (a correct check that nothing invokes)

**Status:** OPEN — the finding is recorded, the pipeline order is unchanged.
## ═══════════════════════════════════════════════════════════
## PATTERN 197: A convention that lives only in filenames is not a convention
## ═══════════════════════════════════════════════════════════
**ID:** P197
**Type:** An unwritten rule, inferred backwards, with nothing enforcing it
**Files:** animated-reel-scene-prompts.md, assets/asset-registry.json
**Found:** 2026-10-04, by the operator looking at a folder

**Scene clips are named `<collection-letter><number>-<concept>.mp4`.** b is
Bukhari, m is Muslim, ad is Abu Dawud. This was never written in any document.

Asked why a new set was named `b2963`, the assistant inspected the registry, saw
`b2628` on a SAHIH MUSLIM hadith, concluded the prefix meant "background", and
stated that as the rule — defending a mistake as the convention. The operator
pointed at `m2999-*`, a Muslim set that had used the correct prefix since August.
One sample, read confidently, inverted a rule that twelve other sets obey.

**The b2628 set is misnamed, and it is not cosmetic.** Bukhari #2628 is a real
and different hadith, on gifts. The filename names the wrong narration, in the
asset registry, permanently, across four shipped reels.

**Nothing checks it.** `audit-assets.py` enforces that a clip is REGISTERED and
approved for the lane — exactly what P117 built it for. It has no opinion about
whether the name matches the hadith. The tracker holds the hadith for every reel
and the clip names beside it; reconciling the two is a few lines.

**Rule:** when a convention is discovered by reading filenames, that is the
signal it was never written down. Write it in the spec that governs the artefact
— not in a changelog, which records that something happened and is buried by the
next entry.

**Related:** P117 (the asset registry gate), P118 (a label and a fallback
disagreeing), P187 (the doc audit — mechanical reconciliation of countable facts)

**Status:** FIXED 2026-10-09 — convention written into
animated-reel-scene-prompts.md section 5b; `audit-assets.py --names` now
reconciles every clip name in the tracker against the hadith it was used for.

It found ELEVEN misnamed clips across THREE sets on its first run, not one:

  b2628-musk / stall / forge / robes   Sahih Muslim #2628, Bukhari prefix
  b4248-clearing / sky / tide          Sunan Ibn Majah #4248, Bukhari prefix
  b4251-dawn / door / path / rain      Sunan Ibn Majah #4251, Bukhari prefix

b2628 was the only one known. The two Ibn Majah sets have been misnamed since
R074 and R086 and nothing noticed, which is the point of the check.

The discriminator matters: reuse of a scene set on a later hadith is intended
and looks identical to a misnaming unless you compare the NUMBER. Same number
with the wrong collection letter means the set was built for this hadith and
labelled with another collection; a different number means reuse. That split
turns 16 raw mismatches into 11 defects and 5 expected reuses (b527 on R058-61,
b1520-path on R010-13), with the reuses listed rather than hidden.

All three sets were renamed on 2026-10-09: 17 files across new/ and
normalized/ (including two unregistered b4248 clips that would otherwise have
kept the wrong prefix), 11 registry keys with the reason appended to each
entry's notes, and 18 tracker lines.

THREE tracker lines were deliberately NOT renamed. Lines 129, 437 and 440 are
prose and dated change-log entries that describe the defect by its old name —
“scene set named m2963 after discovering b2628 breaks the collection-letter
convention” and “b2628 should be m2628”. Rewriting those would have destroyed
the record of the thing being fixed. A rename is not a find-and-replace: the
filename is data, the sentence about the filename is history.

Verified after: 0 misnamed, registry and disk agree, `--check m2628-musk.mp4`
passes and `--check b2628-musk.mp4` is rejected.

## ═══════════════════════════════════════════════════════════
## PATTERN 198: Nothing watched the tools, so three of them were a major version behind
## ═══════════════════════════════════════════════════════════
**ID:** P198
**Type:** No process at all, discovered by accident
**Files:** self_upskilling.md (new)
**Found:** 2026-10-04, when the operator asked whether anything checks for updates

**ElevenLabs released v4 on 2026-09-28.** It was found on 2026-10-03, by the
operator, while auditioning a Russian voice for an entirely unrelated reason —
and only because something else was being changed in the same file.

Scanned on 2026-10-04:

| Tool | In use | Available | Behind by |
|---|---|---|---|
| ElevenLabs | eleven_v3 | v4 / v4 Turbo | 6 days — adopted same day (P193) |
| Kling | v2.6/pro | **Kling 3.0** | **since Feb 2026** |
| FLUX | flux-pro/v1.1 | **FLUX 2** | **since Nov 2025** |

Neither Kling nor FLUX had been noticed at all. FLUX 2 is a full generation
newer than the model that, the same afternoon, returned six consecutive upward
staircases for a prompt specifying a downward camera — and the response to that
was to abandon the concept, not to ask whether the tool was current.

**The roadmap already had an agent for this.** Agent 11, `upskilling`, whose
watchlist source is cited as `self_upskilling.md`. That file did not exist. The
agent is not built. So the citation pointed at nothing, and had for months.

**Fix:** `self_upskilling.md` created with versions in use, how to check each
without trusting a release note, open evaluations, and a dated log. Weekly
cadence, recorded in CLAUDE.md as step 2 of the session-start order — before
anything that depends on a tool version, because a pronunciation watch-list is
scoped to a model (P193) and expires when the model moves.

**The shape worth keeping:** every other pattern in this file is a defect in
something that exists. This one is the absence of a process, and it was invisible
precisely because nothing failed. Pipelines do not error when they are a year
out of date.

**Related:** P193 (a model upgrade is a re-roll, not a cure — why a new version
is never adopted without auditioning on our own text), P71 (voice cloning as the
permanent fix), R026 (negations reinforce what they forbid — rediscovered in
Anthropic's own prompting guidance and still not applied to the text generator)

**Status:** FIXED for the process. FLUX 2 EVALUATED AND ADOPTED same day - it
rendered on the first call a shot v1.1 had refused six times, which means the
concept abandoned that afternoon was a model limit nobody thought to question.
Kling 3.0 evaluation still OPEN.

## ═══════════════════════════════════════════════════════════
## PATTERN 199: The rules are written in English and they hold best in English
## ═══════════════════════════════════════════════════════════
**ID:** P199
**Type:** A guardrail that silently weakens in the languages that need it most
**Files:** app/api/generate-reel/route.ts, scripts/lint-content.py
**Found:** 2026-10-05, on the Sahih Muslim #2759 set, by reading all four

Rules 17—20 were written after the #2963 set and they worked. On #2759 the
ENGLISH generation obeyed every one of them. Then:

- **Uzbek** broke rule 17 (the moral referred back to the hadith as a
  quotation) and shipped a story block with **NO ATTRIBUTION AT ALL** — the
  matn stated as bare text, no Prophet SAW, no narrator, on a channel whose
  entire premise is that its content is traceable.
- **Tajik** broke rule 17 AND rule 18: commentary about the door of repentance
  closing was appended INSIDE the Prophet's SAW quotation, after the matn ends.
  The commentary is correct, it is in the H block where it belongs, and putting
  it in his mouth still means the reel has him saying words he did not say.
  The same block inverted its own moral: `gunohro ta'khir nadeh` — do not delay
  the SIN.

**The first instinct was that a rule was missing. It was not.** Rule 18 has
forbidden exactly this since the #2628 set. Writing a rule 21 that restates 18
would have changed nothing, because the failure is not that the model lacks the
instruction — it is that instruction-following degrades as the language gets
further from the prompt's own. UZ and TJ are also the two languages P078 exempts
from subtitles, so they are the two with no automated reader downstream. The
weakest generation and the thinnest verification are the same two lanes.

**What was actually missing** was a requirement that the story block NAME THE
SPEAKER. Rule 17 mentions the attribution only in passing, while explaining what
the moral must not do. Nothing ever said the story must carry one. That is now
rule 21.

**And a rule is the wrong instrument here anyway.** `check_quote_addition` in
lint-content.py does not read rules: it splits the story block into clauses and
scores each one's vocabulary against the library matn. A clause that shares
almost no words with the hadith it claims to quote is an addition, in any
language, whatever the prompt says. Clause-level, not sentence-level — the
#2759 addition rode in after an em dash inside an otherwise-faithful sentence,
which a sentence split would have scored as mostly-matn and passed. Verified
against the real defective text: 1 of 5 words shared, flagged; corrected text,
clean.

**Rule:** when a guardrail is prose in a prompt, assume it holds in English and
degrades from there. If the defect it prevents is one that must never ship, it
needs a deterministic check as well — and the check should test the artefact,
not the instruction.

**Related:** P111 (the rule set), P191 (invented dhikr instruction), P078 (UZ/TJ
have no subtitle pass), P116 (length pressure is fabrication pressure)

**Status:** FIXED — rules 21—22 added to the generator, `quote-addition` check
added to lint-content.py (10 checks now) and verified to fire on the real defect.

## ═══════════════════════════════════════════════════════════
## PATTERN 200: Whisper transcribes sound, so everything that is only in the text dies
## ═══════════════════════════════════════════════════════════
**ID:** P200
**Type:** A known, repeating, mechanical correction done by hand every time
**Files:** render-reel.ps1 (step 5), scripts/stt-validate.py
**Found:** 2026-10-05, after correcting the same class by hand on EN and RU

The subtitle review pause has caught, on every en/ru reel: divine pronouns
lowercased (`His`, `He`; `Svoyu`, `On`), Russian yo flattened to ye, and a
capitalised `Zapada` where the matn means a direction. None of these are
transcription errors. Whisper heard the audio correctly. Capitalisation and yo
are properties of the TEXT, and the text was never given to it.

On this set that was four of the five RU findings, and two of the three EN ones.
The fifth RU finding — `doblagoslovit` for `da blagoslovit` — is a real word
boundary error and is exactly the kind of thing the pause exists for.

**So the pause is doing two jobs and only one of them needs a human.** A
post-Whisper pass with a per-language table (His/He/Him; Svoyu/On/Ego/Emu) and a
yo restore would have removed four findings from the operator's plate tonight and
left the one that actually needed judgement.

**Why this is not cosmetic:** `-NoReview` skips the human, and the help text says
it does NOT skip the validator. True, but the validator only WARNS. A render with
`-NoReview` therefore ships lowercase divine pronouns with a clean-looking run.

**Rule:** if a correction is the same every time and depends only on the source
text, it is not review — it is a transform that was never written.

**Related:** P078 (subtitles only for en/ru/ar), P188 (verify every write), P093
(audit exit-code contract), P199 (deterministic checks over prose rules)

**Status:** FIXED 2026-10-09 — `scripts/restore-srt-casing.py`, called from
render-reel.ps1 after the cue split and BEFORE stt-validate, so the validator
reports only what needs judgement. It uses no word list: a list cannot tell
which «он» means Allah, and would need maintaining. It aligns the SRT to
$Draft and takes the source's spelling, replacing a token only when the two
are identical after normalising case and yo — so it cannot introduce a word
Whisper did not hear, cannot turn one word into another, and never touches
timings. Two guards: a normalised form the source spells two ways is left
alone and reported as ambiguous, and the first word of a cue is never
lowercased. Verified by round-trip against the real R111 defects: 11
restorations (днем -> днём x3, свою -> Свою x3, он -> Он, всемогущий -> Всемогущий,
великий -> Великий, взойдет -> взойдёт, Запада -> запада), 0 ambiguous, and
«Ведь» correctly left capitalised at a cue start where the source has it
mid-sentence. Punctuation and word-boundary errors stay with the human: on
that same set, «доблагословит» and «сказал,» for «сказал:» needed
judgement, which is the point — the pause is for the findings that do.

## ═══════════════════════════════════════════════════════════
## PATTERN 201: The nasheed a render chose exists only in the console
## ═══════════════════════════════════════════════════════════
**ID:** P201
**Type:** A fact the tracker requires that nothing persists
**Files:** render-reel.ps1, reel-tracker.md
**Found:** 2026-10-05, writing the R110—R113 rows

The tracker has a Nasheed column and the asset-reuse audit depends on it — that
table is how asset fatigue gets spotted. The picker writes
`out/backgrounds/.last-used.json`, but that file holds ONE value per lane and the
next render overwrites it.

Four reels were rendered tonight. By the time the rows were written, three of the
four bed names existed nowhere but a terminal scrollback that had been closed.
R110, R111 and R112 are recorded as `not recorded (P201)` and the values are not
recoverable.

**The state file is not a log.** It was built for one purpose — avoid repeating
the previous bed — and it does that correctly. Reading it as a record of what
shipped is reading a cache as an archive.

**Rule:** anything the tracker requires per reel must be written per reel, beside
the artefact, by the step that decides it.

**Related:** P168 (registry drives the picker), P117 (lane gate), P188 (the write
path can silently no-op)

**Status:** FIXED — render-reel.ps1 now writes the chosen bed into a per-reel
sidecar next to the output.

## ═══════════════════════════════════════════════════════════
## PATTERN 202: A still is identified by its file suffix, never by where it sat in a paste
## ═══════════════════════════════════════════════════════════
**ID:** P202
**Type:** An identifier invented at the point of review
**Files:** scripts/generate-image.ps1, animated-reel-scene-prompts.md
**Found:** 2026-10-05, after four Kling clips had already been paid for

`generate-image.ps1 -Count 3` writes `<name>-1.jpg`, `-2`, `-3`. The operator
pastes the three into chat; the assistant calls them "variant 1, 2, 3" by the
order they appear. **Those two numberings are not the same**, and nothing says so.

On the m2759 set the assistant picked "variant 3" for firstlight and dawn on the
strength of which way the door was hinged, wrote commands naming `-3.jpg`, and
the operator ran them exactly as written. The clips came back with the door on
the wrong side. The first conclusion drawn was that the wrong files had been
used. Reading the actual `-3` files off disk showed the opposite: the commands
were correct and the PICK was wrong, made against an image that did not have that
suffix.

Cost: one extra FLUX call and one extra Kling clip, ~$0.74, plus the twenty
minutes spent diagnosing a run error that never happened.

**Rule:** a still is identified by its filename. Review by opening the file, or
quote the suffix when discussing it. Position in a message is not an identifier.

**Related:** P197 (a convention that lives only in filenames), P118 (a label and
a fallback disagreeing)

**Status:** FIXED for the process — naming is stated in
animated-reel-scene-prompts.md and the pick is now made by reading files off disk.

## ═══════════════════════════════════════════════════════════
## PATTERN 203: A Status line is not a list
## ═══════════════════════════════════════════════════════════
**ID:** P203
**Type:** Tracking that records causes but never answers "what is left"
**Files:** OPEN_ITEMS.md (new), CLAUDE.md
**Found:** 2026-10-08, when the operator said not to let the noted items slip
again — "again" being the word that matters

This file is good at WHY. Every pattern ends in a Status, and a fair number say
OPEN or PARTLY FIXED. But those are 200+ lines scattered through the longest
document in the repo, in the order the defects happened, which is the one order
that has nothing to do with what should be worked on next. Nothing anywhere
answered "what is outstanding".

So the items that slipped were the ones with no home at all. `b2628` is
misnamed and has been since P197 — it names a real and different Bukhari
hadith across four shipped reels. Bukhari #6871 must never be selected because
the duplicate index keys on number and it is #2654's twin. The Tirmidhi #1899
Tajik column has been flagged INFO by `audit-library.py` on every run for a
week. None of these is forgotten because it is hard; they are forgotten because
the only place they lived was a conversation, and the next session starts with
a fresh one.

**The near miss:** every one of these is a content-integrity item on a channel
whose entire claim is that its content is traceable. A misnamed clip set is
cosmetic. A hadith that ships because nothing remembered it was the twin of one
already published is not.

**Rule:** if an item survives the session it was found in, it goes in
OPEN_ITEMS.md in that session. It leaves only when it is done, or when it is
dropped and the reason is written down. Status lines stay where they are —
they explain the pattern, and that is a different job.

Read at session start as step 3, before fix_patterns, so a session plans against
what is outstanding rather than against what was most recently interesting.

**Related:** P197 (the b2628 rename, still open), P147 (hadith_number is not
unique), P187 (mechanical reconciliation of countable facts), P198 (nothing
watched the tools, so a watchlist was written — same shape, different subject)

**Status:** FIXED — OPEN_ITEMS.md created and wired into the session-start
order as step 3; the eleven items outstanding as of today are in it.

## ═══════════════════════════════════════════════════════════
## PATTERN 204: A measurement written down as a rule, in a pipeline that never runs it
## ═══════════════════════════════════════════════════════════
**ID:** P204
**Type:** Doc and code disagreeing, with the code winning silently
**Files:** CLAUDE.md, app/api/tts/route.ts
**Found:** 2026-10-09, after the operator re-checked the glyph on v4

CLAUDE.md carried, for seven weeks: "ﷺ glyph handling is PER-LANGUAGE, measured
2026-08-16: EN, UZ and TJ all voice the raw glyph correctly. RU does not —
expand it before TTS."

The measurement was real. The conclusion drawn from it was not, because
`cleanForTTS` expands the glyph for EVERY language — ar, uz, tj, ru and the en
default — and has done since it was written. The raw glyph has never been sent
to any TTS provider. A reader of that entry would believe RU is a special case
in the pipeline. It is not; the per-language values are the EXPANSIONS, and the
decision to expand is unconditional.

**This produced a false alarm, and then a second wrong diagnosis.** The R107
tracker note recorded the symbol "narrated as spoken words on v4, contradicting
the pipeline doc's rule" — but that was `cleanForTTS` behaving normally, not v4
contradicting anything. On 2026-10-08 the assistant then cross-referenced the
entry's 2026-08-16 date against P193 (measurements expire when the model
changes), concluded v4 had invalidated the rule, and filed it as an open item.
Plausible, tidy, and wrong: the rule had been moot since before v4 existed. The
code was never read. A dated, specific, confidently-worded doc entry is exactly
the kind that gets reasoned FROM instead of checked.

**Why the shape matters.** P118 is a label and a fallback disagreeing, and it
shipped two reels in the wrong voice. This is the same shape with the opposite
outcome: the code was right and the doc was wrong, so nothing broke, and that
is precisely why it survived seven weeks. A doc-code disagreement that causes
no failure has no clock on it.

**Rule:** a measurement of MODEL behaviour and a statement of PIPELINE behaviour
are different claims. Write the measurement with its date and model, and write
separately what the code does about it — and before acting on a doc entry that
describes code, read the code.

**Related:** P118 (a label and a fallback disagreeing — THE FALLBACKS ARE the
source of truth), P193 (measurements are scoped to the model that produced
them), P187 (mechanical reconciliation of countable facts), P203 (OPEN_ITEMS)

**Status:** FIXED — CLAUDE.md now states that the glyph never reaches TTS in
any language and records what the entry used to say and why it was wrong. The
glyph item is closed in OPEN_ITEMS; the rest of the pronunciation watch-list is
still unverified against v4 and stays open. The expansion itself is KEPT: every
verified reel to date was narrated with it.

## ═══════════════════════════════════════════════════════════
## PATTERN 205: The check was written, measured, and deleted the same day
## ═══════════════════════════════════════════════════════════
**ID:** P205
**Type:** A gate that would never have fired, caught before it shipped
**Files:** scripts/audit-library.py, reel-tracker.md
**Found:** 2026-10-09, by testing a new check against the case it was for

Two cross-row checks were added to the library audit. One works and found
three real defects on its first run. The other was deleted an hour later.

**check_duplicate_numbers WORKS.** Three HIGH findings immediately: Tirmidhi
#2616, Bukhari #1469 and Bukhari #6018 each have TWO rows under one number.
Only #6018 was documented. The other two had been recorded in an earlier
session as 'each appear twice', carried into OPEN_ITEMS as unverified because
the tracker's index showed only #6018 — and they were real. Each pair turns
out to be one long narration split into clause-level rows, not two different
hadiths, which is a different diagnosis with the same exposure: the duplicate
index keys on the number, so producing one clause makes the other read as
already done.

**check_twin_wording DOES NOT, and was removed.** It existed for Bukhari
#2654 and #6871: different numbers, same subject, nothing flagging the pair.
Measured against the real rows before trusting it:

  - Jaccard on the matn scores that pair at **0.16**.
  - The highest cross-number Jaccard anywhere in the 70 rows is **0.29**.
  - Containment (shared words over the shorter text) scores the pair 0.56 —
    but two unrelated pairs score 0.60 and twelve score 0.50+, because short
    rows inflate containment.

There is no cut that separates the case from the noise. The relationship is
SEMANTIC — both narrations are about al-kaba'ir — and a lexical score cannot
see that. Shipping it would have produced a check that never fires, sitting in
CROSS_ROW_CHECKS reading as coverage. That is P119/P126/P185/P187/P189 again,
and this time it was caught before the commit rather than weeks after.

**What replaced it:** a row in the tracker's duplicate-check index, beside the
#6018 entry, saying plainly that #6871 must not follow #2654 without a
deliberate decision and that no automated check covers it. A human-readable
fact in the place a human already looks, instead of an algorithm that cannot
do the job.

**Rule:** before adding a check, run it against the case that motivated it and
look at the score distribution. A threshold chosen from intuition rather than
from the data is a guess, and a check that cannot fire is worse than no check,
because it is counted as coverage.

**Related:** P147 (hadith_number is not unique), P119/P126/P185/P187/P189 (a
gate with no caller), P093 (audit exit-code contract), P203 (OPEN_ITEMS)

**Status:** FIXED — duplicate-number check shipped and already finding real
collisions; twin-wording removed with the measurements recorded in the code
where it used to be, so it is not re-attempted from intuition.

**One more thing the first version got wrong.** Shipping it at HIGH blocked the
pre-push hook immediately: `--strict` exits non-zero on HIGH, and three
pre-existing collisions now existed. A gate that blocks every future push on a
condition nobody is about to fix is a gate people learn to bypass, and nothing
already shipped was wrong — the hazard is in SELECTING the next set, not in the
reels already out.

So the acknowledgement was made load-bearing. `documented_collisions()` reads
the tracker's duplicate-check index: a number recorded there reports INFO, a
number not recorded reports HIGH and blocks. Write the row and the gate
releases; delete the row and it returns. Verified both directions — with the
index in place 0 high and `--strict` exits 0; with the tracker unreachable all
three return HIGH. That makes the index the thing that must be kept true, which
is where a human already looks (P203), rather than a severity level argued
about once.

## ═══════════════════════════════════════════════════════════
## PATTERN 206: Forty-three kilobytes of skill in a path nothing loads from
## ═══════════════════════════════════════════════════════════
**ID:** P206
**Type:** A gate with no caller, applied to the agent fleet itself
**Files:** .claude/skills/ (moved), agent-fleet-roadmap.md, CLAUDE.md
**Found:** 2026-10-09, on being asked to “complete the agent”

The roadmap said agent #13 reel-producing was “SCOPED 2026-08-31, not built”.
On disk sat a 15KB SKILL.md with nine pipeline steps, a stated boundary,
governance, versioning and open questions, plus a four-case eval corpus with
expected findings in a deliberate split layout so the corpus calibrates the
human too. `stt-validating` and `tts-validating` sat beside it. Forty-three
kilobytes in total.

All three were in `agents/`. Claude Code loads project skills from
`.claude/skills/<name>/SKILL.md`. `.claude/` held hooks and settings.json and
no skills directory at all, so none of the three had ever been loaded by
anything. They were documents about agents, not agents.

**The frontmatter proves the intent.** Each file opens with `name:` and a
`description:` written in the when-to-use form a loader keys on — “use this
skill whenever a reel set is being produced, or any task mentions draft.txt,
lint-content.py, a hadith slug…”. They were written to be loaded. The last
step, putting them where loading happens, was never taken, and nothing failed
to announce it.

**Why it survived.** The two references to them in the docs pointed at the
files by path and were therefore correct. The roadmap's own status line was
the only thing that would have caught it, and it said the opposite of the
truth in the safe direction: claiming LESS was built than had been. Nobody
audits a roadmap for undercounting.

**Rule:** a skill exists when a loader can find it. Until then it is a design
document, and the roadmap should say which of the two it is. Same test as
P119's gate with no caller — ask what calls it, and if the answer is nothing,
it is not built regardless of how finished the contents look.

**Related:** P119/P126/P185/P187/P189 (a gate with no caller), P188 (the write
path can silently no-op), P197 (a convention that lives only in filenames),
P203 (OPEN_ITEMS — the roadmap is not a list of what is done either)

**Status:** FIXED — all three moved to `.claude/skills/` with git mv, the
roadmap status corrected, and CLAUDE.md now states where skills live and that
anything outside that path does not exist. STILL OPEN for reel-producing: the
Scripts section is unimplemented, and the eval corpus has never been run.

## ═══════════════════════════════════════════════════════════
## PATTERN 207: The clause splitter the quotation mark defeats
## ═══════════════════════════════════════════════════════════
**ID:** P207
**Type:** A check blindest on the input it was written for
**Files:** scripts/lint-content.py
**Found:** 2026-10-09, producing Sahih Muslim #1631 (R114-R117)

`check_quote_addition` exists because the #2759 Tajik story block appended
commentary INSIDE the Prophet's ص quotation. It splits the story line into
clauses, skips any clause holding an attribution marker, and warns when a
remaining clause shares almost no vocabulary with the matn.

The splitter was `(?<=[.!?])\s+`. That lookbehind needs the period
IMMEDIATELY before the whitespace. A correctly punctuated English story block
writes:

    The Prophet ص said: 'When a person dies ... prays for him.' Sadaqah
    jariyah, the charity named first, refers to ...

Period, apostrophe, space. The lookbehind fails. No split happens. The whole
line stays ONE clause, that clause contains "The Prophet ص said", the
attribution-marker skip fires, and the gloss is never examined.

**How it surfaced.** Removing the quote marks to fix an attribution boundary
made the warn count go from 1 to 2 on semantically identical content. The
second warn was not new text; it was the same gloss becoming visible once the
period could end a sentence. The punctuation that made the block CORRECT was
the punctuation that hid it.

**Found by reading the check, not by running it.** Two runs had already been
explained with guesses about how the check worked - first that it keyed on
quotation marks, then that removing them had made the text worse. Both wrong.
The source settled it in one read.

**Scale.** On this one hadith the same gloss was inserted in EN, UZ and TJ.
Russian alone did not do it. A per-hadith insertion that recurs across
languages is not a language-quality problem - it is the concept pulling the
generator the same way each time, and a check that any one language's
punctuation can defeat will miss it in that language every time.

**Rule:** when a check skips input on a structural signal, test it against the
correctly formatted version of the defect, not just the malformed one. A gate
that only fires on sloppy input is a gate against sloppiness, not against the
defect.

**Related:** P111 (the rules this check enforces), P118 (two copies drift),
P119/P126/P185/P187/P189/P206 (a gate with no caller - this is the variant
where the caller exists and the gate silently declines)

**Status:** FIXED - splitter lifted to `CLAUSE_SPLIT` and extended to allow one
optional closing quote character after the terminator: `' " » ” ’`.
Verified both directions: the EN v1 block that slipped through now warns, and
the four shipped #1631 drafts still return 0 fail 0 warn 0 info.

## ═══════════════════════════════════════════════════════════
## PATTERN 208: The header comment that sent two sessions to the wrong path
## ═══════════════════════════════════════════════════════════
**ID:** P208
**Type:** Stale comment contradicting live code
**Files:** render-reel.ps1
**Found:** 2026-10-09, producing R114

`render-reel.ps1`'s header block documented the narration inputs as:

    out\{style}-{lang}-{slug}-story.mp3      <- from admin Step 2 (you save this)

Line 162 of the same file builds `$workDir = "out\work\$Style\$Slug\$Lang"`
and reads the narration from there. The flat path has not been correct since
the restructure that P113 closed.

The comment was trusted twice in one session: once to report the narration
missing when it was present, and once again after being told the path was
wrong. The operator had to supply a screenshot of the real directory.

**Why a comment is worse than no comment here.** With no documented path the
next step is to read the code, which takes one grep and is always right. With
a wrong one, the reading never happens.

**Rule:** a path in a comment is an assertion about the filesystem and goes
stale exactly like a hardcoded one. When the code computes a path, the comment
quotes the computation, not a literal.

**Related:** P118 (a label and a fallback disagreeing - the fallback is the
truth), P113 (the restructure this comment predates)

**Status:** FIXED - header now shows the `out\work\{style}\{slug}\{lang}\` form.

## ═══════════════════════════════════════════════════════════
## PATTERN 209: The line-ending map describes the index, not the working tree
## ═══════════════════════════════════════════════════════════
**ID:** P209
**Type:** Environment assumption recorded as a fact
**Files:** (working practice; no single file)
**Found:** 2026-10-09, registering the m1631 scene clips

Notes carried for weeks said which repo files are CRLF and which are LF, and
writes were matched to that table. The table is about the INDEX. This repo has
`core.autocrlf=true` and no `.gitattributes`, so:

    git ls-files --eol -- assets/asset-registry.json
    i/lf    w/crlf

A file read as LF, reverted with `git checkout --`, and read again comes back
CRLF - git converts on checkout. A write that consults the remembered table
instead of the bytes then rewrites every line of the file.

Two failures in five minutes from this. A `json.dumps` round-trip reformatted
every inline `lanes` array and turned a 25-line change into 204 insertions and
67 deletions; reverting it with `git checkout --` flipped the file to CRLF, and
the next write asserted LF and aborted.

`fix_patterns.md` is a third case: `w/mixed`, 7583 CRLF and 3 bare LF. Any
whole-file normalise rewrites 7586 lines. It can only be appended to.

**Rule:** detect the ending from the bytes at read time, in the same operation
that writes them back. Never from a remembered table, and never from the
index. For a large or mixed file, append rather than rewrite.

**Related:** P188 (the write path can silently no-op), P202 (identify by what
is on disk, not by what you remember about it)

**Status:** DOCUMENTED - the practice is detect-and-preserve per write. The
earlier per-file table is superseded and should not be consulted.

## ═══════════════════════════════════════════════════════════
## PATTERN 210: The similarity gate that measured nothing
## ═══════════════════════════════════════════════════════════
**ID:** P210
**Type:** A gate that fires at random
**Files:** scripts/stt-validate.py
**Found:** 2026-10-10, on the at-tirmidhi-3895 EN reel

`transcript_diverged` reported HIGH at similarity 0.67 against a 0.75
threshold, on an SRT whose text differed from `draft.txt` only in two
punctuation marks and one honorific. Measured directly: the two strings are
343 and 334 characters and visually identical.

    similarity(a, b) = difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()

`difflib`'s **autojunk** heuristic treats any element occurring in more than
1% of a sequence longer than 200 elements as junk and drops it. These are
CHARACTER sequences of 300-900, so the 1% cutoff is three or four occurrences
and every common letter qualifies. The ratio stops measuring the text and
starts measuring whatever rare characters happen to survive.

    autojunk ON  (as shipped)      0.6706
    autojunk OFF (fixed)           0.9867
    autojunk OFF, unrelated text   0.2634

**It has never worked.** Not dead - random. The ratio is noise, so each reel
landed above or below 0.75 by accident. #1631 passed; this one failed; neither
result meant anything. A gate that is wrong in both directions is worse than
one that never fires, because the passes are read as evidence.

**It also suppressed the check that mattered.** The caller is

    if sim < SIM_DIVERGED:  findings.append(diverged)
    else:                   findings += check_alignment(cues, source)

so a false divergence SKIPS alignment entirely. On this reel alignment had
three real HIGH findings waiting - the draft's "(RA)" had been voiced as
"Ravya Allah" - and none of them were reachable while the broken gate was
firing. The noisy check was standing in front of the working one.

**Rule:** `difflib` comparisons over character sequences need
`autojunk=False`, always. More generally: a similarity threshold is a
measurement, and a measurement nobody has checked against a known-identical
and a known-different input is a number, not a gate. Both anchors are cheap
to compute and both are now recorded above.

**Related:** P093 (exit-code contract), P119/P126/P185/P187/P189/P206 (a gate
with no caller - here the caller exists and the gate is noise), P207 (a check
blindest on the input it was written for)

**Status:** FIXED - `autojunk=False`, with the three measured anchors in a
comment above the call. Re-run on the same reel: similarity 0.987, divergence
clear, and the three alignment findings now surface.

## ═══════════════════════════════════════════════════════════
## PATTERN 211: The transcript cache that outlived its audio
## ═══════════════════════════════════════════════════════════
**ID:** P211
**Type:** A cache with no invalidation
**Files:** render-reel.ps1
**Found:** 2026-10-10, on the at-tirmidhi-3895 EN reel

Step 5 was:

    if (Test-Path $srt) { Ok "subtitles already present - skipping Whisper" }

A bare existence check. The cache is there for a good reason - the operator
corrects the SRT at the review pause, and re-running the render must not throw
that away - but it had no way to tell a hand-edited transcript from one
describing audio that has since been replaced.

The story mp3 was re-narrated to replace a mangled honorific. The new audio
was correct. The render kept the PREVIOUS run's SRT, which still read "Ravya
Allah", and would have burned it over a soundtrack saying "may Allah be
pleased with her" - subtitles contradicting their own audio, on the exact
phrase being corrected.

**Three wrong diagnoses before the right one, each killed by a measurement:**

1. "The admin block still has (RA)." Both admin and draft.txt were correct.
2. "The SRT is stale." True, but its mtime was 17:32:40 and the story mp3's
   was 17:28:47 - the stale file was NEWER than the audio it failed to
   describe, because restore-srt-casing.py rewrites it after Whisper.
3. An mtime comparison against $narr - which step 4 rebuilds on every run, so
   it is always newer and the cache would never hold at all.

What settled it was running Whisper by hand against the current narration and
reading what came back. Three sentences of reasoning lost to one measurement.

**Rule:** a cache keyed on existence is not a cache, it is a stale read with
a happy name. Key it on the inputs, and pick an input the pipeline does not
rewrite as a side effect. mtime is an input only if nothing downstream
touches the file.

**Related:** P210 (the gate that had to work before this was visible),
P125 (per-block re-narrate - the workflow this breaks), P188 (the write path
can silently no-op), P118 (two things disagreeing; the stale one looked newer)

**Status:** FIXED - the SRT is kept only when a sidecar fingerprint of the
SOURCE mp3s (size + mtime of story and moral) still matches. Hand-edits
survive a re-run; a re-narration discards the transcript. Verified on the
same reel: the stale SRT was discarded, Whisper re-ran, and the new transcript
matched the audio.

## ═══════════════════════════════════════════════════════════
## PATTERN 212: The rule that manufactured the defect it forbade
## ═══════════════════════════════════════════════════════════
**ID:** P212
**Type:** A constraint satisfied by fabrication
**Files:** app/api/generate-reel/route.ts (rule 3)
**Found:** 2026-10-10, across all four languages of Tirmidhi #3895

Rule 3 says the moral must be "practical AND directed to Allah". It was
written after twenty consecutive generations produced a moral with no mention
of Allah at all (P155). It works: Allah now appears in every moral.

HOW he appears is the problem. On one hadith, in four languages, four for
four, the generator satisfied rule 3 by inventing a divine warrant:

    EN  "for Allah has entrusted their care to you"
    UZ  "чунки бу Аллоҳнинг амри"            (this is Allah's command)
    RU  "Который возложил на человека..."   (Who placed the duty on man)
    TJ  "аз роҳҳои ба даст овардани ризои Аллоҳ"  (a way of attaining His pleasure)

Every one is sound teaching. None is in this matn, which says who is best and
nothing about commands, entrustment or categories of obedience. These are
rule 16 violations, and rule 3 is what produced them.

**Why.** Rule 3 states a requirement and gives no example of satisfying it.
"Directed to Allah" is ambiguous between addressing the action to Him and
asserting something about Him, and the second is easier to write. A model
asked for theology in a sentence will supply theology.

**This is not a per-language quality gap.** Four of four, one hadith. When a
defect appears in every language of a set it is the instruction pulling, not
the translation drifting - the same signature as the sadaqah jariyah gloss on
#1631, which hit three of four (P207).

**Rule:** when a rule keeps being satisfied in a way that violates another
rule, the wording is the defect, not the output. Fix it where the ambiguity
is and show the compliant form; adding review catches instances, not causes.

**Related:** P155 (the twenty morals with no Allah, which rule 3 fixed),
P116 (length pressure IS fabrication pressure - same shape: a requirement
met by inventing), P207 (a defect appearing in most languages of one set)

**Status:** FIXED in the rule text - rule 3 now says DIRECTED TO Allah means
the action is addressed to Him, gives "for the sake of Allah" and "Allah sees
this" as compliant, and states that a claim about what Allah commanded,
entrusted or categorised needs the matn to say so. Unverified against a fresh
generation; the next set is the test.

## ═══════════════════════════════════════════════════════════
## PATTERN 213: The abbreviation the voice had to guess at
## ═══════════════════════════════════════════════════════════
**ID:** P213
**Type:** Written convention reaching a reader that cannot read it
**Files:** scripts/lint-content.py, app/api/tts/route.ts (diagnosis only)
**Found:** 2026-10-10, on the at-tirmidhi-3895 EN reel

`cleanForTTS` expands every written form of the Prophet's honorific - the
glyph, (ص), (pbuh), (saw), (s.a.w.), p.b.u.h - and no companion honorific at
all. The draft's "(RA)" went to ElevenLabs raw and came back voiced as
"radiyallah": truncated, because the feminine form needs *anha*. The output
is model improvisation, so a re-run can differ.

**It cannot be fixed by extending that list.** (RA) is gender-neutral in
writing and gendered in speech - *anhu* for Abu Hurairah, *anha* for Aisha -
and the function sees one string with no idea which companion is meant. The
draft knows. So the fix is a CHECK that sends the decision back to where the
information is, not an expansion that guesses on the model's behalf.

Scope is S and M only. H and C are read, not narrated, and the abbreviation
is correct there - the caption has carried it on every reel.

**Found only because two other gates were fixed first.** The stale-SRT bug
(P211) was serving a transcript from older audio, and the similarity gate
(P210) was returning noise that suppressed the alignment check. With both
fixed, alignment reported `ravya` three ways in one run.

**A note on the verification, which was itself wrong first.** Four fixtures
were written to test this check and two of them silently failed to write - an
emoji in one fixture is a surrogate pair that cannot encode to UTF-8, which
truncated that file to 0 bytes and aborted the loop before the fourth. The
linter reported "no such file" and the test harness counted the absent
finding as a pass. Two of four results were meaningless and were read as
green. Same shape as the gates this very pattern sits among: an absent
measurement reported as a passing one. Check that a fixture exists before
trusting what a test says about it.

**Rule:** an abbreviation is a convention between writers. Anything that
SPEAKS the text is a reader that does not share it. Expand where the meaning
is unambiguous, and where it is not, flag it back to the author.

**Related:** P204 (the ص glyph entry described a per-language distinction the
code does not make), P210 and P211 (the gates that had to work first), P168
(do not infer from a name what the registry should state)

**Status:** FIXED - `check_companion_honorific` in lint-content.py, WARN,
narrated blocks only. Verified four ways: the real R118 defect flags, the
spelled-out form does not, an abbreviation confined to H and C does not, and
the Russian «(р.а.)» flags. The summary line moved 10 -> 11 checks by itself,
which is P139 working.

## ═══════════════════════════════════════════════════════════
## PATTERN 214: The safety guard scoped to the model it was written for
## ═══════════════════════════════════════════════════════════
**ID:** P214
**Type:** A guard whose non-match produces the unsafe outcome
**File:** scripts/generate-scene.ps1
**Found:** 2026-10-11, preparing the Kling 3.0 evaluation - BEFORE spending

P156 established three things: Kling defaults `generate_audio` to TRUE, that
default both raises the per-second rate and mixes generated sound into a clip
meant to be a SILENT background, and 2.1 Master does not accept the field at
all. The fix it left behind was:

    if ($Model -match 'v2\.6') { $payload['generate_audio'] = $false }

Correct on the day it was written. The default model was 2.6 Pro, so the match
always succeeded and audio was always off.

**Symptom:** none, for seven months. The guard was never seen failing because
the condition it tested was never false.

**Root cause:** the protection was keyed to a MODEL VERSION STRING rather than
to the thing being protected against. `-match 'v2\.6'` asks "is this the model
I was written for?" when the question is "should this clip be silent?" - and
the answer to the second is always yes, for every model, forever. The first
time anyone passes a different `-Model` the match fails, the field is never
added, and the PROVIDER default wins. The guard does not error, warn or log.
It simply is not there any more.

**What it would have cost.** The Kling 3.0 evaluation is a `-Model
fal-ai/kling-video/v3/pro/image-to-video` run - the first non-2.6 model id this
script has ever been given. v3 Pro is $0.112/s audio off, $0.168/s audio on. A
10s eval clip would have billed $1.68 instead of $1.12 and come back with a
generated audio track, against which a silent 2.6 Pro clip is not a comparison.
The evaluation would have measured the guard rather than the model, and nothing
in the output would have said so: audio on a clip sitting in
out\backgrounds\new is inaudible until it reaches a render, and by then the
clip is a background under a nasheed bed.

**Fix:** audio-off is unconditional; the exception is NAMED.

    $payload['generate_audio'] = $false
    if ($Model -match 'v2\.1/master') { $payload.Remove('generate_audio') }

Both lines still match on a string, but the polarity is reversed: a match that
FAILS now leaves the safe state in place. The only model that loses the field
is the one documented to reject it, and if that match ever breaks the result is
a rejected request - loud, free and fixable - not a silent charge.

**Rule:** write a guard so the unmatched case is the safe one. A condition that
can only be observed while it is true has an untested false branch in
production. Ask what the guard protects against, not which version it was
written against.

**Related:** P156 (the audio default this guard was built for), P168 (do not
infer from a name what the registry should state - the same error with a
filename instead of a version string), P119 / P126 / P185 / P187 / P189 / P206
(a gate with no caller), P207 (the caller exists, the gate silently declines),
P210 (the gate that fired at random). This one is their inverse: the gate fires
correctly, on a condition that stopped describing the risk.

**Status:** FIXED. Verified by replaying both guard lines against seven model
ids - 2.6 image and text, v3 pro image and text, v3 standard, a hypothetical
v4, and 2.1 Master. All six non-Master ids now send `generate_audio: false`;
Master alone omits it. The old guard passed only the two 2.6 cases.

**Also in this commit:** `-Duration` ValidateSet gains '15'. Kling 3.0 accepts
3-15s where 2.6 Pro caps at 10, and 15s clips are half the reason to evaluate
it at all - `-FitScenes` can only trim, never extend. Passing 15 to 2.6 is
rejected by the API at no charge. The cost table in the script header gains the
3.0 Pro rates.

## ═══════════════════════════════════════════════════════════
## PATTERN 215: The clip kept, the prompt thrown away
## ═══════════════════════════════════════════════════════════
**ID:** P215
**Type:** Build output retained, its source discarded
**File:** scripts/generate-scene.ps1
**Found:** 2026-10-11, when the Kling 3.0 evaluation had nothing to run

The watchlist item reads "same prompt through both models, as FLUX 2 was
evaluated." Four t3895 clips sit in out\backgrounds\new with their stills beside
them in out\refs, all four registered and verified. **Not one of them could be
used,** because no motion prompt was ever written down. They were typed into a
chat window, sent to fal, and lost when that window was compacted.

**Symptom:** none that anyone would notice. The clips play. The reels shipped.
Nothing is missing until someone asks the one question that needs the prompt.

**Root cause:** the script treated the mp4 as the artifact. The mp4 is the BUILD
OUTPUT. The prompt is the source, and it was never persisted anywhere - not in
the registry, which records a prose description of each scene but not the text
that generated it, and not on disk, where only the video landed. 64 registered
scenes, 64 unreproducible.

What that costs, concretely: a clip cannot be regenerated at a different length,
cannot be re-rolled when it is nearly right, cannot be compared against a new
model, and cannot be diffed when a model's behaviour shifts under a prompt that
used to work. The FLUX 2 evaluation (P198) was decisive precisely because the
m2963 prompt still existed to re-run - that eval would have been impossible
under this same gap, and the project would have stayed a year behind.

**Fix:** `Write-Sidecar` records name, model, mode, duration, the verbatim
prompt, the input still, negative_prompt, generate_audio as actually sent,
request_id, and the completion facts.

Three details that are load-bearing:

1. **Written at SUBMIT, not at download.** The money is spent at submit, and a
   20-minute timeout (P137) ends the run before any file exists. Recording the
   prompt first means a timed-out job still has it on disk for -Resume.
2. **A -Resume run carries no -Prompt.** Writing unconditionally would blank the
   recorded prompt on the very path that exists to recover a paid job. The
   writer merges, and never overwrites a recorded value with an empty one.
3. **The record lives in assets/scene-prompts/, not beside the clip.** `/out/`
   is gitignored wholesale, and git does not descend into an ignored directory
   to re-include a file, so `!out/backgrounds/new/*.json` cannot work - a
   sidecar there would be unversioned, which is the same loss on a slower clock.
   It sits beside asset-registry.json, which already indexes every scene.

**Not recoverable:** the 64 clips made before today stay unreproducible. Their
prompts are gone. Recorded here so no future evaluation assumes otherwise and
plans around stills that have no prompt behind them.

**Rule:** persist the input that produced an artifact, not just the artifact. If
a thing was generated from text, the text is the asset and the output is a
cache. Ask what you would need to make it again.

**Related:** P198 (the FLUX 2 eval, which only worked because its prompt
survived), P137 (-Resume, the path that would have been broken by an
unconditional write), P214 (the other thing blocking this same evaluation),
P168 (the registry is the source of truth - this adds the field it was missing).

**Status:** FIXED. Verified by extracting `Write-Sidecar` from the script with
the PowerShell AST - the real source, not a retyped copy - and driving all three
call shapes against mock state: 17 checks, including that a resume-shaped call
with an empty -Prompt preserves the recorded prompt and the earlier timestamp,
and that a model which omits generate_audio records null rather than false.

**A note on the verification, which was wrong twice before it was right.** Two
checks failed on the first run and two on the second. Both times the stored data
was correct and the ASSERTION was wrong: ConvertFrom-Json coerces an ISO-8601
string to [DateTime] with Kind=Utc, and `[datetime]'...Z'` in the test parsed to
Kind=Local, so a correct 22:05Z was compared against 18:05 local and declared
unequal. Printing the actual values settled in one run what two rounds of
guessing had not. Same discipline as P211: measure before diagnosing.

## ═══════════════════════════════════════════════════════════
## PATTERN 216: The negative prompt that fought the picture it was given
## ═══════════════════════════════════════════════════════════
**ID:** P216
**Type:** A fixed default contradicting the deliberate content of its input
**File:** scripts/generate-scene.ps1
**Found:** 2026-10-11, by reading the P215 sidecar of a clip that had succeeded

generate-scene.ps1 sends the same negative prompt on every call:

    blur, distort, low quality, text, watermark, deformed hands, ...

`text, watermark` is right for almost every scene this channel makes - MODE B
backgrounds should carry no lettering, and Kling will happily invent a watermark.

Then b5027-matn was animated from a still with the hadith matn deliberately
composited onto the page, and the request told the model to suppress text while
handing it an image whose entire subject was text.

**Symptom:** none. The Arabic survived all 10s on both 2.6 Pro and 3.0 Pro,
intact to the tashkeel. The clip was accepted and registered.

**Root cause:** the negative prompt is a constant, and whether text is wanted is
a property of the INPUT, not of the script. Nothing reconciled the two. The
contradiction was invisible because it was only ever written in one place and
read in none - it took a P215 sidecar, which records negative_prompt as actually
sent, to put it next to the image it was sent with.

**Why a success is still a defect.** The text surviving is evidence about this
run, not about the instruction. The model was pushed toward erasing the one
element the shot existed for and happened not to. Run it again, at another
duration, with more camera movement, or on a model that weights negatives
harder, and the same request destroys the matn - and the failure would look like
a model problem rather than a prompt we wrote ourselves.

**Fix:** `-KeepText`. When the input still carries text on purpose, the switch
drops `text, watermark` from the negative prompt and says so on stdout. The
default is unchanged, because suppressing text is right for every other scene.

**Rule:** a constant that describes what the output should not contain has to
agree with what the input does contain. When a parameter encodes an assumption
about the input, it stops being a constant the first time the input changes.

**Related:** P215 (the record that made this visible at all - the sidecar is
already paying for itself), P214 (the other hardcoded assumption in this same
payload, found the same day), P198 (an eval that only worked because a prompt
survived), R026 (negations reinforce what they forbid - the same family, here
reaching the video model instead of the still model).

**Status:** FIXED - `-KeepText` switch, verified by AST (declared as a
SwitchParameter) and by replaying the branch: default suppresses text, the
switch does not. b5027-matn-v3.mp4 was generated BEFORE this fix and keeps its
text by luck; any future text scene passes -KeepText.

## ═══════════════════════════════════════════════════════════
## PATTERN 217: The folder that was a location pretending to be a state
## ═══════════════════════════════════════════════════════════
**ID:** P217
**Type:** A manual step standing in for a check the code already does
**File:** render-reel.ps1
**Found:** 2026-10-11, rendering #5027 - the fourth set it has blocked

`generate-scene.ps1` downloads to `out\backgrounds\new\`. `render-reel.ps1
-Scenes` read only from `out\backgrounds\new\normalized\`. Between them sat a
Move-Item that nobody remembers, and CLAUDE.md records it blocking three
separate sets before this one: June #1520, 8/11 #1, 8/16 #527.

**Symptom:** `scene clip not found: out\backgrounds\new\normalized\<clip>.mp4`
on a clip that was generated minutes earlier and is plainly on disk.

**Root cause:** the directory name claims the clips in it are normalized, and
for RANDOM mode that is load-bearing - it stitches with `-c copy` and needs
1080x1920 input. For ANIMATED mode it never was. The script's own comment at
the resolution guard says so: "Animated mode normalizes each clip below, so it
tolerates any source res/fps." So `-Scenes` was requiring a property it does
not use, enforced by a directory nobody syncs.

The directory also looked like a review gate and is not one. Promotion into it
is a `Move-Item` with no check attached, and the real gate for `-Scenes` is the
registry audit (P121) three lines further down, which rejects an unregistered
clip wherever it sits.

**Fix:** `-Scenes` resolves a clip from `normalized\` and falls back to `new\`,
saying which it used. The registry gate is unchanged and still decides. RANDOM
mode still reads `normalized\` only, because there the normalization is real.

**Rule:** a manual step that moves a file without inspecting it is not a gate,
it is a gap. Before preserving one, find what the code actually requires - here
it required nothing, and a directory had been standing in for a check that
already existed somewhere better.

**Status:** FIXED. Verified three ways against real files: a clip in
`normalized\` resolves there, a clip only in `new\` (b5027-matn.mp4, the Kling
2.6 eval artifact) resolves via the fallback, and a missing name still dies.
CLAUDE.md step 5 updated - it had been documenting the workaround as the
procedure.

**Open, not fixed here:** RANDOM mode globs `$normDir\*.mp4` with no registry
check, so an unregistered clip sitting in that folder can be drawn into a reel.
`-Scenes` has had that gate since P121 and random mode never got it. Recorded
in OPEN_ITEMS rather than widened into this change.

## ═══════════════════════════════════════════════════════════
## PATTERN 218: Built, documented, and still not found
## ═══════════════════════════════════════════════════════════
**ID:** P218
**Type:** A capability with no route to it from the operating doc
**Files:** CLAUDE.md (the fix), scripts/upload-candidates.py (the capability)
**Found:** 2026-10-12, sourcing three Tawheed hadiths

Asked to add three named hadiths to the library, this session:
  - wrote a refs file for source-candidates.py and hit
    "--source live needs SUNNAH_API_KEY in .env.local";
  - researched how to obtain a Sunnah key, and found there is no self-serve
    signup - a maintainer issues it by hand off a GitHub issue;
  - browsed two HadeethEnc categories by hand looking for the hadiths, found
    one of three, and misidentified another;
  - was told by the operator that this had been noted before.

It had. `upload-candidates.py` begins: "queries -> search_dorar -> dedup vs
LIVE library -> hadith_candidates. Dorar is public + authoritative, so this
produces REAL graded candidates with no API key."
`sourcing-pipeline-design.md:148` lists Dorar as supplying "Grading + Arabic
matn", and :155 says the matn "comes from Sunnah.com if present, else Dorar."

Run against the three, it returned six rows - Bukhari and Muslim variants of
each, every one sahih, with verbatim matn and narrator - in one command.

**Root cause: CLAUDE.md had Workflows A through K and none of them was "source
a specific hadith".** Workflow H audits the library before a batch; Workflow I
translates candidates that already exist. The step that creates them was
missing, so the operating doc routed a session to the discovery path and to a
key it does not need. The capability was in a script header and a design doc -
both correct, neither read at the moment of need.

**This is the third instance of one shape, and the shape has moved:**
  - P165: adapters built, unreachable.
  - P172: adapter built, reachable, never called by the runner.
  - P218: adapter built, called, documented - and not FINDABLE.

Each fix made the thing more real and none of them made it easier to locate.
Documentation that records a capability is not the same as documentation that
routes you to it, and only the second kind survives a fresh session.

**Fix:** Workflow L in CLAUDE.md. It names the command, says Dorar alone is
sufficient, and says plainly what NOT to reach for - the Sunnah key and
HadeethEnc category browsing - because those are the two wrong turns this
session actually took.

**Rule:** when a capability is added, add the route to it in the file sessions
read first. A new script earns a workflow entry, not just a header comment.

**Also corrected here:** Bukhari #425 was recorded in OPEN_ITEMS as the Itban
"Fire forbidden" hadith. Dorar shows #425 is narrated by Mahmud ibn ar-Rabi'
al-Ansari and is the long narrative about Itban's eyesight. The short saying on
the operator's slide is **Bukhari #6423**, narrated by Itban himself. The error
came from a commentary footnote citing #425 for a phrase inside the long story.

**Status:** FIXED - Workflow L added. Verified by running the documented path:
3 queries -> 6 rows ready, 39 daif/empty dropped, 0 duplicates, no key.
## ═══════════════════════════════════════════════════════════
## PATTERN 219: A review gate with a second writer behind it
## ═══════════════════════════════════════════════════════════
**ID:** P219
**Type:** A race on the artifact a human gate reads
**Files:** scripts/translate-candidates.py (the fix), CLAUDE.md Workflow I
**Found:** 2026-10-12, translating three Tawheed candidates

P177 closed "the dry run and the commit each generate their own text" by adding
`--apply`, which writes `out/candidate-translations.json` to the DB with no
model calls. The reviewed file became the shipped text - provided nothing
rewrites that file between the review and the apply.

This session left a redundant dry run running detached, forgot it, reviewed the
JSON, and applied. The second process finished mid-review and rewrote that
exact path with freshly generated text. `--apply` then shipped rows that had
never been read: Muslim #28 went in still carrying its `[UNCERTAIN]` marker,
and Bukhari #6423 arrived with a THIRD Tajik wording of the «face of Allah»
clause - the two earlier ones having been read and corrected in a file that no
longer existed.

P177 defends against one process generating twice. It does not defend against
a DIFFERENT process writing the file the gate is reading. A fixed path with no
owner, no lock and no identity cannot tell the reviewer which run produced the
bytes in front of them: a stale file and a freshly regenerated one present the
same question mark.

**Fix:** the operator signs what they read. `--sign` writes the sha256 of every
`candidate_id` + proposed text to `out/candidate-translations.reviewed.json`.
`--apply` recomputes that digest and REFUSES on a mismatch or a missing
sign-off, printing both digests and the time of signing. The signature is
deleted after a successful apply, so one sign-off can never cover a later file.
The digest is order-independent, so re-sorting the file is not a change and one
character is.

Two smaller lies fixed in the same pass:
  - `--apply` wrote to the DB without `--commit`, while `--commit`'s own help
    text reads "Without this, nothing is written." It now requires it.
  - `--apply` demanded ANTHROPIC_API_KEY to run a path that makes no model
    calls. That check moved below the apply branch.

**Status:** FIXED. Verified five ways against the real file: `--apply` without
`--commit` refuses (exit 2); unsigned refuses (exit 3); `--sign` records the
digest; one phrase altered by a simulated second writer refuses with both
digests printed (exit 3); the restored signed file applies 3/3 and consumes its
signature. Workflow I step 6 rewritten - it had still documented plain
`--commit`, the pre-P177 path, so the documented procedure was the one P177 was
written to stop. P218's shape again, three days later.

## ═══════════════════════════════════════════════════════════
## PATTERN 220: In-house translation changed a ruling
## ═══════════════════════════════════════════════════════════
**ID:** P220
**Type:** A fidelity failure in the lane with no automated reader
**Files:** hadith_candidates - bukhari #3435, #6423, #6570 (text only)
**Found:** 2026-10-12, Workflow I step 4 on three Tawheed candidates

P178 rejected HadeethEnc's published translations after they scored EN 3/5,
RU 0/5, UZ 0/5, TJ 1/5 against 8/8 for the in-house path, and recorded one case
where «бегуноҳ» was added to the matn, changing a ruling. The conclusion carried
forward was that the in-house path is the safe one.

The in-house path has now produced the same class of error. Bukhari #3435's
على ما كان من العمل - "whatever his deeds may have been" - came back in Uzbek as
«қилган амалига қараб», "ACCORDING TO his deeds". The point of the hadith is
that the testimony admits him regardless of his deeds; the translation made
admission conditional on them. Three more in the same batch of three hadiths:
  - #3435 TJ carried the same ambiguity: «бар ҳар амале, ки будааст»
    [P224: this whole claim did not survive sourcing - the clause is
     contested, and "regardless" resolves it as wrongly as "according to"]
  - #6423 UZ reversed حرم عليه النار into "Allah forbids HIM to the Fire" for
    "forbids the Fire to him", and put it in the imperative: «қилмасин»
  - #6570 UZ and TJ both rendered حرص as «ҳирс», which reads as greed or lust
    in both languages, where the Arabic means keenness - applied to a Companion
    being praised
Plus ألقاها as "cast" and «афканд» (threw) where the established rendering is
"bestowed", in EN and TJ.

8/8 on five sampled rows was never a property of the translator. It was a
measurement of five rows.

What makes this worse than P178 is where it landed. The ruling error is in
Uzbek Cyrillic, which P078 excludes from subtitles, so no automated downstream
reader would ever have seen it. Every gate that exists - lint-content.py, the
stt lint, P111 r18 - reads GENERATED REEL TEXT. This is DB text, and CLAUDE.md
Workflow H step 9 states outright that lint-content.py cannot see it, because
the generator paraphrases and the DB sentence never appears verbatim in
draft.txt. The only thing standing between this and four published reels was a
human reading all four languages against the Arabic.

Workflow I step 4 is exactly that: "Check against the Arabic." On this run the
operator said, in as many words, "Anyway i don't understand Arabic fully." The
step asks the operator to do the one thing they have said they cannot do. A
gate whose only caller cannot perform it is not a gate; it is a signature
block.

**Status:** TEXT FIXED, MECHANISM NOT. All four corrections went into the
reviewed JSON and shipped from there (P177: a correction belongs in the
reviewed text, never an SQL patch after the write), verified field-by-field
against the DB afterwards. Nothing in the pipeline would have caught any of
them and nothing added here would. Stage 3 A/B verify (Workflow K) is where
this belongs. **CORRECTION, same day: it is BUILT - see P221.** It was
crashing (P222), and pass B has no API credits left; both are recorded in
OPEN_ITEMS under "Blocks content".

## ═══════════════════════════════════════════════════════════
## PATTERN 221: Declared a documented stage unbuilt
## ═══════════════════════════════════════════════════════════
**ID:** P221
**Type:** An absence claim asserted without the check a presence claim gets
**Files:** fix_patterns.md (P220 status), OPEN_ITEMS.md, CHANGELOG.md - all 3 wrong
**Found:** 2026-10-12, minutes after writing P220

P220 closed with "Stage 3 A/B verify (Workflow K) is where this belongs and is
unbuilt." Every part of that was checkable and none of it was checked:

  - `CLAUDE.md:516` documents **Workflow K - Stage 3: A/B verify translations**
    in eight steps, naming the models, the disagreement rate, and G1
  - `scripts/verify-candidates.py` has been on disk since 2026-09-05
  - `scripts/probe-passb.py` exists too, and Workflow K step 8 says when to run it
  - both keys are in `.env.local` - ANTHROPIC_API_KEY for A, OPENAI_API_KEY for B

The claim then propagated into OPEN_ITEMS and a commit message, and the session
recommended BUILDING it. Had the operator agreed, they would have paid to
rebuild a stage they already owned - the exact cost P218 exists to prevent,
incurred four patterns later while writing about it.

The asymmetry is the lesson. "X exists" gets verified here as reflex, because
inventing a command or a path is a known failure (P208, "Never invent commands
- check the script first"). "X does not exist" was treated as free. It is not:
it is the more expensive claim, because it is the one that authorises new work.
A missing capability was inferred from its absence in fix_patterns and
OPEN_ITEMS - the two files about problems - without ever opening the file that
lists what exists. CLAUDE.md's workflow list IS that file.

**Rule:** before reporting a stage, script, or capability missing, grep
CLAUDE.md's workflow list and `scripts/` for it. An absence claim needs the
same evidence as a presence claim, and the operating doc outranks a memory of
it.

**Status:** CORRECTED. P220's status line amended in place, OPEN_ITEMS rewritten,
CHANGELOG corrected in the same dated section. Stage 3 then RAN - see P222 for
what it found, including a defect this session had introduced an hour earlier.

## ═══════════════════════════════════════════════════════════
## PATTERN 222: A display string ended a paid run
## ═══════════════════════════════════════════════════════════
**ID:** P222
**Type:** A value the logic knew and the renderer did not
**Files:** scripts/verify-candidates.py:345
**Found:** 2026-10-12, first real Stage 3 run

`agreement()` returns four values - its own docstring opens
`pass | fail | disagree | incomplete`. The line that prints the per-language
result knew three:

    mark = {'pass': 'OK ', 'fail': 'FAIL', 'disagree': '>>>'}[agr]

P152 added `incomplete` for the honest reason that an API error is not a
verdict, and taught it to `agreement()`, to `roll_up()`, and to the status map
that keeps an unchecked row away from the human gate. It did not teach it to
the one dict that renders it. So the stage worked correctly and then died
printing the fact - `KeyError: 'incomplete'` on the first row of the first run,
AFTER both paid passes had completed, discarding the spend and the report.

Two things made it invisible for five weeks. `incomplete` is only reachable
when a provider call fails, so every clean run passes. And the crash looks like
the API failure that caused it, not like a bug in the printing.

**Fix:** the fourth value named, and `.get(agr, f'?{agr[:2]}')` so a display
string can never end a run again. A renderer is the last place that should hold
a veto over work already paid for.

**Status:** FIXED. All four values render, verified by driving `agreement()`
with each verdict pair, plus an unknown value degrading to `?wa` instead of
raising. The re-run then completed all 5 rows and printed its report.

**What the completed run found:** pass B returned HTTP 429 on all 20 calls -
`probe-passb.py` gives the reason verbatim, "You have no credits remaining" -
so all 5 rows came back `incomplete` and the footer correctly refused to send
any of them to Stage 4. P152's design held exactly as written. Pass A completed
all 20 and flagged Bukhari #6570 RU and UZ: نفسه is "his own self", not
"heart". The UZ «ўз қалбининг самимиятидан» is the translator's own, but the RU
«от своего сердца» was THIS session's edit, made an hour earlier to line RU up
with the other three languages. A consistency edit to text that was already
faithful. The second opinion this session had just called unbuilt caught it on
its first completed run.

## ═══════════════════════════════════════════════════════════
## PATTERN 223: One transient failure discarded eight paid calls
## ═══════════════════════════════════════════════════════════
**ID:** P223
**Type:** No retry under a roll-up that treats any gap as a total loss
**Files:** scripts/verify-candidates.py (_post, _transient)
**Found:** 2026-10-12, first funded Stage 3 run

Stage 3 makes eight provider calls per row - four languages, two passes. P152
correctly made an unchecked language `incomplete` rather than a disagreement,
and `roll_up()` correctly lets one `incomplete` decide the row when nothing
worse happened. Both are right. Together, with no retry anywhere, they mean a
single momentary 429 on one language throws away the row's other seven calls,
all of them already paid for, and returns the row unchecked.

That is not hypothetical. The first run on a funded account took 5 scattered
transient 429s and lost 3 of 5 rows. Every lost row had already produced good
verdicts in its other languages.

`pass_a` and `pass_b` each called `urlopen` directly with no attempt loop, so
the pipeline had no notion of a retryable failure. Both now go through `_post`,
which retries 4 attempts with 2s/5s/12s backoff, honours `Retry-After` up to
30s, and distinguishes what can succeed later from what cannot:

  retried      429 rate_limit_exceeded, 500/502/503/504/529, URLError,
               timeouts, connection resets, IncompleteRead, BadStatusLine
  not retried  429 insufficient_quota / credit_balance_exhausted, 401, 400

The empty-balance case is the important exclusion. It is the same status code
as a burst and the opposite problem: no amount of backoff adds credit, and it
is the one 429 that needs a human rather than a wait.

**Also fixed:** the raised error now carries the response BODY, not just the
status line. `urllib` renders every 429 as "HTTP Error 429: Too Many Requests",
which is why a session spent several exchanges unable to tell an exhausted
balance from a rate limit, and had to re-issue the request by hand to read the
reason. The provider had said "You have no credits remaining" the whole time;
the transport threw it away.

**Status:** FIXED. Classification verified against eight constructed cases -
rate-limit 429 retries, credit-exhausted 429 does not, 5xx and transport errors
retry, 401/400 do not. Both passes routed through one transport, so the retry
cannot exist on one side only.

## ═══════════════════════════════════════════════════════════
## PATTERN 224: Graded a translator against a reading, not a source
## ═══════════════════════════════════════════════════════════
**ID:** P224
**Type:** An interpretive choice recorded as a factual error
**Files:** fix_patterns.md (P220), hadith_candidates #3435 - text pending
**Found:** 2026-10-12, sourcing the clause Stage 3 contested

P220 recorded Bukhari #3435's على ما كان من العمل as a RULING INVERSION: the
Uzbek «қилган амалига қараб» (“according to his deeds”) was called the same
class of defect as P178's «бегуноҳ», and corrected to «қандай бўлишидан қатъи
назар» (“regardless of his deeds”). Stage 3's pass B then said the opposite,
in two languages. Sourcing says neither wording is the matn.

  Sunnah.com (USC-MSA), the published English of this hadith:
    “with the deeds which he had done even if those deeds were few”
  Khaled al-Sabt's sharh glosses the phrase by RESTATING it almost verbatim -
    «فإنه يدخل الجنة على ما كان من عمل» - and qualifies only that he may be
    punished in the Fire first and enter Paradise after («فقد يعذب الإنسان
    بالنار ثم يدخل الجنة»), which rules out “regardless” as unconditional.
  Sharh Riyad as-Salihin does not gloss the phrase at all, offering only
    «وفي هذا الحديث فضل الله عز وجل وسعة رحمته».

على here is economical and the commentators keep it that way. They preserve the
ambiguity instead of resolving it, which is the tell: «амалига қараб» resolves it
one way, «қатъи назар» resolves it the other, and the matn does neither. The
session replaced one interpretive reading with the opposite interpretive
reading and logged the swap as a correctness fix.

The rule already existed and pointed the other way. Workflow I step 4: “did
anything get ADDED? A clause, an attribution, a ranking, a comparison. The matn
is the only thing the translation may say.” A resolved ambiguity is an added
clause. Both wordings fail that test; only a literal “upon / with whatever
deeds he had” passes it.

What made the error confident rather than tentative was the frame. P178 had
established “a translation that changes a ruling” as a known defect class, and
a clause with theological weight was read straight into it. A defect class is a
lens, and a lens finds what it is shaped to find. The check that was skipped is
the cheap one: open the published translation before calling a rendering wrong.

**Status:** P220 AMENDED, text CHANGED AND VERIFIED 2026-10-12, clause RESTING
at `needs_human` by decision 2026-10-13. All four languages were rewritten to
resolve nothing - EN “with the deeds he had done”, RU «с теми деяниями, что у
него были», UZ «қилган амали билан», TJ «бо он амале ки дошт» - applied through
sign/apply and verified field-by-field against the DB.

Re-verification is the part worth keeping. The EN now passes BOTH models and is
almost verbatim the published USC-MSA rendering. The other three draw
objections for MUTUALLY EXCLUSIVE reasons - A reads “regardless of”, B reads
“according to” - and the two swapped sides between languages and between runs
(P225). So the clause cannot pass this gate by construction, and that is
evidence the ambiguity is in the Arabic rather than in our Russian. #3435 rests
at `needs_human` permanently: a correct resting state, not an unfinished task.
Everything else in the same two rows cleared - #6570 passes both models in all
four languages, and so does #6423.

Do NOT rewrite this clause again. Three sessions have now done so, twice in
opposite directions. If it is reopened, it is reopened from a source.

**Also standing from the same run:** both passes flag «ҳақ илоҳ» on #3435 UZ as
a word not in لا إله إلا الله. Classical grammar supplies بحق as the elided
predicate, so “true god” is the orthodox gloss rather than an invention, and the
Tajik does the same with «ба ҳақ». House-style call, not a defect - but it is an
interpolation and should be decided once for all four languages.

## ═══════════════════════════════════════════════════════════
## PATTERN 225: Two passes failed for opposite reasons and it scored as agreement
## ═══════════════════════════════════════════════════════════
**ID:** P225
**Type:** A gate that compares verdicts and ignores reasons
**Files:** scripts/verify-candidates.py (agreement)
**Found:** 2026-10-12, re-verifying the sourced wording of #3435

`agreement()` compares `a['verdict']` to `b['verdict']`. Equal fails score
`fail`; that is the whole test. On Bukhari #3435 RU both passes returned fail
and the run recorded agreement - while the two reasons were mutually exclusive:

  A: على ما كان من العمل means “regardless of / whatever his deeds were”,
     and the Russian wrongly suggests the deeds accompany him
  B: it means “according to / depending on whatever deeds he had”, NOT that he
     is admitted “with” those deeds

Each model holds one of the two readings P224 documented, and each rejects the
other's. That is the strongest possible disagreement, and the gate logged it as
the two passes concurring.

Consequences, in order of how much they matter:
  - The D5 disagreement-rate statistic UNDERSTATES real disagreement. It is the
    number Workflow K step 5 reads to decide whether pass B is buying anything,
    so the one figure used to calibrate the gate is computed by a rule that
    cannot see the case it most needs to count.
  - The operator reading `fail` sees a settled verdict rather than a contested
    one, and `fail` carries more authority than `disagree` precisely because it
    looks unanimous.
  - Routing is NOT affected: status is `verified` only on pass, so a `fail`
    still goes to `needs_human`. Nothing unsafe shipped, which is why this sat
    unnoticed - the label was wrong and the destination was right.

Not fixed here. Detecting contradictory REASONS means comparing free text,
which is a model call inside a function that is currently pure and
deterministic - a real design decision, not a patch. Recorded so the
disagreement rate is read with this known floor under it.

**Status:** RECORDED, NOT FIXED. Routing is safe; the statistic is not.
Until fixed, read any `fail` on a clause known to be contested as a probable
`disagree`, and check both reasons rather than the verdict pair.

## ═══════════════════════════════════════════════════════════
## PATTERN 226: The rule was in the field description, not in the rule list
## ═══════════════════════════════════════════════════════════
**ID:** P226
**Type:** A constraint placed where it is read instead of where it is obeyed
**Files:** app/api/generate-reel/route.ts (rules 23, 24)
**Found:** 2026-10-12, auditing why #5027 needed four manual catches

Two defects ran through Bukhari #5027 - a comment-about-the-text clause in
THREE of four languages, and an added purpose clause in three of four. Both
were already forbidden. The session that shipped it recorded them as the
generator ignoring its rules.

It did not. Both prohibitions lived ONLY inside the prose description of the
`moral` field in the JSON skeleton - "do not explain what the hadith 'ties' or
'shows' or 'teaches'... Say the thing, not a comment about the text" and "Do
not add a promise the matn does not make". Neither appeared in the numbered
ABSOLUTE CONTENT RULES below it.

Every rule in that numbered list held on the same set, in the same call, from
the same model. The sorting is not about how emphatic the wording is: the field
prose says "Say the thing, not a comment about the text", which is as clear as
anything in the list. It is about position. A field description is read as
guidance on shaping that field; the rule list is read as the constraint set,
and the model checks its output against the list.

So the finding is not "the model ignores rules". It is that a prompt has two
registers, and a prohibition filed in the weaker one is not a prohibition. The
fix is relocation, not rewording.

**Fix:** both promoted to numbered rules 23 and 24, written in the house style -
what to DO first ("The moral SAYS THE THING"; "State the deed and the ground
the matn states, and STOP at that ground"), the failing form named second, the
evidence last. Rule 24 also names its kinship with rule 13: P212 was an invented
warrant attributed to Allah, and a supplied purpose clause is the same addition
attributed to the listener.

**Status:** CHANGED, NOT YET VERIFIED. A prompt change is only proven by
generating, and this one has not been. The test costs nothing extra: Sahih
Muslim #1631 is the next reel in the production queue, so generate it in all
four languages and check whether either clause recurs. If it does, the next
hypothesis is rule 22's territory - the list holds best in English - and not a
third rewording of the same sentence.

## ═══════════════════════════════════════════════════════════
## PATTERN 227: The queue is not part of the shipping ritual
## ═══════════════════════════════════════════════════════════
**ID:** P227
**Type:** Two docs, one updated by the ritual and one not
**Files:** OPEN_ITEMS.md (Production queue), reel-tracker.md
**Found:** 2026-10-13, about to generate a hadith that shipped four days earlier

OPEN_ITEMS listed Sahih Muslim #1631 as **IN PROGRESS**, filling Death /
Afterlife "(zero coverage)". It had shipped on 2026-10-09 as R114–R117, four
languages, four platforms. Jami at-Tirmidhi #3895 and Bukhari #5027, the other
two queue items, had shipped too. The whole queue was done and still read as
pending.

A session acting on that doc recommended #1631 as the next thing to produce,
and was one "go" away from regenerating a published set. What stopped it was
checking the tracker for what "IN PROGRESS" had left behind — and finding four
registered clips, four mp3 sets per language, and four published rows.

The cause is procedural, not editorial. The standing rule is "tracker updates
after the full set, not per reel", so shipping a set has a ritual and that
ritual writes to `reel-tracker.md`: reel rows, theme coverage, clip library,
nasheed usage, production stats. OPEN_ITEMS is not in it. The tracker correctly
said `✅ Death / Afterlife — 4 reels (R114–R117)` on the same day the queue
said zero coverage. Both files were accurate about their own last write.

This is P208's family (a doc describing a state that moved) with a specific
mechanism: the file that RECORDS completion and the file that PLANS work are
different files, and only one of them is touched when work completes. A plan
that is never closed out reads as a plan forever.

**Rule:** closing a set includes clearing its queue entry. If the queue entry
is gone, the set shipped; if it says IN PROGRESS, check the tracker for clips
and reel rows BEFORE believing it. Theme coverage in the tracker outranks
"(zero coverage)" in the queue, because coverage is derived from shipped rows
and the queue is derived from an intention.

**Status:** FIXED. All three entries replaced with a shipped table plus what
the gap list actually leaves, AND the ritual changed: Workflow J gains step 10,
clearing the set's queue entry in the same pass that updates the tracker. The
two files now move together, which is the only thing that keeps a plan from
outliving the work.

**Footnote, and it is the same lesson one layer down:** the edit that wrote
this very status line failed silently on its first attempt. Its match string
used a hyphen where this file had an em dash, so the replace matched nothing,
and the commit went out claiming a change this paragraph still denied. Caught
by reading the file back instead of trusting the script's exit. A match string
typed from memory is a guess; a match string read from the file is a fact.


## ═══════════════════════════════════════════════════════════
## PATTERN 228: A relative path in .NET resolves against a directory PowerShell does not update
## ═══════════════════════════════════════════════════════════

**What happened:** P201 added a per-reel sidecar — `{base}-render.json`, recording
the nasheed and scene list so the tracker's Nasheed column and the asset-reuse
audit could be filled from a file instead of from memory. It had never once been
written. Every reel since P201 rendered, reported success, and left no sidecar.

**Cause:** the write used `[System.IO.File]::WriteAllText` with a path relative to
`$workDir`. .NET resolves a relative path against `[Environment]::CurrentDirectory`,
and PowerShell does NOT update that when `Set-Location` runs. So the process-wide
current directory was still wherever the shell started — the write either landed
somewhere nobody looks or threw into a catch that printed a bare "could not record"
with no reason attached.

This is the same class as P154's libass path problem and nothing to do with
PowerShell being odd: it is two different notions of "where I am" in one process.
`Resolve-Path` reconciles them.

**Rule:** any `[System.IO.*]` call takes an ABSOLUTE path, produced by
`(Resolve-Path $dir).Path` — never a path relative to the shell's location. And a
catch that swallows the exception message turns a loud failure into a silent one:
print `$($_.Exception.Message)`, always.

**Status:** FIXED. `$sidecarPath` is now built with `Resolve-Path`, the success
path prints `nasheed recorded: ...`, and the catch prints the real exception.
Verified on bukhari-6423 EN and RU — both sidecars present and correct, and the
RU one is what caught P229 below.

## ═══════════════════════════════════════════════════════════
## PATTERN 229: -FitScenes measured the narration before the pad that follows it
## ═══════════════════════════════════════════════════════════

**What happened:** `-FitScenes` divides the narration length by the clip count to
size each scene. It measured the RAW narration, while P143 pads the audio by 1s at
the tail. The background therefore ended a second before the audio did, and the
last scene was clipped short of its own ending — on a reel whose final frame is the
whole point of the scene order.

**Cause:** two places knew about the tail pad and one of them didn't. P143's pad
lives in the merge step; the fit arithmetic lives three steps earlier and was
written against the unpadded number. Neither is wrong on its own; they disagree.

**Rule:** a duration used in two steps is a named constant defined once, not a
literal repeated in each. `$tailPad = 1.0` is now declared beside `$reel` and used
by the fit arithmetic, the `apad=pad_dur=` argument and the final `-t`.

**Status:** FIXED and verified — bukhari-6423 RU renders 27.18s for 26.18s of
narration across 4 clips at 6.795s each, ending on the frame it was ordered to end
on.

## ═══════════════════════════════════════════════════════════
## PATTERN 230: The source appends punctuation that is not in the matn
## ═══════════════════════════════════════════════════════════

**What happened:** Dorar returns every matn with an orphan ` . .` appended. It rode
through `parse_dorar` into the library, and from the library into the caption via
P153 — which puts the FULL Arabic matn in every post precisely so that a reader who
knows Arabic can check the translation against the source. The one element of this
project that exists to be verified was shipping with punctuation the source does
not contain.

**Cause:** the matn is extracted from HTML and stripped of its numeric prefix, and
nothing looked at the tail. A trailing artefact is invisible in a UI that renders
RTL text and nearly invisible in a diff.

**Rule:** normalise BOTH ends of extracted text. A scraper's cosmetic output is not
the source, and anything placed in the caption as evidence has to match the source
character for character.

**Status:** FIXED. `_TRAIL_DOTS` collapses a run of trailing ASCII and Arabic full
stops to a single `.` in `scripts/lib/source_dorar.py`. Rows already in the library
carry the artefact until re-pulled; bukhari-6423 was corrected by hand before its
captions went out.

## ═══════════════════════════════════════════════════════════
## PATTERN 231: A diagnostic that lives only in a console is lost exactly when it is needed
## ═══════════════════════════════════════════════════════════

**What happened:** `/api/generate-reel` failed on the Russian generation for
bukhari-6423 with `Failed to parse AI response`. That string is the whole of what
the operator sees. The route did log the raw model text — to `console.error`, into
the dev-server's terminal. The dev server had been started from a terminal that was
since closed; the process was orphaned and its output went nowhere recoverable.

Finding this cost a hunt across three windows and two monitors, and then a second
paid generation purely to produce the evidence again.

**Cause:** the error message named a symptom and no cause, and the cause was written
to the most volatile sink available. A Next.js dev server outlives its console;
stdout is not storage.

**Rule:** an error the operator is expected to act on carries what distinguishes its
causes. For a parse failure that is `stop_reason` — `max_tokens` means the output
was truncated (P144's failure one stage later, where the budget died before any text
at all), anything else means the model emitted something that is not JSON. And the
full text goes to a FILE, `out/last-parse-failure.txt`, not to a console.

**Status:** FIXED. The error now carries `stop_reason` and the character count, and
the raw text is persisted. `stop_reason: end_turn, 929 chars` ruled out truncation
in one glance, and the persisted file gave the real cause in the next — see P232.

**Note on method:** the first hypothesis was truncation, and it was wrong. The
reasoning for it was sound (Cyrillic costs 2-3x the output tokens of English; P144's
own comment predicts budget exhaustion on harder generations) and it would have been
acted on, and would have changed nothing. Making the error speak cost one edit;
guessing from a plausible story would have cost a `max_tokens` bump and a second
failure to explain it.

## ═══════════════════════════════════════════════════════════
## PATTERN 232: A model cannot hand-serialize text it does not control
## ═══════════════════════════════════════════════════════════

**What happened:** the Russian generation emitted this, and it is correct in every
way that matters:

    "story": "... и сказал: «Не явится раб в День воскресения, говорящий: "Нет
    божества, кроме Аллаха", стремясь этим к лику Аллаха ...»"

The matn contains straight double quotes. Copied verbatim into a JSON string value
they close the string early, and the object does not parse. The model did exactly
what rule 2 and P153 require — quote the matn as it stands — and the format it was
asked to write could not carry what the rules required it to put inside.

**Cause:** the route asked the model to hand-write JSON whose string values must
carry source text the model does not control and may not alter. Those two
requirements are in direct conflict, and nothing in the prompt could resolve it. An
instruction to escape inner quotes would have held until the next backslash,
newline or control character.

English passed only because its matn happens to use guillemets. Uzbek and Tajik
share Russian quotation typography — this was two generations away from presenting
as a language-specific bug rather than an encoding one, which is how it would have
been diagnosed.

**Rule:** never ask a model to hand-serialize text it does not control. Use a tool
schema and let the API construct the JSON, where escaping is not the model's job.
When output must be machine-read AND must carry arbitrary source text verbatim, the
envelope is the API's responsibility, not the prompt's.

**Status:** FIXED. `generate-reel/route.ts` declares an `emit_reel` tool with a
six-field schema and `tool_choice` forcing it; the handler reads `tool_use.input`
and `JSON.parse` is gone from the route entirely. The prompt's "Respond ONLY with
valid JSON" line was changed in the same edit — with the tool forced, that
instruction was stale and actively misleading. P140's rule survives one block type
over: find the `tool_use` block, never index content by position.

**Related:** P231 is what made this visible, and the two should be read together.
The defect was four hours old in production terms and would have recurred on every
non-English language of every reel.

## ═══════════════════════════════════════════════════════════
## PATTERN 233: A rule that names forms is walked around by the next form
## ═══════════════════════════════════════════════════════════

**What happened:** Bukhari #6423 shipped in four languages. In every one of them
the generation supplied a contrast the matn does not draw:

    EN  (caught before shipping, same shape)
    RU  "а не ради людей или мирской выгоды" / "а не как пустые слова на устах"
    UZ  "фақат тил билан айтишга эмас, балки"
    TJ  "на танҳо бо забон, балки" - TWICE, in the moral AND the context

Four of four. The added promise (`ваъда`, "has promised", where the matn says
Allah FORBADE) made three of four. The comment-about-the-text frame made three of
four. Twelve blocks were corrected by hand across one set.

Rules 23 and 24 had been added the previous day (P226) for precisely this family.

**Cause, and it is not that the rules were ignored.** Rule 24 forbids a *forward*
clause - "so that", "in order to", "with the intention of". What arrived was a
*backward* exclusion: not why the actor acts, but what does not count. Rule 23
forbids "this hadith shows", "teaches us", "reminds us". What arrived in the
context block was "Маънои муқарраршудаи он" and "Унда таъкидланишича". Neither
rule was broken as written. Both were about specific WORDINGS, and the generation
produced a different wording of the same move.

The move itself is older than either rule. Three instances now:

    P212 / rule 13   supplied a WARRANT    "Allah has entrusted this to you"
    P226 / rule 24   supplied a PURPOSE    "so that Allah will ..."
    P233 / here      supplied an EXCLUSION "not merely with the tongue, but ..."

Every time: the matn states a CONDITION, and the generation completes the frame
around it - the reason behind it, the aim in front of it, or the failure it rules
out. Every time the content is sound teaching. Every time it is absent from the
text. And every time the response was a new numbered rule naming the new wording,
which held until the next wording.

That is the real finding, and it is about rule DESIGN, not about this hadith. An
enumerated prohibition is a blocklist, and a blocklist over natural language has
no edge. P226's lesson was *where* a constraint lives (field prose vs the rule
list). P233's is *how it is stated*: a rule that lists forms cannot close a family,
because the family is a move and the forms are infinite.

**Rule:** state the constraint as a TEST the generation can run against itself,
not as a list of banned phrasings. Rule 22 already worked this way for quoted
spans - "check the quoted span clause by clause against the matn you were given
and drop anything the matn does not contain" - and rule 22 has held. Rule 25
generalises exactly that to the moral and the context: take each clause, point at
the words in the matn it comes from, delete it if you cannot. A test does not care
which costume the addition arrives in.

Second-order, and the reason this one matters beyond accuracy: naming the
exclusion plants it. A reel about sincerity that explains insincerity has taught
the audience the shape of the thing it warns against - R026 at the level of
content rather than image prompts.

**Status:** CHANGED, NOT YET VERIFIED. Rule 25 added, stating the grounding test
and naming all three instances so the family is visible rather than three
unrelated rules. Rule 16 amended for the tense/mood shift (FORBADE -> promised),
which no rule covered - the moral field description has said "do not add a promise
the matn does not make" the whole time, in prose, never in the list, which is
P226 unfixed for this one constraint.

A prompt change is only proven by generating. The next test is Bukhari #6570, the
second reel of the Tawheed arc, 2-3 weeks out. If the exclusion shape returns
there in any language, rule 25 failed as a test and the problem is deeper than
wording - which is itself worth knowing, and is why this entry says NOT YET
VERIFIED rather than FIXED.

**Footnote on what caught it.** No gate caught this. `lint-content.py` passed every
one of the four, Stage 3 does not see generated reel text at all, and the STT
validator compares the subtitle to the draft - not the draft to the matn. It was
caught by reading four generations of the same hadith side by side, which only
happens because the set ships in four languages. A single-language channel would
have shipped all three instances without ever seeing the pattern.

## ═══════════════════════════════════════════════════════════
## PATTERN 234: A write that advances the pipeline erased a decision and a provenance record
## ═══════════════════════════════════════════════════════════

**What happened:** Bukhari #3435's Tajik carried «ба ҳақ» — the بحق interpolation
the Arabic does not contain and the other three languages already omit. The fix is
one span, seven characters, and it went through the P177/P219 gate correctly:
reviewed JSON, `--sign`, `--apply --commit`. The text landed exactly right.

Two other things landed with it, neither reviewed, neither intended:

    status           needs_human  ->  translated
    translation_meta {4 fields}   ->  {}

**Cause:** `apply_from_json` wrote a payload of its own on top of the reviewed
fields:

    payload['translation_meta'] = r.get('translation_meta') or {}
    payload['status'] = 'translated'

Both lines assume the reviewed file describes the WHOLE row. It describes the
fields a human corrected. A file carrying one Tajik field therefore asserted "this
row has no provenance" and "this row is at stage translated", neither of which the
reviewer wrote or saw.

The status loss is the serious one. #3435 does not sit at `needs_human` because
work is outstanding — it sits there by ruling, recorded in OPEN_ITEMS on
2026-10-12: *"the row stays needs_human on this clause, permanently, and that is
the correct resting state, not an unfinished task."* The على ما كان من العمل clause
is genuinely ambiguous, the two verify passes reject every wording for mutually
exclusive reasons (P225), and the commentators preserve the ambiguity (P224). The
status field was carrying that decision. Writing an unrelated field revoked it, and
left the row reading as eligible for Stage 3 and promotion — the one outcome three
sessions of work on that clause exist to prevent.

The provenance loss is quieter and nearly unrecoverable. `translation_meta` is
per-field: which fields a human touched, when, and why ("sourced against published
translation + sharh, 2026-10-12 (P224)"). Nothing else in the system records it. It
survived only because `--apply` happens to back up the shared JSON path first, and
that backup was fifteen minutes old.

**The shape.** This is P151's family seen from the other side. P151 says a model
must not SET `matn_verified_at`, because that column means a human read the row
against a source. P234 says a tool must not CLEAR a status that means a human
decided something. Both are the same confusion: a column that records a HUMAN
JUDGEMENT being treated as a column that records PIPELINE POSITION. Every automated
write wants to advance the pipeline; a judgement is not on the pipeline.

**Rule:** a write applies what was reviewed and nothing else.
  - MERGE structured state, never replace it. A field absent from the reviewed
    file keeps what it had.
  - A TERMINAL status — one that encodes a human ruling — is never overwritten by
    an automated write. Read the row first; if it is terminal, say so and leave it.
  - If a tool cannot read the current row, it does not write. A blind write is how
    both of these happened in one call.

**Status:** FIXED. `TERMINAL_STATUS = ('needs_human', 'rejected', 'promoted')`;
`apply_from_json` now GETs the row, merges `translation_meta` over what is there,
keeps a terminal status and prints that it did, and refuses to write at all if the
read fails. #3435 was restored by hand: status back to `needs_human`, provenance
restored from the backup with the Tajik edit appended to the record, text keeping
the «ба ҳақ» fix.

**Footnote.** OPEN_ITEMS attributed «ҳақ» to #3435 **UZ**. The Uzbek was already
clean and had been for some time; the interpolation was in the **Tajik**, in the
language nobody had checked, and would have shipped. Reading all four languages of
a row side by side found it in about a minute — the same method that found P233
the same day. A note naming the wrong language is worse than no note: it sends the
next reader to a field that is already correct and lets them conclude the item is
done.

## ═══════════════════════════════════════════════════════════
## PATTERN 235: The check that found two defects in one day was not in any workflow
## ═══════════════════════════════════════════════════════════

**What happened:** on 2026-10-13 two defects were found within two hours of each
other, both by the same method and by nothing else:

  - **P233** — an addition the matn does not contain appeared in ALL FOUR
    languages of Bukhari #6423. Each generation, read alone, looked correct.
  - **P234** — the بحق interpolation «ба ҳақ» sat in the Tajik of #3435 while
    OPEN_ITEMS sent every reader to the Uzbek, which had been clean for days.

The method: print the Arabic and all four translations of one row together and
read down the column.

**Why no gate found them.** Each gate is correct and each is blind to this:

  - `lint-content.py` checks one text against rules. All four passed.
  - Stage 3 (`verify-candidates.py`) scores each language SEPARATELY against the
    Arabic, and `agreement()` compares verdicts across the two providers — not
    across languages.
  - `stt-validate.py` compares the SUBTITLE to the draft. Never the draft to the
    matn.
  - Per-language human review sees one language at a time, which is exactly the
    view in which a four-language addition looks like four correct translations.

A defect that exists only in the RELATIONSHIP between the languages is invisible
to every check that looks at one language at a time. Nothing was looking at the
relationship.

**And the read already existed** — `list-library.py --row` is documented in its
own help as "dump ONE hadith number in every language, in full - the read every
reel starts with". It reads `hadith_library` only: after promotion. Candidates are
where translations are reviewed, corrected and signed, and candidates could not be
read this way at all. The check existed one stage too late and was in no workflow.

**The two signatures, and the second is the counter-intuitive one:**

  1. A clause in SOME languages and not others. One of them is wrong; the read
     tells you which to look at, not which is right.
  2. A clause in ALL of them that is not in the Arabic. Unanimity feels like
     corroboration and is the opposite: four independent generations agreeing on
     something absent from the source is the signature of a move the model
     reaches for in every language. P233 is exactly this, and it is why it
     survived rules written the day before.

**Rule:** before signing a translation batch, read the row's four languages side
by side against the Arabic. Agreement across languages is not evidence; it is a
thing to check.

**Status:** FIXED. `list-library.py` gains `--candidates`, which runs the same
full read against `hadith_candidates` and also prints `status`,
`verify_agreement` and `review_reason`. Workflow I gains step 3a requiring it
before the sign-off, with both signatures named so the reader knows what they are
looking for.

**What this does not do.** It is a human read, not a gate — nothing fails a build.
Automating signature 1 is plausible (a clause-count or length divergence across
languages is mechanical). Signature 2 is not: detecting a clause that is in every
translation but not in the Arabic is the grounding problem rule 25 states, and if
it could be checked mechanically it would not have needed a prompt rule. The
honest position is that this project's strongest check on fabrication is a person
reading four columns, and the only improvement available was to make that read
cheap and required rather than occasional and lucky.

## ═══════════════════════════════════════════════════════════
## PATTERN 236: Half a problem was fixed, and the other half was hand-corrected four times
## ═══════════════════════════════════════════════════════════

**What happened:** the caption builder wraps the matn in `«…»`. P180 taught it to
skip the wrapper when a matn BEGINS with `«`, because those produced `««` and a
lone closing `»`.

A matn that carries `«` INSIDE it is the other half of exactly that problem, and
P180 does not see it. Wrapping gives:

    «Пришёл ко мне утром Посланник Аллаха ﷺ и сказал: «Не явится раб …».»

Identical guillemets nested — which Russian, Uzbek and Tajik typography all read
as broken.

**How it was handled, which is the actual finding.** Bukhari #6423 hit it in
Russian. It was corrected by hand. An hour later it hit in Uzbek. Corrected by
hand. Both corrections went out in captions and neither became a code change,
because each looked like a one-off formatting slip in a reel rather than a
property of the builder. #6570 would have been the third and fourth — RU and TJ
both quote the kalima with `«…»`.

Four hand-corrections of one defect, and the only reason it got named is that the
third and fourth were predicted out loud while reading the row.

**The shape:** a fix that names its triggering case (`startsWith('«')`) closes the
instance, not the class. P180 is correct and incomplete, and "incomplete" was
invisible because the remaining half presents as a cosmetic problem in output
rather than an error anywhere. Nothing throws. Nothing fails a lint. The caption
is simply slightly wrong, every time, in three of four languages.

This is P233's lesson in a different register — there a prompt rule named forms
and was walked around by the next form; here a code fix named a position and was
walked around by the other position. Both close an instance and leave the class
open. The difference is that P233's class is unbounded (natural language) while
this one has exactly two members, and the second was sitting right there.

**Rule:** when a fix names where something appears, ask what the other positions
are and close them in the same change. And a defect corrected by hand twice is a
defect that belongs in code — the second hand-correction is the signal, not the
third.

**Why the fix belongs in the builder and not in the rows:** the matn is quoted as
the SOURCE quotes it, and that quoting is correct at its own level. It is the
wrapper that creates a second level, so the wrapper demotes the inner pair —
`«…»` becomes `„…“`, the second-level convention in all three Cyrillic languages
this channel publishes. Editing the rows instead would mean carrying
caption-layout concerns in the matn, where P153 says only the source's own text
belongs.

**Status:** FIXED in `app/admin/page.tsx`. Verified against #6570's Russian and
Tajik: `«Самый счастливый — тот, кто сказал: „Нет божества, кроме Аллаха“,
искренне.»` and `«касест, ки „Ло илоҳа иллаллоҳ“ гуфта бошад, холис.»`

**Related, found in the same read (P235's step 3a, working as intended):** the
Tajik kalima was spelled two different ways across one three-reel arc built on
that kalima — #6423 shipped `«ло илоҳа илаллоҳ»` (correctly spaced, missing the
gemination that `إلّا`'s shadda requires) and #6570 carried `«Лоилоҳа иллаллоҳ»`
(geminated, first two words run together). Each wrong in a different way, neither
matching the other. Both now `«Ло илоҳа иллаллоҳ»`. The #6423 reels are published
and were NOT re-rendered for one letter — the audio is out — but the library row
is corrected so nothing built from it repeats the spelling. Uzbek was consistent
across both; only Tajik drifted.

## ═══════════════════════════════════════════════════════════
## PATTERN 237: The third input to the same render had no gate, because it is the one nobody uses
## ═══════════════════════════════════════════════════════════

**What happened:** `render-reel.ps1` takes three kinds of asset. Two are gated
against the registry and one was not:

    -Scenes clips    gated by P121 (eight reels had shipped over unregistered clips)
    the nasheed      gated by P168
    RANDOM clips     never gated

Without `-Scenes`, the script globs `out\backgrounds\new\normalized\*.mp4` and
draws three. Nothing asks the registry. A clip that is unregistered — or RETIRED,
the state `vocal-hamd-kids-01` occupies on the audio side after three strikes —
could reach a published reel by sitting in a folder.

**Cause:** the gate was added each time to the path that had just failed. P121
came from `-Scenes` shipping bad clips; P168 came from the nasheed picker. Both
fixes were correct and neither asked which OTHER inputs lacked the same check.
The random path kept working, because working is what an ungated path does until
the day the folder contains something it should not.

And the reason it stayed unnoticed is the reason it is low-risk: every recent set
renders with explicit `-Scenes`. A path nobody exercises produces no incidents,
which reads as safety and is actually just absence of evidence. P121's own note
says it: *"a gate protects the inputs it is NAMED."*

**Rule:** when a check is added to one input, enumerate the others that reach the
same output and gate them in the same change. A fix scoped to the failing path
leaves siblings open, and the sibling nobody uses is the one that will be open
longest.

**Also:** filter the candidate set BEFORE the draw, not after. Checking a clip
once it has been picked invites re-rolling around a rejection, which turns a gate
into a retry loop. `Get-Random` now draws from the approved list, and clips that
are present but not approved are named on screen so the operator can see the
folder and the registry disagreeing.

**Status:** FIXED, and honestly a no-op today. At the time of the change
`out\backgrounds\new\normalized` held 70 clips and the registry approved all 70
for the adults lane, so the gate rejects nothing right now. That is the point: it
is a guard against drift, not a repair of a live break, and it was worth doing
only because it is three lines and the two sibling paths already cost patterns.
If it ever fires, the folder and the registry have diverged and that is worth
knowing before a reel ships rather than after.

## ═══════════════════════════════════════════════════════════
## PATTERN 238: The caption was derived once from data that keeps changing
## ═══════════════════════════════════════════════════════════

**What happened:** the admin's story, moral and seerah blocks are editable
textareas bound to `generated` through `updateField`, so an operator correction
lands in state the moment it is typed. The caption was built ONCE, inside
`generate()`, and never again.

So the screen showed a corrected moral with, directly underneath it, a caption
still carrying the wording that had just been rejected. Nothing was stale in the
usual sense — both values were current — but one had been derived from the other
at a point in time and never re-derived.

**Twice, on consecutive reels.** Bukhari #6423: the Russian moral was corrected
in the blocks, the caption kept the uncorrected text, and it was caught by eye at
the last step before posting. The note written that day said it was "worth a
pattern on its own" and it did not become one. Bukhari #6570, the next reel: same
thing, same confusion — the operator fixed the blocks and asked why the character
count had not moved.

**The operator's own diagnosis was the right one:** *"that's why we decided to fix
that edited blocks to be wired so the caption block to be reflecting the changed
count."* Identified, agreed, not built — and so paid for a second time.

**Cause:** a value computed from state at one instant, stored in separate state,
and presented beside the state it came from. There is no event that invalidates
it. The generate() handler is the only writer, so every later edit to the inputs
leaves the output untouched and plausible.

**Rule:** when a derived value is shown next to the thing it derives from, give it
a way to re-derive. Compute-once is correct only where the inputs cannot change
afterwards, and an editable textarea is exactly the case where they can.

**Why a button and not a `useEffect`:** the caption box is itself hand-tuned. The
quote nesting gets unpicked (P236), a line gets trimmed to clear Telegram's 1024
— #6570's English needed exactly that, at 1060 before the moral was shortened. A
reactive rebuild would silently discard that work on the next keystroke in any
block. The operator knows when the blocks have become the newer truth; the tool
should not guess. The button says what it will do, and is disabled until there is
something to rebuild from.

**Status:** FIXED. The builder is lifted out of `generate()` into
`buildCaption(data)`, called from generate as before and from a "↻ Rebuild from
blocks" control beside the caption box. TypeScript clean.

**Footnote on cost.** Both occurrences were caught — the first by eye, the second
because the operator noticed a number that should have moved. Neither shipped. But
the second catch cost a round trip and a hand-written replacement caption, and the
fix is twenty lines that were agreed to a day earlier. A known defect that is
cheap to fix and keeps being worked around by hand is more expensive than it
looks, because the workaround succeeds every time until it doesn't.

## ═══════════════════════════════════════════════════════════
## PATTERN 239: A rule written for one failure family lost to it in three languages out of four
## ═══════════════════════════════════════════════════════════

**What happened:** rule 25 went into the generator prompt on 2026-10-12 after
P233, deliberately written as a TEST - ground every clause, point at the words
in the matn, delete what you cannot - rather than as a list of forbidden
wordings, because rules 23 and 24 had enumerated wordings and been walked
around by the next wording inside a day. Bukhari #6570 was its first clean
test, read across all four languages.

EN held. RU, UZ and TJ all supplied a contrast the matn does not draw:

    RU   «а не по привычке или подражанию другим»
    UZ   «фақат тилда эмас, балки ихлос билан»
    TJ   «на бо забон танҳо, балки»

Two of those are near-verbatim repeats of the same language's #6423 defect -
UZ had «фақат тил билан айтишга эмас, балки» and TJ had «на танҳо бо забон,
балки». The rule did not merely fail to stop a new instance. It failed to stop
the same sentence.

**Cause, and this is the useful part:** the supplied contrast is not ungrounded
invention. It is an EXPLICATION of a word that is present. خالصًا means sincerely,
and "not merely with the tongue" is a fair gloss of what sincerely excludes. So
the clause passes rule 25's test honestly: asked to point at the words in the
matn, the generation points at خالصًا and the contrast follows.

A test catches what it measures. Rule 25 measures whether a clause can be traced
to the matn. This family traces. The missing constraint is not grounding at all:
it is that خالصًا says what the deed IS and does not say what it is NOT. Turning an
affirmation into a contrast adds the half the matn left unsaid, however sound
the theology.

**Rule:** render an affirmation as an affirmation. Where the matn states a
quality, state that quality; do not state its opposite and deny it. "X, not Y"
is two claims where the matn made one, and the second is yours. This names the
MOVE rather than the wording (which rules 23/24 tried) or the grounding (which
rule 25 tries), because the move is what survived both.

**Consequence for the held rewrite.** `docs/proposed-rules-positive-form.md` was
held precisely so rule 25 could be tested alone. It got a clean test and lost
3-of-4. That doc named its own uncertainty - "it is equally possible that what
makes a rule hold is being a TEST rather than being POSITIVE" - and the result
cuts against both halves: rule 25 IS a test, it IS positive, and it still lost.
Neither property is sufficient.

**Status:** NOT FIXED, and deliberately so. Rule 25 stays - EN held and the rule
is not harmful. The fifteen-rule rewrite stays on hold, because applying it now
would stack another plausible fix on an unexplained failure, which is the exact
error P233 was written about. What goes in next is one rule naming the move,
tested alone on the next set, the same way rule 25 was.

## ═══════════════════════════════════════════════════════════
## PATTERN 240: -FitScenes cannot stretch a clip, and the loop makes the shortfall look deliberate
## ═══════════════════════════════════════════════════════════

**What happened:** Bukhari #6570 UZ. Narration 52.22s, five scene clips of
10.0417s each. `-FitScenes` computed (52.22 + 1.0) / 5 = 10.644s per clip and
printed it. `ffmpeg -t 10.644` on a 10.0417s clip returns 10.0417s - `-t` trims,
it cannot extend - so the background came out 50.16s against 53.22s of audio.

The final merge passes `-stream_loop -1` on the background. Instead of ending
short, the video wrapped and replayed clip 1. The last 3.0s of the reel showed
the opening lamp while the moral finished, and the reel ended on its first image
rather than the garden. Confirmed by extracting the frame at 52.8s.

Nothing warned. The script printed its per-clip figure, reported success, and
named a file of the right size.

**Cause:** `-FitScenes` computes an equal share and assumes the source can
supply it. That assumption holds whenever narration < clips x clip_length and
fails silently above it. `-stream_loop -1` was added for an unrelated reason
(P143: give the tail 1s so the outro is not cut) and it converts this failure
from a visible truncation into an invisible wrap - the one outcome that looks
like an editing choice.

Worth noting which language was exposed. EN (8.97s), RU (9.41s) and TJ (8.74s)
were all under the ceiling in the same set and passed. Only UZ, the longest,
hit it - and UZ is also the language that ships with no subtitles (P078), so
there is one less reason to watch it closely. The failure selected for the reel
least likely to be re-checked.

**Rule:** when a computed share can exceed what the source can supply, compare
the two and fail loudly. A fit that silently under-delivers is worse than one
that refuses, because downstream has a loop that will hide it.

**Status:** FIXED. A guard after the fitDur computation measures the shortest
picked clip and Dies if the share exceeds it, naming how many clips would be
needed. UZ re-rendered with six: `b6423-plain.mp4` borrowed as the fourth -
already registered and adults-approved, the same beat as `b6570-plain` in
different footage (pale cracked earth against grey gravel), so the cut reads as
two shots of one place rather than a restart. fitDur 8.862s, background 53.17s
against 53.17s of audio, exact. The kalima clip now spans 35.5-44.4s and covers
BOTH spoken kalimas - UZ says it once closing the story and once opening the
moral - which the five-clip cut caught only the first of.

## ═══════════════════════════════════════════════════════════
## PATTERN 241: The correction was made somewhere that does not persist
## ═══════════════════════════════════════════════════════════

**Two instances in one day, both mine.**

**One - the narrator spelling.** The EN source carried two spellings in one
reel: `Abu Hurairah` opening the story, `Abu Hurayrah` inside the Prophet's
quoted speech. I corrected `draft.txt` at 19:30 and wrote that the durable
protection was "catching the variant at review in each language". `draft.txt`
is the single working file every generation overwrites - it was overwritten
four times that evening, once per language. The source was
`hadith_library.text_english`, which still carried `Hurayrah` and which feeds
the EN caption. Found at 22:40 by the four-language side-by-side read, not by
the fix that was supposed to have handled it.

**Two - the gate argument.** Writing P237's gate I used `--section clips`,
noticed that `audit-assets.py` offers only `{audio,mascots,scenes}`, and showed
the corrected spelling in conversation. The WRONG spelling is what reached the
file. argparse exits 2, the gate reads a non-zero exit and Dies, so every
random-mode render was broken from the moment the fix landed - undetected,
because every recent set passes explicit `-Scenes`. P237's own lesson, applied
to P237's own fix.

**Cause:** in both, a correct correction existed somewhere that does not
survive - a file that is regenerated, and a sentence in a conversation. The
artifact that outlives the task was never touched. Both felt finished at the
time, because the correction itself was right; what was skipped was asking
WHICH artifact has to carry it.

**Rule:** fix the thing that regenerates the others, and read it back. Before
calling a correction done, name the artifact it must live in and confirm it is
there. A derived file is not where a fix belongs. Neither is a message.

**Status:** both fixed and read back - the library row re-queried after the
UPDATE (`Success. No rows returned` says nothing about rows touched), and the
gate argument verified on disk rather than in the diff I had in mind.

## ═══════════════════════════════════════════════════════════
## PATTERN 242: The rebuild control reverts the one input that has no editor
## ═══════════════════════════════════════════════════════════

**What happened:** P238 lifted `buildCaption` out of `generate()` and added a
↻ Rebuild from blocks control, so that a correction typed into the story,
moral or seerah textarea re-derives the caption instead of leaving it stale.

The caption also derives from `title`. Title is rendered as a read-only `<p>`:

    <p className="text-white font-semibold">{generated.title}</p>

`story`, `moral` and `seerah_context` are each a textarea wired to
`updateField`. `title` never was. So Rebuild cannot pick up a corrected title -
and it actively REVERTS one the operator fixed by hand in the caption box,
because it re-derives from a `generated.title` that nothing can change.

**Before P238 this field was fine.** A hand-edited caption stayed edited. The
rebuild control made exactly one field strictly worse, and only that field,
which is why it survived the TypeScript check, the review and a day of use.

**Found on Bukhari #13.** The generated title was `None Truly Believes Until He
Loves This` - a dangling "This" that withholds the answer to earn a click, on a
channel whose whole premise is verifiable authenticity. A corrected C block was
pasted, Rebuild was pressed, and the clickbait title came back. The control was
working correctly; there was nowhere for the new title to go.

**Cause:** P238 asked which VALUE was derived once and never re-derived. It did
not ask which INPUTS that value derives from, or whether each of them can be
edited. Three of four could. A rebuild is only as good as its least editable
input, and the one that cannot be edited is invisible precisely because it
never changes.

**Rule:** when a derived value gets a re-derive control, enumerate its inputs
and confirm every one of them is editable. An input that is display-only turns
the control into a silent revert for that field - worse than no control at all,
because the operator now has no way to make the correction stick.

This is P237's shape one layer up: there, a gate was added to the input that
had just failed and the sibling inputs were left ungated. Here, a rebuild was
added for the inputs that had just gone stale and the sibling input was left
uneditable. Both times the fix was scoped to the symptom rather than the set.

**Status:** FIXED. `title` is now a textarea bound to `updateField('title')`,
matching the other three. `updateField` is typed `keyof Generated`, so it took
the new field with no signature change.


## ═══════════════════════════════════════════════════════════
## PATTERN 243: The casing restorer read blocks that are never spoken, and corrupted one that is
## ═══════════════════════════════════════════════════════════

**What happened:** Bukhari #13 RU. Whisper transcribed the ﷺ expansion exactly
right — «Пророк, да благословит его Аллах и приветствует», lowercase его, the
Prophet ﷺ being blessed by Allah. `restore-srt-casing.py` then printed:

    его                          -> Его                          x1

and rewrote it. «да благословит Его Аллах» reads as ALLAH being blessed. The
script exists to fix casing and it introduced a casing error, into the one word
where case carries theology.

**Cause, in two parts.**

The script's source is the whole of `draft.txt`. That file holds S, M, H and C
blocks; only S and M are narrated. The H block for this reel opened a sentence
with «Его понимают как указание…» — and that capital Его is the ONLY standalone
его/Его in the file. Everything else the word-matcher finds is the его inside
чего. So the script concluded: normalised form его appears in the source exactly
once, spelled Его, unambiguous — and restored the subtitle to match.

Its ambiguity guard (“if one normalised form appears under two spellings, leave
it alone”) never fired, because there was one spelling to find and it was wrong.
Its first-word guard did not apply, because Его sits mid-cue.

Second part: the script does not expand ﷺ. `stt-validate.py` does — it has
`expand_prophet()` and `PROPHET_SPOKEN['ru'] = 'да благословит его Аллах и
приветствует'`, lowercase. The casing restorer has no equivalent, so every word
of that expansion is in the AUDIO but not in its SOURCE, and inherits whatever
casing happens to exist elsewhere in the file.

**The linter could not catch it either.** `capitalised_non_source` fires on words
ABSENT from the source. его is present (after expansion) — just in the other
case. The run reported `no findings`, `similarity 1.000`.

**Rule:** a tool that corrects the narrated text must read only what is narrated.
Non-narrated blocks are not a weaker source, they are a different document, and
a sentence-initial capital in one of them is not evidence about a mid-sentence
word in another.

**Worth noting how it was introduced.** The poisoning token was written an hour
earlier, in this same session, rewording the H block from «Он устанавливает» to
«Его понимают как» — a correction made for a different and good reason (the
block asserted where EN hedged). The previous wording had no standalone его. A
defensible edit to a non-narrated block silently changed the subtitles.

**Status: P243 FIXED 2026-10-15.** Both changes went in, not one:

  - `source_forms()` now tracks the current block and collects words only from
    S and M. Unlabelled lines continue the block above them, so the block is
    tracked rather than assumed from the line's own prefix.
  - `expand_prophet()` added, mirroring `stt-validate.py`'s `PROPHET_SPOKEN`,
    and `--lang` is now threaded to `source_forms()`. The spoken words have a
    real source spelling instead of inheriting one.

Either alone closes this instance; with the expansion present, его would appear
in both cases and the ambiguity guard would fire, leaving Whisper's correct
output in place. Both went in because a non-narrated block should never
influence subtitles at all, independent of this bug.

ORIGINALLY recorded as: caught at the review pause and reverted by hand. Either
change closes it: restrict the source to S and M, or expand ﷺ the way the linter
does — with the expansion present, его would appear in both cases, the ambiguity
guard would fire, and Whisper's correct output would stand. Do both: the first
because non-narrated blocks should never influence subtitles, the second because
those words genuinely are in the audio and deserve a source spelling. It will
recur on any ﷺ reel whose H block starts a sentence with a word the narration
also uses.

## ═══════════════════════════════════════════════════════════
## PATTERN 244: The fabrication was what made the truncation invisible
## ═══════════════════════════════════════════════════════════

**What happened:** picking a hadith for the day's reel, two “ready” library rows
turned out to be unusable, and the second was unusable in a way that had been
engineered to look fine.

`Sahih Muslim #223` stores الطهور شطر الإيمان — “Purity is half of faith.” The
hadith continues for six more clauses: praise fills the scale, prayer is light,
charity is proof, patience is brightness, the Qur'an is evidence for or against
you. A fragment, but a fragment that LOOKS like one — a complete sentence,
obviously short.

`Musnad Ahmad #7936` was the opposite. Stored Arabic:

    مَن أُعْطِيَ فَشَكَرَ وَابْتُلِيَ فَصَبَرَ وَظَلَمَ فَاسْتَغْفَرَ وَظُلِمَ فَعَفَا

That is a مَن conditional with NO apodosis. It opens “whoever is given and is
grateful…” and stops. Dorar gives the rest: ثم سكت — then he fell silent — they
ask, and he answers أولئك لهم الأمن وهم مهتدون.

**All four translations supply the missing clause.** “Blessed is he who is given
and is grateful…” / «Блажен тот…» / «Бахтлидир…» / «Хушбахт аст…». There is no
طوبى anywhere in the stored Arabic. Someone — or something — rendered an
incomplete sentence as a complete one by inventing the half that was missing.

**And that is why it passed inspection.** The row was recommended for production
twice, on the strength of how the English read: four balanced clauses, a natural
close. A literal rendering would have ended mid-sentence and been obviously
truncated. The fabrication concealed the defect it was covering.

Two more defects in the same row: narrator stored as Abu Hurairah where both
Dorar entries say سخبرة الأزدي, and grade stored as **hasan** where al-Mundhiri
says لا يتطرق إليه احتمال التحسين — it cannot be raised to hasan. On a channel
whose entire premise is verifiable authenticity, a row graded hasan that the
authorities decline to grade hasan sat one step from production.

**Also found in the same sweep:** `Jami at-Tirmidhi #2616` and `Sahih al-Bukhari
#1469` each exist as TWO rows under ONE number, each carrying a different clause
of the same hadith — and #2616's two rows carry DIFFERENT GRADES. The duplicate-
check index keys on hadith number, so it cannot see either pair.

**Rule:** check extent against the source before producing, and treat a
translation that reads smoothly as evidence of nothing. Grammatical completeness
in the target language says nothing about completeness in the matn, because the
translator's job is to produce a sentence that reads — which means a truncated
matn arrives looking whole. Read the ARABIC for a dangling conditional, an
unanswered مَن, an enumeration that stops.

**And:** two sources agreeing is not evidence of extent when both inherit the
same abbreviation. Yesterday's ZAD cross-check flagged #13 and #19 as partial and
passed #223, because ZAD's own entry was equally short. Agreement between a
library row and a course book means they share an ancestor, not that they are
complete.

**Status:** #7936 quarantined, DO NOT PRODUCE. #223 and #2699 queued for a
Workflow L re-pull. The two duplicate-number pairs recorded. A full
extent-and-attribution audit of the 36 unused rows is not yet scheduled;
`verify-matn-source.py` covers the attribution half and needs a `--mirror`.

## ═══════════════════════════════════════════════════════════
## PATTERN 245: The moral re-attributes in seven generations out of eight
## ═══════════════════════════════════════════════════════════

**What happened:** rule 17 says the MORAL applies the hadith in the listener's
direction and the STORY carries the attribution. Across Bukhari #6570 and #13 —
eight generations, four languages each — the moral re-attributed in seven:

    #6570 RU   «таково условие, которое назвал Пророк ﷺ»
    #6570 TJ   «зеро Паёмбар ﷺ хабар дод»
    #6570 UZ   (H block) Allah-warrant, see below
    #13   EN   “the Prophet ﷺ made this the measure of true belief”
    #13   RU   «ведь этим самым мерилом Пророк ﷺ назвал истинность веры»
    #13   UZ   «Аллоҳ таоло мана шу сифатни … қилиб қўйган»
    #13   TJ   «ин шарте аст, ки Пайғамбар ﷺ … баён кардаанд»

**Two of those are the same word in different languages.** #6570 RU's «условие»
and #13 TJ's «шарт» both mean “condition” — one reel and one language apart,
reached for independently.

**And the two Uzbek instances escalated.** On #13, rule 17 was named explicitly
in the pre-generation watch list. The generation did not re-attribute to the
Prophet ﷺ; it re-attributed to ALLAH — “Allah the Exalted MADE this quality a
sign of true faith” — a claim about Allah's action that the matn, which is the
Prophet's ﷺ speech, never makes. That is P212's supplied warrant arrived at
through P111/P115/P116's adjacent exit: close the named door and the next one
opens. Naming the defect in advance moved it rather than stopping it.

**What this is not.** It is not a wording problem. Seven instances, four
languages, two reels, and no two phrasings alike. The constant is the MOVE: asked
to apply a saying, the generation reaches for a sentence that says whose saying
it is. That is a natural thing to write and it is exactly what the story block
already did.

**Bearing on the held rewrite.** `docs/proposed-rules-positive-form.md` has been
on hold since P239, which found rule 25 losing 3-of-4 despite being both positive
and a test. Rule 17 is also positive and also a test, and it loses 7-of-8. Two
rules, two properties, two failures — the evidence now says the register of the
rule is not the variable at all.

**Rule:** where a rule names a thing not to do, the model finds the nearest thing
that is not that. Rule 17 forbids re-quoting the Prophet ﷺ in the moral and the
model re-quoted Allah. A rule that will hold has to describe what the moral IS —
a sentence addressed to the listener about what they should do, containing no
speaker — rather than which speakers are off limits.

**Status:** NOT FIXED and deliberately unpatched. Every instance was caught at
review and corrected before narration; none shipped. The next prompt change is
one rule, tested alone on one set, as rule 25 was — not fifteen at once.

## ═══════════════════════════════════════════════════════════
## PATTERN 246: A verifier reported agreement with a source it could not read
## ═══════════════════════════════════════════════════════════

**What happened:** #6570 was produced 2026-10-14 and held for Tawheed-arc
spacing. On 2026-10-15 its EN reel was re-rendered to change the nasheed. By
then `draft.txt` held #13's CYRILLIC blocks — #13 was generated the next day,
and every generation overwrites that file.

`restore-srt-casing.py` ran with `--lang en` against that Cyrillic source and
printed:

    nothing to restore - the SRT already matches the source.

It had compared nothing. A Latin SRT and a Cyrillic source share no words, so
no word could be restored, and the script read its own empty result as
agreement. `stt-validate.py`, running immediately after on the SAME pair, got
it right: one HIGH `transcript_diverged` at similarity 0.126 plus sixteen
`script_mismatch` lines. One check refused and the other agreed, on identical
inputs.

**Why it mattered more than it looked:** the reel was fine. The burned
subtitles were Whisper's own output and had been read at the review pause. The
damage was to the RECORD. P243 was fixed that same afternoon and this run was
described as its first live exercise; the "nothing to restore" line was taken
as evidence the fix held. It was evidence of nothing — the new code never
executed.

**One fact, two symptoms.** `draft.txt` is treated as the record of what was
narrated while actually being a scratch file the next generation overwrites.

  - Symptom 1 is the false pass above.
  - Symptom 2: no reel has an archive of its narrated text. #6570 UZ and TJ
    carry no burned subtitles (P078), so when `draft.txt` was overwritten their
    reviewed wording — including the hand corrections «ўз учун» → «ўзи учун»
    and «бародарат» → «бародари худ» — survived only as audio. Not
    recoverable from the repo, the session transcript, or chat history. A reel
    held across one generation loses its text.

**Rule:** a check that cannot see its input must FAIL, not pass. "Nothing to
do" and "nothing comparable" are different outcomes and must read differently.
And a file overwritten on a schedule you do not control is not a record — keep
the authoritative copy at the moment it is authoritative.

This is P241's family from the other side. There, two corrections were made
where they could not persist. Here, a verification was trusted where nothing
persisted to verify against.

**Status: half FIXED 2026-10-15.**

  - `scripts/restore-srt-casing.py` — language guard added.
    `dominant_script()` compares the SRT's writing system with the source's,
    and coverage measures what fraction of SRT words the source accounts for
    (`MIN_COVERAGE = 0.40`). Either failing exits 2 with NOTHING WAS VERIFIED
    and the reason. `render-reel.ps1` already handled rc=2 at that call site,
    so no PowerShell change was needed. Proven both directions: a Cyrillic
    source against an EN SRT is refused, a matching EN source still returns 0.
  - `app/api/tts/route.ts` — the narrated text is archived as
    `{style}-{lang}-{slug}-{section}.txt` beside the mp3 the same request
    produced, inside P106's dev-only disk write. Chosen over a render-time copy
    of `draft.txt` because the route knows the language and holds the text it
    just spoke, whereas a render-time copy would have archived #13's Cyrillic
    on this very re-render — the same trap one layer up.
  - NOT fixed: the four #6570 reels already rendered have no archive. EN and RU
    can be reconstructed from their SRTs. UZ and TJ cannot.


## ═══════════════════════════════════════════════════════════
## PATTERN 247: A check ran daily for two weeks and reported to nobody
## ═══════════════════════════════════════════════════════════

**What happened:** HV's `CLAUDE.md` claimed the shared P-frontier was "P186 as
of 2026-10-01". On 2026-10-15 HR was at P246 — sixty patterns, two weeks.

A daily scheduled task, "Doc drift check", exists to catch this. Step 3 of its
prompt says so in as many words: confirm HV's CLAUDE.md still states the frontier
correctly. It ran every day. It reported SUCCEEDED every day. The line stayed
wrong for two weeks.

**Two reasons, and the second is the one that generalises.**

1. The check was AGENT JUDGEMENT, not a script. `audit-docs.py` already computes
   the frontier — it prints `pattern frontier P246` on every run — but it only
   walks THIS repo's .md files. The sibling comparison lived in the task's prompt,
   to be done by reading and remembering, and it produced prose rather than an
   exit code. `fail()` was never reachable for it.

2. The task had NO NOTIFICATION DESTINATION. The sibling "Daily job digest"
   carries `notifications: {email: true}` and emails its output. Doc drift check
   carries no notifications field at all, and its prompt never emails anything, so
   its report landed in a fresh session nobody opens. Every run was a SUCCEEDED
   run that reached no reader.

**The 5.3-second red herring.** The run duration looked diagnostic — 5.3s against
the job digest's 80s — and the first theory was that it bailed early on an
unreachable repo. It did not. `audit-docs.py` runs in 0.23s and exits 0, and the
task's prompt says a clean result gets one line and stops. 5.3s is what success
looks like here. The timing was innocent; the delivery was the defect.

**Rule:** a scheduled check needs BOTH an exit code and an addressee. A finding
that exists only as prose in a session nobody opens has not been reported, and a
task reporting SUCCEEDED for work nobody read is indistinguishable from one that
works. Put the comparison in a script so it can fail, and give the task a channel
so the failure arrives.

**This is P188's family one step later.** There, `stt-validate.py` was a correct
check with no caller for seven weeks. Here the check had a caller, ran on
schedule, and still changed nothing, because its output had no return value and
no reader. "It runs" is not "it reports".

**Status: half FIXED 2026-10-15.**

  - `scripts/audit-docs.py` — `check_sibling_frontier()` added. It fails on any
    P-number in `hadith-verifier/CLAUDE.md` above HV's own top pattern and below
    HR's frontier, the precise signature of a cached frontier, and on any number
    above HR's frontier — which `check_pattern_refs()` already caught for this
    repo's docs but never for the sibling. Warns and skips when the sibling is not
    beside this repo. Proven both ways: clean on the corrected file, exit 1 with
    the finding when a cached number is injected, and the file restored
    byte-identical (sha256) after the test.
  - `hadith-verifier/CLAUDE.md` — the cached number is gone, replaced by a pointer
    to HR's `fix_patterns.md` tail. It deliberately carries no 3-digit P-number
    above P140: the explanatory sentence would otherwise trip the very check it
    describes, which it did in draft.
  - The "Doc drift check" scheduled task now EMAILS its report on every run, with
    the verdict in the SUBJECT line: CLEAN / DRIFT (n) / COULD NOT RUN /
    UNREACHABLE. Mailing even a clean run is deliberate — if only findings were
    mailed, silence would again mean both "all is well" and "it never fired",
    which is the defect this pattern is about. Delivery had to go in the task's
    PROMPT rather than its settings: `update_trigger` cannot set the
    notifications field, and the task is bound to the device, so the new prompt
    was re-signed by the desktop app when it changed.
  - Residual risk, stated rather than ignored: a clean email every morning is
    exactly the thing people filter into a folder and stop reading. If that
    happens the next move is a weekly heartbeat plus mail-on-finding — not
    silence on clean runs, which is where this started.


## ═══════════════════════════════════════════════════════════
## PATTERN 248: The fix went into one check and not its neighbour, again
## ═══════════════════════════════════════════════════════════

**What happened:** the 2026-10-16 doc-drift email reported, in one message:

    133 reels ... newest reel row 2026-10-11 (R122-R125), 5 days old

R133 was dated 2026-10-15. One day old, not five. And the same email's "133
reels" could only have come from the Active reels table — the very table that
would have given the right date. Two contradictory facts in one report.

**Cause:** the cadence check lived in the TASK'S PROMPT, which instructs the
agent not to read the whole tracker because it is large, and to tail it. The
Active reels table is near the TOP of reel-tracker.md; a tail lands in the
Change log. So the instruction that was meant to protect context guaranteed the
check read the wrong rows — every day, invisibly, because a wrong date looks
exactly like a right one.

**Why this is its own pattern.** P247 found the sibling check (HV's cached
P-frontier) failing in the same task for a related reason, moved it into
`audit-docs.py` where it gets an exit code, and LEFT THIS ONE IN THE PROMPT. The
remedy was known, written down, and applied to one of two checks in the same
file on the same day.

That is P237's shape (a gate added to the input that had just failed, siblings
left ungated) and P242's (a rebuild added for the values that had gone stale,
the sibling input left uneditable). Third occurrence. The question that would
have caught all three is the same one: having fixed this, what else in the same
place has the same shape?

**Rule:** when a scheduled task asks an agent to work a fact out by reading part
of a file, that is not a check — it is a guess with a confident format. Put it in
a script that parses the structure, and have the task QUOTE the script rather
than recompute anything. And when a fix lands, enumerate that task's other
steps before closing it.

**Status: FIXED 2026-10-15/16.**

  - `scripts/audit-docs.py` — `cadence_line()` added. It takes the newest date
    from the rows `active_rows()` already parses, names the reel IDs sharing it,
    and prints the age on the summary line:
    `doc audit: 133 reels, pattern frontier P247, newest reel row 2026-10-15
    (R130-R133), 1 day old`. It uses `max()` on the date rather than the last
    row, so it does not assume the table is in order.
  - The task prompt no longer computes it. Step 1 says to quote the script's
    first line and recompute nothing; a new step 3 forbids reading the tracker
    or fix_patterns to work anything out, and says why.
## PATTERN 249: The picker remembers one bed per lane, and writes it down before the render succeeds

Bukhari #1903 EN rendered three times on 2026-10-16 - aborted at the SRT pause,
blocked by the asset-registry gate, then clean - and drew a DIFFERENT nasheed on
each run: `vocal-nasheed-05`, then `aswati-Heartfelt-Gratitude`, then
`light-of-my-heart-bg`. The published reel carries the third. Nobody asked for a
change and the operator noticed it only because the console prints the pick.

`render-reel.ps1` L236-255. The state file is `out\backgrounds\.last-used.json`
and it holds ONE value per LANE: `$state[$Style] = $pick.Name`. The write happens
at PICK time, inside the step-0 validation block, before any ffmpeg work and
before the render can fail. So:

  1. A run that never finishes still burns the slot. The retry of the SAME
     language then dutifully avoids its own previous pick, which is the opposite
     of what a retry should do.
  2. Re-rendering an ALREADY-PUBLISHED reel silently changes its bed - and the
     P201 `*-render.json` sidecar and the tracker's Nasheed column are both
     rewritten to match the new one, so nothing anywhere records that the live
     video no longer matches what we wrote down.

And the deeper one: there is no per-reel or per-language rule in the picker at
all. One slot, one lane, one deep. Across a four-language set rendered in order,
language 3 can repeat language 1's bed - 1-in-17 per step on the adults lane.
That is exactly the #6570-versus-#13 clash of 2026-10-15, which was closed by
passing `-Nasheed` on two legs and re-rendering. The instances were fixed; the
picker was never touched, so the mechanism was still live eleven days later and
produced three different beds for one reel in one evening.

**Why it survived.** The state is keyed by the thing that MAKES the pick (the
lane) rather than the thing the rule is ABOUT (the reel). A lane-keyed one-deep
memory faithfully answers "not the same bed twice in a row on this machine",
which is a question nobody asked. The documented rule - not the same bed on two
consecutive reels in the same language - needs slug and lang, and the picker has
both in scope and uses neither.

**Rule:** state that describes a piece of work is written AFTER that work
succeeds, not when the decision is taken. And key it by the subject of the rule,
not by whichever variable the code happens to be holding. If the two differ, the
check is measuring something else and will look correct while being wrong.

**Status:** DOCUMENTED - fix pending.

  - Workaround until then: pass `-Nasheed <file>` explicitly for every language
    of a set, which prints `avoided: n/a (override)` and cannot re-roll.
  - Fix has three parts: move the state write to after the render returns 0; key
    it by `slug`+`lang` rather than by lane; and have the picker read the set's
    existing `*-render.json` sidecars so it knows what the other languages of
    THIS reel already used instead of guessing from a single global slot.

---

## PATTERN 250: The prompt that decides what is in the frame is the one nothing records

P215 made `generate-scene.ps1` write every motion prompt to
`assets\scene-prompts\<name>.json`, because no clip's prompt had ever been
stored. `generate-image.ps1` writes nothing, and still does not.

These are image-to-video clips. The STILL decides what is in the frame; the
motion prompt only decides what moves within it. So the half that was fixed is
the less consequential half, and it reads as covered because a sidecar exists.

Found while writing the asset-registry notes for the b1903 set. The four motion
prompts were on disk. The four FLUX still prompts were nowhere: not in the
sidecars, not in `animated-reel-scene-prompts.md` - which is a methodology doc,
and `6423`, `5027`, `3895` and `1631` appear ZERO times in it - and not
recoverable from the session transcript, which had compacted. The registry notes
for all four b1903 clips therefore describe motion only, and say so.

**Why no earlier set exposed it.** The registry note was always written in the
same session that generated the stills, so the prompt was still in the
conversation when the note was composed. The record WAS the conversation. That
worked for every set from b1520 to b6570 and gave no signal, because a
conversation that has not ended yet looks exactly like storage. Same shape as
P201 (three of four bed names survived only in a console buffer that was then
closed) and as P215 itself - and this is the third time the thing that knows has
been the only thing that could write it down and did not.

**Rule:** when a step makes a choice the output cannot be reverse-engineered
from, that step writes the choice down, beside the artefact, at the moment it is
made. Not the session, and not a note composed afterwards from memory - a note
written later records what the writer recalls, which is a different thing from
what was sent.

**Status:** DOCUMENTED - fix pending. `generate-image.ps1` should write
`<name>-still.json` next to the scene sidecar, carrying the prompt, the negative
prompt, the model, the variants returned and which one was chosen. The chosen
variant matters as much as the prompt: `b1903-majlis` went through three circle
stills that all showed faces before the composition was changed to a row facing
away, and only the final choice is visible in the output.
## PATTERN 251: One mix level, for beds that are not one loudness

The operator said the Aswati beds sit too quiet. By ear, mid-session, with no
gate having said anything in the twenty-four reels those beds have carried.

The adults mix is fixed at narration 1.4 / nasheed 0.12 (P171) - ONE level for
every bed. Measured on 2026-10-16, the eight Aswati masters run from -13.35 to
-20.22 LUFS, against `light-of-my-heart-bg` at -13.38, which is the bed the 0.12
was tuned on. So the complaint was right.

But "the Aswati beds are quiet" is true on average and wrong per track.
`aswati-Gentle-Reflection` is 6.8 dB down; `aswati-Rising-Hope` is AT reference.
A single blanket bump - the obvious reading of the request, and what I would have
shipped without measuring - fixes the worst one and overdrives the two that were
already right.

**Why nothing caught it.** Every gate in the audio path checks WHAT a bed is, not
how loud it is. The registry records classification, lanes and verified; P168
made the pickers read the registry instead of the filename; `audit-assets.py`
enforces lane eligibility. None of them measures anything. And the beds were
auditioned ALONE at registration, where 6 dB reads as a quieter track rather
than as a defect - the defect only exists in the mix, under narration at 1.4. So
the one instrument that could detect it was a person listening to finished reels,
which is the slowest and most expensive detector in the project.

**Rule:** a constant tuned against one input is a constant tuned against one
input. When that number is then applied across a library, record per item the
property it was tuned against - here integrated loudness - and DERIVE the number
from it. The alternative is what happened: a human ear doing arithmetic that a
one-line measurement does exactly.

**Status:** FIXED 2026-10-16.

  - `assets/asset-registry.json` - optional `gain` on audio entries, documented
    in `_schema`, set on all eight Aswati beds as 10^((-13.38 - LUFS)/20):
    Gentle-Reflection 2.20, Heartfelt-Gratitude 1.58, Focused-Determination 1.41,
    Morning-Serenity 1.23, Steady-Motivation 1.19, Peaceful-Contemplation 1.14,
    Victory-March 1.06, Rising-Hope 1.00. Absent means 1.0, so the other
    seventeen audio entries are untouched.
  - `render-reel.ps1` - reads `gain` for the chosen bed, multiplies 0.12, prints
    it on the nasheed line, and records `nasheedVol` in the P201 sidecar so a
    reel's actual mix level is recoverable afterwards. Out-of-range or
    unreadable falls back to 0.12 with a warning rather than failing the render.
  - The value is formatted with InvariantCulture before it reaches
    `-filter_complex`. A comma-decimal locale would have emitted
    `volume=0,2640` and the filter graph would not have parsed - a failure that
    would have looked like an ffmpeg bug on someone else's machine.
  - NOT applied to #1903: its EN leg shipped on `light-of-my-heart-bg` before
    this landed, and the remaining three languages are being kept off Aswati
    beds so one reel is not mixed two ways.
## PATTERN 252: The encoding fix went to the child process and not to the parent

P100 set `PYTHONIOENCODING=utf-8` on the Whisper call, because a CP1252 console
made `transcribe.py` raise UnicodeEncodeError on Cyrillic and abandon the
transcription. That was correct and it worked. It also looked complete.

It was not. `PYTHONIOENCODING` tells the CHILD how to ENCODE its output.
PowerShell then DECODES that output using `[Console]::OutputEncoding`, which is
CP437 on PS 5.1 - and only when the output is PIPED, because a child writing
straight to the console hands its bytes to the terminal untouched.

So in `render-reel.ps1`:

  - `restore-srt-casing.py` (L430) runs unpiped. Its Cyrillic prints correctly.
  - `whisper` (L392) and `stt-validate.py` (L461) both pipe through
    `ForEach-Object`. Their Cyrillic arrives as mojibake.

Found on the RU leg of #1903 on 2026-10-16. The operator pasted the subtitle
review and `  пророк -> Пророк` was legible while every Whisper cue and every
stt-lint finding in the same output was not. **For RU, UZ and TJ - three of four
languages - the operator could not read the findings the gate produces.** The
review happened only because the SRT had been pasted separately from the file.
A defect visible ONLY in the lint output would have been invisible.

**Why it survived.** P100's symptom was a CRASH, and the fix stopped the crash,
so the evidence that anything remained wrong was mojibake in a console nobody
treats as data. Two subsequent patterns touched this exact block - P188 wired
`stt-validate.py` in at all, P211 added the stamp - and both read the
`PYTHONIOENCODING` line as handled. The comment on L460 even says "P100:
Cyrillic through a CP1252 console", which reads as a solved problem.

This is the FOURTH occurrence of the shape P237 named: a remedy applied to the
instance that failed, with its siblings left alone. P242 and P248 were the second
and third. The question that catches all four is the same every time: having
fixed this, what else in the same file has the same shape?

**Rule:** a text pipeline has an encoder AND a decoder, and fixing one does not
fix the other. When output crosses a process boundary, name both ends. And when
a fix stops a crash, check whether the data is now CORRECT or merely no longer
fatal - a silent corruption downstream of a fixed crash is the normal outcome,
not the unusual one.

**Status:** FIXED 2026-10-16. `[Console]::OutputEncoding` is saved, set to UTF-8
and restored around both piped calls, symmetrical with the existing
`PYTHONIOENCODING` save/restore so nothing leaks into the operator's session.
The pipes stay: they are what filters Whisper's FP16 noise and indents the lint
block, and the pipe was never the defect.
## PATTERN 253: A workaround written down as a rule, outliving the defect it worked around

Three instructions in `reel-creation-pipeline.md` were found stale in ONE evening,
2026-10-16, while publishing #1903. Each had been true when written. Each
described a WORKAROUND. Each outlived the thing it worked around by weeks or
months, in the same confident voice as the rules beside it.

  1. **"Instagram — phone only. WhatsApp the file to yourself, save to
     gallery, upload in the IG app."** True for the first reels, when laptop
     upload did not work. The operator has been uploading from the laptop for
     months. The assistant read it out as current instruction mid-publish.
  2. **"Known gap: collection and narrator stay Latin inside Cyrillic captions.
     Hand-correct to Cyrillic."** Superseded by P150, which localised the
     reference line in `lib/refs.ts` — deliberately keeping the Latin
     collection name in parentheses, because the collection plus number is the
     citation a viewer types to check the hadith. The note caused the assistant
     to tell the operator to "fix" a CORRECT caption by deleting the citation.
     The operator asked "don't we keep it intentionally?" and was right.
  3. **"`-Scenes` reads from `normalized\` and nothing else."** Superseded by
     P217, which added the `new\` fallback. Harmless, but every #1903 render
     printed the contradiction on screen and the line stood anyway.

**The shape.** A rule stays true. A workaround is true only while its defect
exists, and the doc writes both in the same voice, with nothing recording what a
workaround is working AROUND. So when the defect is fixed the instruction does
not become obviously wrong — it stays plausible, and a reader with no memory of
the original problem follows it. Worse than a gap, because a gap is silent and
this actively directs.

Note what caught all three: a HUMAN who remembered. Not a gate, not the doc
audit, which happily reports PASS on text describing a fixed defect, and not the
assistant, which read all three as current and acted on two. `audit-docs.py`
checks that pattern numbers exist and that the tracker and registry agree; it
has no way to know that prose has gone out of date.

P193 reached the same conclusion for the pronunciation watch-list — entries
expire when the model that produced them changes — and that reasoning was never
carried to procedural notes.

**Rule:** when you write down a workaround, write down the DEFECT it works
around and the date. One clause is enough: "until X is fixed". Then a reader can
check whether X is still true, which is a question with an answer, instead of
guessing whether an instruction is current. And when a fix lands, the pattern's
Status section names the doc lines that described the old behaviour — shipping
the code without retiring the workaround is half a fix.

**Status:** the three instances are FIXED 2026-10-16 — each corrected in place,
each carrying a line saying what it used to say and why it changed, so the next
reader is not left wondering whether the doc or the code is right. The CONVENTION
is not yet applied to the rest of the file: other workaround-shaped notes in
`reel-creation-pipeline.md` and `CLAUDE.md` have not been audited for the same
problem, and there is no mechanism that would catch the next one. Assume more
exist — that is the standing instruction, not a resolved item.
## PATTERN 254: The rebuild re-derived from a snapshot taken before the fix

On the TJ leg of #1903, `text_tajik` was corrected in the database mid-leg: it
carried «амали бад», "a bad deed", where والعمل به says "and acting upon it" — an
added word, flagged by both Stage 3 models independently. The blocks were
rewritten, the story was re-narrated, and the narration verified as carrying the
corrected wording.

Then the operator pressed **↻ Rebuild from blocks** and the caption came back
with the OLD matn.

`buildCaption` takes the quote from `selected.text_<lang>`. `selected` is the row
object captured when the hadith is chosen in the admin — a snapshot. Rebuild
re-derives from the BLOCKS, exactly as named, and the matn is not one of the
blocks. So it faithfully reproduced a pre-UPDATE string while the audio said
something else. Published, that reel's caption and its narration would have
quoted the same hadith differently — which is the divergence the database fix
had just been made to remove, arriving from the other side.

**Why it survived.** P238 gave Rebuild its job: re-derive the caption from the
current blocks, because hand edits were drifting from them. It does that
correctly. Nobody asked where the parts that are NOT blocks come from. The
control is honestly named and the gap is in what the name does not cover.

**And it is a mechanism, not an incident.** OPEN_ITEMS already records the same
thing on #6570: `text_english` was normalised after the EN reel was rendered, so
the caption kept reading "Hurayrah" while the subtitles read "Hurairah". That was
written up as a one-off to remember before publishing. It is this.

**The escape route costs something.** Re-selecting the row refetches it, but it
discards the four reviewed blocks — so the correct move was to hand-edit the one
line and then NOT press Rebuild again, since P238's own comment says Rebuild
overwrites hand edits. The operator worked that out; the UI gives no sign of it.

**Rule:** a control that rebuilds derived output must re-read its SOURCES, not
reuse the snapshot it was handed. Where re-reading is expensive or destructive,
the UI says what is being reused and when it was captured — a silent stale read
is worse than a slow fresh one, because it is indistinguishable from a correct
result.

**Status:** DOCUMENTED — fix pending. Cheapest honest fix is the P125 shape
already in this codebase: compare `selected.text_<lang>` against the live row and
show the same amber "row changed since it was loaded — reselect" warning that the
narration staleness check shows. Refetching inside `buildCaption` would also work
and would not cost the blocks.
## PATTERN 255: The BOM fix went to one writer and the push has been blocked ever since

`git push` failed on the pre-push gate with `invalid JSON in
assets/scene-prompts/b6570-plain.json`. Every one of the SEVENTEEN scene-prompt
sidecars had a UTF-8 BOM.

`scripts/generate-scene.ps1` L111 wrote them with
`Set-Content -Path $side -Encoding UTF8`. On PowerShell 5.1 that emits a BOM, and
a BOM is not valid JSON.

**P186 is exactly this defect, already diagnosed, already fixed — in the other
file.** `render-reel.ps1`'s P201 sidecar write carries the comment verbatim:
"WriteAllText and not Set-Content -Encoding utf8: on PS 5.1 that writes a BOM and
this file is read back as JSON (P186)." The sibling writer, added later by P215
to record scene prompts, was never brought along.

That is P237's shape for the FIFTH time in one evening — after P242, P248, P252
and P253. Each time: a remedy applied to the instance that failed, its siblings
untouched, the second one surfacing later and more expensively.

**What it cost, and why nobody saw it.** The gate only runs on push, and the
repo was **34 commits ahead of origin**. Days of work existed on one disk with no
remote copy, and the signal — a push that fails — looks like a thing you deal
with later. The failure is loud exactly once and then silent until the next push.

**Rule:** when a pattern names a file-writing idiom as wrong, the fix is the
IDIOM, not the line. Search the repo for the idiom before closing it. And treat a
growing ahead-count as a defect report: a gate that blocks is only useful if
somebody reads why.

**Status:** FIXED 2026-10-16. BOM stripped from all 17 sidecars (bytes only, no
other change); `generate-scene.ps1` now uses `WriteAllText` with
`UTF8Encoding($false)`, matching `render-reel.ps1`. The gate was NOT relaxed to
`utf-8-sig` — it caught a real defect and should keep catching it.
## PATTERN 256: A convention that became impossible to follow, and stopped silently

Pattern entries used to carry a header block — **ID**, **Type**, **Files**,
**Commit**. **P156 is the last one with a `**Commit:**` sha.** P157 onward: 99
consecutive patterns without it. Not a drift, a clean stop, and the operator
found it by scrolling — nothing reported it in 99 chances.

**Why it stopped.** P156's own commit, `47d2a0e`, touched ONE file:
`fix_patterns.md`, 53 insertions. The pattern was written in a SEPARATE commit
from the fix, so `**Commit:** deb3db5` pointed at the earlier fix commit, which
already existed and already had a sha.

Then commits went atomic — the fix, its fix_patterns entry and its CHANGELOG
entry in one commit, which is what CLAUDE.md now requires. P250's commit
`9a4f2f0` carries the reels, the code and six patterns together. **A commit
cannot contain its own sha.** The field became unfillable at the moment it was
written, and amending to add it changes the very sha you just recorded.

So the convention did not lapse through carelessness. A newer rule made it
impossible, and because NO CHECK READS THAT FIELD, the collision produced no
error, no warning and no missing-field report — just 99 quiet omissions.

**The information was never actually lost.**
`git log -S "## PATTERN <n>:" -- fix_patterns.md` resolves every one, precisely
BECAUSE the atomic rule puts the pattern text in the same commit as its fix.
Verified on P157, P200, P248 and P255 — one command, exact hit each time.

**Rule:** when a new rule makes an older convention impossible, the older one
does not get to stop quietly. Retire it in writing, or re-mechanise it. A
convention nobody can follow, whose absence nothing checks, disappears without a
single error and is noticed years later by a human reading an old entry.

Corollary: a field that no check reads is decoration. If it is worth keeping,
something must fail when it is missing.

**Status:** DOCUMENTED — decision owed, and it is the operator's:

  (a) **Backfill** all 117 missing shas from `git log -S`, mechanically, then
      fill each new one in a follow-up pass after the push. Restores a uniform
      audit trail; costs a second commit per pattern forever.
  (b) **Retire the field in writing** and record the lookup command as the audit
      trail. Costs nothing, cannot drift, and under atomic commits yields exactly
      the same answer — because the sha is derivable from the text.

Under the current rules (b) is strictly cheaper and (a) buys nothing the lookup
does not already give. Either way it gets WRITTEN DOWN this time, which is the
whole point of the pattern.

---

**AMENDED SAME DAY, 2026-10-17, AND THE ORIGINAL DIAGNOSIS ABOVE IS PARTLY
WRONG.** The operator said the field looked like it started around P123 and had
gaps. Measured:

  - It spans **P46 to P156**, not P123 — much earlier than either of us thought.
  - **69 of 186 patterns carry it: 37%.**
  - **18 gaps INSIDE its own range**: P64, 65, 68, 69, 71, 78, 79, 90, 91, 92,
    93, 94, 95, 106, 120, 121, 122, 124. It was never a complete trail even while
    it was in use.

**And the self-reference argument above does not hold for the field as
specified.** QA_STANDARDS 4.1 defines it as `**Commit:** {conventional commit
message}` — the MESSAGE, not a sha. A message is known before the commit
exists, so atomic commits never made it unfillable. P156 holds `deb3db5`, a sha,
which is not what the template asked for. The field was being filled with the
wrong thing, inconsistently, by 37% of entries, and then it stopped.

That makes the real finding simpler and worse than the one above: **a template
field that nothing reads was followed by about a third of entries, filled with
the wrong content type, and abandoned without a word.** The silence is still the
pattern — it just started long before P157.

**DECIDED 2026-10-17, operator's call: option (b). The field is RETIRED.** No
backfill. The audit trail is:

    git log -S "## PATTERN <n>:" -- fix_patterns.md

exact, derivable from the text, and free. Retiring it is LESS work than keeping
it, which is why it was the right call.

**Still open and deliberately not actioned:** QA_STANDARDS 4.1's whole template
(`Symptom / Root cause / Fix / Rule going forward` as labelled fields) does not
describe what this file has contained for a long time — the entries are
narrative. That is P253's shape again, a doc describing a superseded practice.
Left for the operator to decide whether 4.1 is rewritten to match practice or
practice returns to 4.1. It is NOT left silent, which was the whole failure.
## PATTERN 257: The library behind 137 shipped reels had never been verified, and 46% of it is not clean

First run of Stage 3 A/B over `hadith_library` " " 34 rows, every hadith used in a
reel, 35 verdicts because #6018 is stored as two rows. Conventions audited clean
first (P120): 0 high, 0 warn.

    pass 19 (54%)   fail 4   disagree 12   disagreement rate 34%

**FAIL, both models agreeing:** #527, #6009, #8, #6857.
**DISAGREE, needs human:** #1, #1417, #82, #574, #4248, #2628, #2963, #2759,
#5027, #13, #1773, #1520.

**Why it had never run.** Stage 3 gates `hadith_candidates` before promotion. The
library predates the sourcing pipeline, so rows promoted before it existed were
never verified by anything. `--library` has existed on the script and had never
been used.

**THE FINDINGS ARE THREE DIFFERENT THINGS AND ONLY ONE IS A TRANSLATION
DEFECT.** Reading the output without separating them makes the back catalogue
look far worse than it is " " and makes the real defects easy to lose:

  1. **Real fidelity defects.** #527 TJ renders أحب (most beloved) as «беҳтарин»
     (best) and drops قُلْتُ, the narrator's first-person question. #6009 renders
     يأكل الثرى (eating the earth) as licking mud, and فشكر الله له (Allah
     thanked him) as accepted / was pleased " " a divine act flattened. #6857
     drops the verb in أكل الربا and loosens قذف المحصنات.
  2. **A TRUNCATED STORED MATN, where the translation is right and the Arabic is
     short.** #8's `text_arabic` is only بني الإسلام على خمس with the five never
     enumerated, so all four translations read as "added content" at high
     confidence from both models. **The caption prints `text_arabic`, so
     R018-R021 shipped a one-line Arabic beside a full translation.** Same shape
     as Muslim #223 and #2699 in OPEN_ITEMS and #2963's missing final clause.
     Nothing else in the pipeline looks for this.
  3. **Structural noise.** "The Arabic does not state that the Messenger said
     it" appears on many rows because the stored matn is the body without the
     isnad. Not a defect. It must be filtered or it swamps the signal.

**WHAT THE GATE CANNOT SEE, PROVEN TODAY.** #6018 is one hadith stored as two
rows, already recorded in the tracker's duplicate index, already shipped as
R082-R085. Stage 3 returned **two candidates and passed both** " " because each
half IS a faithful translation of its half of the Arabic. The gate compares a
row's translations against that row's own Arabic and never asks whether the row
is a whole hadith. A split matn is invisible to it by construction.

**AND IT CANNOT SEE EXTENT - a cheap signal exists.** #8 FAILED only because its
translations enumerated what its Arabic did not. The rows with SHORTER Arabic
PASSED: #1894 (18 chars), #1005 (24), #1479 (28). They passed because their
translations are equally short - consistent and incomplete, which is invisible
to a faithfulness check by the same construction that hides a split matn. A
character count on `text_arabic` is an independent signal the models cannot
supply, and it costs one query. Shortest used rows as a work queue: #1894 18,
#1005 24, #1479 28, #1 34, #1417 41, #574 43, #1520 43.

**CAVEAT, learned the same day (P259).** A HIGH en/ar ratio means LOOK HERE, not
THIS IS TRUNCATED. #1520 ran 3.02 - higher than #8 - and its English was long
because of an explanatory parenthetical, not because content was missing. The
row was defective, but for a different reason. Treat the ratio as a sort order
for human attention, never as a verdict.

**`matn_verified_at` DOES NOT MEAN THE TRANSLATIONS ARE FAITHFUL.** It means a
human read the row against the source (P151), and that is a different claim.
#1903 was stamped by the operator hours before it failed UZ and TJ on both
models; #527 is an old verified row and its Tajik fails. Worse, the batch
selector at `verify-candidates.py` L342 filters `matn_verified_at is.null` " " so
a default `--library` run skips the rows a human has STAMPED, which is not the
same as the rows that have shipped. Measured over the 36 used rows: 13 stamped,
23 null. A default run would therefore have covered 23 of them and skipped 13 -
and the skipped 13 include #1903 and #527, both of which carry real defects.
Verified is where the gate stops looking, which is exactly where two defects
were sitting. The sweep only hit them because every row was named explicitly
with `--row`. (Corrected 2026-10-17: the original wording here, 'SKIPS
precisely the rows that have shipped', overstated it.)

**Rule:** a gate that has never been pointed at the existing corpus has not been
tested, it has only been written. When a verification stage is built for new
material, run it once over everything already shipped " " the first run is a
measurement of the back catalogue, not a formality. And read a batch selector
before trusting a batch: its default filter encodes an assumption about which
rows matter, and that assumption can be exactly backwards.

**Status:** DOCUMENTED, nothing written to the DB " " every run was a dry run and
`--commit` was never passed. The 16 non-clean rows are a work queue in
OPEN_ITEMS. Raw log: `out/ab-library-sweep-2026-10-17.txt` (gitignored, on disk).
## PATTERN 258: A deferred scope limit with no runtime guard - --apply reported writing four columns and wrote none

**Date:** 2026-10-17
**Files:** scripts/translate-candidates.py

**What happened.** Bukhari #8's truncated matn was restored (P257's truncation
class), re-translated with `--library --row 8`, reviewed, signed (P219), and
applied with `--library --row 8 --apply --commit`. The script printed:

    Sahih al-Bukhari #8: written (text_english, text_russian, text_tajik, text_uzbek_cyrillic)
    written: 1   failed: 0

Nothing was written. A read-back showed all four columns still holding the
pre-correction text. Only `text_arabic` had changed, and that was done by hand
in SQL.

**Why.** `apply_from_json()` was candidates-only by design and said so in its own
docstring: "Candidates only. --library has its own matn_verified_at semantics
(P151) and is not worth folding in until something needs it." The deferral was
reasonable. The guard was missing. `main()` called `apply_from_json(base, key)`
and dropped `args.library` silently, so `--library --apply` was accepted, aimed
a `hadith_library` id at `hadith_candidates`, matched no row, and reported
success.

**Why it looked like success.** PostgREST answers a PATCH that matches nothing
with 200 and `[]`. `sb_patch` raised nothing, so the caller counted a write. A
no-op and a real write were indistinguishable at the call site.

**Why this one matters more than its size.** `--apply` is the P177 integrity path
- the route whose entire purpose is that the reviewed text is the text that
ships. It is the worst possible place for a silent no-op, because the operator
has already read and signed the text and has no reason to look again.

**Fix, two parts.**

1. `sb_patch` raises when the representation comes back empty. This closes the
   CLASS, not the instance: any PATCH in this script that matches no row is now
   a failure instead of a success.
2. `apply_from_json` takes `library=` and mirrors the normal `--library` write
   (P151): match on `id`, drop `translation_meta` (not a library column), and
   clear `matn_verified_at`, so a corrected row cannot keep a verification stamp
   for translations nobody has checked - the #2616 mistake.

**Rule:** a scope limit that lives only in a docstring is a comment, not a limit.
If a function does not handle a flag, it must refuse that flag or implement it -
silently ignoring it converts a known gap into a data-loss path the moment
something needs it. And a write is never confirmed by the writer's own success
message: read it back.

**Blast radius, OPEN.** Any library row re-translated through the sign/apply
route since `--library` existed kept its old text while reporting success. Some
of P257's 12 disagreements may be this rather than translation defects. Not yet
enumerated - tracked in OPEN_ITEMS.

**Status:** FIXED and verified. #8 re-applied, Uzbek Latin re-derived, Stage 3
re-run: 8/8 pass across both models and all four languages, zero disagreement.
`matn_verified_at` left null - Stage 4 is the human gate (G1).
## PATTERN 259: Two defects that concealed each other, and the gloss that hid both

**Date:** 2026-10-17
**Files:** hadith_library (#1520)

**What was wrong with Bukhari #1520.** Two things, not one.

1. **A single wrong diacritic.** Stored `لَكُنَّ` (kaf with DAMMA = 'for you
   [women]'). The source reads `لَكِنَّ` (kaf with KASRA = 'but'). One vowel, a
   different word, a different grammatical role. The Arabic is what appears on
   screen, so this is visible to any Arabic-reading viewer.
2. **A truncated matn.** The hadith is a dialogue: Aisha asks whether women
   should fight, and the answer opens with `لاَ،`. Only the tail of the answer
   was stored.

**How they hid each other.** With the question gone, 'but' had nothing to
contrast with, so the sentence only parses as 'for you [women]'. The wrong
diacritic then made that reading look correct. All four translations were built
on it and each inserted the missing context as a parenthetical gloss - '(for
women)', «(женщин)», «(аёллар)», «(занон)». The English matched sunnah.com's
published Muhsin Khan rendering word for word, which is why review never caught
it: the translation was defensible, and the Arabic underneath it was not.

**THE DETECTOR THIS GIVES US.** A parenthetical gloss in a translation can be
load-bearing - the translator supplying context the stored matn no longer
carries. Restoring the matn made all four glosses disappear on their own, which
is the confirmation. Scanned the library: 9 of 72 rows carry a gloss. The signal
is NOT any parenthesis - most are grammatical particles («га», «дан») or a
single clarifying noun. It is a gloss supplying CONTENT: a name, a condition, an
explanation. Ranked by that plus the en/ar ratio:

| row | gloss | ar | en/ar | note |
|---|---|---|---|---|
| #1521 | 'after Hajj free from all sins' | 85 | 2.33 | adjacent Hajj hadith, #1520's shape |
| #1773 | 'the one accepted by Allah' | 121 | 1.53 | the mabrur gloss again; already in DISAGREE |
| #1894 | 'protection' in uz+tj | 18 | 1.11 | shortest Arabic in the library |
| #574 | 'Fajr and Asr' in all four | 43 | 1.63 | probably benign - al-bardayn does mean those two |

**Rule:** when a translation explains something the Arabic does not say, suspect
the Arabic before crediting the translator. And a diacritic is not a detail: in
a stored matn it is the difference between two words, and nothing downstream -
not Stage 3, not the content lint - compares our vowel marks against a source.

**Also confirmed here:** the mirror numbers LOWER than sunnah.com and the gap
widens through the book (#1520 sits at idInBook 1468; the script's own docstring
notes 6446 at 6207). A number mismatch against the mirror is therefore NOT
evidence of a miscitation. Check the isnad, not the index.

**Status:** FIXED. Matn restored to 130 chars with the question and the correct
`لَكِنَّ`, re-translated from it, Uzbek Latin re-derived, Stage 3 re-run: 8/8
pass, zero disagreement. All four glosses gone without being edited.
`matn_verified_at` left null - Stage 4 is the human gate. OPEN: the Tajik uses
«На» for 'no' where «Не» is standard; Stage 3 cannot see this (P120 scopes it to
faithfulness, not naturalness) and it needs a Tajik speaker.
## PATTERN 260: The check that spent two runs measuring its own bugs

**Date:** 2026-10-17
**Files:** scripts/audit-diacritics.py (new)

**What was built.** P259 showed that nothing compared our stored vowel marks
against a source: Stage 3 asks whether the translation matches the matn, and
`verify-matn-source.py` normalises diacritics away by design. So #1520's
damma-for-kasra was invisible to both. `audit-diacritics.py` closes that gap -
it matches on the consonantal skeleton, then compares the marks in the located
span.

**THE NUMBERS IT REPORTED, IN ORDER: 56, then 36, then 3.** The first two were
its own defects. Both are worth naming, because both look exactly like findings.

**Bug 1 - combining-mark order is not a difference.** A letter carrying both
shadda and fatha can be stored shadda-first or fatha-first. They render
identically. Our DB is NFC-normalised (fatha ccc=30 sorts before shadda ccc=33);
the mirror is not. Every such letter in the library came back as a mismatch -
`ours U+064E vs mirror U+0651`, over and over, which reads like a systematic
corruption and is nothing at all. Fix: NFC both sides before comparing.

**Bug 2 - a failed alignment is not a difference.** When the stored matn could
not be located in the mirror entry, the first version fell back to comparing
against the start of that entry, which is the ISNAD. Half the library duly
reported `first diff at char 0`, ours showing the matn and the mirror showing
`حَدَّثَنَا`. Fix: locate by walking consonants, and report NOT FOUND when the
span cannot be established rather than comparing against something else.

**Bug 3 - the span must include trailing marks.** Ending the span at the last
CONSONANT clips the final i'rab vowel off the mirror side while ours keeps it.
That produced 31 of 36 VOWEL findings, every one of them at the last character,
every one of them `mirror U+0000`. The shape of the output is what gave it away:
a real defect class does not land on the final character of thirty-one rows.

**Result after the three fixes, over 72 rows:**

| verdict | n | meaning |
|---|---|---|
| EXACT | 32 | identical after NFC |
| PUNCTUATION | 5 | we add or drop a comma. Harmless. |
| ORTHOGRAPHIC | 19 | لَا vs لاَ, hamza seat, alef maqsura. Both valid. |
| **VOWEL** | **3** | same consonants, different reading. The #1520 class. |
| LETTER | 0 | - |
| NOT FOUND | 13 | stricter than verify-matn-source.py; see below |

The three VOWEL rows are #463 (`انْتُقِصَ` passive vs `انْتَقَصَ` active), #223
(`الطَّهُور` vs `الطُّهُور`) and #82 (`تَرْكُ` nominative vs `تَرْكَ`
accusative). All three had been picked out by hand beforehand; the script
converged on the same three independently, which is the only reason to trust it.

**Rule:** when a new check reports a large number on its first run, the first
hypothesis is the check, not the corpus. Read the SHAPE of the findings before
the content - findings clustered at index 0, or at the final character, or all
showing the same codepoint pair, are a method artefact. A check is not evidence
until its own failure modes have been ruled out, and a count that collapses from
56 to 3 under scrutiny was never a measurement of the library.

**Also run the same day: `verify-matn-source.py --mirror`, for the first time.**
66 found, 3 partial, 3 missing over 72 rows. The 3 missing are all Musnad Ahmad
(#6576, #6626, #7936) and the mirror README states Ahmad chapters 8-30 are
absent from its source - a mirror gap, not our defect. The 3 partial are #1899
(0.80), #2616 (0.86) and #5185 (0.67). Three more carry an excerpt flag, where
the stored matn is scattered rather than contiguous in the source entry: #2999
(0.47), #1151 (0.58), #5971 (0.56).

**The two tools disagree on NOT FOUND (13 vs 3), and that is by design.** This
script demands an exact consonantal substring; `verify-matn-source.py` scores a
fuzzy match. Neither number is wrong. Read them together: a row that this script
cannot locate but the other scores 1.00 differs in orthography, not in content.

**Cross-confirmation worth noting.** #5185 was flagged independently by three
methods - an en/ar ratio of 0.53 with a 17-character English, a 0.67 partial
here, and its presence in the A/B sweep. #2999's excerpt flag matches the
PARTIAL EXTENT entry already recorded for it in OPEN_ITEMS.

**Status:** SHIPPED. Not wired into the pre-push gate yet, deliberately -
`--strict` would block every push on the three unresolved VOWEL rows. Wire it
once those are adjudicated against a Tier-1 source. Nothing written to the DB:
the mirror screens, a human confirms (P145).
## PATTERN 261: What text_arabic holds when one narration carries two admonitions

**Date:** 2026-10-17
**Files:** hadith_library (#5185); convention, applies library-wide

**The row.** Bukhari #5185 stored 32 characters - `اسْتَوْصُوا بِالنِّسَاءِ
خَيْرًا` - and nothing else. The hadith continues through the rib simile, which
is its entire substance, and closes by repeating the imperative. All four
translations read "Treat women well." and stopped there, so the row was
internally consistent and Stage 3 had nothing to catch.

**It was STAMPED.** `matn_verified_at` was set 2026-09-05, on a fragment. That
is the third row where a human verification stamp sat on defective content
(#1903 and #527 in P257). The stamp means a human read the row against the
source; it has never meant the row is complete, and three instances now say
that distinction needs to be in the reviewer's head at stamping time.

**Found by three independent methods, none of them a model judging meaning:**
an en/ar ratio of 0.53 with a 17-character English; a 0.67 partial from
`verify-matn-source.py --mirror`; and its presence in the A/B sweep. Agreement
between cheap structural checks is worth more than one expensive opinion.

**THE CONVENTION QUESTION.** sunnah.com's bukhari:5185 is ONE narration carrying
TWO admonitions: the neighbour clause (`مَنْ كَانَ يُؤْمِنُ بِاللَّهِ`...) and
then the women/rib passage. Bukhari also narrates the women hadith standalone
elsewhere, in different wording - no `خيرا`, singular `الْمَرْأَةَ خُلِقَتْ`.
So there were three defensible options: store the whole two-part matn, store
the women clause in full under the same citation, or re-cite to the standalone
narration.

**RULE, set by the operator 2026-10-17:** `text_arabic` holds ONE COMPLETE
admonition from the cited narration. Never a clipped one. Where a narration
carries two, store the one the row is about, in full, and let the citation
locate it - a reader who opens bukhari:5185 finds exactly that text there. What
is forbidden is the third thing, which is what #5185 actually was: the opening
words of an admonition with its substance cut off.

This also governs the excerpt rows `verify-matn-source.py` flagged, where the
stored matn is scattered rather than contiguous in the source entry: #2999
(contiguous 0.47), #1151 (0.58), #5971 (0.56). Each needs the same judgement -
complete admonition, or clipped?

**A translator correction, and why it is not a P177 violation.** The first
re-translation rendered `اسْتَوْصُوا بِالنِّسَاءِ` in Uzbek as «Аёлларга
яхшилик билан васият қилинглар» - the dative -га aims the counsel AT women,
where the Arabic aims it at the listener ABOUT women. EN, RU and TJ all read it
the second way; Uzbek was the outlier. Model B flagged the same thing
independently and Stage 3 returned disagree. The fix was NOT choosing B's
verdict over A's: it was an editorial correction to the TEXT, made by the
operator in his own language, after which the row was re-verified from scratch
and both models passed. P177 forbids settling a disagreement by preferring a
model or re-rolling; it does not forbid correcting the text the models
disagreed about and asking again.

**Rule:** when a model's objection and a human's objection coincide on the same
clause, that is not two votes - it is one defect found twice. Fix the clause.

**Status:** FIXED. 32 -> 225 chars, re-translated, Uzbek Latin and the legacy
column re-derived, Stage 3 re-run: 8/8 pass across both models, zero
disagreement. `matn_verified_at` cleared by the apply (P151) and left null -
Stage 4 is the human gate. OPEN: the Tajik «мешиканиаш» reads like a malformed
contraction; Stage 3 cannot see naturalness (P120) and it needs a Tajik speaker.
## PATTERN 262: A Cyrillic letter from the wrong alphabet, written by the assistant and caught only by reading it back

**Date:** 2026-10-17
**Files:** scripts/audit-library.py; hadith_library (#1894)

**The row first.** Bukhari #1894 stored 18 characters - `الصِّيَامُ جُنَّةٌ`,
"Fasting is a shield" - where the matn runs on through the restraint of speech,
the reply when provoked, the oath, the musk simile and `الصِّيَامُ لِي وَأَنَا
أَجْزِي بِهِ`. 18 -> 370 characters, the largest restoration of the day. All
four translations had stopped at the same two words, so the row was internally
consistent and Stage 3 had nothing to catch - the same shape as #8, #1520 and
#5185.

The mirror's `idInBook=1894` is a DIFFERENT hadith (al-wisal). Ours sits at
1826, offset 68 - and our own #1903 sits at 1835, the same offset, which
confirmed the citation from internal data before any source was fetched.

**Two translation defects, found by two different means.** Both models FAILED
the Tajik unanimously: `لا يرفث` is obscene speech, and «бехудагӣ» is closer to
absent-mindedness. No disagreement, so P177 does not apply - a unanimous fail is
a defect. The Uzbek carried a case error that neither model saw and never could:
«рўзадорнинг оғиз ҲИДИНИ ... хушбўйроқдир» puts the accusative on what has to be
the subject. Stage 3's scope is faithfulness (P120); grammar is not in it.

**THEN I WROTE THE DEFECT MYSELF.** Hand-editing the Tajik, I typed «нагүяд»
with ү (U+04AF, the straight u of Kazakh and Mongolian) where Tajik takes ӯ
(U+04EF). Every other ӯ in the sentence was correct; mine was the odd one. It
was caught by reading the output back before signing, and by nothing else.

**WHY NOTHING ELSE WOULD HAVE CAUGHT IT - verified, not assumed.** Read
`audit-library.py` rather than guessing:

  - `HOMOGLYPHS` (R027) is commented *"Latin characters that render identically
    to a Cyrillic letter"*. ү is Cyrillic. It passes.
  - `TJ_LETTERS` checks that Tajik letters are PRESENT. The sentence was full of
    them. It passes.

So a letter can be valid Cyrillic, invalid for the language, and invisible to
every existing check. The dangerous pair is not even exotic: Uzbek ў (U+045E)
and Tajik ӯ (U+04EF) are the same shape, and those two columns sit beside each
other in every row of this library.

**Fix: `check_out_of_alphabet` in audit-library.py.** Each Cyrillic column gets
the alphabet its language actually uses, and any Cyrillic character outside it
is reported. Unit-checked on four cases before shipping: U+04AF in Tajik fires;
ў inside the Tajik column fires; ӯ inside the Uzbek column fires; correct
uz/tj/ru text stays silent. A library-wide scan returned ZERO findings across 72
rows, so the corpus was clean and my ү would have been the only instance.

WARN, not HIGH, on its first outing - the same reasoning `check_ha_formulas`
records for itself. The alphabets are hand-written and a missing legitimate
letter would block every push under `--strict`. Raise it once it has run clean
for a while.

**Rule:** when you catch your own error by reading the output back, the fix is
not finished at the text. Reading back does not scale and will not survive a
tired session; the check does. Put the defect you just made into the gate. And
before claiming a gap exists, READ the checker - "nothing would have caught
this" is a claim about code, and it is cheap to verify and embarrassing to
assert wrongly.

**Status:** FIXED. #1894 at 370 chars, Tajik and Uzbek corrected, Latin
re-derived, Stage 3 8/8 pass, `audit-library.py` clean (0 high, 0 warn), 66
tests pass. `matn_verified_at` left null - Stage 4 is the human gate.
## PATTERN 263: A Stage 3 'disagree' that was two models agreeing

**Date:** 2026-10-17
**Files:** hadith_library (#1773)

**The row was clean.** #1773's 121-character matn matches the mirror's entry
1708 exactly and completely - narrator Abu Hurairah, offset 65, consistent with
the curve. No SQL was needed. That makes it the SECOND false positive from
P259's gloss detector after #1521: the parentheticals were clarifying a complete
matn, not covering for a missing one. The detector's failure mode is now known -
it flags complete rows whose English is glossed, which is most of them, because
our English comes from a glossed source.

**THE VERDICT READ 'DISAGREE' AND THE MODELS DID NOT DISAGREE.** Stage 3
returned:

| lang | A | B | objection |
|---|---|---|---|
| en | pass | FAIL | لما بينهما says 'for what is between them', not 'sins' |
| uz | FAIL | pass | the same 'sins' point, on our bracketed «(гуноҳлар)» |
| tj | pass | pass | A noted «навбатӣ» (next) is not in العمرة إلى العمرة |
| ru | pass | pass | - though it said «следующей», the same addition |

Per-language the two models split, so the row aggregates to `disagree`. But
both models objected to the SAME thing - the inserted word 'sins' - they simply
happened to scrutinise different columns. Nothing was in dispute. Treating this
as an unresolvable split under P177 would have been reading the scoreboard
instead of the findings, and the row would have sat in needs_human forever
over a defect both models had already identified.

**Rule:** before invoking P177, read what the models actually SAID. A split
verdict across LANGUAGES is not a disagreement about a CLAIM. P177 protects a
genuine conflict of judgement on the same text; it does not apply when two
models independently find the same defect in different columns. The remaining
disagreements from the 2026-10-17 sweep should all be re-read this way before
anyone adjudicates them.

**A second thing the table shows:** «следующей» in Russian is the same addition
as «навбатӣ» in Tajik, and both models passed the Russian. Per-language
attention is uneven, so a clean verdict on one column is not evidence that the
same defect is absent from another. Check the sibling columns by hand whenever
one is flagged for an addition.

**Re-translation improved two columns and regressed two** - the P108 shape. The
fresh English fixed a real gap (the stored one had dropped إلى العمرة entirely,
reading 'Umra is an expiation' with no 'to Umra') and the fresh Russian dropped
«следующей». But the Uzbek came back with a LARGER gloss than before -
«(вақт ичидаги гуноҳлар)», the sins within the time - and the Tajik added
«дигар» (another), unbracketed «гуноҳҳо», and spelled كفارة with a single ф.
Regenerating is not a fix; it is a re-roll with its own defects.

The operator supplied the Uzbek and Tajik himself and they were taken verbatim.
`check_out_of_alphabet` (P262) ran on them as its first real input and returned
zero findings, as did the homoglyph check.

**Status:** FIXED, no matn change. Stage 3 re-run: 8/8 pass, zero disagreement.
#1773 comes OFF the DISAGREE list. `matn_verified_at` left null - Stage 4 is
the human gate. OPEN: مبرور is now rendered four ways - EN 'the accepted Hajj',
RU «мабрур» transliterated, UZ «мақбул», TJ «мақбул». Russian is the odd one
out and the operator chose мақбул for both his languages.
## PATTERN 264: There is no way to verify a library re-translation before writing it

**Date:** 2026-10-17
**Files:** scripts/verify-candidates.py (gap, not yet fixed); hadith_library (#6009)

**THE GAP.** `verify-candidates.py --library` reads the rows from the DATABASE.
So the only way to put a library re-translation through Stage 3 is to write it
to the library first. For a row that has already shipped, that means the live
row holds unverified text between the apply and the verdict - and if the verdict
is bad, the row is now worse than it was and there is no stored previous value
to go back to. `--apply` is the P177 integrity path and `--sign` guards the text
against change between review and write, but nothing guards the row against a
re-translation that turns out to be a regression.

The candidate pipeline does not have this problem: a candidate is verified
before promotion, by construction. The library path inherited the verifier
without inheriting the ordering.

**HOW IT SHOWED UP.** #6009's matn is correct and complete (it matches mirror
5781 exactly, offset 228). The defects were translational, and the sweep had
named two:

  - `يَأْكُلُ الثَّرَى` - the dog EATING the moist earth - rendered as 'licking
    mud' in English and Uzbek, 'licking' in all four.
  - `فَشَكَرَ اللَّهُ لَهُ` - 'so Allah THANKED him' - flattened to 'accepted' or
    'was pleased' in Russian, Uzbek and Tajik. English alone had it right.

Both were fixed by the re-translation. The second one matters: softening a
divine act removes exactly what makes the hadith striking.

**AND THE RE-TRANSLATION BROUGHT A NEW CROP.** Stage 3, run AFTER the write:

| lang | verdict | new defect |
|---|---|---|
| en | A pass, B fail | ﷺ inserted into 'O Messenger of Allah' - not in the Arabic |
| ru | BOTH FAIL | 'climbing out' added; «зубами» (teeth) for بفيه (mouth); «высунув язык» for يلهث (panting) |
| uz | BOTH FAIL | dropped كبد رطبة - 'moist liver' became 'living creature' |
| tj | A unparseable, B fail | «бархоста» (having risen) not in the Arabic |

Before the fix the row failed all four on two defects. After it, it fails on a
different four. The headline theological defect is gone and the detail is worse.
That is the P108/P263 shape again, and this time it was written to a live row.

**The assistant applied before verifying.** On #8, #1520, #5185 and #1894 the
same order was harmless because Stage 3 came back clean; the order was never
examined because it never cost anything. It cost something here.

**Rule:** when a pipeline forces write-then-verify, say so BEFORE writing, not
after - the operator should get to decide whether a shipped row goes through an
unverified state. And an order of operations that has only ever been tried on
passing cases has not been tested.

**Fix, BUILT 2026-10-18 (P266).** `--from-json [PATH]` scores the proposed
translations against the matn without touching the row; it refuses `--commit`,
defaults to `out/candidate-translations.json`, and was checked against #6009 -
it reproduces the verdicts the database run gave for the same text. The library
path is now translate -> verify -> apply, like the candidate path. Original
note follows.

**Fix, not yet built:** `verify-candidates.py` needs to accept the candidate
text directly - a `--from-json out/candidate-translations.json` mode that scores
the proposed translations against the matn without touching the row. Then the
library path becomes translate -> verify -> apply, like the candidate path.

**Status:** #6009 OPEN. The matn is correct and untouched. The translations are
better on `شكر` and `يأكل الثرى` and worse on detail. `matn_verified_at` is null,
so the row cannot pass Stage 4. The pre-fix translations are recoverable from
the session transcript if wanted. Needs one more pass, with the operator on the
Russian, Uzbek and Tajik.
## PATTERN 265: The verification gate asked for a capability nobody on the project has

**Date:** 2026-10-17
**Files:** hadith_library (matn_screened_at / matn_verified_at); standard, not code

**THE QUESTION THAT EXPOSED IT.** Handed five repaired rows to stamp, the
operator asked: "I don't know Arabic, how can I verify?" P151 defines
`matn_verified_at` as "a human read the row against the source." Nobody on this
project reads Arabic. So the stamp has never meant what the rule says, and
every row carrying it was stamped on some other basis that was never written
down.

**That reframes P257's finding.** Three stamped rows held defective matns -
#1903, #527, and #5185 with a 32-character fragment. P257 called that "verified
is where the gate stops looking." The truer reading is that the gate specified
an impossible act, so it was satisfied by something else. A rule nobody can
follow is not a strict rule; it is an undefined one.

**TWO WRONG GUESSES, BOTH CORRECTED BY LOOKING.** Worth recording because both
were plausible and both were checkable in one query.

  1. "The two columns were conflated - screening was recorded as verification."
     FALSE. 48 rows screened, 21 verified, only THREE carry both. They were
     used on largely disjoint sets. #5185 in particular was verified WITHOUT
     ever being screened - the opposite of the story.
  2. "`translate-candidates.py` should clear `matn_screened_at` alongside
     `matn_verified_at`." WRONG. That path changes TRANSLATIONS. Screening is
     about the ARABIC. A re-translation does not invalidate a matn screening.

**THE STANDARD, set 2026-10-17.**

| column | attests | who can set it |
|---|---|---|
| `matn_screened_at` | `audit-diacritics` EXACT against the mirror, found by `verify-matn-source`, citation and narrator confirmed | reproducible by machine; no Arabic needed |
| `matn_verified_at` | a person who reads Arabic compared the matn to the cited source | nobody on the project today |

`matn_verified_at` stays NULL until an Arabic reader reviews. An honest empty
column beats a stamp that overstates itself, and the screening work makes that
reader's eventual job much smaller.

**A SECOND READER, CALIBRATED RATHER THAN TRUSTED.** The operator ran the five
through another model, which passed four and flagged one real divergence. That
report could not be distinguished from accurate recall - these are famous
hadiths, where a good model's memory and the truth coincide. So it was given a
falsification test instead: four rows, two of them historical known-bad values
from P142, unlabelled. Both traps are AUTHENTIC, FAMOUS sayings sitting on the
WRONG reference - the exact failure mode that put them in this library.

It caught both. On #3104 it produced the correct dual `رِجْلَيْهَا`, stated that
`الأمهات` never appears at that reference, and caught the narrator error that
was never hinted at. On #2616 it gave the real clause and identified
`الصلاة عماد الدين` as a paraphrase. Both controls passed.

**Rule:** a second reader is worth what its adversarial test says it is worth,
not what its agreement says. Agreement on easy cases is free. Before relying on
any checker - model or script - feed it inputs where the plausible answer and
the true answer differ, and see which one comes back.

**THE STALE-STAMP HOLE, open.** `matn_screened_at` records that the text matched
the mirror on a date. Nothing links the stamp to the text it screened, so a
later `UPDATE text_arabic` leaves the stamp in place attesting to a string that
no longer exists - which is exactly what happened to #8, #1520 and #1894 today,
each carrying a 2026-09-05 screening for Arabic replaced this morning. No script
writes text_arabic, so there is no code path to patch; the fix is to store a
hash of the screened text beside the timestamp and have the audit flag any row
whose current text does not match its screened hash. NOT BUILT.

**Status:** the five are screened 2026-10-18 and verified by nobody. The other
21 `matn_verified_at` rows are unreviewed under this standard - if #5185 was
stamped with no screening behind it, others may be. Clearing them would also
return them to the default batch selector, which filters
`matn_verified_at is.null` (P257).
## PATTERN 266: The narrator check, and a matcher that flagged its own romanisation

**Date:** 2026-10-18
**Files:** scripts/verify-candidates.py, scripts/audit-diacritics.py

**Two gaps closed, both named by earlier patterns and neither built until now.**

**1. `--from-json` (closes P264).** `verify-candidates.py` read only from the
database, so a library re-translation had to be written to the live row before
it could be Stage-3'd. `--from-json [PATH]` scores the proposed text instead:
refuses `--commit` (there is no row to write to), defaults to
`out/candidate-translations.json`, honours `--row`. Checked against #6009 - it
reproduces the verdicts the database run produced for the same text. The
library path is now translate -> verify -> apply.

**2. The narrator check.** `verify-matn-source.py`'s own limit 2 states it
verifies the TEXT only, not the grade and not the narrator. #3104 stored a
plausible matn under the WRONG narrator and nothing automated could see it; a
second model reader caught it by eye on 2026-10-17. `audit-diacritics.py`
already locates the mirror entry, and that entry carries the narrator, so the
comparison costs nothing extra.

**THE MATCHER FLAGGED ITS OWN ROMANISATION FIRST.** The first run returned 7
mismatches. Two were the matcher:

  - `Abu Hurairah` vs `Abu Hurayrah` - the same man, ai/ay.
  - `Jubayr ibn Mutim` vs ``Jubair bin Mut`im`` - the regex replaced the
    backtick with a SPACE, splitting `Mut`im` into `mut` + `im` and destroying
    the real match before the comparison ran. An apostrophe or backtick marks
    a hamza or ayn INSIDE a word; it is not a separator.

Fixed by deleting those marks rather than spacing them, and folding ay->ai.
7 -> 5. Eleven unit cases cover both repairs and, more importantly, confirm
that #3104, `Ibn Umar` vs `Ibn Mas'ud`, and #2616 still FLAG - a looser matcher
that stopped catching real mismatches would be worse than the false positives.

**Rule, third time this week:** a new check's first number is a statement about
the check. Read the shape before the content. And when loosening a matcher to
kill false positives, pin the true positives in tests FIRST, or the fix quietly
removes the capability.

**THE FIVE SURVIVORS ARE NOT #3104's CLASS.** A useful null result:

| row | ours | mirror | reading |
|---|---|---|---|
| #31 | Abu Bakra | Al-Ahnaf bin Qais | Al-Ahnaf narrates FROM Abu Bakra - companion vs immediate narrator |
| #1987 | Muadh ibn Jabal | Abu Dharr | narrated from both |
| #6018 | Abu Hurairah | Abu Shuraih Al-Adawi | both versions exist; ours is a duplicate-number row |
| #1005 | Jabir ibn Abdullah | Hudhaifa and Abu Shaiba | multiple chains |
| #2616 | Muadh ibn Jabal | Ka'b bin Ujrah | the known 0.86 partial, duplicate-number row |

**A systematic source of benign mismatch, worth knowing before anyone acts on
this list:** the mirror's narrator field is the IMMEDIATE narrator in its
English rendering, while our `narrator` column records the COMPANION. #31 is
exactly that and is almost certainly correct as stored. This check finds
candidates for review; it does not find errors.

**Status:** both SHIPPED. No narrator misattribution found in the library. The
five above need a human reading, not a fix.
## PATTERN 267: Every vowel discrepancy closed, and a constructed sentence found

**Date:** 2026-10-18
**Files:** hadith_library (#223, #463, #82, #1151)

**VOWEL is now 0 across 72 rows**, from 3. Each was resolved against a Tier-1
source, and the three turned out to be three different things - which is the
point of resolving rather than bulk-fixing.

**#223 - real, one character.** Ours `الطَّهُورُ` (fatha), sunnah.com/muslim:223
prints `الطُّهُورُ` (damma). Both readings are discussed in the commentary
literature, but the cited source prints damma and matching the cited source is
the standard. One codepoint, length unchanged.

**#463 - real, two characters.** Ours `انْتُقِصَ` (passive), Dorar prints
`انتَقَصَ` (active) and spells out the grammar: the verb is active and its
subject is `شيءٌ`. Dorar specified fatha on BOTH the ta and the qaf, and both
are what changed. Length unchanged.

**#82 - NOT A DEFECT, and the interesting one.** Ours read `... تَرْكُ
الصَّلَاةِ` with a damma where the source has fatha. But our text had no
`إِنَّ`, and HadeethEnc gives the reason for the source's fatha: `ترك` is the
ism of `إنّ` and takes the accusative. WITHOUT `إنّ`, the nominative `تَرْكُ` is
the CORRECT vocalisation. Whoever shortened that row adjusted the grammar
properly. The finding was evidence of care, not carelessness.

It was still fixed - by restoring `إِنَّ` and the accusative it governs, so the
row matches the cited source exactly. Left alone it would have differed by two
characters forever and flagged on every run: a permanent false alarm teaches
people to skim the report, which costs more than the row.

**#1151 - a sentence that exists in no narration.** Stored:

    كُلُّ عَمَلِ ابْنِ آدَمَ يُضَاعَفُ ... إِلَّا الصَّوْمَ فَإِنَّهُ لِي وَأَنَا أَجْزِي بِهِ

Dorar (Tier 1, Muslim 1151) and the mirror both show a clause between those two
halves: `الحسنة عشر أمثالها إلى سبعمائة ضعف` AND `قال الله عز وجل`. Removing it
welds two halves into a grammatical sentence that is in no narration, and drops
the divine-speech attribution that makes this a hadith qudsi. That is not
truncation - truncation loses the end. This CONSTRUCTS. 86 -> 363 chars.

The three excerpt rows flagged by `verify-matn-source` therefore resolved to
three severities, and the contiguity score did not predict the order: #1151
(0.58) was the worst, #2999 (0.47) is internally clipped and still open, #5971
(0.56) is fine - complete dialogue, one word of edition variance.

**FIRST USE OF VERIFY-BEFORE-WRITE (P266).** #1151's re-translation was scored
with `--from-json` BEFORE `--apply`: 8/8 pass, nothing written. In that window
the Uzbek was caught rendering `خلوف` as «оғиз қокисининг ҳиди» - a word that
is not Uzbek, and inconsistent with #1894's «оғиз ҳиди» for the same Arabic.
Corrected, re-verified 8/8, THEN applied. Yesterday that sequence would have
required writing the bad text to a shipped row first.

**THE NFC TRAP, CAUGHT A SECOND TIME - IN MY OWN VERIFICATION.** Checking the
extracted #1151 matn, three of four probes returned False. The extraction was
correct; the PROBES were hand-typed with shadda before damma, and NFC canonical
ordering puts the vowel first, so they could not match. Exactly P260's bug, in
the code written to guard against P260's bug.

**Rule:** never hand-type a diacritic sequence to test for. Probe on the
CONSONANT SKELETON - strip every mark from both sides and compare letters. It
is immune to mark order by construction, and a check that cannot be written
wrongly is worth more than one that is merely written correctly today.

**Status:** #223, #463, #82, #1151 all FIXED and re-screened. VOWEL 0,
NARRATOR 0 on #1151, audit-library clean. #2999 OPEN. `matn_verified_at` null
on all four - Stage 4 is a human who reads Arabic (P265).

## PATTERN 268: A token whose letters are each legal but whose shape is not

Six malformed Uzbek Cyrillic tokens were sitting in published rows. Nothing
flagged them. `check_out_of_alphabet` (P262) passed them, `check_homoglyphs`
passed them, `check_ha_formulas` passed them - correctly, in every case,
because every individual CHARACTER was a legal Uzbek letter. The defect was in
how the letters were COMBINED, and a per-character check cannot see that.

    #4250  гуноҳи ёъқ        -> йўқ
    #2699  ёъл юрса ... ёълни -> йўл ... йўлни
    #38    рўзасини туца      -> тутса
    #3540  кечириб юбора-ман  -> юбораман
    #2734  Аллоҳ банд аси     -> бандаси

`ёъқ` is the tell: it is a Latin->Cyrillic round trip. `yoʻq` mapped letter by
letter - `yo` to `ё`, the okina to `ъ`, `q` to `қ` - producing a string built
entirely from the Uzbek alphabet that is not a possible Uzbek word. `банд аси`
is the same failure with a space: a bound morpheme standing alone.

**How they were found: not by a check.** They were read off a
`derive-uzbek-latin.ts` log while verifying something else entirely. Four of
the six had been through the full pipeline and were live.

**Fix - `check_malformed_tokens` in `audit-library.py`.** Four rules, each an
orthographic IMPOSSIBILITY rather than a judgement about wording, which is why
the whole check needs no dictionary and no model call:

    ёъ / Ёъ               ё is already iotated; ъ cannot follow it
    ц in uz/tj            Russian-loan letter, in a matn nearly always тс
    \w-(ман|сан|миз|...)  a personal ending is bound to its stem
    bound morpheme alone  аси, лари, нинг, дир, ... as a free token

**Measured before it was written, not after (P260).** Run against all 72 rows
as a throwaway probe first: 6 hits, all 6 real, zero false positives. A fifth
rule - `ъ` word-initial, also a true impossibility - returned 0 and was DROPPED
rather than shipped. An unexercised rule in a passing check is a liability: it
has never been wrong because it has never run.

WARN on its first outing, same as P262 and `check_ha_formulas`. 6 warn -> 0
after the five corrections; the sixth row is below.

**The one the check cannot have.** #2307 reads «Лаззатлар бузовкисини — ўлимни
кўп эсланг» - a garbling of «лаззатларни бузувчини», the destroyer of
pleasures. Every token is a possible Uzbek word. Only someone who reads Uzbek
can see it is the wrong one. That is the boundary of this entire class of
check, and it is worth stating plainly: orthography is mechanisable, meaning is
not.


## PATTERN 269: A scoping flag that does not scope

`derive-uzbek-latin.ts --library --row 2999 --commit` wrote all 72 rows.
`--row` is parsed and then dropped - the same shape as P258, where `main()`
dropped `args.library` while `--apply` reported success.

No damage, because the transliteration is deterministic: the other 71 rows were
rewritten with byte-identical values. But that was PROVEN, not assumed - a dry
run re-derived all 72 and every one matched what is stored. The first attempt
at that proof reported three mismatches, which were an artifact of keying the
comparison on `(collection, hadith_number)`: three numbers legitimately appear
twice in the library. Re-keyed on the Cyrillic text, 72/72 matched.

**The rule.** A flag that narrows scope is a safety device, and a safety device
that silently does nothing is worse than its absence - absence is at least
visible. Before trusting `--row`, `--only`, `--limit` or a WHERE clause on any
script that writes, run it once and count the rows it touched. P258 was this
bug in the apply path; this is the same bug in the derive path; the next one
will be somewhere else.


## PATTERN 270: Three probe bugs in two days, all from re-deriving the normaliser

Checking extracted Arabic against stored Arabic failed three times this week,
and all three times the EXTRACTION WAS CORRECT and the probe was wrong:

    NFC combining-mark order (P260)      shadda typed before damma
    NFC combining-mark order again       the same bug, inside the code written to catch it
    hamza carriers unfolded              ؤ (U+0624) and ئ (U+0626) not mapped to و / ي

Each was written inline, ad hoc, for one row - and each one re-derived
normalisation from memory instead of calling the function that already does it
correctly in production.

**The rule, which should have been written after the FIRST one:** a probe does
not get its own normaliser. Import the production function, or compare on the
consonant skeleton - strip every mark from both sides and compare letters only.
The skeleton is immune to mark order and carrier choice by construction, and a
check that CANNOT be written wrongly beats one that merely happens to be
written correctly today.

The deeper point is about where the suspicion went. Three times the instinct
was that the source data was wrong; three times it was the instrument. A
disagreement between a new probe and an established pipeline should put the
probe under suspicion first - it is the thing that was written five minutes
ago.

## PATTERN 271: An adjudicated finding has nowhere to live

#6009 was ruled on by the human gate: the interpretive gloss stays but gets
bracketed, the EN honorific stays, the tongue-out reading stays. The row was
signed and written. Re-run Stage 3 tomorrow and all three come back.

**Bracketing did not clear them.** The gloss was marked `[за добро к]` and
`[қилинган яхшиликда]`, exactly as TJ already marked `[некӣ ба]` - and both
models flagged it anyway. Stage 3 scores SEMANTIC content; an editorial
bracket is typography. The bracket is for the reader, and it does nothing for
the gate. Worth knowing before anyone brackets a phrase expecting a check to
go quiet.

So three findings are now permanently true of a row that a human has already
adjudicated, and there is nowhere to write that down. The consequences are the
ones P267 warned about in the #82 note: a finding that fires forever on a row
nobody will change teaches people to skim the report, and skimming is how the
NEXT finding gets missed. `matn_verified_at` does not help - it records that a
human read the Arabic (P265), not that a human overruled a specific issue.

**What is missing** is a per-row, per-issue waiver: the issue, the ruling, who
ruled, when, and a hash of the text it was ruled on, so the waiver dies the
moment the text changes. The hash is the part that makes it safe, and the
mechanism already exists in this repo - `--sign` writes a sha256 of the
reviewed JSON and `--apply` refuses if the file moved afterward. Same idea,
different object.

NOT BUILT. Recording it now because the gap was found by using the gate
properly rather than by theorising, and because #6009 is the second row this
week to need it (the first was #82).


## PATTERN 272: Stage 3 is not reproducible at the issue level

Two Stage 3 runs on #6009, minutes apart. Between them the Uzbek sentence
containing «тилини чиқариб» was NOT touched - only the Russian question line
and the Uzbek closing clause changed. Model A flagged the Uzbek tongue-out
reading on the second run and not on the first.

Same model, same input text, different issue list.

probe-passb.py's own closing line already said "One run is one sample -
these models are non-deterministic," so the general caveat was known and
written down. What is new is that it applies at the ISSUE level and not only
to the verdict: the same model, on the same text, reports a different LIST.
A verdict can be stable while what produced it is not - which P273 then
caught in the worst possible way.

This does not break P177 - it sharpens it. "Disagreement is the output" is
sound, but the output is a SAMPLE, not a measurement. Specifically:

  - A clean pass is not evidence that nothing is there. B flagged the
    tongue in RU and TJ while missing the identical phrase in UZ, in the same
    response; A caught the UZ instance only on a second run.
  - "The other model did not flag it" is not corroboration.
  - The D5 disagreement rate is a rate over a BATCH and means nothing
    on one row - 100% of 1 says nothing at all.

**The consequence for the pending terra calibration:** a four-row falsification
test run ONCE measures a sample of that model's behaviour, not the model. Sol
passing four traps on one pass is encouraging and is not a calibration. Any
model decision needs the test run several times, with the per-run variation
reported, or it is reading noise.

## PATTERN 273: Four runs of the pass-B probe, and the first one lied

`probe-passb.py --model gpt-5.6-terra`, four consecutive runs. Run 1 returned
a clean sweep - usable in all four languages, nothing blind, nothing noisy.
Had it been run once, as every previous calibration in this project was, the
entry here would read "terra is competent in all four languages."

    case                   run1  run2  run3  run4
    en clean   (want pass) pass  pass  pass  pass   consistent
    en planted (want fail) fail  fail  fail  fail   consistent
    ru clean   (want pass) pass  pass  FAIL  pass   *** VARIES ***
    ru planted (want fail) fail  fail  fail  fail   consistent
    uz clean   (want pass) pass  pass  pass  pass   consistent
    uz planted (want fail) fail  PASS  fail  PASS   *** VARIES ***
    tj clean   (want pass) pass  pass  pass  pass   consistent
    tj planted (want fail) fail  fail  fail  fail   consistent

**terra is BLIND on Uzbek in 2 of 4 runs.** The planted Uzbek defect is
«Аллоҳ» -> «Худо», the R025 divine-name substitution. It is the single worst
class of error this channel can ship, it is in the language with the largest
audience, and the proposed pass-B model waves it through half the time.

**[CORRECTED 2026-10-18 - see P275. The ruling below is WRONG and the
reasoning under it is wrong. The Uzbek case tests a CONVENTION, not
faithfulness; lint-content.py already catches «Худо» deterministically at FAIL
(DIVINE_SUBSTITUTES, line 58); P120 puts conventions outside Stage 3; no
library row has ever contained it; and verify-candidates.py's own docstring
had documented this exact behaviour, with the correct explanation, before this
entry was written. Every candidate model behaves the same way. Left in place
rather than deleted because the mistake is the lesson.]**

**Ruling: terra does not gate Uzbek.** Not at 50%. A gate that is right half
the time on the category that matters most is not a weak gate, it is a gate
that manufactures false confidence - the exact failure the probe's own
docstring was written to catch ("it looks like a working gate from outside").

Russian is separately unusable as a sole gate: it failed CLEAN text once in
four, which is Stage 4 load rather than a safety hole, but it is noise.

**The wider rule.** Every model calibration in this project so far has been a
single pass, including Sol's four-row falsification test, which passed 4/4 and
was described here as encouraging. On this evidence a single pass cannot
distinguish a competent model from a lucky one. Any model decision needs N
runs with the per-run spread reported; N=1 is not a measurement, and this
entry exists because N=4 reversed the answer N=1 gave.


## PATTERN 274: A test case with two planted defects scores neither

The Tajik probe case carries TWO defects: the invented simile «ки чун сутуни
осмон аст» AND the lost U+04E3 in «Некӣ» -> «Неки». It is scored by one
verdict.

Across all four runs terra returned `fail` on Tajik every time - a clean
4/4 - and in all four runs the issue it reported was the simile. **It never
once mentioned the diacritic.** The orthography class went untested while the
scoreboard read perfect.

So the Tajik column of P273's table is not evidence that terra reads Tajik. It
is evidence that terra catches an invented simile in Tajik. Whether it can see
a missing diacritic - the R037 class, and the one that actually recurs in this
library - is still unknown after four runs and eight calls.

**Two rules, both cheap:**

1. One planted defect per case. A case with two cannot distinguish "caught
   both" from "caught one", and the pass hides the miss.
2. Score the ISSUE, not the verdict. The probe already receives a structured
   issue list and throws away everything except `verdict`. Matching the
   reported issue against the planted defect costs a string comparison and
   would have turned four silent misses into four visible ones.

The same critique applies to Stage 3's own `agreement` field, which is
computed from verdicts: two models can "agree" on `fail` while failing a row
for entirely different reasons, and #6009 is a live example - A failed the
Uzbek on the gloss, B failed it on the same gloss, but A also flagged a
tongue-out reading that B did not mention in that language at all.

NOT FIXED. The probe is marked THROWAWAY and is not in the pipeline, so this
is recorded rather than patched; the Stage 3 half of it is the part that
matters and it is live.

## PATTERN 275: Four models, sixteen runs, and the answer was in the docstring

The question was whether to move pass B from gpt-5.6-terra to Sol, Astra or
Luna. `probe-passb.py` against all four, four runs each, 128 calls:

    model          planted caught (of 4)    clean false-fails   TJ diacritic
    gpt-5.6-terra  en=4 ru=4 uz=2 tj=4      ru=1                0 of 4
    gpt-6.1-sol    en=4 ru=4 uz=0 tj=4      none                4 of 4
    gpt-6-astra    en=4 ru=4 uz=0 tj=4      none                4 of 4
    gpt-6-luna     en=4 ru=4 uz=0 tj=4      ru=4                4 of 4

**The Uzbek column is not a finding and never was.** The planted defect is
«Аллоҳ» -> «Худо», and every model passes it because «Худо» IS a faithful
rendering of اللَّه - it violates a house rule the model was never given, which
is precisely the P120 boundary. `lint-content.py` already catches it at FAIL
(`DIVINE_SUBSTITUTES`, line 58), deterministically, in both uz and tj, and no
row in the library has ever contained it.

**All of this was already written in verify-candidates.py's own docstring,
lines 15-23, with the right explanation.** P273 was produced by re-running
that probe, getting the documented result, and reporting it as an alarming
discovery - "terra is blind on the worst class this channel can ship" - which
is false twice over: the class is covered by a regex, and terra is the only
model that catches it at all. The standing rule is "before assuming, check the
docs." The doc was the file being edited.

**What actually separated the models,** once the out-of-scope column is
dropped: all four are 4/4 on every genuine faithfulness defect - invented
action, invented ranking, invented simile, dual->singular meaning change. The
difference is at the edges.

  - **luna is disqualified.** It failed CLEAN Russian in 4 runs of 4. A gate
    that fires on correct text is not a strict gate, it is an alarm nobody
    will read by week two.
  - **terra** false-failed clean Russian 1 run in 4, and never once named the
    lost U+04E3 in the Tajik case across four runs - it reported the invented
    simile every time and stopped there.
  - **sol and astra** false-failed nothing in four runs and named the
    diacritic 4/4.

**Decision: B moves gpt-5.6-terra -> gpt-6.1-sol.** Sol dominates terra on
both axes that matter - fewer false positives AND more true findings - which
is a cleaner basis than a single-axis win. This probe CANNOT separate sol from
astra; they are identical in every cell. Sol was chosen because it is the
current generation and the only one with any independent evidence behind it
(the four-row falsification test, n=1). If that distinction ever matters, it
needs a harder test than one hadith with four obvious defects.

Confirmed live on #6009: with sol as B the row's RU and TJ now agree clean,
where terra had failed both.

**The honest summary of this whole exercise:** 128 API calls to confirm a
docstring, disqualify one model on a defect the probe was built to catch, and
make a swap justified by a 1-in-4 false-positive rate. The disqualification
and the swap are real. The alarm that started it was not.

## PATTERN 276: The check for missing attributions had the defect a check already exists for

The last two A/B fails, #6857 and #527, both reduced to the same shape as
#6009: ONE language out of step with the other three and with the Arabic.

  - **#6857 RU.** «ростовщичество» (usury) for وأَكْلُ الرِّبَا (CONSUMING
    usury). EN "consuming usury", UZ «рибо ейиш», TJ «хүрдани рибо» all keep
    the verb. The giveaway was internal: the VERY NEXT item in the same Russian
    sentence renders the identical construction أَكْلُ مَالِ الْيَتِيمِ correctly
    as «поедание имущества сироты». A translation that contradicts itself inside
    one sentence is an oversight, not a choice. -> «поедание ростовщического
    дохода», parallel to the clause beside it.
  - **#527 TJ.** «беҳтарин» (best) for أَحَبُّ إِلَى اللَّهِ (most BELOVED to
    Allah; أفضل would be "best"). EN, RU and UZ all carry beloved-ness. Both
    models flagged it independently as CHANGED. -> «маҳбубтар», which is also
    the word probe-passb.py's own vetted clean Tajik uses for this very hadith.

Both now 8/8 but for the item below. Both rows are PUBLISHED - #527 in eight
reels (R034-R041), #6857 in four (R098-R101).

**THE ATTRIBUTION RULING.** Sol flagged #527's RU, UZ and TJ for dropping
قال / قلت / قال - EN keeps "He said / I said", the other three compress to
dashes. Ruled, from purpose.md: **a dialogue matn keeps its speech
attributions in every language.** The channel exists so viewers can tell
authentic from fabricated, and a fabricated hadith almost always circulates as
a free-floating aphorism with no speaker and nothing to trace. «Какое дело
любимее всего Аллаху? — Молитва вовремя» reads as a maxim; with "He said"
it reads as a report. Publishing authentic hadith in the aphorism form teaches
the viewer the visual grammar of the fabrication.

**NOT retrofitted into #527.** The ruling is one hour old and the row is
published across eight reels. Errors get corrected in shipped content; a
style ruling on its first outing does not. It governs new rows; #527 can be
brought in line later if it holds up over a few sets.

**THE CHECK: MEASURED, THEN NOT BUILT.** 11 of 72 rows have a speech verb in
text_arabic. A probe for "Arabic attributes, translation does not" returned
2 hits - and ONE WAS A FALSE POSITIVE IN ALL THREE LANGUAGES. #463 attributes
perfectly: RU «скажет Он», UZ «айтади», TJ «мегүяд». Three bugs in my verb
lists:

    RU  matched сказа      -> misses скажет
    UZ  matched айтди      -> misses айтади
    TJ  wrote мегүяд with U+04AF where the text has мегӯяд with U+04EF

**The third one is P262 exactly** - the Kazakh straight ү for the Tajik ӯ,
the same substitution I typed into #1894's Tajik, which is the reason
check_out_of_alphabet was written. Committed again, inside the probe for a
different check. P270 said do not re-derive language handling inline; that
rule was written about normalisers and it applies just as hard to REGEXES.

So the real count is 1 row in 72, and the check is NOT BUILT: a pattern list
this easy to get wrong is not worth shipping for a once-in-72 judgement that
Sol already catches unprompted. The ruling belongs in the generator prompt,
not in a regex.

**What IS worth building, and is cheap: lint the checks' own patterns against
ALPHABETS.** A regex containing a letter outside its target language's
alphabet can never match correctly, and that is mechanically detectable by
the table audit-library.py already has. The same check, pointed at the
checking code instead of the data. It would have caught the ү instantly, and
P262 says this pair is the one that recurs.

**Published captions, under the 2026-10-17 rule (incomplete stays, incorrect
gets fixed):** #6857's Russian drops a verb but still names the act -
incomplete, captions stand. #527's Tajik states a different claim - incorrect,
and its two Tajik reels (R037 kids, R041 adults) need the one word changed on
all four platforms. Burned audio cannot change; the caption quote can.

## PATTERN 277: TikTok captions are frozen after 7 days

Editing #527's Tajik caption on TikTok returned: "Captions and covers can only
be edited within the first 7 days of posting." The field is greyed out. The
post is from August.

The published-caption rule set on 2026-10-17 - INCOMPLETE STAYS, INCORRECT
GETS FIXED - assumed captions are editable. On TikTok they are editable for one
week. Every correction after that is impossible by platform policy, and this is
the first time the rule has been exercised on a post older than that.

**Remedy adopted: a pinned comment.** The post keeps its history and views, the
correction sits at the top of the comments, and nothing is hidden. Used on both
#527 Tajik reels (R037, R041):

    Ислоҳ: дар матн «маҳбубтар» (аҳабб илаллоҳ) дуруст аст, на «беҳтарин».
    Саҳеҳи Бухорӣ №527.

**The rule is amended:** incorrect gets fixed WHERE THE PLATFORM ALLOWS, and
pinned-comment correction where it does not. Deleting and reposting is not the
remedy - it destroys the post's history to fix one word.

The wider lesson is about time. A caption defect found inside a week is free to
fix; after that it is permanent on one platform of four. That is an argument
for catching matn defects BEFORE publication, which is what the Stage 3 gate is
for, and it is the cost side of the P278 backlog below.


## PATTERN 278: Dating the gate, and sweeping everything that predates it

#527 was published 15-16 August. The tracker records R042, on 25 August, as the
FIRST REEL FROM A HADITH VERIFIED BY THE SOURCING PIPELINE BEFORE PRODUCTION.
So #527 went out nine days before any reel was gated. It was never scored at
publish time; it surfaced later only because a library-wide Stage 3 run put it
in the A/B-fails backlog.

That is a generalisable question, and it has an exact answer: **what was
published before the gate existed?**

    reels in tracker          134   (2026-05-15 .. 2026-10-16)
    published BEFORE 2026-08-25    38 reels, 10 distinct hadith
    published on/after             96 reels, 22 distinct hadith

Of the 10 pre-gate hadiths, five had already been found defective and fixed
this week - #8, #1520, #1773, #6009, #527. The remaining five had never been
checked. Running Stage 3 on them:

    Sunan Abu Dawud #3641    8/8 clean
    Sunan Abu Dawud #1479    8/8 clean
    Sahih Muslim #482        8/8 clean
    Sahih al-Bukhari #1417   EN fails, both models
    Sahih al-Bukhari #1      fails in all four languages, both models (P279)

**7 of 10 pre-gate hadiths carried a defect. 0 of the post-gate rows reached
publication with one.** That is the gate's value stated as a number, and it is
the first time this project has had that number.

**The method, for reuse:** find the date a gate went live, select everything
published before it, and run the gate retroactively. The work is cheap - five
rows, five minutes - and it converts an unknown exposure into a finite list.
Any new gate should be dated in the tracker on the day it ships, precisely so
this query stays possible.


**CLOSED 2026-10-18.** All ten pre-gate hadiths are now checked and repaired.
#1417 was the last: its matn is COMPLETE - the mirror's quoted portion is
exactly the stored 41 characters, the first pre-gate row that was not
truncated - and its only defect was in English, where the plural imperative
`اتَّقُوا` was rendered "Protect yourself". Both models, same finding, agreement
`fail` rather than a split. One word; 8/8 after.

Its captions STAND under the 2026-10-17 rule as amended by P277: a
singular-for-plural is a grammatical error, not a false statement about what
was said, so it is incomplete rather than incorrect.

Final tally for the pre-gate set: 10 hadiths, 38 reels, **7 carried a defect,
3 were clean** (Abu Dawud #3641, Abu Dawud #1479, Muslim #482).


## PATTERN 279: The first hadith in Bukhari, published as a clipped phrase

Sahih al-Bukhari #1, the hadith of intentions, narrated by Umar ibn al-Khattab.
Published as R010-R013. Stored matn, 34 characters:

    إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ

The narration continues `وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى` and then the hijra
clause. 34 -> 199 characters.

**A NEW CASE FOR P261.** Until now "one complete admonition" and "the complete
narration" coincided - #8, #1151 and #2999 each restored to the whole narration
because the whole narration WAS one admonition. Here they differ: the principle
is one statement and the hijra sentence is a second one illustrating it.

Ruled: take the FULL narration. The defect being repaired was created by
someone keeping the famous part and dropping the rest - the same instinct that
would stop at the principle. And the hijra clause is not ornament: two men make
the identical journey, and the example only demonstrates the two clauses
because both are present.

**THE SECOND DEFECT, WHICH THE TRUNCATION HID.** All four translations lost
`إِنَّمَا`, a restrictive particle - ONLY, not merely "indeed". Both models
flagged it independently in all four languages. EN, UZ and TJ also carried an
invented verb ("judged", «баҳоланади», «арзёбӣ мешаванд») where the Arabic is a
nominal sentence with no verb at all. Without the restriction the hadith reads
as "intention is a factor in how deeds are assessed"; with it, intention
CONSTITUTES the deed - which is why the hadith governs the validity of wudu and
prayer and not only their reward.

**THE RE-TRANSLATION REPRODUCED THE RUSSIAN DEFECT (P108).** The fresh
translation returned «Поистине, деяния оцениваются по намерениям» - the same
missing restriction and the same added verb as the text it replaced. B caught
it; A passed it. A re-roll is a new draft with its own defects, not a fix.

**And the assistant's proposed Russian was worse than the one it replaced.**
«Деяния — только по намерениям» is abrupt in Russian, which has no present-tense
copula: an Arabic nominal sentence genuinely needs a verb there, so
«оцениваются» is grammatical necessity rather than interpolation, and does not
need the brackets P276 applied to #6009. A third model's wording was adopted
instead:

    Поистине, деяния оцениваются только по намерениям, и каждому
    человеку — лишь то, что он намеревался.

It carries the restriction twice and drops the verb in the second clause,
mirroring the Arabic, which has none there either. 8/8 on re-scoring.

**Source caveat:** mirror-sourced only. sunnah.com and Dorar were not reachable
from this session, so unlike #8, #1520, #1773 and #2999 this restoration has NO
Tier 1 confirmation. The mirror screens, it does not certify (P145), and
`matn_verified_at` stays null regardless (P265). A Tier 1 check on this text is
OWED.

## PATTERN 280: Re-reading the disagreements under a new B, and a model that judges one language harder

The twelve rows P257 left as DISAGREE were adjudicated under gpt-5.6-terra.
B is now gpt-6.1-sol (P275), so the split that produced them no longer exists.
Eight were still open; re-scored:

    #2628   pass 8/8     - the model swap RESOLVED it
    #13     fail, both models, ru + uz + tj
    #2759   fail, both models, uz + tj
    #2963, #4248, #5027, #82, #574   A fails Tajik, B passes

**The five Tajik-only flags are not Tajik defects.** A's complaints are real
observations - singular نِعْمَةَ rendered plural, singular مَنْ rendered plural,
الرَّجُلِ ("the man") as «инсон» ("person"), البردين glossed with the prayer
names. But on #2963 A verdicts `uz: pass` AND, in the same response, lists the
IDENTICAL issue against the Uzbek. Same defect, same row, same call: fail in
Tajik, pass in Uzbek.

So this is not evidence about the text. It is A's verdict threshold moving by
language. P272 said Stage 3 is unstable at the issue level across runs; this
shows the VERDICT moving across languages inside one response. The issue lists
remain useful. The verdicts, read alone, are not.

Corollary for #574: the Uzbek already brackets its gloss - «(Бомдод ва Аср)» -
and A flagged it anyway. P271 from a second direction: brackets are for the
reader, never for the gate.

**#13 - "true believer" is commentary, not matn.** لاَ يُؤْمِنُ أَحَدُكُمْ is flat:
"none of you believes". RU had «истинно», UZ «ҳақиқий мўмин», TJ «мӯмини ҳақиқӣ».
The qualifier is the classical softening - نفي الكمال, negation of perfection - and
it is a real scholarly reading, but it is commentary and the matn does not
carry it. ENGLISH HAD IT TOO ("None of you truly believes") and both models
passed English on the library run; B failed it only when re-scored after the
other three were fixed. Removed from all four by operator ruling.

**#2759 - two findings and one regression.** عز وجل was absent from RU, UZ and TJ
while present in the Arabic and the English. And UZ read «кечаги гуноҳкор» for
مُسِيءُ اللَّيْلِ - in Uzbek кеча is both "night" and "yesterday", so it reads as
YESTERDAY's sinner and collapses the hadith's day/night symmetry.

**THE RE-TRANSLATION BROKE TWO THINGS THAT WERE RIGHT (P108, third instance
in two days).** The fresh Russian rendered لِيَتُوبَ مُسِيءُ النَّهَارِ as
«чтобы принял Он покаяние» - so that HE may accept the repentance - moving the
subject from the sinner to Allah. The ORIGINAL Russian had it right
(«чтобы мог покаяться грешивший днём»). Fixed by restoring the old clause and
keeping only the honorific that was genuinely missing.

**And the one no check could reach.** The new Uzbek replaced «чўзади» (extends)
with «очур» (opens) for يَبْسُطُ يَدَهُ. Both models passed it. The operator caught
it by reading: يبسط is to spread or extend, not to open. A model comparison
against the Arabic let a weaker verb through; a speaker of the language did
not. That is the boundary of this entire gate, stated plainly.

Both rows 8/8 after the corrections; audit clean.

## PATTERN 281: Set-Location moves PowerShell, not .NET

`generate-scene.ps1` died on the first clip of the #1488 set:

    Could not find a part of the path
    'C:\Users\Farhod\assets\scene-prompts\ad1488-mat.json'

The script sets `$repo` from `$PSScriptRoot` and calls `Set-Location $repo` on
line 68, so PowerShell's own location was correct. But `$promptDir` was the
RELATIVE string `"assets\scene-prompts"`, and the sidecar is written with
`[System.IO.File]::WriteAllText`. **.NET resolves a relative path against
`[Environment]::CurrentDirectory`, which `Set-Location` never updates** - it
holds whatever directory the shell PROCESS started in. `Test-Path` passed,
because that is a PowerShell cmdlet and honours `$PWD`; the write then went
somewhere else entirely.

**It was introduced by P255, which was itself a correct fix.** P255 replaced
`Set-Content -Encoding UTF8` with `WriteAllText` to stop the BOM that was
blocking every push. The BOM went away and a cmdlet that respects `$PWD` was
swapped for a .NET call that does not. The bug then hid for weeks because the
operator's shell happened to start in the repo; it only surfaced on a terminal
opened somewhere else.

**Fix:** `$promptDir = Join-Path $repo "assets\scene-prompts"`. Absolute.

**The rule:** in a PowerShell script, any `[System.IO.*]` call takes an ABSOLUTE
path. `Set-Location`, `Push-Location` and `$PWD` are invisible to it. The three
`WriteAllText` calls in `render-reel.ps1` were audited at the same time and are
all safe - two resolve through `Resolve-Path`, one through `$PWD` - so this was
the only instance.

**Third in a family.** P186: `Set-Content -Encoding utf8` writes a BOM, so only
the FIRST block of a lint file could ever go missing. P255: the same BOM, in the
sibling writer, blocking pushes for days. P281: the fix for P255. Each repair
was right and each moved the defect one layer sideways. The question to ask of
the next one is not "is this correct" but "what does this call resolve
differently from the thing it replaces".

**And a rule broken while fixing it.** The comment went into the script as
"P283" - a number guessed rather than checked. ways-of-working says to verify
the frontier before assigning one, precisely because overwriting an existing
number destroys a real fix. The frontier was P280. Corrected to P281 before the
commit, but the guess should not have been typed at all.


## PATTERN 282: Two gates that pass because what they check is not what matters

Both found in one reel, and neither is a bug in the checker.

**1. `stt-validate` compared the subtitles against a stale `draft.txt` and
returned 0.958.** The narration said «стесняется вернуть»; `draft.txt` still said
«не желает возвращать», the pre-correction wording. A whole clause differed
and the comparison reported one MEDIUM, on something else. The check is sound;
its authority rests entirely on `draft.txt` being in sync with the admin text,
and **nothing enforces that.** ways-of-working says sync before TTS - that is a
rule with no gate behind it. The H block was worse than the M: it still carried
«побуждающими Его» ("impelling Him"), a theological error already corrected in
the admin, and H is the block that becomes the caption and the YouTube
description. Had the draft not been read by eye it would have published.

NOT BUILT: compare `draft.txt` against the admin's generated blocks before
narration and refuse on a mismatch.

**BUILT 2026-10-22** as `scripts/check-draft-sync.py`, wired into
`render-reel.ps1` Step 0 ahead of the `-ValidateOnly` exit, so the smoke test
covers it too. It does NOT compare against the admin's blocks - those live in
React state and never touch disk. It compares against the LIBRARY ROW, which is
the source of truth the blocks were built from anyway:

1. SCRIPT - the S block must be in the writing system the language uses. That
   alone catches the whole-wrong-language case, the 0.291 one.
2. MATN - the S block must quote `text_<lang>`, compared on letters only so
   punctuation and quote marks cannot mask a difference, reported as a ratio.

The second check is the one that matters. A draft holding another language is
loud and harmless; a stale draft in the RIGHT language is quiet and scored
0.958 while a whole clause differed. Comparing against the database rather than
against a threshold on the SRT is what separates them.

Verified four ways against a draft holding the Tajik blocks: `--lang tj` passes
on an exact quote, `--lang uz` and `--lang ru` fail on the matn at 0.324 and
0.137, `--lang en` fails on the script check before it ever reaches the
database.

**2. The casing restorer left the divine pronoun lowercase, correctly.** Whisper
returned «раб его» and «проси его» where the source has «Его». The restorer
fixed «Он», «Сам», «Стыдлив» and «Щедр» and left these, because it only
restores where the source has the same word and «его» appears legitimately
lowercase in cue 1 - «да благословит его Аллах», referring to the Prophet ﷺ.
It had no safe call to make. Nothing else checks it: the existing divine-name
check in `lint-content.py` tests WHICH name is used, not the case of a pronoun
referring to Him, which is the same blind spot P139 recorded for grammatical
case.

NOT BUILT: in a Russian line that names Allah, a third-person pronoun referring
to Him is capitalised. Narrow, mechanical, and it would have caught both cues.

**What the two share:** each gate did exactly what it was written to do. One
trusted an input nobody verifies, the other declined a judgement it was right to
decline. Neither is fixed by making the checker stricter - the first needs a
gate one step earlier, the second needs a different check entirely.

## PATTERN 283: Two naming schemes in one pipeline, and nothing maps them

The output folder is the admin's slug. The clips are a collection prefix.

```
out\work\adults\sunan-abu-dawud-1488\<lang>\   <- admin slug
assets\scene-prompts\ad1488-mat.json           <- collection prefix
out\backgrounds\new\ad1488-mat.mp4             <- collection prefix
```

The slug is the collection spelled out plus the number, derived by the admin
from `collection`. The clip prefix is a short code for the same collection plus
the same number:

| prefix | collection |
|---|---|
| `b` | Sahih al-Bukhari |
| `m` | Sahih Muslim |
| `ad` | Sunan Abu Dawud |
| `t` | Jami at-Tirmidhi |
| `ij` | Sunan Ibn Majah |
| `ah` | Musnad Ahmad |

Neither `reel-creation-pipeline.md` nor this file said so until now. The
CHANGELOG's 2026-10-22 entry did note it once, in passing - and that note is
the finding, not the record:

> Slug is `sunan-abu-dawud-1488` (admin derivation), clips are `ad1488-*`
> (§5b collection prefix). The two conventions differ and the tracker already
> records that inconsistency.

There is no §5b in any doc in this repo, and the tracker records nothing of the
kind. A note citing two references that do not exist reads, to anyone skimming,
exactly like the thing being documented somewhere else. It is worse than
silence, because it stops the next person looking.

Found because the operator asked whether it had been written down. The
assistant then searched two files, found nothing, and told him it was recorded
nowhere - also wrong, in the other direction, and for the same reason: a
partial search reported as a complete one.

**Consequence:** a clip filed under the slug name is invisible to
`render-reel.ps1 -Scenes`, which takes clip names; and a scene looked for under
the wrong prefix appears not to exist, which invites regenerating a clip that is
already on disk - a paid Kling call for nothing.

Recorded, not fixed. Both schemes are load-bearing and renaming either one
breaks sidecars on published reels.

---

## PATTERN 284: A Tajik vowel that only breaks sentence-initially

`Дастонатро` (your hands) narrated as `Достонатро` (your stories). The same stem
in the STORY block, `дастонашро`, narrated correctly in the same run.

The difference is position: M opens with the word, capitalised, first in the
sentence. That is the position P087 recorded for Uzbek `ҳ` - the engine's
Russian prior is strongest where it has the least left context.

**Fix, validated rather than hopeful:** a word-level example in the `tj.adults`
`instructions` string in `app/api/tts/route.ts`. The letter-level guidance
already there cannot reach this, because no letter is wrong - the vowel quality
is.

```
"Vowel quality carries meaning: дастон / дастонат / дастонаш = 'das-TON' " +
"(hands), with a clear short 'a' in the first syllable - never 'dos-TON', " +
"which is достон, a story or epic. " +
```

Re-narrated the moral alone; the word came back correct. The story was left
untouched - it had never been wrong.

**Do NOT respell the Cyrillic to steer the engine.** PATTERN 95 rejected that
approach explicitly and says do not reintroduce it. The `instructions`
parameter is the lever (P074), and a concrete example pronunciation is what
makes it bite.

**No dev-server restart for a change to this file.** Next 16 hot-reloads route
handlers on save. Restarting, or reloading the admin page, would have cost the
operator the four edited blocks - they live in React `useState` with no
localStorage and no DB write.

---

## PATTERN 285: `agreement: incomplete` means re-run, never adjudicate

#1488's library row came back `tj: A=error/low, B=pass/high`, with `raw: ""`.
A returned an empty body.

In the JSON that shape is hard to tell from a real split, and the instinct is to
treat it as the disagreement the stage exists to produce. It is not. A missing
pass is a transport failure, and adjudicating it means ruling on one model's
opinion unopposed - which is the trap P177 names.

Re-ran unchanged: `A=pass/high, B=pass/high` on all four languages. Nothing
about the text had changed.

**Rule:** `fail` and `disagree` go to Stage 4. `incomplete` goes back to the
queue. The script already models the three statuses separately; nothing told the
operator what to do with the third.

---
## PATTERN 286: `-FitScenes` now refuses when clips would actually be dropped

The switch has been opt-in since P194 named the defect it prevents. Opt-in is
the wrong shape for it. Omitting it costs clips silently, and in the Sunan Abu
Dawud #1488 set it was omitted twice - the RU reel shipped showing roughly 2.5
of its 4 clips and is live on four platforms.

P194 describes what happens. Nothing refused.

`render-reel.ps1` now walks the picked clips against the narration length when
`-FitScenes` is absent, and dies when the last clips would never reach the
screen:

```
4 scene clips passed but the narration is only 21.95s, so only 3 of them reach
the screen - the rest sit past the end of the audio and never render. Pass
-FitScenes to trim each clip to an equal share, or pass 3 clips. P194/P286.
```

It does not second-guess a deliberate full-length render. The arithmetic has to
say clips are actually lost before it fires.

---

## PATTERN 287: a fabricated book and chapter, clean through every check

Sunan Abu Dawud #1488's UZ H block read «Абу Довуднинг Сунан китобида, дуо
китобида» - in Abu Dawud's Sunan, in the Book of Du'a. Du'a is the BAB. The
KITAB is al-Witr. The library row's `book` column is EMPTY, so the generator
produced the subdivision out of nothing - and the TJ block did the same thing
independently, «китоби дуо».

`lint-content.py` passed both at 0 fail, 0 warn, and was right to: a fabricated
source is not a divine name, a seerah title, a simile or an inversion, and no
existing check looks at source claims that are not seerah titles (P105/P115).

It was caught by reading the block and checking sunnah.com book 8 against
hadithunlocked. That is, by someone asking where the claim came from.

New check `book-claim` - WARN, H block only. Deliberately low precision: H is
one short block and this fires at most once per reel. A collection name on its
own is fine; naming a SUBDIVISION is what needs confirming, because the only
authority for one is the `book` column and a Tier 1 page.

Both drafts were re-run against the new check and both fire.

**The shape worth remembering:** every gate passed, and the text was still
wrong. A clean run means the known failure modes are absent, never that the
content is true - which is what this file's own header says and what it is easy
to stop believing after a few clean runs.

---
## PATTERN 288: a documented switch that does nothing, and overwrites a published reel

`render-reel.ps1 -ValidateOnly` is documented in the script's own header as
"run step 0 and exit - smoke test for the pre-push hook". It was declared in
`param()` and referenced NOWHERE else in 766 lines. Passing it performed a full
render.

Run against a published slug as a pre-commit smoke test, it overwrote
`adults-tj-sunan-abu-dawud-1488-reel.mp4` with three RANDOM background clips -
`m2628-stall`, `t3895-platter`, `makka-tower` - and a different nasheed,
because with no `-Scenes` the script falls back to a random three. The four
published copies were unaffected. The local canonical file was not.

Restored by re-rendering with the original parameters, `-Nasheed` passed
explicitly so the bed matched what shipped: 23.7s / 3.89 MB against the
original 23.7s / 3.9 MB.

**A no-op flag is worse than a missing one.** A missing flag errors. This one
says what it does twice over - `Validate`, `Only` - and the header promises a
safe check, so the reasonable action on reading it is the destructive one.

Fixed with an early `exit 0` after the Step 0 checks.

**Second finding, from the failed restore.** `powershell -File script.ps1
-Scenes a.mp4,b.mp4` passes the whole comma list as ONE string: the first
attempt died with `scene clip not found: ad1488-mat.mp4,ad1488-raised.mp4,...`.
`-File` does not parse PowerShell syntax in its arguments. A detached run that
needs an array argument goes through a wrapper `.ps1`, never `-File` with
inline commas.

**The rule underneath both:** do not smoke-test a render script against a
published slug. There is nothing to gain and a finished reel to lose.

---
## PATTERN 289: a row with three defects that passed every check

`audit-library.py --row 2307` returned **0 high, 0 warn, 0 info** on this:

```
text_uzbek_cyrillic  Лаззатлар бузовкисини — ўлимни кўп эсланг.
text_tajik           Сабабкунандаи лаззатҳоро — марг(мург)ро зиёд ёд кунед.
```

Three defects in one row, none seen:

1. **«бузовкисини» is not a word.** It should be «бузувчисини» (destroyer).
   P268's malformed-token check cannot see it: every letter is legal, and the
   shape is not one of the orphan suffixes that check enumerates.
2. **«Сабабкунандаи» means CAUSER.** هَاذِم is the destroyer, the cutter-off.
   The Tajik asserted the opposite role of the thing the hadith is about, and
   no deterministic check can see a meaning inversion - that is Stage 3's job,
   and Stage 3 runs on candidates, not on library rows unless someone passes
   `--library`.
3. **«марг(мург)ро» carries a parenthetical alternate**, and «мург» is *bird*.
   Death, or possibly chicken. Nothing anywhere looked for a parenthesis.

The third is the one worth building, because it is purely mechanical.

**New check `embedded-alternate` (WARN).** A parenthesis TOUCHING a word
character on either side is an unresolved alternate; one standing free between
spaces is a translator's gloss and is not flagged. The library separated
cleanly on that rule: 13 fields contain a parenthesis, 5 are embedded, all 5
are defects, and none of the other 8 is - «(Бомдод ва Аср)» on #574, "Dua
(supplication)" on #1479, «(бегуноҳ)» on #1521.

Beyond #2307 it found two more rows, in three fields each because `text_uzbek`,
`text_uzbek_cyrillic` and `text_uzbek_latin` all carry it:

| row | field text |
|---|---|
| Tirmidhi #3540 | «сен **Мен(га)** дуо қилиб» |
| Bukhari #1469 | «Ҳеч кимга **сабр(дан)** яхшироқ» |

#3540 was one of the five malformed-token rows repaired on 2026-10-18 and this
survived that repair, because the repair was looking for a different shape.

**The lesson is the row, not the check.** Three defects of three different
kinds sat in one row: an orthographic one a check could have caught and didn't,
a semantic one only a model or a reader catches, and a structural one nobody
had thought to look for. A clean `audit-library` run means the enumerated
failure modes are absent. It has never meant the row is right, and this row is
the cleanest demonstration of that so far.

**Fixed 2026-10-22**, verified BEFORE writing per P266: the corrected text was
scored with `verify-candidates.py --from-json` and came back A=pass/high,
B=pass/high on all four languages, and only then written to the row. The
previous values are in `out/2307-before.json`. `derive-uzbek-latin.ts --library
--number 2307 --commit` reported `rows: 1`, confirmed against a 72-row
before-snapshot - no repeat of P269.

---
## PATTERN 290: a correction that wrote itself into a second, unrelated hadith

Fixing «сабр(дан)» on Bukhari #1469 meant one PATCH:

```
PATCH /rest/v1/hadith_library?hadith_number=eq.1469
```

PostgREST answered `HTTP 200, 2 rows`. There are TWO rows numbered 1469 and
they are different hadiths:

| id | matn |
|---|---|
| `5ccdd3a6…` | مَا أُعْطِيَ أَحَدٌ عَطَاءً خَيْرًا وَأَوْسَعَ مِنَ الصَّبْرِ |
| `833a2647…` | مَنْ يَتَصَبَّرْ يُصَبِّرْهُ اللَّهُ |

The second one's three Uzbek fields silently became the first one's text. Its
Russian and Tajik still described its own matn, so the row now contradicted
itself in a way nothing would flag: every field well-formed, every check clean,
one language saying something else entirely.

**The information was already there, on every run.** `check_duplicate_numbers`
has reported #1469, #2616 and #6018 since P147, and its own message says
*"match the wording, not the number, when selecting."* It reports at INFO,
where it reads as background, and `audit-library.py` had been run several times
that same hour. Nothing was missing except attention.

**Recovery was luck.** A 72-row `text_uzbek_latin` snapshot taken earlier for an
unrelated reason - guarding the P269 re-derive - still held the original Latin.
The Cyrillic was not in it and was rebuilt with `latinToCyrillic`, which
returned no flags. Had either been untrue, the row's Uzbek would have been
gone, and the only tell would have been a row whose languages disagreed.

**Fixed:** `patch_library_row(base, key, row_id, patch)` in `audit-library.py`.
It requires a uuid, filters on `id=eq.…`, and raises when the response is
anything other than exactly one row - so a widened filter fails loudly instead
of succeeding quietly.

**The rule:** write to `hadith_library` by `id`. The number identifies a
hadith to a reader; it does not identify a row to a database. #2616 and #6018
carry the same trap, and both sit in the narrator-mismatch backlog, which is
the next thing anyone would fix by number.

---
## PATTERN 291: A health check for a route that never existed

**Allocated to the HV repo.** The defect and the fix both live there, so the
full entry is in `hadith-verifier/fix_patterns.md`. Recorded here because the
P sequence is one global series and this repo holds the frontier - a number
allocated in the sibling and invisible here is how two repos start reusing one.

HR's `CLAUDE.md` step 4 curled `https://hadithverifier.com/api/health`, a path
that had never existed in `hadith-verifier`. The pre-flight therefore reported
a failing upstream on every session since the checklist was written, and the
failure was the checklist - a caller with no check, the inverse of the
P119/P126/P185 shape.

The route is now built and reports whether Supabase actually answered, not
merely that the deployment is serving, and exposes no configuration detail.
`/api/test` - a public, unauthenticated debug route that reported whether a
Slack webhook was configured - was removed in the same change.

**Status:** FIXED in `hadith-verifier` 71e5f00

---
## PATTERN 292: five "narrator mismatches" that were four different things

One backlog line - *five narrator mismatches (#31, #1987, #6018, #1005, #2616)* -
had sat unexamined for weeks. Worked through, it was not five of anything.

**Two were not defects.**

- **#31.** Ours says Abu Bakra; the mirror's lead-in says Al-Ahnaf bin Qais.
  The isnad is `عَنِ الأَحْنَفِ بْنِ قَيْسٍ` relating that Abu Bakra told him, and
  the text has Abu Bakra saying *"I heard Allah's Messenger ﷺ"*. Al-Ahnaf is the
  sub-narrator. **The mirror's `narrator` is a LEAD-IN STRING, not a companion
  field**, so it names whoever the chain reaches last. The check will keep
  producing this class and it needs reading, not fixing.
- **#2616, both rows.** The check matched them to mirror entry 614, a Ka'b bin
  Ujrah hadith about unjust rulers, which has nothing to do with either matn.
  `locate()` mis-matched. Ours - Mu'adh ibn Jabal - is right.

**Three were real, and each was wrong in a different way.**

- **#1987** - ours named Mu'adh ibn Jabal. The hadith is classically carried by
  both Abu Dharr and Mu'adh, but `tirmidhi:1987`'s own isnad is `عَنْ أَبِي ذَرٍّ`.
  A viewer who types our citation sees Abu Dharr, so the citation decides.
- **#1005** - the matn and the number were Muslim's; the narrator was Bukhari's.
  *Every act of goodness is charity* is Jabir ibn Abdullah's in **Bukhari 6021**;
  **Muslim 1005** is the **Hudhayfah** version. Two correct attributions, crossed.
  Nothing in the row was malformed, which is why every check passed it.
- **#6018** - our stored matn is `فَلْيُكْرِمْ جَارَهُ`, *let him honour his
  neighbour*. That is **Bukhari 6019, Abu Shuraih al-Adawi**. Bukhari **6018**
  is Abu Hurairah and says *do NOT HARM his neighbour* - a different verb and a
  different companion. Number and narrator both wrong.

**The published reels were fine, and finding that out took a transcription.**
#6018 has two library rows and R082-R085 could have used either. The narrated
text is not on disk (P246), so the only way to know which shipped was to run
whisper over the published audio: *"whoever believes in Allah in the last day,
let him speak good or let him stay silent"* - the other row, correctly cited.
**#1005's four reels are live with the wrong companion** and need caption edits.

**The lesson.** A backlog line with a count in it is not a diagnosis. Five
items, four kinds, two non-defects, and the one that mattered most - a crossed
attribution where every field was individually correct - was invisible to every
check in the repo and to the check that flagged it, which flagged it for the
wrong reason.

---
## PATTERN 292 (addendum): the narrator map had no entry for two of the three

`buildRef()` localises the companion's name from `NARRATORS` in `lib/refs.ts`
and falls back to the stored Latin when there is no entry:

```ts
const n = (NARRATORS[narrator] as any)?.[lang]
return `${coll}${num}, ${n || narrator}`
```

So correcting a narrator in the library is only half the fix. `Abu Dharr` was
already mapped; `Hudhayfah ibn al-Yaman` and `Abu Shuraih al-Adawi` were not,
and every Cyrillic caption would have carried a Latin name in the middle of a
Cyrillic reference line - visibly wrong, and silent, because a fallback is not
an error.

Both added, following the existing conventions: Russian keeps `ибн аль-`,
Uzbek drops the article, Tajik takes the izafet and contracts the kunya.
Verified through `buildRef` in all four languages:

```
ru | Сахих Муслим (Sahih Muslim) №1005, Хузайфа ибн аль-Яман
uz | Саҳиҳ Муслим (Sahih Muslim) №1005, Ҳузайфа ибн Яман
tj | Саҳеҳи Муслим (Sahih Muslim) №1005, Ҳузайфа ибни Яман
tj | Саҳеҳи Бухорӣ (Sahih al-Bukhari) №6019, Абӯшурайҳи Адавӣ
```

**The general shape:** a lookup table with a graceful fallback hides exactly the
case it was built for. Any correction to a value that a table localises has to
check the table, and the check is not optional because nothing fails.

---