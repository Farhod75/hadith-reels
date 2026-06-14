// scripts/backfill-uzbek-scripts.ts
// ============================================================
// Uzbek two-script backfill — GENERATE step (READ-ONLY, no DB writes).
// Reads hadith_library.text_uzbek (live: 61 Latin / 13 Cyrillic),
// derives BOTH scripts with Cyrillic canonical (D4), and writes a
// review checkpoint to out/uzbek-scripts.json.
//
// Mirrors the tj-translation-process.md pattern:
//   generate (this file) → human review JSON → dry-run apply → apply.
// The apply step is a SEPARATE script, run only AFTER the migration
// adds text_uzbek_cyrillic / text_uzbek_latin and the human reviews.
//
// Run:  npx tsx scripts/backfill-uzbek-scripts.ts
// ============================================================
import { config } from 'dotenv';
import { createClient } from '@supabase/supabase-js';
import { mkdirSync, writeFileSync } from 'node:fs';
import { deriveBothScripts, cyrillicToLatin } from './lib/uzbek-translit';

config({ path: '.env.local' });

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
if (!url || !key) {
  console.error('❌ Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.local');
  process.exit(1);
}
const supabase = createClient(url, key);

interface Row {
  id: string;
  hadith_number: string | null;
  collection: string | null;
  text_uzbek: string | null;
}

interface Proposal {
  id: string;
  hadith_number: string | null;
  collection: string | null;
  source_script: string;
  text_uzbek_original: string;
  text_uzbek_cyrillic_proposed: string; // canonical (D4)
  text_uzbek_latin_proposed: string;    // derived (or source if Latin)
  flags: string[];
  status: 'ok' | 'needs_attention';
  cleaned_from_mixed?: boolean;
  corrected_text_uzbek?: string; // mixed rows only: clean pure-Latin to write back to source text_uzbek
}

async function main() {
  console.log('📖 Reading hadith_library (read-only)...');
  const { data, error } = await supabase
    .from('hadith_library')
    .select('id, hadith_number, collection, text_uzbek')
    .order('hadith_number', { ascending: true });

  if (error) { console.error('❌ Supabase read error:', error.message); process.exit(1); }
  const rows = (data ?? []) as Row[];
  if (rows.length === 0) { console.error('❌ No rows returned.'); process.exit(1); }

  const proposals: Proposal[] = [];
  const byScript: Record<string, number> = {};
  let needsAttention = 0;
  let totalFlags = 0;

  for (const r of rows) {
    const original = r.text_uzbek ?? '';
    let d = deriveBothScripts(original);
    const origScript = d.sourceScript;
    let cleanedFromMixed = false;
    let correctedSource: string | undefined;

    // Stray look-alike Cyrillic in an otherwise-Latin string: convert ONLY the
    // Cyrillic chars → clean pure-Latin, then derive both scripts normally.
    if (origScript === 'mixed') {
      correctedSource = cyrillicToLatin(original).output;
      cleanedFromMixed = true;
      d = deriveBothScripts(correctedSource);
      d.flags.unshift('auto-cleaned from mixed-script source — VERIFY before apply');
    }

    byScript[origScript] = (byScript[origScript] ?? 0) + 1;
    totalFlags += d.flags.length;
    const status: Proposal['status'] =
      origScript === 'mixed' || origScript === 'empty' || d.flags.length > 0
        ? 'needs_attention'
        : 'ok';
    if (status === 'needs_attention') needsAttention += 1;

    proposals.push({
      id: r.id,
      hadith_number: r.hadith_number,
      collection: r.collection,
      source_script: origScript,
      text_uzbek_original: original,
      text_uzbek_cyrillic_proposed: d.cyrillic,
      text_uzbek_latin_proposed: d.latin,
      flags: d.flags,
      status,
      ...(cleanedFromMixed ? { cleaned_from_mixed: true, corrected_text_uzbek: correctedSource } : {}),
    });
  }

  mkdirSync('out', { recursive: true });
  const outPath = 'out/uzbek-scripts.json';
  writeFileSync(outPath, JSON.stringify(proposals, null, 2), 'utf8');

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`✅ Wrote ${proposals.length} proposals → ${outPath}  (NO DB writes)`);
  console.log(`📊 By source script: ${JSON.stringify(byScript)}`);
  console.log(`🔎 Needs attention:  ${needsAttention}  ·  total flags: ${totalFlags}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  const mixed = proposals.filter((p) => p.cleaned_from_mixed);
  if (mixed.length) {
    console.log(`\n🧹 Mixed rows auto-cleaned to Latin (${mixed.length}) — VERIFY each:`);
    for (const p of mixed) {
      console.log(`  #${p.hadith_number}`);
      console.log(`    was:  ${p.text_uzbek_original}`);
      console.log(`    now:  ${p.corrected_text_uzbek}`);
    }
  }
  const eOnly = proposals.filter((p) => !p.cleaned_from_mixed && p.flags.length).length;
  console.log(`\nℹ ${eOnly} more rows carry only word-initial e→э flags (normally correct).`);
  console.log('\nNext: open out/uzbek-scripts.json, verify the cleaned rows + spot-check e→э,');
  console.log('edit any *_proposed / corrected_text_uzbek field in place. Apply uses the JSON.');
}

main().catch((e) => { console.error('❌ Unexpected:', e); process.exit(1); });
