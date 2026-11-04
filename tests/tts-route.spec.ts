// tests/tts-route.spec.ts
// P354: unit tests for the /api/tts handler, called directly - no server, no
// network. ELEVENLABS_API_KEY is removed for the run, so a request that gets
// past every check stops at 503 "not configured" and nothing is ever narrated.

import { test, expect } from '@playwright/test'
import { NextRequest } from 'next/server'
import { POST } from '../app/api/tts/route'

const env = process.env as Record<string, string | undefined>
const saved = { ...env }

test.beforeEach(() => {
  delete env.ELEVENLABS_API_KEY
  delete env.VERCEL
  env.NODE_ENV = 'development'          // the dev exception: localhost, no cookie
})
test.afterAll(() => {
  for (const k of ['ELEVENLABS_API_KEY', 'VERCEL', 'NODE_ENV']) {
    if (saved[k] === undefined) delete env[k]; else env[k] = saved[k]
  }
})

function call(body: Record<string, unknown>) {
  return POST(new NextRequest('http://localhost:3002/api/tts', {
    method: 'POST',
    headers: { host: 'localhost:3002', 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }))
}

test('a normal block passes every check (and stops at the missing key)', async () => {
  const res = await call({ text: 'Abu Hurairah narrated.', lang: 'en', style: 'adults',
                           slug: 'muslim-2749', section: 'story' })
  expect(res.status).toBe(503)
})

test('over the limit is refused with the length, never cut short', async () => {
  const res = await call({ text: 'a'.repeat(1001), lang: 'en' })
  expect(res.status).toBe(413)
  expect((await res.json()).error).toContain('1001')
})

test('the limit is measured after the honorific is expanded', async () => {
  // 990 + one glyph -> "Да благословит его Аллах и приветствует" (39) = 1029
  const res = await call({ text: 'а'.repeat(990) + 'ﷺ', lang: 'ru' })
  expect(res.status).toBe(413)
})

test('exactly at the limit still passes', async () => {
  const res = await call({ text: 'a'.repeat(1000), lang: 'en' })
  expect(res.status).toBe(503)
})

for (const [field, value] of [
  ['style',   '../../../outside'],
  ['slug',    '../../escape'],
  ['slug',    'Muslim 2749'],
  ['section', '../story'],
  ['lang',    'xx'],
] as const) {
  test(`a path-shaped or unknown ${field} (${value}) is refused before any call`, async () => {
    const res = await call({ text: 'ok', lang: 'en', style: 'adults',
                             slug: 'muslim-2749', section: 'story', [field]: value })
    expect(res.status).toBe(400)
  })
}

test('uz_cyrillic and uz_latin are still accepted as uz', async () => {
  for (const lang of ['uz_cyrillic', 'uz_latin']) {
    const res = await call({ text: 'ok', lang, slug: 'muslim-2749', section: 'moral' })
    expect(res.status).toBe(503)
  }
})
