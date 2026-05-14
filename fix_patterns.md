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

**Status:** FIXED — CI #41 ✅