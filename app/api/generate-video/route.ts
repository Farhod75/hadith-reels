// app/api/generate-video/route.ts
// Generates cinematic Islamic video via fal.ai + Kling
// Uses direct REST API — no SDK import issues in CI

import { NextRequest, NextResponse } from 'next/server'

const SCENE_PROMPTS: Record<string, string> = {
  intro: `Cinematic Islamic mosque interior at golden hour, soft rays of light streaming through ornate arched windows, intricate geometric tile patterns on walls, hanging lanterns glowing warm amber, slow gentle camera drift upward, no people, peaceful sacred atmosphere, vertical 9:16, photorealistic, 4K, cinematic`,
  arabic: `Ancient Arabic calligraphy manuscript on aged parchment, soft candlelight illuminating golden ink, ornate Islamic geometric border patterns, dust particles floating in light, slow zoom in, no people, vertical 9:16, photorealistic, 4K`,
  story: `Aerial view of ancient Madinah at twilight, golden dome of Al-Masjid an-Nabawi glowing, date palm trees swaying gently in warm breeze, stars appearing in deep blue sky, slow cinematic push forward, no people, vertical 9:16, photorealistic, 4K, cinematic`,
  moral: `Single candle flame burning in dark room, warm golden light spreading outward, soft bokeh background, gentle flickering motion, no people, vertical 9:16, photorealistic, 4K`,
  outro: `Night sky over desert, thousands of stars in Milky Way, gentle camera tilt upward revealing vast galaxy, warm crescent moon glowing on horizon, date palm silhouettes in foreground, no people, vertical 9:16, photorealistic, 4K, cinematic`,
  kids: `Bright colorful Islamic garden, flowers blooming, butterflies floating gently, small fountain sparkling, warm sunlight, joyful peaceful atmosphere, no people, cartoon-friendly aesthetic, vertical 9:16, vibrant, 4K`,
}

export async function POST(req: NextRequest) {
  try {
    const { scene = 'intro', style = 'adults' } = await req.json()

    const falKey = process.env.FAL_KEY
    if (!falKey) {
      return NextResponse.json({ error: 'FAL_KEY not configured' }, { status: 503 })
    }

    const promptKey = style === 'kids' ? 'kids' : scene
    const prompt = SCENE_PROMPTS[promptKey] || SCENE_PROMPTS.intro

    // Submit job to fal.ai queue
    const submitRes = await fetch(
      'https://queue.fal.run/fal-ai/kling-video/v1.6/standard/text-to-video',
      {
        method: 'POST',
        headers: {
          'Authorization': `Key ${falKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt,
          duration: '10',
          aspect_ratio: '9:16',
        }),
      }
    )

    if (!submitRes.ok) {
      const err = await submitRes.text()
      return NextResponse.json({ error: 'fal.ai submit failed: ' + err }, { status: 500 })
    }

    const submitted = await submitRes.json()
    const requestId = submitted.request_id

    if (!requestId) {
      return NextResponse.json({ error: 'No request_id from fal.ai', raw: submitted }, { status: 500 })
    }

    // Poll for result — max 3 minutes (36 × 5s)
    for (let i = 0; i < 36; i++) {
      await new Promise(r => setTimeout(r, 5000))

      const statusRes = await fetch(
        `https://queue.fal.run/fal-ai/kling-video/v1.6/standard/text-to-video/requests/${requestId}`,
        {
          headers: { 'Authorization': `Key ${falKey}` },
        }
      )

      const status = await statusRes.json()

      if (status.status === 'COMPLETED') {
        const videoUrl = status.output?.video?.url
        if (!videoUrl) {
          return NextResponse.json({ error: 'No video URL in response', raw: status }, { status: 500 })
        }
        return NextResponse.json({ ok: true, videoUrl, requestId, scene, style })
      }

      if (status.status === 'FAILED') {
        return NextResponse.json({ error: 'Video generation failed', raw: status }, { status: 500 })
      }
    }

    // Timeout — return requestId so client can poll later
    return NextResponse.json(
      { error: 'Timeout — still generating', requestId },
      { status: 202 }
    )

  } catch (error: any) {
    console.error('generate-video error:', error?.message)
    return NextResponse.json(
      { error: error?.message || 'Video generation failed' },
      { status: 500 }
    )
  }
}