import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null)
  if (!body || !body.text || !body.voiceId) {
    return NextResponse.json({ error: 'text and voiceId required' }, { status: 400 })
  }
  const apiKey = process.env.ELEVENLABS_API_KEY
  if (!apiKey) {
    return NextResponse.json({ error: 'TTS not configured' }, { status: 503 })
  }
  try {
    const res = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${body.voiceId}/stream`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'xi-api-key': apiKey },
        body: JSON.stringify({
          text: body.text.slice(0, 500),
          model_id: 'eleven_multilingual_v2',
        }),
      }
    )
    if (!res.ok) return NextResponse.json({ error: 'ElevenLabs error' }, { status: 502 })
    const audio = await res.arrayBuffer()
    return new NextResponse(audio, { headers: { 'Content-Type': 'audio/mpeg' } })
  } catch {
    return NextResponse.json({ error: 'TTS failed' }, { status: 500 })
  }
}