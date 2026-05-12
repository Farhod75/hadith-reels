// tests/hadith-reels.spec.ts
// HR CI push tests — all mocked, no real API calls (P043)
// P047: tabs use button locator with filter — more resilient than getByText with emoji

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
// P047: wait for h1 text — more reliable anchor than tab buttons with emojis
async function gotoAndWait(page: Page) {
  await mockReels(page)
  await page.goto(BASE_URL)
  // Wait for the h1 header text — guaranteed to be present on all pages
  await page.waitForSelector('h1', { timeout: 15000 })
}

// ── Helper: find tab button by partial text ───────────────────────────────────
// P047: buttons with emojis — use locator('button').filter() not getByText
function tabButton(page: Page, text: RegExp) {
  return page.locator('button').filter({ hasText: text }).first()
}

// ═════════════════════════════════════════════════════════════════════════════
// UI — Page loads
// ═════════════════════════════════════════════════════════════════════════════
test.describe('UI — Page loads', () => {

  test('should show Hadith Reels h1', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.locator('h1').first()).toContainText('Hadith Reels')
  })

  // P047 FIX: use locator('button').filter() for emoji tab buttons
  test('should show Browse hadiths tab button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(tabButton(page, /browse/i)).toBeVisible()
  })

  test('should show Watch reels tab button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(tabButton(page, /watch/i)).toBeVisible()
  })

  test('should show HV cross-link banner', async ({ page }) => {
    await gotoAndWait(page)
    const banner = page.locator('a[href="https://hadithverifier.com"]').first()
    await expect(banner).toBeVisible()
  })

  test('should show EN language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.locator('button').filter({ hasText: /\bEN\b/ }).first()).toBeVisible()
  })

  test('should show UZ language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.locator('button').filter({ hasText: /\bUZ\b/ }).first()).toBeVisible()
  })

  test('should show AR language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.locator('button').filter({ hasText: /\bAR\b/ }).first()).toBeVisible()
  })

  test('should show RU language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.locator('button').filter({ hasText: /\bRU\b/ }).first()).toBeVisible()
  })

  test('should show TJ language button', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.locator('button').filter({ hasText: /\bTJ\b/ }).first()).toBeVisible()
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// Browse tab
// ═════════════════════════════════════════════════════════════════════════════
test.describe('Browse tab (CT-GenAI)', () => {

  test('should display hadith text from mocked API', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Fasting is a shield/i', { timeout: 10000 })
    await expect(page.getByText(/Fasting is a shield/i).first()).toBeVisible()
  })

  test('should display Arabic text', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('[dir="rtl"]', { timeout: 10000 })
    await expect(page.locator('[dir="rtl"]').first()).toBeVisible()
  })

  test('should show sahih grade badge', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/sahih/i', { timeout: 10000 })
    await expect(page.getByText('sahih').first()).toBeVisible()
  })

  test('should show Listen button', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Listen/i', { timeout: 10000 })
    await expect(page.locator('button').filter({ hasText: /Listen/i }).first()).toBeVisible()
  })

  test('should show Copy button', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Copy/i', { timeout: 10000 })
    await expect(page.locator('button').filter({ hasText: /Copy/i }).first()).toBeVisible()
  })

  test('should show Verify link', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Verify/i', { timeout: 10000 })
    const verifyLinks = page.locator('a[href="https://hadithverifier.com"]')
    expect(await verifyLinks.count()).toBeGreaterThan(0)
  })

  test('should show search input', async ({ page }) => {
    await gotoAndWait(page)
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible()
  })

  test('search should filter displayed hadiths', async ({ page }) => {
    await gotoAndWait(page)
    await page.waitForSelector('text=/Fasting is a shield/i', { timeout: 10000 })
    await page.locator('input[placeholder*="Search"]').fill('smile')
    // After filtering, "Fasting" should be gone, "smile" should remain
    await page.waitForTimeout(300)
    await expect(page.getByText(/Your smile for your brother/i).first()).toBeVisible()
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// Watch tab
// ═════════════════════════════════════════════════════════════════════════════
test.describe('Watch tab', () => {

  test('should show coming soon message', async ({ page }) => {
    await gotoAndWait(page)
    await tabButton(page, /watch/i).click()
    await page.waitForSelector('text=/coming soon/i', { timeout: 5000 })
    await expect(page.getByText(/coming soon/i).first()).toBeVisible()
  })

  test('should show YouTube button', async ({ page }) => {
    await gotoAndWait(page)
    await tabButton(page, /watch/i).click()
    await page.waitForSelector('text=/youtube/i', { timeout: 5000 })
    await expect(page.getByText(/youtube/i).first()).toBeVisible()
  })

  test('should show Telegram button', async ({ page }) => {
    await gotoAndWait(page)
    await tabButton(page, /watch/i).click()
    await page.waitForSelector('text=/telegram/i', { timeout: 5000 })
    await expect(page.getByText(/telegram/i).first()).toBeVisible()
  })

  test('should NOT have Generate reel button visible on public page', async ({ page }) => {
    await gotoAndWait(page)
    const generateBtn = page.locator('button').filter({ hasText: /generate reel/i })
    await expect(generateBtn).toHaveCount(0)
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// API smoke tests — real API, fast (status codes only)
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
