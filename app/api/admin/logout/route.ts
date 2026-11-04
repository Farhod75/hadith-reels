// app/api/admin/logout/route.ts
// P361: ends the admin session set by /api/admin/verify (P353). The cookie is
// HttpOnly, so page script cannot clear it - only a response can.

import { NextResponse } from 'next/server'
import { ADMIN_COOKIE, sessionCookieOptions } from '@/lib/admin-session'

export async function POST() {
  const res = NextResponse.json({ ok: true })
  res.cookies.set(ADMIN_COOKIE, '', { ...sessionCookieOptions(), maxAge: 0 })
  return res
}
