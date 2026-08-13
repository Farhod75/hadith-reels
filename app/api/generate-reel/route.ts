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
      name: 'Uswa al-Hasana (Усваи Ҳасана)',
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
  "story": "3-4 sentences explaining what this hadith teaches and why it matters, drawing on ${seerahSource.name} where it records something relevant. Warm and accessible, not academic. Use only what the hadith and that source actually record — if neither records an incident for this hadith, explain the teaching plainly. A shorter, plainer story is correct; an invented one is not.",
  "moral": "1-2 sentence practical takeaway. What should someone DO or FEEL differently after watching this reel? Make it actionable for modern life.",
  "seerah_context": "2-3 sentences of context. If the sources tie this hadith to a specific period or event, name it. If they do not, give the collection and book, the narrator, and the classical scholarly reading of the hadith's meaning — and nothing more. Do not supply a period, setting, or occasion that the sources do not record.",
  "source_attribution": "${seerahSource.attribution}",
  "caption_intro": "First 2 lines of social media caption — must grab attention immediately. No hashtags here."
}

RULES:
1. ALL fields in the language specified above (${lang})
2. story may reference the Prophet ﷺ or his companions ONLY as the hadith and
   cited seerah source record them. If neither records an incident for this
   hadith, do NOT construct one — explain the teaching itself instead.
3. moral MUST be practical — what to do TODAY
4. title MUST be shareable — would someone click on this?
5. For Kids style: use simple, concrete language a child can follow. Do NOT invent
   a scene — describe the historical setting and the lesson in plain words
6. seerah_context cites a real period ONLY if the sources tie this hadith to one.
   Otherwise state exactly three things and nothing more: the collection and book,
   the narrator, and the classical scholarly reading of the hadith's meaning.
   Do NOT add a period, setting, or occasion in softened form — phrases like
   "during a time when" or "in an era where" are occasions and are forbidden.
   Do NOT name a seerah source unless you are citing a specific documented
   passage from it about THIS hadith.

ABSOLUTE CONTENT RULES (violating any of these is a fabricated hadith):
7. NEVER invent an incident, scene, or conversation that is not in the hadith text
   or the cited seerah source
8. NEVER attribute direct or indirect speech to the Prophet ﷺ, any prophet, or any
   companion beyond what the hadith itself records. No quotation marks around words
   they did not say.
9. NEVER state what any person or group felt, thought, saw, or did afterwards.
   NEVER assert the occasion, setting, or audience of the hadith unless the
   narration itself records it. Most hadith have no recorded occasion — say
   nothing rather than supply one.
10. If the hadith text is short, expand ONLY into documented historical context of
    the period. Do NOT compensate with narrative — a shorter story is correct;
    an invented one is not.
11. Name narrators plainly - "narrated by Ibn Umar", nothing more. Do NOT add
    epithets, honorific descriptions, family relationships, or standing among
    the companions ("the great companion", "son of the second caliph", "one of
    the closest companions"). Standard honorifics that follow a name in the
    target language (RA, رضي الله عنه, розияллоҳу анҳу) are permitted.
12. Use isnad verbs correctly. The Prophet ﷺ SAID the hadith; the companion
    NARRATED or TRANSMITTED it. Never write that the Prophet ﷺ transmitted,
    related, or passed on a hadith - in Russian use "сказал", not "передал"
    or "рассказал"; the equivalent distinction applies in every language.`

    const response = await anthropic.messages.create({
      model:      'claude-sonnet-4-6',
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
    
    return NextResponse.json(result)

  } catch (error: any) {
    console.error('Generate reel error:', error?.message)
    return NextResponse.json(
      { error: 'Generation failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
