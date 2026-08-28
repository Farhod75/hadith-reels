// tests/hadith-reels.spec.ts
// HR CI push tests — all mocked, no real API calls (P043)
// P047: tab button locators with emoji text — fragile in CI headless
// P048: test FUNCTIONALITY not UI label text — if hadiths load, browse tab works

import { test, expect, Page } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:3002'

// ── Mock /api/reels ───────────────────────────────────────────────────────────
async function mockReels(page: Page) {
  await page.route('**/api/reels*', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        reels: [
          {
            id: 'test-1',
            text_arabic: 'الصِّيَامُ جُنَّةٌ',
            text_english: 'Fasting is a shield.',
            text_display: 'Fasting is a shield.',
            narrator: 'Abu Hurairah',
            collection: 'Sahih al-Bukhari',
            hadith_number: '1894',
            grade: 'sahih',
            tags: ['fasting', 'sawm'],
            source_url: 'https://sunnah.com/bukhari:1894',
          },
          {
            id: 'test-2',
            text_arabic: 'تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ',
            text_english: 'Your smile for your brother is charity.',
            text_display: 'Your smile for your brother is charity.',
            narrator: 'Abu Dharr',
            collection: 'Jami at-Tirmidhi',
            hadith_number: '1956',
            grade: 'sahih',
            tags: ['kindness', 'smile'],
            source_url: 'https://sunnah.com/tirmidhi:1956',
          },
        ],
        total: 2,
        offset: 0,
        limit: 40,
      }),
    })
  )
}

// ── Helper: navigate and wait for page ready ──────────────────────────────────
async function gotoAndWait(page: Page) {
  await mockReels(page)
  await page.goto(BASE_URL)
  await page.waitForSelector('h1', { timeout: 15000 })
}

