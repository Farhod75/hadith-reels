// scripts/derive-uzbek-latin.ts
// Fills text_uzbek_latin from the canonical text_uzbek_cyrillic (D4).
// Derived, never translated — see uzbek-translit.ts for okina vs tutuq.
//
//   npx tsx scripts/derive-uzbek-latin.ts            # dry run
//   npx tsx scripts/derive-uzbek-latin.ts --commit

import { createClient } from '@supabase/supabase-js'
import * as path from 'path'
import * as dotenv from 'dotenv'
import { deriveBothScripts } from './lib/uzbek-translit'

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') })

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
const key = process.env.SUPABASE_SERVICE_ROLE_KEY!
if (!url || !key) { console.error('missing supabase env'); process.exit(1) }

const commit = process.argv.includes('--commit')
const sb = createClient(url, key)

async function main() {
  const { data, error } = await sb
    .from('hadith_candidates')
    .select('candidate_id, collection, hadith_number, text_uzbek_cyrillic, text_uzbek_latin')
    .not('text_uzbek_cyrillic', 'is', null)

  if (error) { console.error(error.message); process.exit(1) }
  if (!data?.length) { console.log('no candidates with Uzbek Cyrillic'); return }

  console.log(commit ? '[COMMIT]' : '[DRY RUN]')

  for (const row of data) {
    const r = deriveBothScripts(row.text_uzbek_cyrillic!)
    console.log(`\n${row.collection} #${row.hadith_number}`)
    console.log(`  cyr:   ${r.cyrillic}`)
    console.log(`  latin: ${r.latin}`)
    if ((r as any).flags?.length) console.log(`  FLAGS: ${JSON.stringify((r as any).flags)}`)

    if (commit) {
      const { error: e } = await sb
        .from('hadith_candidates')
        .update({ text_uzbek_latin: r.latin, updated_at: new Date().toISOString() })
        .eq('candidate_id', row.candidate_id)
      console.log(e ? `  WRITE FAILED: ${e.message}` : '  -> written')
    }
  }

  if (!commit) console.log('\nDRY RUN — nothing written. Read the Latin, then --commit.')
}

main()