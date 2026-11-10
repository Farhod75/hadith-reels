// app/api/health/route.ts
// P388: health probe for the uptime monitor and the session pre-flight.
//
// One question: can this deployment reach the library in Supabase. The public
// HR site makes no Claude call (generation runs on the operator's dev server),
// so unlike HV's probe there is no model check here. 200 only when the database
// answered; 503 otherwise, so a monitor reading only the status code catches it.
// No environment detail in the body - the route is public and unauthenticated.

import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const dynamic = 'force-dynamic'

export async function GET() {
  const started = Date.now()
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY || ''
  let db: 'reachable' | 'unreachable' | 'unconfigured' = 'unconfigured'
  if (url.startsWith('https://') && key.length >= 20) {
    try {
      // head + exact count: the cheapest round trip that proves the database answered
      const { error } = await createClient(url, key)
        .from('hadith_library')
        .select('id', { count: 'exact', head: true })
      db = error ? 'unreachable' : 'reachable'
    } catch {
      db = 'unreachable'
    }
  }
  const ok = db === 'reachable'
  return NextResponse.json(
    { status: ok ? 'ok' : 'degraded', db, ms: Date.now() - started },
    { status: ok ? 200 : 503 }
  )
}
