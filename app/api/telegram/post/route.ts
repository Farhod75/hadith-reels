// app/api/telegram/post/route.ts
// POST: sends a hadith reel to the Telegram channel.
//
// Body: { caption, hadith?, generated?, lang?, style?, videoPath? }
//
//   without videoPath -> sendMessage, text only (the admin studio's button)
//   with    videoPath -> sendVideo, the reel itself with the caption attached
//
// The videoPath form is what lets the pipeline post without a human: Telegram
// is the only one of the four platforms with a real publishing API, so it is
// the only one that can be automated at all. The path is resolved against the
// repo root and refused if it points outside it.
//
// Telegram caps a MESSAGE at 4096 characters but a VIDEO CAPTION at 1024.
// build-caption.ts already fits captions to 1024 (P184), so a caption that
// overflows here means something upstream stopped fitting it, and that is
// reported rather than silently truncated.
//
// P-fix in passing: this route used to append hadith.text_arabic to whatever
// caption it was handed. Captions built by build-caption.ts already carry the
// Arabic line, so that appended a second copy. It is now appended only when
// the caption does not already contain it.

import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import path from 'path'

const MESSAGE_LIMIT = 4096
const CAPTION_LIMIT = 1024

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}))
    const { caption, hadith, videoPath } = body

    const botToken = process.env.TELEGRAM_ALERT_BOT_TOKEN
    const chatId   = process.env.TELEGRAM_CHANNEL_CHAT_ID ||
                     process.env.TELEGRAM_ALERT_CHAT_ID

    if (!botToken || !chatId) {
      return NextResponse.json(
        { error: 'Telegram not configured. Set TELEGRAM_ALERT_BOT_TOKEN and TELEGRAM_CHANNEL_CHAT_ID.' },
        { status: 503 }
      )
    }
    if (!caption) {
      return NextResponse.json({ error: 'caption required' }, { status: 400 })
    }

    const arabic = hadith?.text_arabic
    const message = (arabic && !caption.includes(arabic))
      ? `${caption}\n\n${arabic}`
      : caption

    // ── text only ────────────────────────────────────────────────────────────
    if (!videoPath) {
      const res = await fetch(
        `https://api.telegram.org/bot${botToken}/sendMessage`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: chatId,
            text: message.slice(0, MESSAGE_LIMIT),
            disable_web_page_preview: false,
          }),
        }
      )
      const data = await res.json()
      if (!res.ok || !data.ok) {
        console.error('Telegram error:', data)
        return NextResponse.json(
          { error: data.description || 'Telegram API error' },
          { status: 502 }
        )
      }
      return NextResponse.json({
        ok: true, mode: 'message',
        message_id: data.result?.message_id, chat_id: chatId,
      })
    }

    // ── the reel ─────────────────────────────────────────────────────────────
    const root = process.cwd()
    const abs = path.resolve(root, videoPath)
    if (abs !== root && !abs.startsWith(root + path.sep)) {
      return NextResponse.json(
        { error: 'videoPath must be inside the project directory' },
        { status: 400 }
      )
    }
    if (path.extname(abs).toLowerCase() !== '.mp4') {
      return NextResponse.json({ error: 'videoPath must be an .mp4' }, { status: 400 })
    }
    if (message.length > CAPTION_LIMIT) {
      return NextResponse.json(
        { error: `caption is ${message.length} chars, Telegram caps a video caption at ${CAPTION_LIMIT}` },
        { status: 400 }
      )
    }

    let bytes: Buffer
    try {
      bytes = await readFile(abs)
    } catch {
      return NextResponse.json({ error: `cannot read ${videoPath}` }, { status: 400 })
    }
    if (!bytes.length) {
      return NextResponse.json({ error: `${videoPath} is empty` }, { status: 400 })
    }

    const form = new FormData()
    form.append('chat_id', String(chatId))
    form.append('caption', message)
    form.append('supports_streaming', 'true')
    // A Node Buffer is a Uint8Array over an ArrayBufferLike, which TS will not
    // accept as a BlobPart. Copying into a plain Uint8Array gives it an
    // ArrayBuffer-backed view, which it does accept.
    form.append('video', new Blob([new Uint8Array(bytes)], { type: 'video/mp4' }),
                path.basename(abs))

    const res = await fetch(
      `https://api.telegram.org/bot${botToken}/sendVideo`,
      { method: 'POST', body: form }
    )
    const data = await res.json()
    if (!res.ok || !data.ok) {
      console.error('Telegram error:', data)
      return NextResponse.json(
        { error: data.description || 'Telegram API error' },
        { status: 502 }
      )
    }

    return NextResponse.json({
      ok: true, mode: 'video',
      message_id: data.result?.message_id,
      chat_id: chatId,
      bytes: bytes.length,
      caption_chars: message.length,
    })

  } catch (error: any) {
    console.error('Telegram post error:', error?.message)
    return NextResponse.json(
      { error: 'Post failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
