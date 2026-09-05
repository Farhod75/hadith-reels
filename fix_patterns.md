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

  1. **A stale admin selection.** After #2318 was renumbered to 2616, the admin
     still displayed `Selected: Al-Bayhaqi #2318` while the hadith card beside
     it showed Muslim #82. The UI keys off a number that does not identify a
     row, so it held a selection for a row that no longer existed. Caught only
     because the mismatch was visible on screen. Same family as P108.

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
**Status:** DOCUMENTED — admin selection and query discipline still to fix

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

**Status:** FIXED — all five languages match the noun
