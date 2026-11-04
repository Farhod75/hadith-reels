// tests/admin-session.spec.ts
// P353: unit tests for lib/admin-session.ts - no browser, no server, no network.
// The guard decides whether a request may publish to the channel or spend on a
// paid API, so each way in and each way out is pinned here.

import { test, expect } from '@playwright/test'
import { NextRequest } from 'next/server'
import {
  ADMIN_COOKIE, SESSION_TTL_SECONDS, issueSessionToken, verifySessionToken,
  passwordMatches, requireAdmin,
} from '../lib/admin-session'

const env = process.env as Record<string, string | undefined>
const saved = { ...env }

test.beforeEach(() => {
  env.ADMIN_PASSWORD = 'correct horse'
  delete env.ADMIN_SESSION_SECRET
  delete env.VERCEL
  env.NODE_ENV = 'production'
})
test.afterAll(() => {
  for (const k of ['ADMIN_PASSWORD', 'ADMIN_SESSION_SECRET', 'VERCEL', 'NODE_ENV']) {
    if (saved[k] === undefined) delete env[k]; else env[k] = saved[k]
  }
})

function req(url: string, headers: Record<string, string> = {}) {
  const host = new URL(url).host
  return new NextRequest(url, { method: 'POST', headers: { host, ...headers } })
}

test('password: exact match only, and nothing matches when none is configured', () => {
  expect(passwordMatches('correct horse')).toBe(true)
  expect(passwordMatches('correct horse ')).toBe(false)
  expect(passwordMatches(undefined)).toBe(false)
  delete env.ADMIN_PASSWORD
  expect(passwordMatches('')).toBe(false)
})

test('token: a fresh token verifies, an expired one does not', () => {
  const now = Date.now()
  const token = issueSessionToken(now)!
  expect(verifySessionToken(token, now)).toBe(true)
  expect(verifySessionToken(token, now + (SESSION_TTL_SECONDS + 1) * 1000)).toBe(false)
})

test('token: tampering with the expiry or the signature is refused', () => {
  const token = issueSessionToken()!
  const [v, exp, sig] = token.split('.')
  expect(verifySessionToken(`${v}.${Number(exp) + 3600}.${sig}`)).toBe(false)
  expect(verifySessionToken(`${v}.${exp}.${sig.slice(0, -1)}A`)).toBe(false)
  expect(verifySessionToken('v1.notanumber.x')).toBe(false)
  expect(verifySessionToken('')).toBe(false)
})

test('token: changing the password signs every session out', () => {
  const token = issueSessionToken()!
  env.ADMIN_PASSWORD = 'new password'
  expect(verifySessionToken(token)).toBe(false)
})

test('production: no cookie -> 401, valid cookie -> allowed', () => {
  expect(requireAdmin(req('https://www.hadithreels.com/api/tts'))?.status).toBe(401)
  const cookie = `${ADMIN_COOKIE}=${issueSessionToken()}`
  expect(requireAdmin(req('https://www.hadithreels.com/api/tts', { cookie }))).toBeNull()
})

test('cross-origin browser request is refused even with a valid cookie', () => {
  const cookie = `${ADMIN_COOKIE}=${issueSessionToken()}`
  const res = requireAdmin(req('https://www.hadithreels.com/api/telegram/post',
    { cookie, origin: 'https://evil.example' }))
  expect(res?.status).toBe(403)
  const same = requireAdmin(req('https://www.hadithreels.com/api/telegram/post',
    { cookie, origin: 'https://www.hadithreels.com' }))
  expect(same).toBeNull()
})

test('next dev on localhost lets the pipeline scripts through without a cookie', () => {
  env.NODE_ENV = 'development'
  expect(requireAdmin(req('http://localhost:3002/api/telegram/post'))).toBeNull()
  expect(requireAdmin(req('http://127.0.0.1:3002/api/tts'))).toBeNull()
})

test('the dev exception never applies on Vercel, to a LAN host, or cross-origin', () => {
  env.NODE_ENV = 'development'
  expect(requireAdmin(req('http://192.168.1.20:3002/api/tts'))?.status).toBe(401)
  expect(requireAdmin(req('http://localhost:3002/api/tts',
    { origin: 'https://evil.example' }))?.status).toBe(403)
  env.VERCEL = '1'
  expect(requireAdmin(req('http://localhost:3002/api/tts'))?.status).toBe(401)
})

test('production build run locally (next start) still needs the cookie', () => {
  expect(requireAdmin(req('http://localhost:3002/api/telegram/post'))?.status).toBe(401)
})