// ═════════════════════════════════════════════════════════════════════════════
// UI — Page loads
// P048: test stable elements — h1, cross-link, lang buttons
// NOT tab button text (emoji labels are fragile in headless CI)
// ═════════════════════════════════════════════════════════════════════════════
test.describe('UI — Page loads', () => {

  test('should show Hadith Reels h1', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.locator('h1').first()).toContainText('Hadith Reels')
  })

  test('should show HV cross-link to hadithverifier.com', async ({ page }) => {
    await gotoAndWait(page)
    const link = page.locator('a[href="https://hadithverifier.com"]').first()
    await expect(link).toBeVisible()
  })

  test('should show EN language button', async ({ page }) => {
    await gotoAndWait(page)
    // Use filter with regex — emoji comment nodes make exact text match fragile
    await expect(
      page.locator('header button').filter({ hasText: /EN/ }).first()
    ).toBeVisible()
  })

  test('should show UZ language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(
      page.locator('header button').filter({ hasText: /UZ/ }).first()
    ).toBeVisible()
  })

  test('should show AR language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(
      page.locator('header button').filter({ hasText: /AR/ }).first()
    ).toBeVisible()
  })

  test('should show RU language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(
      page.locator('header button').filter({ hasText: /RU/ }).first()
    ).toBeVisible()
  })

  test('should show TJ language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(
      page.locator('header button').filter({ hasText: /TJ/ }).first()
    ).toBeVisible()
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// Browse tab — test functionality (content loads) not tab label text
// ═════════════════════════════════════════════════════════════════════════════
test.describe('Browse tab functionality (CT-GenAI)', () => {

  test('should display hadith text from mocked API', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Fasting is a shield/i', { timeout: 10000 })
    await expect(page.getByText(/Fasting is a shield/i).first()).toBeVisible()
  })

  test('should display Arabic text block', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('[dir="rtl"]', { timeout: 10000 })
    await expect(page.locator('[dir="rtl"]').first()).toBeVisible()
  })

  test('should show sahih grade badge', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/sahih/i', { timeout: 10000 })
    await expect(page.getByText('sahih').first()).toBeVisible()
  })

  test('should show collection name', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Sahih al-Bukhari/i', { timeout: 10000 })
    await expect(page.getByText(/Sahih al-Bukhari/i).first()).toBeVisible()
  })

  test('should show narrator name', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Abu Hurairah/i', { timeout: 10000 })
    await expect(page.getByText(/Abu Hurairah/i).first()).toBeVisible()
  })

  test('should show hashtags', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/#fasting/i', { timeout: 10000 })
    await expect(page.getByText(/#fasting/i).first()).toBeVisible()
  })

  test('should show search input', async ({ page }) => {
    await gotoAndWait(page)
    const input = page.locator('input[placeholder*="Search"]')
    await expect(input).toBeVisible()
  })

  test('search filters hadiths correctly', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Fasting is a shield/i', { timeout: 10000 })
    await page.locator('input[placeholder*="Search"]').fill('smile')
    await page.waitForTimeout(300)
    await expect(page.getByText(/Your smile for your brother/i).first()).toBeVisible()
  })

  test('should show Source link', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Source/i', { timeout: 10000 })
    const sourceLink = page.locator('a[href*="sunnah.com"]').first()
    await expect(sourceLink).toBeVisible()
  })

  test('should show Verify link per hadith card', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Fasting is a shield/i', { timeout: 10000 })
    const verifyLinks = page.locator('a[href="https://hadithverifier.com"]')
    expect(await verifyLinks.count()).toBeGreaterThan(0)
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// Watch tab — navigate by href not by tab label text
// ═════════════════════════════════════════════════════════════════════════════
test.describe('Watch tab', () => {

  test('should show Watch reels heading on Watch tab', async ({ page }) => {
    await gotoAndWait(page)
    await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.textContent?.toLowerCase().includes('watch'))
  btn?.click()
}) 
    await expect(page.getByText(/Watch our reels/i).first()).toBeVisible()
  })

  test('should show YouTube link on Watch tab', async ({ page }) => {
    await gotoAndWait(page)
    await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.textContent?.toLowerCase().includes('watch'))
  btn?.click()
})
    await expect(page.locator('a[href*="youtube"]').first()).toBeVisible()
  })

  test('should show Telegram link on Watch tab', async ({ page }) => {
    await gotoAndWait(page)
    await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find(b => b.textContent?.toLowerCase().includes('watch'))
  btn?.click()
})
    await expect(page.locator('a[href*="t.me"], a[href*="telegram"]').first()).toBeVisible()
  })

  test('Generate reel button NOT on public page', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.getByRole('button', { name: /generate reel/i })).toHaveCount(0)
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// API smoke tests
// ═════════════════════════════════════════════════════════════════════════════
test.describe('API — smoke tests', () => {

  test('GET /api/reels returns 200', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/reels`)
    expect(res.status()).toBe(200)
  })

  test('GET /api/reels returns reels array', async ({ request }) => {
    const res  = await request.get(`${BASE_URL}/api/reels`)
    const body = await res.json()
    expect(Array.isArray(body.reels)).toBe(true)
  })

  test('POST /api/tts without text returns 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/tts`, {
      data: { lang: 'en' }
    })
    expect(res.status()).toBe(400)
  })

  test('POST /api/generate-reel without hadith_text returns 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/generate-reel`, {
      data: { lang: 'en' }
    })
    expect(res.status()).toBe(400)
  })

  // ── ADMIN STUDIO ────────────────────────────────────────────────────────────
// P126 part B: the admin studio — picker, generation, editing, TTS, caption,
// publish — had NO test coverage at all, and UI_PATTERNS in the pre-push hook
// is anchored to `^app/page\.tsx$` so it never matched `app/admin/`. Widening
// that pattern before these tests existed would have run 25 public-site tests
// on an admin change and reported green.
//
// All mocked per P043 — including /api/admin/verify, so ADMIN_PASSWORD is not
// needed and no secret enters the repo.

const ADMIN_URL = `${BASE_URL}/admin`

async function mockAdminAuth(page: Page, accept = true) {
  await page.route('**/api/admin/verify', route =>
    route.fulfill({
      status: accept ? 200 : 401,
      contentType: 'application/json',
      body: JSON.stringify(accept ? { ok: true } : { error: 'nope' }),
    }))
}

