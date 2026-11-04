// lib/admin-session.ts
// P353: the admin password used to gate only the admin PAGE. /api/admin/verify
// answered {ok:true} and set nothing, so every route that spends money or
// publishes - telegram/post, tts, generate-reel, generate-video, render-reel -
// took a request from anyone who knew its URL. On 2026-11-04 an empty POST to
// the production telegram route answered "caption required": the bot token was
// configured, and the next request with a caption would have posted to the
// channel. (Sol 6.1 audit R7; the env vars were removed from Vercel the same
// night as the stop-gap.)
//
// Now: a correct password gets a signed, HttpOnly, SameSite=Strict cookie, and
// requireAdmin() checks it on the server before a route does anything else.
//
// Local development is the one exception, because the pipeline scripts
// (tg-post-set.py, narrate-reel.py) call http://localhost:3002 with no browser
// and no cookie. It is allowed only under `next dev` (NODE_ENV=development),
// never on Vercel, and only for a localhost Host header. A cross-origin browser
// request is refused everywhere, which is what stops a web page you happen to
// have open from POSTing to your dev server.

import { createHmac, timingSafeEqual } from 'node:crypto'
import { NextRequest, NextResponse } from 'next/server'

export const ADMIN_COOKIE = 'hr_admin'
export const SESSION_TTL_SECONDS = 12 * 60 * 60

const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]', '::1'])

// ADMIN_SESSION_SECRET when set; otherwise the admin password itself, so the
// fix needs no new environment variable to work. Changing either one signs
// every existing session out.
function signingKey(): string | null {
  const key = process.env.ADMIN_SESSION_SECRET || process.env.ADMIN_PASSWORD
  return key ? key : null
}

function sign(payload: string, key: string): string {
  return createHmac('sha256', key).update(payload).digest('base64url')
}

function safeEqual(a: string, b: string): boolean {
  const x = Buffer.from(a)
  const y = Buffer.from(b)
  return x.length === y.length && timingSafeEqual(x, y)
}

/** The password check itself, constant-time. False when no password is configured. */
export function passwordMatches(candidate: unknown): boolean {
  const expected = process.env.ADMIN_PASSWORD
  if (!expected || typeof candidate !== 'string') return false
  return safeEqual(candidate, expected)
}

/** `v1.<expiry-seconds>.<hmac>`, or null when nothing is configured to sign with. */
export function issueSessionToken(now: number = Date.now()): string | null {
  const key = signingKey()
  if (!key) return null
  const payload = `v1.${Math.floor(now / 1000) + SESSION_TTL_SECONDS}`
  return `${payload}.${sign(payload, key)}`
}

export function verifySessionToken(token: string | undefined, now: number = Date.now()): boolean {
  const key = signingKey()
  if (!key || !token) return false
  const parts = token.split('.')
  if (parts.length !== 3 || parts[0] !== 'v1' || !/^\d+$/.test(parts[1])) return false
  if (Number(parts[1]) * 1000 <= now) return false
  return safeEqual(parts[2], sign(`v1.${parts[1]}`, key))
}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    secure:   process.env.NODE_ENV === 'production',
    sameSite: 'strict' as const,
    path:     '/',
    maxAge:   SESSION_TTL_SECONDS,
  }
}

function hostname(hostHeader: string | null): string {
  if (!hostHeader) return ''
  // "[::1]:3002" -> "[::1]", "localhost:3002" -> "localhost"
  return hostHeader.startsWith('[')
    ? hostHeader.slice(0, hostHeader.indexOf(']') + 1)
    : hostHeader.split(':')[0]
}

/** `next dev` on this machine, reached by a localhost name. Never true on Vercel. */
export function isLocalDevRequest(req: NextRequest): boolean {
  return process.env.NODE_ENV === 'development'
      && !process.env.VERCEL
      && LOCAL_HOSTS.has(hostname(req.headers.get('host')).toLowerCase())
}

/**
 * Call first in every side-effecting route:
 *   const denied = requireAdmin(req); if (denied) return denied
 * Returns null when the request may proceed, otherwise the response to send.
 */
export function requireAdmin(req: NextRequest): NextResponse | null {
  const origin = req.headers.get('origin')
  if (origin) {
    let originHost = ''
    try { originHost = new URL(origin).host } catch { /* malformed -> refused below */ }
    if (originHost !== req.headers.get('host')) {
      return NextResponse.json({ error: 'cross-origin request refused' }, { status: 403 })
    }
  }
  if (isLocalDevRequest(req)) return null
  if (verifySessionToken(req.cookies.get(ADMIN_COOKIE)?.value)) return null
  return NextResponse.json({ error: 'admin session required - sign in to /admin' }, { status: 401 })
}
