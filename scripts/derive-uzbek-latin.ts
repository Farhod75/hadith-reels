// scripts/derive-uzbek-latin.ts
// Fills text_uzbek_latin from the canonical text_uzbek_cyrillic (D4).
// Derived, never translated — see uzbek-translit.ts for okina vs tutuq.
//
//   npx tsx scripts/derive-uzbek-latin.ts                          # dry run, candidates
//   npx tsx scripts/derive-uzbek-latin.ts --commit                 # write candidates
//   npx tsx scripts/derive-uzbek-latin.ts --library                # dry run, library
//   npx tsx scripts/derive-uzbek-latin.ts --library --number 5971  # one library row
//   npx tsx scripts/derive-uzbek-latin.ts --library --number 5971 --commit
//
// P160: --library added for rows re-translated after a matn correction, where
// the new translation writes Cyrillic only and leaves Latin and the legacy
// column NULL. Same gap P151 fixed in translate-candidates.py.

import { createClient } from '@supabase/supabase-js'
import * as path from 'path'
import * as dotenv from 'dotenv'
import { deriveBothScripts } from './lib/uzbek-translit'

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') })

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
const key = process.env.SUPABASE_SERVICE_ROLE_KEY!
if (!url || !key) { console.error('missing supabase env'); process.exit(1) }

const commit  = process.argv.includes('--commit')
const library = process.argv.includes('--library')

const numIdx = process.argv.indexOf('--number')
const number = numIdx !== -1 ? process.argv[numIdx + 1] : null
if (numIdx !== -1 && !number) { console.error('--number needs a value'); process.exit(1) }
if (number && !library) { console.error('--number only applies with --library'); process.exit(1) }

const table  = library ? 'hadith_library' : 'hadith_candidates'
const keyCol = library ? 'id' : 'candidate_id'

const sb = createClient(url, key)

async function main() {
  let q = sb
    .from(table)
    .select(`${keyCol}, collection, hadith_number, text_uzbek_cyrillic, text_uzbek_latin`)
    .not('text_uzbek_cyrillic', 'is', null)

  // P147: hadith_number is not unique, so this can legitimately match >1 row.
  if (number) q = q.eq('hadith_number', number)

  const { data, error } = await q

  if (error) { console.error(error.message); process.exit(1) }
  if (!data?.length) { console.log(`no ${table} rows with Uzbek Cyrillic${number ? ` for #${number}` : ''}`); return }

  console.log(commit ? '[COMMIT]' : '[DRY RUN]', `table: ${table}`, `rows: ${data.length}`)

  for (const row of data as any[]) {
    const r = deriveBothScripts(row.text_uzbek_cyrillic!)
    console.log(`\n${row.collection} #${row.hadith_number}`)
    console.log(`  cyr:   ${r.cyrillic}`)
    console.log(`  latin: ${r.latin}`)
    if ((r as any).flags?.length) console.log(`  FLAGS: ${JSON.stringify((r as any).flags)}`)

    if (commit) {
      // P097: the legacy text_uzbek column takes LATIN, not Cyrillic --
      // matches all 74 rows backfilled in August.
      // hadith_library has no updated_at column; hadith_candidates does.
      const patch: Record<string, any> = { text_uzbek_latin: r.latin }
      if (library) patch.text_uzbek = r.latin
      else patch.updated_at = new Date().toISOString()

      // P096: .update() alone reports a zero-row match as success.
      const { data: written, error: e } = await sb
        .from(table)
        .update(patch)
        .eq(keyCol, row[keyCol])
        .select(keyCol)

      if (e) console.log(`  WRITE FAILED: ${e.message}`)
      else if (!written?.length) console.log(`  WRITE MATCHED 0 ROWS (${keyCol}=${row[keyCol]})`)
      else console.log('  -> written')
    }
  }

  if (!commit) console.log('\nDRY RUN — nothing written. Read the Latin, then --commit.')
}

main()