async function mockGenerate(page: Page) {
  await page.route('**/api/generate-reel', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        title:          'Fasting Is A Shield',
        story:          'The Prophet said that fasting is a shield.',
        moral:          'Fast one voluntary day this month.',
        seerah_context: 'Recorded in Sahih al-Bukhari, number 1894.',
        caption_intro:  '',
      }),
    }))
}

// A one-frame silent MP3 is enough — the component only needs a blob to build
// an object URL from. It never inspects the audio.
async function mockTts(page: Page) {
  await page.route('**/api/tts', route =>
    route.fulfill({
      status: 200,
      contentType: 'audio/mpeg',
      body: Buffer.from('\xFF\xFB\x90\x00', 'binary'),
    }))
}

async function loginAndPick(page: Page) {
  await mockAdminAuth(page)
  await mockReels(page)
  await page.goto(ADMIN_URL)
  await page.getByPlaceholder('Admin password').fill('anything')
  await page.getByRole('button', { name: /Enter Studio/i }).click()
  // P048: assert FUNCTIONALITY — if hadiths render, the picker works
  await expect(page.getByText('Fasting is a shield.').first()).toBeVisible()
}

test.describe('Admin — auth gate', () => {
  test('rejects a wrong password and stays on the login screen', async ({ page }) => {
    await mockAdminAuth(page, false)
    await page.goto(ADMIN_URL)
    await page.getByPlaceholder('Admin password').fill('wrong')
    await page.getByRole('button', { name: /Enter Studio/i }).click()
    await expect(page.getByText(/Incorrect password/i)).toBeVisible()
    await expect(page.getByPlaceholder('Admin password')).toBeVisible()
  })

  test('accepts a valid password and loads the picker', async ({ page }) => {
    await loginAndPick(page)
  })
})

test.describe('Admin — generate to preview', () => {
  test('selecting a hadith and generating reaches the preview step', async ({ page }) => {
    await loginAndPick(page)
    await mockGenerate(page)

    await page.getByText('Fasting is a shield.').first().click()
    await page.getByRole('button', { name: /Generate/ }).first().click()
    await page.getByRole('button', { name: /Generate story/i }).click()

    await expect(page.locator('[data-test="story-edit"]')).toBeVisible()
    await expect(page.locator('[data-test="moral-edit"]')).toBeVisible()
    await expect(page.locator('[data-test="story-edit"]'))
      .toHaveValue(/fasting is a shield/i)
  })
})

// P125: before the fix, narration was generated once and the button became
// playback only — editing the textarea afterwards reached nothing, and the
// only re-narrate path was the whole-reel Regenerate. These two tests are the
// regression guard for that, and they are why this file exists.
test.describe('Admin — P125 re-narrate', () => {
  async function toPreview(page: Page) {
    await loginAndPick(page)
    await mockGenerate(page)
    await mockTts(page)
    await page.getByText('Fasting is a shield.').first().click()
    await page.getByRole('button', { name: /Generate/ }).first().click()
    await page.getByRole('button', { name: /Generate story/i }).click()
    await expect(page.locator('[data-test="story-edit"]')).toBeVisible()
  }

  test('re-narrate appears only after narration exists', async ({ page }) => {
    await toPreview(page)
    await expect(page.locator('[data-test="story-renarrate"]')).toHaveCount(0)
    await page.locator('[data-test="story-play"]').click()
    await expect(page.locator('[data-test="story-renarrate"]')).toBeVisible()
  })

  test('editing the story after narration raises the stale warning', async ({ page }) => {
    await toPreview(page)
    await page.locator('[data-test="story-play"]').click()
    await expect(page.locator('[data-test="story-renarrate"]')).toBeVisible()

    // clean: no warning yet
    await expect(page.locator('[data-test="story-stale"]')).toHaveCount(0)

    // dirty: the exact case that shipped the wrong audio on UZ #2999
    await page.locator('[data-test="story-edit"]').fill('A deliberately different story.')
    await expect(page.locator('[data-test="story-stale"]')).toBeVisible()

    // re-narrating clears it
    await page.locator('[data-test="story-renarrate"]').click()
    await expect(page.locator('[data-test="story-stale"]')).toHaveCount(0)
  })
})

})


