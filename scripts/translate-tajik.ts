// scripts/translate-tajik.ts
// Reads all hadiths from Supabase, translates text_uzbek -> Tajik via Claude API,
// saves results to a JSON file for human review BEFORE any DB update.
//
// Usage (from HR repo root):
//   npx tsx scripts/translate-tajik.ts
//
// Requires in .env.local:
//   NEXT_PUBLIC_SUPABASE_URL
//   SUPABASE_SERVICE_ROLE_KEY
//   ANTHROPIC_API_KEY
//
// Output:
//   out/tajik-translations.json
//
// Review the JSON. When happy, run scripts/apply-tajik-translations.ts to write to DB.

import { createClient } from '@supabase/supabase-js'
import Anthropic from '@anthropic-ai/sdk'
import * as fs from 'fs'
import * as path from 'path'
import * as dotenv from 'dotenv'

// Load .env.local
dotenv.config({ path: path.resolve(process.cwd(), '.env.local') })

// ── Config ────────────────────────────────────────────────────────────────
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY
const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('❌ Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.local')
  process.exit(1)
}
if (!ANTHROPIC_KEY) {
  console.error('❌ Missing ANTHROPIC_API_KEY in .env.local')
  process.exit(1)
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)
const claude = new Anthropic({ apiKey: ANTHROPIC_KEY })

// ── Translation prompt ────────────────────────────────────────────────────
const SYSTEM_PROMPT = `You are an expert translator of classical Islamic hadith content. You translate from Uzbek Cyrillic to Tajik Cyrillic.

Rules:
- Preserve religious phrases exactly: Аллоҳ, Расулуллоҳ, Пайғамбар, ﷺ, etc.
- Tajik uses ҷ (not ж), ӣ (long i), ӯ (long u), ҳ, қ, ғ — use them properly per Tajik convention.
- Tajik has Persian-derived word forms; do NOT just transliterate Uzbek letters. Use proper Tajik vocabulary.
- Match register: hadith translations are formal and reverent, not colloquial.
- Output ONLY the Tajik translation. No explanation, no preamble, no quotes around the output.
- If the input contains a name or place that is the same in Tajik (e.g. Абу Ҳурайра, Мадина), keep it as-is in Tajik Cyrillic.`

// ── Types ─────────────────────────────────────────────────────────────────
interface HadithRow {
  id: string
  hadith_number: string
  collection: string
  text_english: string
  text_uzbek: string
  text_russian: string
  text_tajik: string | null
}

interface TranslationResult {
  id: string
  hadith_number: string
  collection: string
  text_english_preview: string
  text_uzbek: string
  text_tajik_proposed: string
  status: 'success' | 'error'
  error?: string
}

// ── Main ──────────────────────────────────────────────────────────────────
async function translateOne(uzbekText: string): Promise<string> {
  const response = await claude.messages.create({
    model: 'claude-sonnet-4-5',
    max_tokens: 1500,
    system: SYSTEM_PROMPT,
    messages: [
      {
        role: 'user',
        content: `Translate this Uzbek Cyrillic hadith text to Tajik Cyrillic:\n\n${uzbekText}`,
      },
    ],
  })

  const block = response.content[0]
  if (block.type !== 'text') {
    throw new Error('Unexpected non-text response block')
  }
  return block.text.trim()
}

async function main() {
  console.log('📖 Fetching hadiths from Supabase...')

  const { data: hadiths, error } = await supabase
    .from('hadith_library')
    .select('id, hadith_number, collection, text_english, text_uzbek, text_russian, text_tajik')
    .order('created_at', { ascending: true })

  if (error) {
    console.error('❌ Supabase query failed:', error.message)
    process.exit(1)
  }
  if (!hadiths || hadiths.length === 0) {
    console.error('❌ No hadiths returned from Supabase')
    process.exit(1)
  }

  console.log(`✅ Fetched ${hadiths.length} hadiths`)
  console.log('🌐 Translating each text_uzbek -> Tajik via Claude Sonnet 4.5...')
  console.log('   (estimated ~30 sec per hadith, ~30 min total for 60 hadiths)')
  console.log('')

  const results: TranslationResult[] = []
  let successCount = 0
  let errorCount = 0

  for (let i = 0; i < hadiths.length; i++) {
    const h = hadiths[i] as HadithRow
    const num = `[${i + 1}/${hadiths.length}]`

    if (!h.text_uzbek?.trim()) {
      console.log(`${num} ⚠️  #${h.hadith_number} — empty text_uzbek, skipping`)
      results.push({
        id: h.id,
        hadith_number: h.hadith_number,
        collection: h.collection,
        text_english_preview: (h.text_english || '').slice(0, 60),
        text_uzbek: '',
        text_tajik_proposed: '',
        status: 'error',
        error: 'empty text_uzbek',
      })
      errorCount++
      continue
    }

    try {
      const tajik = await translateOne(h.text_uzbek)
      console.log(`${num} ✅ #${h.hadith_number} (${h.collection})`)
      console.log(`     UZ: ${h.text_uzbek.slice(0, 80)}${h.text_uzbek.length > 80 ? '...' : ''}`)
      console.log(`     TJ: ${tajik.slice(0, 80)}${tajik.length > 80 ? '...' : ''}`)
      console.log('')

      results.push({
        id: h.id,
        hadith_number: h.hadith_number,
        collection: h.collection,
        text_english_preview: (h.text_english || '').slice(0, 60),
        text_uzbek: h.text_uzbek,
        text_tajik_proposed: tajik,
        status: 'success',
      })
      successCount++

      // Polite rate-limit pacing: 1 sec between calls
      await new Promise(resolve => setTimeout(resolve, 1000))

    } catch (err: any) {
      console.log(`${num} ❌ #${h.hadith_number} — ${err.message}`)
      results.push({
        id: h.id,
        hadith_number: h.hadith_number,
        collection: h.collection,
        text_english_preview: (h.text_english || '').slice(0, 60),
        text_uzbek: h.text_uzbek,
        text_tajik_proposed: '',
        status: 'error',
        error: err.message,
      })
      errorCount++
    }
  }

  // Write results to JSON
  const outDir = path.resolve(process.cwd(), 'out')
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true })
  }
  const outPath = path.join(outDir, 'tajik-translations.json')
  fs.writeFileSync(outPath, JSON.stringify(results, null, 2), 'utf-8')

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log(`✅ Success: ${successCount}`)
  console.log(`❌ Errors:  ${errorCount}`)
  console.log(`📁 Output:  ${outPath}`)
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('')
  console.log('Next steps:')
  console.log('1. Open out/tajik-translations.json — review every text_tajik_proposed')
  console.log('2. Edit any translations that need correction directly in the JSON')
  console.log('3. When happy, run: npx tsx scripts/apply-tajik-translations.ts')
}

main().catch(err => {
  console.error('💥 Fatal error:', err)
  process.exit(1)
})
