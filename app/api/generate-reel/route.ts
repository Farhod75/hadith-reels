// app/api/generate-reel/route.ts
// POST /api/generate-reel
// Body: { hadith_id, hadith_text, hadith_arabic, narrator, collection, style, lang }
// Returns: { story, moral, seerah_context, title }
// Uses same Claude model as HV — claude-sonnet-4-20250514

import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY! })

function getLangInstruction(lang: string): string {
  if (lang === 'uz' || lang === 'uz_cyrillic')
    return 'Write ALL text in UZBEK CYRILLIC script (Ўзбек Кириллча). Every character must be Cyrillic.'
  if (lang === 'uz_latin')
    return 'Write ALL text in Uzbek Latin script (O\'zbek lotin).'
  if (lang === 'ru')
    return 'Write ALL text in Russian (Русский язык).'
  if (lang === 'ar')
    return 'Write ALL text in Modern Standard Arabic (العربية الفصحى).'
  if (lang === 'tj')
    return 'Write ALL text in Tajik Cyrillic (Тоҷикӣ).'
  return 'Write ALL text in English.'
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}))
    const {
      hadith_text,
      hadith_arabic,
      narrator,
      collection,
      hadith_number,
      style = 'adults',
      lang  = 'en',
    } = body

    if (!hadith_text?.trim()) {
      return NextResponse.json({ error: 'hadith_text required' }, { status: 400 })
    }

    const langInstruction = getLangInstruction(lang)
    const audienceInstruction = style === 'kids'
      ? 'Audience: children aged 6-14. Use SIMPLE words, short sentences, fun comparisons. No scholarly terms.'
      : 'Audience: adults. Use eloquent, scholarly tone. Deep reflection encouraged.'

    const prompt = `${langInstruction}
${audienceInstruction}

Hadith: "${hadith_text}"
Arabic: "${hadith_arabic || ''}"
Narrator: ${narrator || 'unknown'}
Collection: ${collection || 'unknown'}${hadith_number ? ` #${hadith_number}` : ''}

Generate content for a short video reel about this hadith.
Respond ONLY with valid JSON (no markdown, no backticks):
{
  "title": "Short engaging title for the reel (max 8 words)",
  "story": "A 3-4 sentence story from the life of the Prophet ﷺ (from Ar-Raheeq Al-Makhtum / Seerah sources) that gives human emotional context to this hadith. Warm, vivid, story-like — not academic.",
  "moral": "1-2 sentence takeaway lesson from this hadith. Practical, actionable, inspiring.",
  "seerah_context": "The historical moment or context when this teaching was most relevant in the Prophet's ﷺ life. 2-3 sentences."
}

RULES:
1. All fields in the language specified above
2. story must mention the Prophet ﷺ or his companions
3. moral must be practical for modern life
4. title must be engaging and shareable`

    const response = await anthropic.messages.create({
      model:      'claude-sonnet-4-20250514',
      max_tokens: 1000,
      messages:   [{ role: 'user', content: prompt }]
    })

    const raw = response.content[0].type === 'text' ? response.content[0].text : '{}'

    let result: any
    try {
      result = JSON.parse(raw.replace(/```json|```/g, '').trim())
    } catch {
      console.error('Parse error:', raw.slice(0, 200))
      return NextResponse.json({ error: 'Failed to parse AI response' }, { status: 500 })
    }

    return NextResponse.json(result)

  } catch (error: any) {
    console.error('Generate reel error:', error?.message)
    return NextResponse.json(
      { error: 'Generation failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
