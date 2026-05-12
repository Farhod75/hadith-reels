// app/api/reels/route.ts
// GET /api/reels — fetch hadiths from hadith_library for Browse tab
// Filters: style, lang, grade, limit, offset
// Uses SUPABASE_SERVICE_ROLE_KEY (P001 — never anon key server-side)

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const grade  = searchParams.get('grade')  || 'all'
    const lang   = searchParams.get('lang')   || 'en'
    const limit  = parseInt(searchParams.get('limit')  || '20')
    const offset = parseInt(searchParams.get('offset') || '0')
    const tag    = searchParams.get('tag')    || ''

    const sb = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    )

    let query = sb
      .from('hadith_library')
      .select('id, text_arabic, text_english, text_uzbek, text_russian, narrator, collection, hadith_number, grade, tags, source_url, authority')
      .order('collection')
      .range(offset, offset + limit - 1)

    // Grade filter — only sahih/hasan for reels (never daif per AGENTS.md)
    if (grade !== 'all') {
      query = query.eq('grade', grade)
    } else {
      // Default: only sahih and hasan — never daif in reels
      query = query.in('grade', ['sahih', 'hasan'])
    }

    // Tag filter
    if (tag) {
      query = query.contains('tags', [tag])
    }

    const { data, error } = await query

    if (error) {
      console.error('Reels fetch error:', error)
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    // Map translation field based on requested language
    const results = (data || []).map(h => ({
      ...h,
      text_display:
        lang === 'uz' || lang === 'uz_cyrillic' || lang === 'uz_latin'
          ? (h.text_uzbek   || h.text_english)
          : lang === 'ru' || lang === 'tj'
          ? (h.text_russian || h.text_english)
          : lang === 'ar'
          ? h.text_english  // Arabic users read Arabic text directly
          : h.text_english,
    }))

    return NextResponse.json({
      reels: results,
      total: results.length,
      offset,
      limit,
    })

  } catch (error: any) {
    console.error('Reels route error:', error?.message)
    return NextResponse.json(
      { error: 'Failed to fetch reels: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
