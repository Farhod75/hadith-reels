// app/api/tts/route.ts
// ElevenLabs TTS proxy — all languages via ElevenLabs eleven_v3
// POST { text, lang, style, mascot, slug, section }
// Returns audio/mpeg stream; in dev also writes to out/work/{style}/{slug}/{lang}/
// P070: text cleaning for Prophet name + Islamic symbols
// P102: UZ/TJ moved from OpenAI to ElevenLabs eleven_v3
// P103: kids voices split by mascot (boy lamb = male, girl lamb = female);
//       RU kids migrated off OpenAI Nova — OpenAI fully retired from this route
// P106: TTS writes narration to disk directly — removes manual download/rename/move

import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import path from 'path'

type VoiceSet = {
  adults: string
  kids: { boy: string; girl: string }
}

const VOICE_MAP: Record<string, VoiceSet> = {
  ar: {
    adults: process.env.ELEVENLABS_VOICE_HIJAZI    || 'pNInz6obpgDQGcFmaJgB',
    kids: {
      girl: process.env.ELEVENLABS_VOICE_AR_KIDS     || 'pNInz6obpgDQGcFmaJgB',
      boy:  process.env.ELEVENLABS_VOICE_AR_KIDS_BOY || 'pNInz6obpgDQGcFmaJgB',
    },
  },
  ru: {
    adults: process.env.ELEVENLABS_VOICE_ABRAR     || 'ErXwobaYiN019PkySvjV',
    kids: {
      girl: process.env.ELEVENLABS_VOICE_RU_KIDS     || 'ocFEgn1SP9oWO9QrLDgb', // Arabella Calm & Mature
      boy:  process.env.ELEVENLABS_VOICE_RU_KIDS_BOY || 'pw8bioilqsSn2jApHYwT', // Liam Youthful
    },
  },
  en: {
    adults: process.env.ELEVENLABS_VOICE_EN_ADULTS || 'EkK5I93UQWFDigLMpZcX', // James
    kids: {
      girl: process.env.ELEVENLABS_VOICE_EN_KIDS     || 'FVQMzxJGPUBtfz1Azdoy', // Danielle
      boy:  process.env.ELEVENLABS_VOICE_EN_KIDS_BOY || 'cjVigY5qzO86Huf0OWal', // Eric
    },
  },
  uz: {
    adults: process.env.ELEVENLABS_VOICE_UZ_ADULTS || 'R3XXDwKMU2YHwBcuYUH3', // Opa Johann
    kids: {
      girl: process.env.ELEVENLABS_VOICE_UZ_KIDS     || 'hO2yZ8lxM3axUxL8OeKX', // Mini
      boy:  process.env.ELEVENLABS_VOICE_UZ_KIDS_BOY || 'JBFqnCBsd6RMkjVDRZzb', // George
    },
  },
  tj: {
    adults: process.env.ELEVENLABS_VOICE_TJ_ADULTS || 'KXptrwcsEqqFSwRKJukF', // Meisam
    kids: {
      girl: process.env.ELEVENLABS_VOICE_TJ_KIDS     || '0zUZ5qUGb8wympsfJH8d', // Katherine Polished
      boy:  process.env.ELEVENLABS_VOICE_TJ_KIDS_BOY || 'VCgLBmBjldJmfphyB8sZ', // Liam Viral
    },
  },
}

// P073: per-language phonetic instructions, written for OpenAI gpt-4o-mini-tts.
// RETAINED FOR REFERENCE ONLY — no longer called. eleven_v3 handles these
// phonemes natively (that was the reason for P102). Kept because this encodes
// hard-won Uzbek/Tajik pronunciation knowledge worth preserving if a future
// provider or an ElevenLabs pronunciation dictionary needs it.
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
    "CRITICAL: plain г is a plain hard g as in 'go' — do NOT harden plain г into the throaty ғ/gh. " +
    "Example pronunciations: Мадинага = 'ma-di-na-GA'; қилган = 'qil-GAN'; келган = 'kel-GAN'; " +
    "мавзуга = 'mav-zu-GA'; қараганда = 'qa-ra-GAN-da' (all plain g, never gh). " +
    "By contrast пайғамбар = 'pay-GHAM-bar' keeps the throaty ғ. " +
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
    // P103: `mascot` defaults to 'girl' — if the admin payload omits the field
    // (the P084 failure mode), reels fall back to the voices already shipped
    // rather than silently switching gender.
    const { text, lang = 'en', style = 'adults', mascot = 'girl',
            slug = '', section = '' } = await req.json()

    if (!text?.trim()) {
      return NextResponse.json({ error: 'text required' }, { status: 400 })
    }

    const cleanText = cleanForTTS(text, lang)
    const langKey = lang.replace('_cyrillic', '').replace('_latin', '')

    const apiKey = process.env.ELEVENLABS_API_KEY
    if (!apiKey) {
      return NextResponse.json({ error: 'ElevenLabs not configured' }, { status: 503 })
    }

    const voiceSet = VOICE_MAP[langKey] || VOICE_MAP.en
    const voiceId =
      style === 'kids'
        ? (mascot === 'boy' ? voiceSet.kids.boy : voiceSet.kids.girl)
        : voiceSet.adults

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
          model_id: 'eleven_v3',
          voice_settings: { stability: 0.5, similarity_boost: 0.75 },
        }),
      }
    )

    if (!elevenRes.ok) {
      return NextResponse.json({ error: 'TTS failed: ' + elevenRes.status }, { status: elevenRes.status })
    }

    const audioBuffer = await elevenRes.arrayBuffer()

    // P106: in dev, write the narration straight into the work tree so the
    // operator doesn't download → rename → move by hand. Vercel's filesystem is
    // read-only and ephemeral, so this is dev-only and never blocks the response.
    let savedPath = ''
    if (process.env.NODE_ENV !== 'production' && slug && section) {
      try {
        const dir = path.join(process.cwd(), 'out', 'work', style, slug, langKey)
        await mkdir(dir, { recursive: true })
        const filename = `${style}-${langKey}-${slug}-${section}.mp3`
        await writeFile(path.join(dir, filename), Buffer.from(audioBuffer))
        savedPath = path.join('out', 'work', style, slug, langKey, filename)
        console.log(`[tts] saved ${savedPath}`)
      } catch (e: any) {
        // Never fail the request over a disk write — the audio still streams back.
        console.error('[tts] disk write failed:', e?.message)
      }
    }

    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'no-store',
        ...(savedPath ? { 'X-Saved-Path': savedPath } : {}),
      },
    })

  } catch (error: any) {
    console.error('TTS route error:', error?.message)
    return NextResponse.json({ error: 'TTS failed: ' + (error?.message || 'unknown') }, { status: 500 })
  }
}