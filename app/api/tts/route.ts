// app/api/tts/route.ts
// ElevenLabs TTS proxy — same pattern as hadith-verifier
// POST { text, lang, style }
// Returns audio/mpeg stream

import { NextRequest, NextResponse } from 'next/server'

// Voice matrix: lang × style → ElevenLabs voice ID
// Store actual IDs in .env.local
const VOICE_MAP: Record<string, Record<string, string>> = {
  ar: {
    adults: process.env.ELEVENLABS_VOICE_HIJAZI     || 'pNInz6obpgDQGcFmaJgB',
    kids:   process.env.ELEVENLABS_VOICE_ABU_SALEM  || 'pNInz6obpgDQGcFmaJgB',
  },
  ru: {
    adults: process.env.ELEVENLABS_VOICE_ABRAR      || 'ErXwobaYiN019PkySvjV',
    kids:   process.env.ELEVENLABS_VOICE_ABRAR      || 'ErXwobaYiN019PkySvjV',
  },
  uz: {
    adults: process.env.ELEVENLABS_VOICE_ABRAR      || 'ErXwobaYiN019PkySvjV',
    kids:   process.env.ELEVENLABS_VOICE_ABRAR      || 'FVQMzxJGPUBtfz1Azdoy',
  },
  en: {
    adults: process.env.ELEVENLABS_VOICE_EN_ADULTS  || 'EkK5I93UQWFDigLMpZcX',
    kids:   process.env.ELEVENLABS_VOICE_EN_KIDS    || 'FVQMzxJGPUBtfz1Azdoy',
  },
  tj: {
    // Tajik: fallback to Russian voice
    adults: process.env.ELEVENLABS_VOICE_ABRAR      || 'ErXwobaYiN019PkySvjV',
    kids:   process.env.ELEVENLABS_VOICE_ABRAR      || 'ErXwobaYiN019PkySvjV',
  },
}

export async function POST(req: NextRequest) {
  try {
    const { text, lang = 'en', style = 'adults' } = await req.json()

    if (!text?.trim()) {
      return NextResponse.json({ error: 'text required' }, { status: 400 })
    }

    const apiKey = process.env.ELEVENLABS_API_KEY
    if (!apiKey) {
      return NextResponse.json({ error: 'ElevenLabs not configured' }, { status: 503 })
    }

    // Get voice ID for lang + style
    const langKey  = lang.replace('_cyrillic', '').replace('_latin', '') // uz_cyrillic → uz
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
          text: text.slice(0, 1000), // cap to avoid quota burn
          model_id: 'eleven_multilingual_v2',
          voice_settings: {
            stability:        0.5,
            similarity_boost: 0.75,
          },
        }),
      }
    )

    if (!elevenRes.ok) {
      const errText = await elevenRes.text()
      console.error('ElevenLabs error:', errText)
      return NextResponse.json(
        { error: 'TTS failed: ' + elevenRes.status },
        { status: elevenRes.status }
      )
    }

    // Stream audio back to client
    const audioBuffer = await elevenRes.arrayBuffer()
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type':  'audio/mpeg',
        'Cache-Control': 'no-store',
      },
    })

  } catch (error: any) {
    console.error('TTS route error:', error?.message)
    return NextResponse.json(
      { error: 'TTS failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
