// tests/hadith-reels.spec.ts
// HR CI push tests — all mocked, no real API calls (P043)
// Real API tests: run manually against production

import { test, expect, Page } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:3002'

// ── Mock /api/reels response ──────────────────────────────────────────────────
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
            tags: ['kindness', 'smile', 'sadaqah'],
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

// ═════════════════════════════════════════════════════════════════════════════
// UI — Page loads correctly
// ═════════════════════════════════════════════════════════════════════════════
test.describe('UI — Page loads', () => {
  test('should show Hadith Reels header', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await expect(page.getByText('Hadith Reels').first()).toBeVisible()
  })

  test('should show Browse hadiths tab', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await expect(page.getByText(/browse hadiths/i).first()).toBeVisible()
  })

  test('should show Watch reels tab', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await expect(page.getByText(/watch reels/i).first()).toBeVisible()
  })

  test('should show HV cross-link banner', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await expect(page.getByText(/hadithverifier\.com/i).first()).toBeVisible()
  })

  test('should show all 5 language buttons', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await expect(page.getByText('EN').first()).toBeVisible()
    await expect(page.getByText('UZ').first()).toBeVisible()
    await expect(page.getByText('AR').first()).toBeVisible()
    await expect(page.getByText('RU').first()).toBeVisible()
    await expect(page.getByText('TJ').first()).toBeVisible()
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// Browse tab — mocked data
// ═════════════════════════════════════════════════════════════════════════════
test.describe('Browse tab (CT-GenAI)', () => {
  test('should display hadiths from API', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.waitForSelector('text=/Fasting is a shield/i', { timeout: 10000 })
    await expect(page.getByText(/Fasting is a shield/i).first()).toBeVisible()
  })

  test('should display Arabic text', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.waitForSelector('text=/الصِّيَامُ/i', { timeout: 10000 })
    await expect(page.locator('text=الصِّيَامُ').first()).toBeVisible()
  })

  test('should show grade badge', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.waitForSelector('text=/sahih/i', { timeout: 10000 })
    await expect(page.getByText('sahih').first()).toBeVisible()
  })

  test('should show Listen button', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.waitForSelector('text=/Listen/i', { timeout: 10000 })
    await expect(page.getByText(/Listen/i).first()).toBeVisible()
  })

  test('should show Copy button', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.waitForSelector('text=/Copy/i', { timeout: 10000 })
    await expect(page.getByText(/Copy/i).first()).toBeVisible()
  })

  test('should show Verify link to hadithverifier.com', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.waitForSelector('text=/Verify/i', { timeout: 10000 })
    const verifyLinks = page.locator('a[href="https://hadithverifier.com"]')
    const count = await verifyLinks.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should filter by grade — sahih', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.getByText('sahih').filter({ hasText: /^sahih$/ }).first().click()
    // Grade filter button click — page refetches (mocked)
    await page.waitForTimeout(500)
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible()
  })

  test('should have working search input', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    const searchInput = page.locator('input[placeholder*="Search"]')
    await expect(searchInput).toBeVisible()
    await searchInput.fill('fasting')
    await page.waitForSelector('text=/Fasting is a shield/i', { timeout: 5000 })
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// Watch tab
// ═════════════════════════════════════════════════════════════════════════════
test.describe('Watch tab', () => {
  test('should show coming soon content', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.getByText(/watch reels/i).first().click()
    await expect(page.getByText(/coming soon/i).first()).toBeVisible()
  })

  test('should show YouTube follow button', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.getByText(/watch reels/i).first().click()
    await expect(page.getByText(/youtube/i).first()).toBeVisible()
  })

  test('should show Telegram follow button', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    await page.getByText(/watch reels/i).first().click()
    await expect(page.getByText(/telegram/i).first()).toBeVisible()
  })

  test('should NOT show Generate reel button (removed from public)', async ({ page }) => {
    await mockReels(page)
    await page.goto(BASE_URL)
    const generateBtn = page.getByText(/generate reel/i)
    await expect(generateBtn).toHaveCount(0)
  })
})

// ═════════════════════════════════════════════════════════════════════════════
// API — basic smoke tests (real API, fast — just status codes)
// ═════════════════════════════════════════════════════════════════════════════
test.describe('API — smoke tests', () => {
  test('GET /api/reels should return 200', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/reels`)
    expect(res.status()).toBe(200)
  })

  test('GET /api/reels response should have reels array', async ({ request }) => {
    const res  = await request.get(`${BASE_URL}/api/reels`)
    const body = await res.json()
    expect(Array.isArray(body.reels)).toBe(true)
  })

  test('POST /api/tts without text should return 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/tts`, {
      data: { lang: 'en' }
    })
    expect(res.status()).toBe(400)
  })

  test('POST /api/generate-reel without hadith_text should return 400', async ({ request }) => {
    const res = await request.post(`${BASE_URL}/api/generate-reel`, {
      data: { lang: 'en' }
    })
    expect(res.status()).toBe(400)
  })
})
