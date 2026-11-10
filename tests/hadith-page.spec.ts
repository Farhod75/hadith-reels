// tests/hadith-page.spec.ts
// P387: the hadith explanation page. NOT in the CI list - CI runs against the
// production URL, which has the page only after this branch is deployed. Run it
// against the dev server:  npx playwright test tests/hadith-page.spec.ts --project=chromium
import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:3002'

test('Muslim 2564 in Uzbek: explanation, lessons and credit to HadeethEnc', async ({ page }) => {
  await page.goto(`${BASE_URL}/hadith/muslim/2564?lang=uz`)
  await expect(page.getByRole('heading', { name: 'Ҳадиснинг шарҳи' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Ҳадисдан олинадиган сабоқлар' })).toBeVisible()
  const credit = page.getByTestId('credit').getByRole('link')
  await expect(credit).toHaveAttribute('href', 'https://hadeethenc.com/uz/browse/hadith/4555')
})

test('the language toggle switches the explanation to Tajik', async ({ page }) => {
  await page.goto(`${BASE_URL}/hadith/muslim/2564?lang=uz`)
  await page.getByRole('link', { name: 'TJ', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Шарҳи ҳадис' })).toBeVisible()
  await expect(page.getByTestId('credit').getByRole('link'))
    .toHaveAttribute('href', 'https://hadeethenc.com/tg/browse/hadith/4555')
})

test('an unknown collection is a 404, not an empty page', async ({ page }) => {
  const res = await page.goto(`${BASE_URL}/hadith/riyad/1`)
  expect(res?.status()).toBe(404)
})
