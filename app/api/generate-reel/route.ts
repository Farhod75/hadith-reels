import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

export async function POST(req: NextRequest) {
  const { textArabic, textTranslation, narrator, collection, audience, lang } = await req.json()

  if (!textArabic || !textTranslation) {
    return NextResponse.json({ error: 'textArabic and textTranslation required' }, { status: 400 })
  }

  const isKids     = audience === 'kids'
  const outputLang = lang === 'ar' ? 'English' : lang === 'uz' ? 'Uzbek' : lang === 'ru' ? 'Russian' : lang === 'tj' ? 'Tajik' : 'English'

  const prompt = isKids
    ? `You create Islamic educational content for CHILDREN aged 6-14.

Hadith: "${textTranslation}"
Narrator: ${narrator} | Collection: ${collection}

Generate a JSON object with these fields:
{
  "story_behind": "A simple, fun 2-3 sentence story a child can understand about when/why this was said. Use simple words. Start with something like 'One day...' or 'The Prophet ﷺ once...'",
  "moral_lesson": "One very simple lesson in ${outputLang} that a child aged 8 can understand. Maximum 20 words. Example: 'Always be kind, because Allah loves kind people!'",
  "hook_line": "An exciting opening sentence in ${outputLang} that grabs a child's attention. Maximum 10 words.",
  "key_words": ["3 to 5 simple words from the hadith"],
  "fun_fact": "One amazing fun fact about Islamic history related to this hadith that kids would find exciting"
}

Rules: Simple language only. No complex theology. Fun and engaging. JSON only, no preamble.`

    : `You are an Islamic scholar creating short educational reels for adult Muslims.

Hadith (Arabic): "${textArabic}"
Translation: "${textTranslation}"
Narrator: ${narrator} | Collection: ${collection}

Generate a JSON object:
{
  "story_behind": "2-3 sentences of historical context — what was happening when this was said. Be specific and vivid but accurate. In ${outputLang}.",
  "moral_lesson": "One clear modern practical lesson from this hadith. 1-2 sentences in ${outputLang}.",
  "hook_line": "One powerful opening line for social media under 10 words in ${outputLang}.",
  "key_words": ["3 to 5 key Arabic or translated words"],
  "visual_description": "A peaceful halal scene representing this hadith — no human faces, focus on nature/architecture/light/geometry."
}

Rules: Scholarly but accessible. Historically accurate. JSON only.`

  try {
    const message = await anthropic.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 1000,
      messages: [{ role: 'user', content: prompt }]
    })

    const raw = message.content[0].type === 'text' ? message.content[0].text : '{}'
    const clean = raw.replace(/```json|```/g, '').trim()
    const jsonStart = clean.indexOf('{')
    const jsonEnd = clean.lastIndexOf('}')
    const data = JSON.parse(clean.slice(jsonStart, jsonEnd + 1))

    return NextResponse.json({ ...data, audience, lang })
  } catch (err: any) {
    console.error('generate-reel error:', err?.message)
    return NextResponse.json({ error: 'Generation failed' }, { status: 500 })
  }
}