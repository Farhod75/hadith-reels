// app/api/tts/route.ts
// ElevenLabs TTS proxy — EN/AR/RU via ElevenLabs, UZ/TJ via OpenAI gpt-4o-mini-tts
// POST { text, lang, style }
// Returns audio/mpeg stream
// P070: text cleaning for Prophet name + Islamic symbols
// P071: OpenAI Nova for UZ/TJ Cyrillic
// P073: gpt-4o-mini-tts + instructions parameter for Uzbek/Tajik phonetics

import { NextRequest, NextResponse } from 'next/server'

const VOICE_MAP: Record<string, Record<string, string>> = {
  ar: {
    adults: process.env.ELEVENLABS_VOICE_HIJAZI    || 'pNInz6obpgDQGcFmaJgB',
    kids:   process.env.ELEVENLABS_VOICE_ABU_SALEM || 'pNInz6obpgDQGcFmaJgB',
  },
  ru: {
    adults: process.env.ELEVENLABS_VOICE_ABRAR     || 'ErXwobaYiN019PkySvjV',
    kids:   process.env.ELEVENLABS_VOICE_ABRAR     || 'ErXwobaYiN019PkySvjV',
  },
  en: {
    adults: process.env.ELEVENLABS_VOICE_EN_ADULTS || 'EkK5I93UQWFDigLMpZcX',
    kids:   process.env.ELEVENLABS_VOICE_EN_KIDS   || 'FVQMzxJGPUBtfz1Azdoy',
  },
}

// P073: per-language phonetic instructions for gpt-4o-mini-tts
// Keyed as `${lang}.${style}` — e.g., 'uz.kids', 'tj.adults'
const TTS_INSTRUCTIONS: Record<string, string> = {
  'ru.kids':
    "Speak as a native Russian speaker reading to young children. Use a warm, " +
    "gentle, joyful and clear tone. This is a religious children's story — speak " +
    "with reverence, kindness and care. Natural Russian pronunciation and pacing.",

  'uz.kids':
    "Speak as a native Uzbek (O'zbek) speaker reading to children. Use warm, gentle, joyful tone. " +
    "Pronounce these Uzbek Cyrillic letters precisely: ҳ as a clear breathy aspirated H (like the H in 'house'/'hello') — it must ALWAYS be audibly pronounced as H, never dropped and never softened to an s/с sound, never Russian х; " +
    "қ as deep uvular k from back of throat (like Arabic ق, not Russian к) — pronounce қ consistently strong " +
    "whether at start, middle, or end of word; ў as 'o' sound in 'go'; ғ as voiced uvular g (like Arabic غ); " +
    "ж as English 'j' in 'judge'/'jam' — a soft single J sound, NEVER the Russian/French 'zh' (as in 'measure'); apply this to EVERY ж including at the end of a word. " +
    "Example pronunciations: жилмайиб = 'JIL-mai-ib' (start with soft English J, no D); " +
    "иссиқ = 'is-SEEQ' (strong throat-back Q at end, NOT soft K); " +
    "қуёшдек = 'qu-yosh-DEK' (strong Q at start); меҳрибон = 'meh-hree-BON' (clear breathy H in the middle, NEVER 'mes-ri-bon'); сувга = 'suv-GA' (plain hard g like 'go' — do NOT harden plain г into the throaty ғ/gh); жонзот = 'JON-zot' (English J like 'judge', NOT 'zhon'); муҳтож = 'muh-TOJ' (clear H, and end with English J — NOT 'muh-tozh'). " +
    "Place word stress on the final syllable per Uzbek convention. " +
    "Do not use Russian phonetic patterns. This is a religious children's story — speak with reverence and clarity.",

  'uz.adults':
    "Speak as a native Uzbek (O'zbek) speaker. Use scholarly, reverent tone. " +
    "Pronounce these Uzbek Cyrillic letters precisely: ҳ as aspirated h (like in 'house', not Russian х); " +
    "қ as deep uvular k from back of throat (like Arabic ق, not Russian к) — pronounce қ consistently strong " +
    "whether at start, middle, or end of word; ў as 'o' sound in 'go'; ғ as voiced uvular g (like Arabic غ); " +
    "ж as English 'j' in 'judge' or 'jim', NOT French 'zh' / Russian zh. " +
    "Place word stress on the final syllable per Uzbek convention. " +
    "Do not use Russian phonetic patterns. This is religious content — speak with gravity and respect.",

  'tj.kids':
    "Speak as a native Tajik (Тоҷикӣ) speaker reading to children. Use warm, gentle, joyful tone. " +
    "Pronounce these Tajik Cyrillic letters precisely: ҳ as aspirated h (like Arabic ح); " +
    "қ as deep uvular k (like Arabic ق); ҷ as English 'j' in 'judge'; ӣ as long 'ee'; ӯ as long 'oo'; " +
    "ғ as voiced uvular g (like Arabic غ). Do not use Russian phonetic patterns. " +
    "This is a religious children's story — speak with reverence and clarity.",

  'tj.adults':
    "Speak as a native Tajik (Тоҷикӣ) speaker. Use scholarly, reverent tone. " +
    "Pronounce these Tajik Cyrillic letters precisely: ҳ as aspirated h (like Arabic ح); " +
    "қ as deep uvular k (like Arabic ق); ҷ as English 'j' in 'judge'; ӣ as long 'ee'; ӯ as long 'oo'; " +
    "ғ as voiced uvular g (like Arabic غ). Do not use Russian phonetic patterns. " +
    "This is religious content — speak with gravity and respect.",
}

