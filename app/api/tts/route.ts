// app/api/tts/route.ts
// ElevenLabs TTS proxy — EN/AR/RU via ElevenLabs, UZ/TJ via OpenAI Nova
// POST { text, lang, style }
// Returns audio/mpeg stream
// P070: text cleaning for Prophet name + Islamic symbols
// P071: OpenAI Nova for UZ/TJ Cyrillic

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

function cleanForTTS(text: string, lang: string): string {
  const prophetPhrase =
    lang === 'ar' ? 'صلى الله عليه وسلم' :
    lang === 'uz' ? 'Саллаллоҳу алайҳи васаллам' :
    lang === 'tj' ? 'Салаллоҳу алайҳи васаллам' :
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
    const useOpenAI = ['uz', 'tj'].includes(langKey)

    // ── OpenAI Nova for UZ/TJ ─────────────────────────────────────────────────
    if (useOpenAI) {
      const openAIKey = process.env.OPENAI_API_KEY
      if (!openAIKey) {
        return NextResponse.json({ error: 'OPENAI_API_KEY not configured' }, { status: 503 })
      }

      const openAIRes = await fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openAIKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'tts-1',
          voice: style === 'kids' ? 'nova' : 'onyx',
          input: cleanText,
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

    // ── ElevenLabs for EN/AR/RU ───────────────────────────────────────────────
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