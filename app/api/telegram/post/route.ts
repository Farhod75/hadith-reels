// app/api/telegram/post/route.ts
// POST: sends hadith reel caption to Telegram channel
// Uses existing Telegram bot from HV (Railway)
// Body: { caption, hadith, generated, lang, style }

import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}))
    const { caption, hadith, generated, lang, style } = body

    const botToken = process.env.TELEGRAM_ALERT_BOT_TOKEN
    const chatId   = process.env.TELEGRAM_CHANNEL_CHAT_ID ||
                     process.env.TELEGRAM_ALERT_CHAT_ID

    if (!botToken || !chatId) {
      return NextResponse.json(
        { error: 'Telegram not configured. Set TELEGRAM_ALERT_BOT_TOKEN and TELEGRAM_CHANNEL_CHAT_ID in Vercel env vars.' },
        { status: 503 }
      )
    }

    if (!caption) {
      return NextResponse.json({ error: 'caption required' }, { status: 400 })
    }

    // Build the message — caption + Arabic text + verification link
    const arabicText = hadith?.text_arabic
      ? `\n\n${hadith.text_arabic}`
      : ''

    const message = caption + arabicText

    // Send to Telegram channel
    const telegramRes = await fetch(
      `https://api.telegram.org/bot${botToken}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id:    chatId,
          text:       message.slice(0, 4096), // Telegram max
          parse_mode: 'HTML',
          disable_web_page_preview: false,
        }),
      }
    )

    const tgData = await telegramRes.json()

    if (!telegramRes.ok || !tgData.ok) {
      console.error('Telegram error:', tgData)
      return NextResponse.json(
        { error: tgData.description || 'Telegram API error' },
        { status: 502 }
      )
    }

    return NextResponse.json({
      ok:         true,
      message_id: tgData.result?.message_id,
      chat_id:    chatId,
    })

  } catch (error: any) {
    console.error('Telegram post error:', error?.message)
    return NextResponse.json(
      { error: 'Post failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