function cleanForTTS(text: string, lang: string): string {
  const prophetPhrase =
    lang === 'ar' ? 'صلى الله عليه وسلم' :
    lang === 'uz' ? 'Саллаллоҳу алайҳи васаллам' :
    lang === 'tj' ? 'Саллаллоҳу алайҳи васаллам' :
    lang === 'ru' ? 'Да благословит его Аллах и приветствует' :
    'peace be upon him'

  return text
    .replace(/ﷺ/g, prophetPhrase)
    .replace(/\(ﷺ\)/g, prophetPhrase)
    .replace(/p\.b\.u\.h\.?/gi, prophetPhrase)
    .replace(/\(pbuh\)/gi, prophetPhrase)
    .replace(/\(saw\)/gi, prophetPhrase)
    .replace(/\(s\.a\.w\.?\)/gi, prophetPhrase)
    .replace(/ﷲ/g, lang === 'ar' ? 'الله' : 'Аллоҳ')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .slice(0, 1000)
    .trim()
}

export async function POST(req: NextRequest) {
  try {
    const { text, lang = 'en', style = 'adults' } = await req.json()

    if (!text?.trim()) {
      return NextResponse.json({ error: 'text required' }, { status: 400 })
    }

    const cleanText = cleanForTTS(text, lang)
    const langKey = lang.replace('_cyrillic', '').replace('_latin', '')
    // RU kids -> OpenAI Nova (female); RU adults stays on ElevenLabs (Abrar)
    const useOpenAI = ['uz', 'tj'].includes(langKey) || (langKey === 'ru' && style === 'kids')

    // ── OpenAI gpt-4o-mini-tts for UZ/TJ ─────────────────────────────────────
    if (useOpenAI) {
      const openAIKey = process.env.OPENAI_API_KEY
      if (!openAIKey) {
        return NextResponse.json({ error: 'OPENAI_API_KEY not configured' }, { status: 503 })
      }

      // P073: pick language-specific phonetic instructions
      const instructionsKey = `${langKey}.${style}`
      const instructions = TTS_INSTRUCTIONS[instructionsKey] || TTS_INSTRUCTIONS[`${langKey}.adults`]

      const openAIRes = await fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openAIKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'gpt-4o-mini-tts',
          voice: style === 'kids' ? 'nova' : 'onyx',
          input: cleanText,
          instructions,
        }),
      })

      if (!openAIRes.ok) {
        const err = await openAIRes.text()
        return NextResponse.json({ error: 'OpenAI TTS failed: ' + err }, { status: openAIRes.status })
      }

      const audioBuffer = await openAIRes.arrayBuffer()
      return new NextResponse(audioBuffer, {
        headers: { 'Content-Type': 'audio/mpeg', 'Cache-Control': 'no-store' },
      })
    }

    // ── ElevenLabs for EN/AR/RU ──────────────────────────────────────────────
    const apiKey = process.env.ELEVENLABS_API_KEY
    if (!apiKey) {
      return NextResponse.json({ error: 'ElevenLabs not configured' }, { status: 503 })
    }

    const voiceMap = VOICE_MAP[langKey] || VOICE_MAP.en
    const voiceId  = voiceMap[style] || voiceMap.adults

    const elevenRes = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream`,
      {
        method: 'POST',
        headers: {
          'xi-api-key':   apiKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: cleanText,
          model_id: 'eleven_multilingual_v2',
          voice_settings: { stability: 0.5, similarity_boost: 0.75 },
        }),
      }
    )

    if (!elevenRes.ok) {
      const errText = await elevenRes.text()
      return NextResponse.json({ error: 'TTS failed: ' + elevenRes.status }, { status: elevenRes.status })
    }

    const audioBuffer = await elevenRes.arrayBuffer()
    return new NextResponse(audioBuffer, {
      headers: { 'Content-Type': 'audio/mpeg', 'Cache-Control': 'no-store' },
    })

  } catch (error: any) {
    console.error('TTS route error:', error?.message)
    return NextResponse.json({ error: 'TTS failed: ' + (error?.message || 'unknown') }, { status: 500 })
  }
}
