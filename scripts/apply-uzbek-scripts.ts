// scripts/apply-uzbek-scripts.ts
// ============================================================
// Uzbek two-script backfill — APPLY step.
// Reads the REVIEWED out/uzbek-scripts.json and writes to hadith_library:
//   • text_uzbek_cyrillic  ← canonical (D4)
//   • text_uzbek_latin     ← derived
//   • text_uzbek           ← corrected, ONLY for the 9 cleaned mixed rows
//                            (de-corrupts the shared source; HV benefits too)
//
// GATED: aborts unless the migration columns exist (run
//        20260614_add_uzbek_script_columns.sql after HV sign-off first).
//
// Dry-run (default):  npx tsx scripts/apply-uzbek-scripts.ts
// Real write:         npx tsx scripts/apply-uzbek-scripts.ts --apply
// ============================================================
import { config } from 'dotenv';
import { createClient } from '@supabase/supabase-js';
import { readFileSync } from 'node:fs';

config({ path: '.env.local' });

const APPLY = process.argv.includes('--apply');
const JSON_PATH = 'out/uzbek-scripts.json';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
if (!url || !key) {
  console.error('❌ Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.local');
  process.exit(1);
}
const supabase = createClient(url, key);

interface Proposal {
  id: string;
  hadith_number: string | null;
  source_script: string;
  text_uzbek_cyrillic_proposed: string;
  text_uzbek_latin_proposed: string;
  status: 'ok' | 'needs_attention';
  cleaned_from_mixed?: boolean;
  corrected_text_uzbek?: string;
}

async function preflightColumnsExist(): Promise<boolean> {
  // Cheap existence probe: select the two new columns. PostgREST errors if missing.
  const { error } = await supabase
    .from('hadith_library')
    .select('text_uzbek_cyrillic, text_uzbek_latin')
    .limit(1);
  if (error) {
    console.error('❌ Target columns not found — migration has not run.');
    console.error(`   (${error.message})`);
    console.error('   Run supabase/migrations/20260614_add_uzbek_script_columns.sql after HV sign-off, then retry.');
    return false;
  }
  return true;
}

async function main() {
  console.log(APPLY ? '⚠️  APPLY MODE — will write to hadith_library' : '🧪 DRY RUN — no DB writes');

  if (!(await preflightColumnsExist())) process.exit(1);

  let proposals: Proposal[];
  try {
    proposals = JSON.parse(readFileSync(JSON_PATH, 'utf8')) as Proposal[];
  } catch {
    console.error(`❌ Could not read ${JSON_PATH}. Run scripts/backfill-uzbek-scripts.ts first.`);
    process.exit(1);
  }

  const valid = proposals.filter(
    (p) => p.text_uzbek_cyrillic_proposed?.trim() && p.text_uzbek_latin_proposed?.trim(),
  );
  const skipped = proposals.length - valid.length;
  const sourceFixes = valid.filter((p) => p.cleaned_from_mixed && p.corrected_text_uzbek?.trim());

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`📦 Proposals: ${proposals.length}  ·  writable: ${valid.length}  ·  skipped (empty): ${skipped}`);
  console.log(`🧹 Of those, source text_uzbek corrected (mixed rows): ${sourceFixes.length}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  console.log('\nFirst 3 writes preview:');
  for (const p of valid.slice(0, 3)) {
    console.log(`  #${p.hadith_number}`);
    console.log(`    cyr:   ${p.text_uzbek_cyrillic_proposed.slice(0, 60)}`);
    console.log(`    latin: ${p.text_uzbek_latin_proposed.slice(0, 60)}`);
    if (p.cleaned_from_mixed) console.log(`    + correcting source text_uzbek`);
  }

  if (!APPLY) {
    console.log('\n🧪 Dry run complete. If correct, re-run with --apply.');
    return;
  }

  let ok = 0;
  let fail = 0;
  for (const p of valid) {
    const update: Record<string, string> = {
      text_uzbek_cyrillic: p.text_uzbek_cyrillic_proposed,
      text_uzbek_latin: p.text_uzbek_latin_proposed,
    };
    if (p.cleaned_from_mixed && p.corrected_text_uzbek?.trim()) {
      update.text_uzbek = p.corrected_text_uzbek;
    }
    const { error } = await supabase.from('hadith_library').update(update).eq('id', p.id);
    if (error) {
      fail += 1;
      console.error(`  ✗ #${p.hadith_number} (${p.id}): ${error.message}`);
    } else {
      ok += 1;
      console.log(`  ✓ #${p.hadith_number}${p.cleaned_from_mixed ? ' (+source fix)' : ''}`);
    }
  }

  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`✅ Wrote ${ok}  ·  ❌ failed ${fail}  ·  skipped ${skipped}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  if (fail === 0) {
    console.log('Verify in Supabase:');
    console.log("  SELECT count(text_uzbek_cyrillic) AS cyr, count(text_uzbek_latin) AS lat FROM hadith_library;  -- expect 74 / 74");
  }
}

main().catch((e) => { console.error('❌ Unexpected:', e); process.exit(1); });
