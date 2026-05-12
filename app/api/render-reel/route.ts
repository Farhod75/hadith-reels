// app/api/render-reel/route.ts
// POST: triggers Remotion render → returns MP4 download URL
// Uses @remotion/renderer for server-side rendering
// Called from admin panel after story generation

import { NextRequest, NextResponse } from 'next/server'
import path from 'path'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const {
      compositionId = 'HadithReel', // 'HadithReel' | 'KidsReel'
      props,
      audioUrl,
    } = body

    if (!props?.hadithArabic) {
      return NextResponse.json({ error: 'props.hadithArabic required' }, { status: 400 })
    }

    // Dynamically import Remotion renderer (server-side only)
    const { renderMedia, selectComposition } = await import('@remotion/renderer')

    const bundlePath = path.join(process.cwd(), 'remotion', 'index.ts')

    // Select the composition
    const composition = await selectComposition({
      serveUrl: bundlePath,
      id:       compositionId,
      inputProps: { ...props, audioUrl },
    })

    // Output path — temp file in /tmp
    const outputPath = `/tmp/reel-${Date.now()}.mp4`

    // Render the video
    await renderMedia({
      composition,
      serveUrl:   bundlePath,
      codec:      'h264',
      outputLocation: outputPath,
      inputProps: { ...props, audioUrl },
      imageFormat: 'jpeg',
      jpegQuality: 80,
      concurrency: 1,    // single thread to avoid memory issues on serverless
      onProgress: ({ progress }) => {
        console.log(`Render progress: ${Math.round(progress * 100)}%`)
      },
    })

    // Read the rendered file and return as download
    const fs = await import('fs')
    const videoBuffer = fs.readFileSync(outputPath)

    // Clean up temp file
    fs.unlinkSync(outputPath)

    return new NextResponse(videoBuffer, {
      headers: {
        'Content-Type':        'video/mp4',
        'Content-Disposition': `attachment; filename="hadith-reel-${Date.now()}.mp4"`,
        'Cache-Control':       'no-store',
      },
    })

  } catch (error: any) {
    console.error('Render error:', error?.message)

    // Remotion not installed — return helpful error
    if (error?.message?.includes('Cannot find module')) {
      return NextResponse.json({
        error: 'Remotion renderer not installed. Run: npm install @remotion/renderer',
        install_command: 'npm install remotion @remotion/renderer @remotion/bundler',
      }, { status: 503 })
    }

    return NextResponse.json(
      { error: 'Render failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
