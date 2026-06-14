// app/api/reels/route.ts
// P050: TJ has no text_tajik column — shows Russian as display fallback
// P073: text_tajik column added, TJ now reads native Tajik with RU fallback for safety

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url)
    const grade  = searchParams.get('grade')  || 'all'
    const lang   = searchParams.get('lang')   || 'en'
    const limit  = parseInt(searchParams.get('limit')  || '40')
    const offset = parseInt(searchParams.get('offset') || '0')

    const sb = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    )

    let query = sb
      .from('hadith_library')
      .select('id, text_arabic, text_english, text_uzbek, text_russian, text_tajik, narrator, collection, hadith_number, grade, tags, source_url, authority', { count: 'exact' })
      .order('collection')
      .range(offset, offset + limit - 1)

    if (grade !== 'all') {
      query = query.eq('grade', grade)
    } else {
      query = query.in('grade', ['sahih', 'hasan'])
    }

    const { data, error, count } = await query
    if (error) return NextResponse.json({ error: error.message }, { status: 500 })

    // Accurate Sahih sub-count for the header (independent of pagination)
    let sahihCount = 0
    {
      const { count: sc } = await sb
        .from('hadith_library')
        .select('id', { count: 'exact', head: true })
        .eq('grade', 'sahih')
      sahihCount = sc ?? 0
    }

    const results = (data || []).map(h => ({
      ...h,
      text_display:
        lang === 'uz' || lang === 'uz_cyrillic' || lang === 'uz_latin'
          ? (h.text_uzbek   || h.text_english)
          : lang === 'tj'
          ? (h.text_tajik   || h.text_russian || h.text_english)
          : lang === 'ru'
          ? (h.text_russian || h.text_english)
          : h.text_english,
      // P073: TJ now shows native Tajik when available, RU fallback only if missing
      display_lang:
        lang === 'tj'
          ? (h.text_tajik ? 'tj' : 'ru_fallback')
          : lang,
    }))

    return NextResponse.json({ reels: results, total: count ?? results.length, sahih: sahihCount, offset, limit, lang })

  } catch (error: any) {
    return NextResponse.json({ error: error?.message || 'Failed' }, { status: 500 })
  }
}
