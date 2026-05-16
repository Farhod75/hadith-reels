// scripts/apply-tajik-translations.ts
// Reads out/tajik-translations.json (after human review) and writes text_tajik back to Supabase.
//
// Safety:
//   - Refuses to apply if any entry has status !== 'success' UNLESS --force is passed
//   - Refuses to apply empty text_tajik_proposed
//   - Dry-run by default; pass --apply to actually write
//
// Usage (from HR repo root):
//   npx tsx scripts/apply-tajik-translations.ts            # dry-run preview
//   npx tsx scripts/apply-tajik-translations.ts --apply    # actually write to DB

import { createClient } from '@supabase/supabase-js'
import * as fs from 'fs'
import * as path from 'path'
import * as dotenv from 'dotenv'

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') })

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('❌ Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.local')
  process.exit(1)
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

const APPLY = process.argv.includes('--apply')
const FORCE = process.argv.includes('--force')

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

async function main() {
  const jsonPath = path.resolve(process.cwd(), 'out', 'tajik-translations.json')

  if (!fs.existsSync(jsonPath)) {
    console.error(`❌ JSON file not found: ${jsonPath}`)
    console.error('   Run scripts/translate-tajik.ts first.')
    process.exit(1)
  }

  const raw = fs.readFileSync(jsonPath, 'utf-8')
  const entries: TranslationResult[] = JSON.parse(raw)

  console.log(`📁 Loaded ${entries.length} entries from ${jsonPath}`)
  console.log('')

  // Validation
  const errors: string[] = []
  const failedStatus = entries.filter(e => e.status !== 'success')
  const emptyTranslations = entries.filter(e => e.status === 'success' && !e.text_tajik_proposed?.trim())

  if (failedStatus.length > 0 && !FORCE) {
    errors.push(`${failedStatus.length} entries have status !== 'success' (use --force to skip them)`)
    failedStatus.slice(0, 5).forEach(e => {
      errors.push(`   • #${e.hadith_number}: ${e.error || 'unknown error'}`)
    })
  }

  if (emptyTranslations.length > 0) {
    errors.push(`${emptyTranslations.length} entries have empty text_tajik_proposed`)
    emptyTranslations.slice(0, 5).forEach(e => {
      errors.push(`   • #${e.hadith_number}`)
    })
  }

  if (errors.length > 0) {
    console.error('❌ Validation failed:')
    errors.forEach(err => console.error(`   ${err}`))
    if (!FORCE) {
      process.exit(1)
    }
    console.warn('⚠️  --force passed; proceeding anyway, will skip invalid entries')
  }

  // Build the writable set
  const writable = entries.filter(e =>
    e.status === 'success' && e.text_tajik_proposed?.trim()
  )

  console.log(`✅ ${writable.length} entries ready to write`)
  console.log(`🚫 ${entries.length - writable.length} entries skipped`)
  console.log('')

  if (!APPLY) {
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    console.log('DRY RUN — no DB writes performed')
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    console.log('')
    console.log('Preview of first 3 writes:')
    writable.slice(0, 3).forEach(e => {
      console.log(`  #${e.hadith_number} (${e.collection})`)
      console.log(`    → ${e.text_tajik_proposed.slice(0, 100)}${e.text_tajik_proposed.length > 100 ? '...' : ''}`)
    })
    console.log('')
    console.log('To actually write to Supabase, re-run with --apply:')
    console.log('   npx tsx scripts/apply-tajik-translations.ts --apply')
    return
  }

  // Real writes
  console.log('🚀 Writing to Supabase...')
  console.log('')

  let successCount = 0
  let failCount = 0

  for (let i = 0; i < writable.length; i++) {
    const e = writable[i]
    const num = `[${i + 1}/${writable.length}]`

    const { error } = await supabase
      .from('hadith_library')
      .update({ text_tajik: e.text_tajik_proposed })
      .eq('id', e.id)

    if (error) {
      console.log(`${num} ❌ #${e.hadith_number} — ${error.message}`)
      failCount++
    } else {
      console.log(`${num} ✅ #${e.hadith_number}`)
      successCount++
    }
  }

  console.log('')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log(`✅ Wrote:   ${successCount}`)
  console.log(`❌ Failed:  ${failCount}`)
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('')
  console.log('Verify in Supabase:')
  console.log('   SELECT hadith_number, LEFT(text_tajik, 60) AS tj_preview')
  console.log('   FROM hadith_library WHERE text_tajik IS NOT NULL LIMIT 10;')
}

main().catch(err => {
  console.error('💥 Fatal error:', err)
  process.exit(1)
})
