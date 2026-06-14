// scripts/lib/uzbek-translit.test.ts
// Run:  npx tsx --test scripts/lib/uzbek-translit.test.ts
// Dependency-free (Node built-in node:test + assert). Exits non-zero on failure.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  latinToCyrillic,
  cyrillicToLatin,
  detectScript,
  deriveBothScripts,
} from './uzbek-translit';

const L2C = (s: string) => latinToCyrillic(s).output;
const C2L = (s: string) => cyrillicToLatin(s).output;

// ---- Religious / corpus terms: Latin → Cyrillic ----
const latToCyr: [string, string][] = [
  ['Alloh', 'Аллоҳ'],
  ['Rasululloh', 'Расулуллоҳ'],
  ['Qurʼon', 'Қуръон'],
  ['Muhammad', 'Муҳаммад'],
  ['paygʻambar', 'пайғамбар'],
  ['roʻza', 'рўза'],
  ["qo'l", 'қўл'],          // ASCII apostrophe okina — regression: normalize before tokenize
  ["bo'lgan", 'бўлган'],    // ASCII apostrophe okina
  ['namoz', 'намоз'],
  ['hadis', 'ҳадис'],
  ['taqvo', 'тақво'],
  ['masjid', 'масжид'],
  ['shukr', 'шукр'],
  ['eshik', 'эшик'],     // word-initial e → э
  ['men', 'мен'],         // non-initial e → е
];

test('Latin → Cyrillic: corpus terms', () => {
  for (const [lat, cyr] of latToCyr) assert.equal(L2C(lat), cyr, `L2C("${lat}")`);
});

// ---- Religious / corpus terms: Cyrillic → Latin ----
const cyrToLat: [string, string][] = [
  ['Аллоҳ', 'Alloh'],
  ['Қуръон', 'Qurʼon'],
  ['рўза', 'roʻza'],
  ['пайғамбар', 'paygʻambar'],
  ['намоз', 'namoz'],
  ['ҳадис', 'hadis'],
  ['Муҳаммад', 'Muhammad'],
  ['тақво', 'taqvo'],
];

test('Cyrillic → Latin: corpus terms', () => {
  for (const [cyr, lat] of cyrToLat) assert.equal(C2L(cyr), lat, `C2L("${cyr}")`);
});

// ---- Round-trip stability (only unambiguous words) ----
test('round-trip Latin→Cyr→Latin is stable for unambiguous words', () => {
  for (const w of ['namoz', 'roʻza', 'paygʻambar', 'taqvo', 'shukr', 'masjid']) {
    assert.equal(C2L(L2C(w)), w, `round-trip "${w}"`);
  }
});

// ---- Script detection ----
test('detectScript', () => {
  assert.equal(detectScript('Alloh'), 'latin');
  assert.equal(detectScript('Аллоҳ'), 'cyrillic');
  assert.equal(detectScript('Alloh Аллоҳ'), 'mixed');
  assert.equal(detectScript('   '), 'empty');
});

// ---- deriveBothScripts: canonical = Cyrillic (D4) ----
test('deriveBothScripts keeps Cyrillic canonical', () => {
  const fromLatin = deriveBothScripts('namoz');
  assert.equal(fromLatin.sourceScript, 'latin');
  assert.equal(fromLatin.cyrillic, 'намоз'); // derived canonical
  assert.equal(fromLatin.latin, 'namoz');    // source preserved

  const fromCyr = deriveBothScripts('намоз');
  assert.equal(fromCyr.sourceScript, 'cyrillic');
  assert.equal(fromCyr.cyrillic, 'намоз');   // source is canonical
  assert.equal(fromCyr.latin, 'namoz');      // derived

  const mixed = deriveBothScripts('Alloh Аллоҳ');
  assert.equal(mixed.sourceScript, 'mixed');
  assert.ok(mixed.flags.length > 0);         // flagged, not auto-converted
});

// ---- Ambiguities are flagged, not silently guessed ----
test('ambiguous cases produce flags', () => {
  assert.ok(latinToCyrillic('eshik').flags.some((f) => f.includes("'e'→э")));
  assert.ok(!cyrillicToLatin('Эшик').flags.some((f) => f.includes('ye'))); // э is unambiguous → no ye flag
  assert.ok(cyrillicToLatin('ер').flags.some((f) => f.includes('ye'))); // word-initial е
});
