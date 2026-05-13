// app/api/generate-video/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { fal } from '@fal-ai/client'

const SCENE_PROMPTS: Record<string, string> = {
  intro: `Cinematic Islamic mosque interior at golden hour,
    soft rays of light streaming through ornate arched windows,
    intricate geometric tile patterns on walls,
    hanging lanterns glowing warm amber,
    slow gentle camera drift upward,
    no people, peaceful sacred atmosphere,
    vertical 9:16, photorealistic, 4K, cinematic`,

  arabic: `Ancient Arabic calligraphy manuscript on aged parchment,
    soft candlelight illuminating golden ink,
    ornate Islamic geometric border patterns,
    dust particles floating in light, slow zoom in,
    no people, vertical 9:16, photorealistic, 4K`,

  story: `Aerial view of ancient Madinah at twilight,
    golden dome of Al-Masjid an-Nabawi glowing,
    date palm trees swaying gently in warm breeze,
    stars appearing in deep blue sky,
    slow cinematic push forward, no people,
    vertical 9:16, photorealistic, 4K, cinematic`,

  moral: `Single candle flame burning in dark room,
    warm golden light spreading outward,
    soft bokeh background, gentle flickering motion,
    no people, vertical 9:16, photorealistic, 4K`,

  outro: `Night sky over desert, thousands of stars in Milky Way,
    gentle camera tilt upward revealing vast galaxy,
    warm crescent moon glowing on horizon,
    date palm silhouettes in foreground, no people,
    vertical 9:16, photorealistic, 4K, cinematic`,

  kids: `Bright colorful Islamic garden, flowers blooming,
    butterflies floating gently, small fountain sparkling,
    warm sunlight, joyful peaceful atmosphere, no people,
    cartoon-friendly aesthetic, vertical 9:16, vibrant, 4K`,
}

export async function POST(req: NextRequest) {
  try {
    const { scene = 'intro', style = 'adults' } = await req.json()

    if (!process.env.FAL_KEY) {
      return NextResponse.json(
        { error: 'FAL_KEY not configured' },
        { status: 503 }
      )
    }

    const promptKey = style === 'kids' ? 'kids' : scene
    const prompt = SCENE_PROMPTS[promptKey] || SCENE_PROMPTS.intro

    const result = await fal.subscribe('fal-ai/kling-video/v1.6/standard/text-to-video', {
      input: {
        prompt,
        duration: '5',
        aspect_ratio: '9:16',
      },
      
      logs: true,
    })

    const videoUrl = (result.data as any)?.video?.url

    if (!videoUrl) {
      return NextResponse.json(
        { error: 'No video URL returned', raw: result.data },
        { status: 500 }
      )
    }

    return NextResponse.json({ ok: true, videoUrl, scene, style })

  } catch (error: any) {
    console.error('fal.ai error:', error?.message)
    return NextResponse.json(
      { error: error?.message || 'Video generation failed' },
      { status: 500 }
    )
  }
}