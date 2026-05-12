// app/api/generate-reel/route.ts
// POST /api/generate-reel
// Generates story + moral + seerah_context + caption for a hadith reel
//
// Seerah sources (dual — matched to language):
//   AR/EN → Ar-Raheeq Al-Makhtum (Safiur Rahman al-Mubarakpuri)
//   UZ/TJ/RU → Uswa al-Hasana (Усваи Хасана) — Turkish Islamic Seerah
//              translated to Russian/Uzbek, emotional devotional style

import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY! })

// ─── Language instruction ─────────────────────────────────────────────────────
function getLangInstruction(lang: string): string {
  if (lang === 'uz' || lang === 'uz_cyrillic')
    return 'Write ALL text in UZBEK CYRILLIC script (Ўзбек Кириллча). Every single character must be Cyrillic. Do NOT use Latin.'
  if (lang === 'uz_latin')
    return 'Write ALL text in Uzbek Latin script (O\'zbek lotin).'
  if (lang === 'ru')
    return 'Write ALL text in Russian (Русский язык).'
  if (lang === 'ar')
    return 'Write ALL text in Modern Standard Arabic (العربية الفصحى).'
  if (lang === 'tj')
    return 'Write ALL text in Tajik Cyrillic (Тоҷикӣ). Use Tajik vocabulary, not Russian.'
  return 'Write ALL text in English.'
}

// ─── Seerah source selection ──────────────────────────────────────────────────
// Ar-Raheeq Al-Makhtum: scholarly, historical, Arabic/English audience
// Uswa al-Hasana: emotional, devotional, warm — Russian/Uzbek/Tajik audience
function getSeerahSource(lang: string): { name: string; description: string; attribution: string } {
  if (lang === 'ru' || lang === 'uz' || lang === 'uz_cyrillic' || lang === 'uz_latin' || lang === 'tj') {
    return {
      name: 'Uswa al-Hasana (Усваи Хасана)',
      description: 'the multi-volume Turkish Islamic Seerah translated into Russian and Uzbek, known for its warm emotional and devotional style, strong emphasis on love for the Prophet ﷺ',
      attribution: lang === 'ru'
        ? '📖 Источник: Усваи Хасана'
        : lang === 'tj'
        ? '📖 Сарчашма: Усваи Ҳасана'
        : '📖 Манба: Усваи Ҳасана',
    }
  }
  return {
    name: 'Ar-Raheeq Al-Makhtum',
    description: 'the award-winning biography of the Prophet ﷺ by Safiur Rahman al-Mubarakpuri, first prize of the Muslim World League Seerah competition 1979, known for its scholarly and eloquent style',
    attribution: '📖 Source: Ar-Raheeq Al-Makhtum',
  }
}

// ─── Audience instruction ─────────────────────────────────────────────────────
function getAudienceInstruction(style: string): string {
  if (style === 'kids') {
    return `Audience: children aged 6-14.
- Use SIMPLE, short sentences. Max 10 words per sentence.
- Use vivid comparisons children understand (like a kind teacher, like the sun warming you)
- No scholarly terms. No Arabic terms without immediate simple explanation.
- Warm, encouraging, wonder-inspiring tone.
- End with something a child can DO today.`
  }
  return `Audience: adults seeking spiritual growth.
- Use eloquent, warm, scholarly tone.
- Can include deeper reflection and nuance.
- Reference historical context naturally.
- Inspire without being preachy.`
}

// ─── Main handler ─────────────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}))
    const {
      hadith_text,
      hadith_arabic,
      narrator,
      collection,
      hadith_number,
      tags,
      style = 'adults',
      lang  = 'en',
    } = body

    if (!hadith_text?.trim()) {
      return NextResponse.json({ error: 'hadith_text required' }, { status: 400 })
    }

    const langInstruction     = getLangInstruction(lang)
    const audienceInstruction = getAudienceInstruction(style)
    const seerahSource        = getSeerahSource(lang)

    const prompt = `${langInstruction}

${audienceInstruction}

Hadith to create a reel about:
Text: "${hadith_text}"
Arabic: "${hadith_arabic || ''}"
Narrator: ${narrator || 'unknown'}
Collection: ${collection || 'unknown'}${hadith_number ? ` #${hadith_number}` : ''}
Tags: ${tags?.join(', ') || ''}

Seerah source to draw from:
"${seerahSource.name}" — ${seerahSource.description}

Generate reel content. Respond ONLY with valid JSON (no markdown, no backticks, no preamble):
{
  "title": "Short engaging reel title — max 8 words, shareable, inspiring",
  "story": "A 3-4 sentence story from the life of the Prophet ﷺ drawn from ${seerahSource.name}. Must be warm, vivid, story-like — NOT academic. Must give human emotional context to WHY this hadith matters. Must feel real and touching.",
  "moral": "1-2 sentence practical takeaway. What should someone DO or FEEL differently after watching this reel? Make it actionable for modern life.",
  "seerah_context": "2-3 sentences: the specific historical moment or period when this teaching was most lived or demonstrated by the Prophet ﷺ. Grounded in Seerah facts.",
  "source_attribution": "${seerahSource.attribution}",
  "caption_intro": "First 2 lines of social media caption — must grab attention immediately. No hashtags here."
}

RULES:
1. ALL fields in the language specified above (${lang})
2. story MUST mention the Prophet ﷺ or his companions by name
3. moral MUST be practical — what to do TODAY
4. title MUST be shareable — would someone click on this?
5. For Kids style: story must be a simple scene a child can picture
6. seerah_context must cite a real period (Makkah, Madinah, Hijra, etc.)`

    const response = await anthropic.messages.create({
      model:      'claude-sonnet-4-20250514',
      max_tokens: 1200,
      messages:   [{ role: 'user', content: prompt }],
    })

    const raw = response.content[0].type === 'text' ? response.content[0].text : '{}'

    let result: any
    try {
      const clean = raw.replace(/```json|```/g, '').trim()
      const start = clean.indexOf('{')
      const end   = clean.lastIndexOf('}')
      result = JSON.parse(clean.slice(start, end + 1))
    } catch {
      console.error('Parse error:', raw.slice(0, 300))
      return NextResponse.json({ error: 'Failed to parse AI response' }, { status: 500 })
    }

    // Add metadata
    result.lang           = lang
    result.style          = style
    result.seerah_source  = seerahSource.name
    result.attribution    = seerahSource.attribution

    return NextResponse.json(result)

  } catch (error: any) {
    console.error('Generate reel error:', error?.message)
    return NextResponse.json(
      { error: 'Generation failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
