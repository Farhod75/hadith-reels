// app/api/render-reel/route.ts
// P054: Remotion renderer uses native binaries — cannot run on Vercel serverless
// This route works LOCALLY only for MP4 generation
// On Vercel: returns 501 with instructions to run locally
//
// LOCAL USAGE:
//   npm run remotion:adults  → renders HadithReel to out/adults.mp4
//   npm run remotion:kids    → renders KidsReel to out/kids.mp4
//
// The route is kept for future cloud rendering (Lambda/AWS Batch)

import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  // Detect if running on Vercel/serverless
  const isVercel = !!process.env.VERCEL || !!process.env.VERCEL_URL

  if (isVercel) {
    return NextResponse.json({
      error: 'Remotion rendering is not supported on Vercel serverless.',
      instructions: [
        'Run locally instead:',
        '  npm run remotion:adults  → generates out/adults.mp4',
        '  npm run remotion:kids    → generates out/kids.mp4',
        'Future: AWS Lambda rendering will be added in Phase 4',
      ],
      local_commands: {
        adults: 'npm run remotion:adults',
        kids:   'npm run remotion:kids',
        preview: 'npm run remotion:preview',
      },
    }, { status: 501 })
  }

  // Local rendering — lazy import to avoid build-time bundling
  try {
    const body = await req.json()
    const { compositionId = 'HadithReel', props, audioUrl } = body

    if (!props?.hadithArabic) {
      return NextResponse.json({ error: 'props.hadithArabic required' }, { status: 400 })
    }

    // Dynamic import — only resolves locally where native binaries exist
    const { renderMedia, selectComposition } = await import('@remotion/renderer')
    const path = await import('path')
    const fs   = await import('fs')

    const bundlePath = path.default.join(process.cwd(), 'remotion', 'index.tsx')
    const outputPath = `/tmp/reel-${Date.now()}.mp4`

    const composition = await selectComposition({
      serveUrl:   bundlePath,
      id:         compositionId,
      inputProps: { ...props, audioUrl },
    })

    await renderMedia({
      composition,
      serveUrl:       bundlePath,
      codec:          'h264',
      outputLocation: outputPath,
      inputProps:     { ...props, audioUrl },
      imageFormat:    'jpeg',
      jpegQuality:    80,
      concurrency:    1,
    })

    const videoBuffer = fs.default.readFileSync(outputPath)
    fs.default.unlinkSync(outputPath)

    return new NextResponse(videoBuffer, {
      headers: {
        'Content-Type':        'video/mp4',
        'Content-Disposition': `attachment; filename="hadith-reel-${Date.now()}.mp4"`,
        'Cache-Control':       'no-store',
      },
    })

  } catch (error: any) {
    console.error('Render error:', error?.message)
    return NextResponse.json(
      { error: 'Local render failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
