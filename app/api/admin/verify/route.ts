// app/api/admin/verify/route.ts
// Simple password gate for admin panel
// Password stored in ADMIN_PASSWORD env var — never hardcoded
// Set in Vercel: vercel env add ADMIN_PASSWORD production

import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  try {
    const { password } = await req.json()
    const adminPassword = process.env.ADMIN_PASSWORD

    if (!adminPassword) {
      return NextResponse.json(
        { error: 'Admin not configured' },
        { status: 503 }
      )
    }

    if (password === adminPassword) {
      return NextResponse.json({ ok: true })
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
