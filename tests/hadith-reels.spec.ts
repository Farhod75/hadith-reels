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
})
