// scripts/audit-tags.ts
// Diffs the library's live `tags` vocabulary against lib/tags.ts (P182).
//
//   npx tsx scripts/audit-tags.ts                 # full report
//   npx tsx scripts/audit-tags.ts --quiet         # failures only, for a hook
//
// Exits 1 on a REAL gap — a tag the caption cannot localise. Exits 0 on the
// informational sections, which are housekeeping, not defects.
//
// P182: P150 mapped ~100 library tags onto 56 canonical concepts and nothing
// kept that current. The column reached ~150 values and 53 were falling
// through buildTags()'s fallback, each emitting only its English form and
// losing the localised half. Nothing logged it; «#maruf» shipped bare in the
// RU and TJ captions of Muslim #1005 and was caught by reading a screenshot.
// A mapping table that is not diffed against its data drifts silently.
//
// P096: .update() reports a zero-row match as success — the reason this script
// only READS. It reports; a human edits lib/tags.ts. Nothing here writes.

import { createClient } from '@supabase/supabase-js'
import * as path from 'path'
import * as dotenv from 'dotenv'
import { TAG_CANONICAL, TAG_FORMS } from '../lib/tags'

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') })

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
const key = process.env.SUPABASE_SERVICE_ROLE_KEY!
if (!url || !key) { console.error('missing supabase env'); process.exit(2) }

const quiet = process.argv.includes('--quiet')

// Tags filtered before they reach buildTags(), per the note in lib/tags.ts:
// #date reaches dating content and #hellfire skews to metal and gaming. They
// are listed here so they do not read as gaps forever — and listed EXPLICITLY,
// with a reason, rather than silently filtered, which is the failure P182
// documents. If the upstream blocklist moves or grows, this must follow it.
const BLOCKED_UPSTREAM: Record<string, string> = {
  date: 'P106 — reaches dating content',
  hellfire: 'P106 — skews to metal and gaming',
}

const LANGS = ['en', 'ru', 'uz', 'tj'] as const

const sb = createClient(url, key)

function section(title: string, lines: string[], hint?: string) {
  if (!lines.length) return
  console.log(`\n${title}  (${lines.length})`)
  console.log('-'.repeat(title.length + 8))
  lines.forEach(l => console.log(`  ${l}`))
  if (hint) console.log(`  → ${hint}`)
}

async function main() {
  const { data, error } = await sb
    .from('hadith_library')
    .select('id, collection, hadith_number, tags')

  if (error) { console.error(error.message); process.exit(2) }
  // Exit 2, never 0. An empty read is a gate that cannot see its data — wrong
  // env, RLS, wrong project — and a gate that cannot run must not report pass
  // (P093: a Playwright gate exited 0 having run zero tests). 1 means gaps
  // were found; 2 means the check did not happen.
  if (!data?.length) { console.error('no hadith_library rows — cannot audit'); process.exit(2) }

  // How often each raw tag is used, and where — the count is what says which
  // gaps to close first. A tag on one row is not the same problem as one on 20.
  const usage = new Map<string, string[]>()
  let untagged = 0

  for (const row of data as any[]) {
    const tags: string[] = Array.isArray(row.tags) ? row.tags : []
    if (!tags.length) { untagged++; continue }
    for (const raw of tags) {
      const t = String(raw).toLowerCase().trim()
      if (!t) continue
      const where = `${row.collection} #${row.hadith_number}`
      const seen = usage.get(t) ?? []
      if (seen.length < 3) seen.push(where)   // keep three examples, not all
      usage.set(t, seen)
    }
  }

  // Recount properly — the example list above is capped at three.
  const counts = new Map<string, number>()
  for (const row of data as any[]) {
    for (const raw of (Array.isArray(row.tags) ? row.tags : [])) {
      const t = String(raw).toLowerCase().trim()
      if (t) counts.set(t, (counts.get(t) ?? 0) + 1)
    }
  }

  const unmapped: string[] = []
  const blocked: string[] = []

  for (const [tag, examples] of [...usage.entries()].sort()) {
    if (TAG_CANONICAL[tag]) continue
    const n = counts.get(tag) ?? 0
    if (BLOCKED_UPSTREAM[tag]) {
      blocked.push(`${tag.padEnd(20)} ${String(n).padStart(3)} rows   ${BLOCKED_UPSTREAM[tag]}`)
    } else {
      unmapped.push(`${tag.padEnd(20)} ${String(n).padStart(3)} rows   e.g. ${examples.join(', ')}`)
    }
  }

  // A raw tag mapping to a concept that carries no forms is worse than an
  // unmapped tag: buildTags() finds no forms and falls through to the raw
  // English exactly as if the mapping did not exist, so the entry reads as
  // done while behaving as missing.
  const dangling: string[] = []
  for (const [raw, canon] of Object.entries(TAG_CANONICAL)) {
    if (!TAG_FORMS[canon]) dangling.push(`${raw.padEnd(20)} -> ${canon}  (no TAG_FORMS entry)`)
  }

  // A blank form is a silent single-tag emission for that language only, which
  // is invisible unless someone reads a caption in that language.
  const incomplete: string[] = []
  for (const [canon, forms] of Object.entries(TAG_FORMS)) {
    const missing = LANGS.filter(l => !(forms as any)[l] || !String((forms as any)[l]).trim())
    if (missing.length) incomplete.push(`${canon.padEnd(16)} missing: ${missing.join(', ')}`)
  }

  // Housekeeping, not defects.
  const reachable = new Set(Object.values(TAG_CANONICAL))
  const unreachable = Object.keys(TAG_FORMS).filter(k => !reachable.has(k)).sort()
  const unusedMappings = Object.keys(TAG_CANONICAL).filter(t => !counts.has(t)).sort()

  const failures = unmapped.length + dangling.length + incomplete.length

  if (!quiet) {
    console.log(`hadith_library: ${data.length} rows, ${counts.size} distinct tags, ` +
                `${Object.keys(TAG_CANONICAL).length} raw mappings -> ${Object.keys(TAG_FORMS).length} concepts`)
    if (untagged) console.log(`${untagged} row(s) carry NO tags — see P181 (--tags on promote)`)
  }

  section('UNMAPPED — emits English only, loses the localised tag', unmapped,
          'add to TAG_CANONICAL; if the concept is new it also needs four forms in TAG_FORMS')
  section('DANGLING — mapped to a concept with no forms', dangling,
          'behaves exactly like unmapped, but reads as done')
  section('INCOMPLETE — concept missing a language form', incomplete,
          'that language emits one tag instead of two')

  if (!quiet) {
    section('unreachable concepts — no raw tag maps here', unreachable,
            'harmless; either dead vocabulary or a missing alias')
    section('mappings with no library row using them', unusedMappings,
            'harmless; kept for tags that may appear later')
  }

  console.log(failures === 0
    ? '\nOK — every library tag resolves to four forms.'
    : `\nFAILED — ${failures} gap(s). Captions are shipping with half their reach.`)

  process.exit(failures === 0 ? 0 : 1)
}

main()
