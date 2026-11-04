// app/api/admin/verify/route.ts
// Password gate for the admin panel.
// Password stored in ADMIN_PASSWORD env var — never hardcoded
// Set in Vercel: vercel env add ADMIN_PASSWORD production
//
// P353: a correct password now also sets the signed session cookie that the
// side-effecting API routes check (lib/admin-session.ts). Before, this route
// answered {ok:true} and nothing else, so the password protected the page and
// not one of the routes behind it.

import { NextRequest, NextResponse } from 'next/server'
import {
  ADMIN_COOKIE, issueSessionToken, passwordMatches, sessionCookieOptions,
} from '@/lib/admin-session'

export async function POST(req: NextRequest) {
  try {
    const { password } = await req.json()

    if (!process.env.ADMIN_PASSWORD) {
      return NextResponse.json(
        { error: 'Admin not configured' },
        { status: 503 }
      )
    }

    if (passwordMatches(password)) {
      const token = issueSessionToken()
      const res = NextResponse.json({ ok: true })
      if (token) res.cookies.set(ADMIN_COOKIE, token, sessionCookieOptions())
      return res
    }

    return NextResponse.json(
      { error: 'Invalid password' },
      { status: 401 }
    )
  } catch {
    return NextResponse.json(
      { error: 'Bad request' },
      { status: 400 }
    )
  }
}
