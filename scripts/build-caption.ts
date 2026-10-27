// scripts/build-caption.ts
// Build a reel's captions WITHOUT the admin, from the library row plus the two
// generated blocks supplied as JSON.
//
//   npx tsx scripts/build-caption.ts --blocks out/caption-6570.json
//   npx tsx scripts/build-caption.ts --blocks out/caption-6570.json --stdout
//
// WHY (P305, and P246 is what forced it). The caption body used to exist only
// inside app/admin/page.tsx, so the admin was the only way to produce one. When
// #6570's generated blocks were lost with draft.txt, rebuilding its captions
// meant either re-generating the blocks — P245 re-attributed the moral in 7 of
// 8 generations — or hand-assembling four captions and hoping the guillemet
// rules were applied the same way the admin applies them. Neither is a method.
//
// The body itself now lives in lib/caption.ts and is IMPORTED here, never
// restated: this script and the admin produce byte-identical bodies because
// they call the same function. The tag line is fitted with the same
// fitTagLine() the admin uses, against the same TELEGRAM_CAPTION_LIMIT.
//
// INPUT JSON
//   {
//     "hadith_number": "6570",
//     "id": "<uuid>",            // optional; required if the number is not unique
//     "style": "adults",         // adults | kids — kids adds the #kids tag
//     "langs": {
//       "en": { "title": "...", "moral": "..." },
//       "ru": { "title": "...", "moral": "..." }
//     }
//   }
//
// Read-only against the database. Writes only out/caption-<num>-<lang>.txt.

import { createClient } from '@supabase/supabase-js'
import * as path from 'path'
import * as fs from 'fs'
import * as dotenv from 'dotenv'
import { fitTagLine, TAG_BLOCKLIST, TELEGRAM_CAPTION_LIMIT } from '../lib/tags'
import { buildCaptionBody, CAPTION_L10N } from '../lib/caption'

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') })

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
const key = process.env.SUPABASE_SERVICE_ROLE_KEY!
if (!url || !key) { console.error('missing supabase env'); process.exit(2) }

function arg(name: string): string | undefined {
  const i = process.argv.indexOf(name)
  return i >= 0 ? process.argv[i + 1] : undefined
}

const blocksPath = arg('--blocks')
const toStdout = process.argv.includes('--stdout')
if (!blocksPath) {
  console.error('usage: npx tsx scripts/build-caption.ts --blocks <file.json> [--stdout]')
  process.exit(2)
}

interface BlocksFile {
  hadith_number?: string | number
  id?: string
  style?: 'adults' | 'kids'
  langs: Record<string, { title: string; moral: string }>
}

const spec: BlocksFile = JSON.parse(fs.readFileSync(blocksPath, 'utf8'))
if (!spec.langs || !Object.keys(spec.langs).length) {
  console.error(`${blocksPath}: no "langs" object`); process.exit(2)
}
const style = spec.style || 'adults'

const sb = createClient(url, key)

async function main() {
  // P147 / P290: hadith_number is NOT unique. Select on it, then refuse to
  // guess — an `id` in the spec file settles it.
  // No text_display in the select: it is NOT a column. /api/reels computes it
  // per language from these same text_* columns (P108), so this script reads
  // the columns and picks per language below — the same resolution the admin
  // receives already done.
  let q = sb.from('hadith_library').select(
    'id, collection, hadith_number, narrator, tags, text_english, ' +
    'text_arabic, text_russian, text_uzbek_cyrillic, text_tajik, translation_source')
  if (spec.id) q = q.eq('id', spec.id)
  else if (spec.hadith_number != null) q = q.eq('hadith_number', String(spec.hadith_number))
  else { console.error('spec needs "id" or "hadith_number"'); process.exit(2) }

  const { data, error } = await q
  if (error) { console.error(error.message); process.exit(2) }
  // Exit 2, never 0, on an empty read — same rule as audit-tags.ts: a tool that
  // could not see its data must not report success (P093).
  if (!data?.length) { console.error('no matching hadith_library row'); process.exit(2) }
  if (data.length > 1) {
    console.error(`hadith_number ${spec.hadith_number} matches ${data.length} rows ` +
                  `(P147) — put one of these uuids in the spec as "id":`)
    data.forEach((r: any) => console.error(`  ${r.id}  ${r.collection} #${r.hadith_number}`))
    process.exit(2)
  }
  const row: any = data[0]

  // The matn column per language. text_display is the admin's override and
  // applies to whatever language it was written for, so it is only honoured
  // for `en` here — the same place the admin reads it.
  const MATN: Record<string, string> = {
    en: row.text_display || row.text_english,
    ru: row.text_russian,
    uz: row.text_uzbek_cyrillic,
    tj: row.text_tajik,
  }

  const outDir = path.resolve(process.cwd(), 'out')
  fs.mkdirSync(outDir, { recursive: true })

  let failed = 0
  for (const lang of Object.keys(spec.langs)) {
    const blocks = spec.langs[lang]
    const matn = MATN[lang]
    if (!matn) { console.error(`${lang}: no matn column for this language`); failed++; continue }
    if (!blocks.title || !blocks.moral) {
      console.error(`${lang}: spec is missing title or moral`); failed++; continue
    }

    const body = buildCaptionBody({
      // text_english carries the per-language matn so buildCaptionBody quotes
      // the right one; text_display is left unset so it cannot win over it.
      row: {
        text_english: matn,
        text_arabic: row.text_arabic,
        collection: row.collection,
        hadith_number: row.hadith_number,
        narrator: row.narrator,
        translation_source: row.translation_source,
      },
      blocks,
      lang,
    })

    const l10n = CAPTION_L10N[lang] || CAPTION_L10N.en
    const topicTags = (row.tags || []).filter(
      (t: string) => !TAG_BLOCKLIST.includes(t.toLowerCase()))

    // P184: UZ and TJ clear Telegram's 1024 on nearly every set. fitTagLine
    // drops the English hashtags first, then the language tag, then topic
    // concepts — and reports what it gave up.
    const fitted = fitTagLine({
      rawTags: topicTags,
      lang,
      suffix: `${l10n.tags}${style === 'kids' ? ' ' + l10n.kids : ''}`,
      langTag: l10n.lang,
      budget: TELEGRAM_CAPTION_LIMIT - body.length,
    })

    const caption = body + fitted.line
    const file = path.join(outDir, `caption-${row.hadith_number}-${lang}.txt`)
    // P186: no BOM, and read the file back rather than trusting the write.
    fs.writeFileSync(file, caption, { encoding: 'utf8' })
    const back = fs.readFileSync(file, 'utf8')
    const ok = back === caption

    const over = caption.length > TELEGRAM_CAPTION_LIMIT
    console.log(
      `${lang}  ${String(caption.length).padStart(4)} chars` +
      `${over ? '  OVER TELEGRAM 1024' : ''}` +
      `  read-back=${ok ? 'ok' : 'MISMATCH'}  ${file}`)
    if (fitted.note) console.log(`      tag line: ${fitted.note}`)
    if (!ok) failed++
    if (toStdout) console.log('\n' + caption + '\n' + '-'.repeat(60))
  }

  process.exit(failed ? 1 : 0)
}

main()
