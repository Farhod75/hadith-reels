// scripts/lib/uzbek-translit.ts
// ============================================================
// Curated Uzbek Latin <-> Cyrillic transliterator.
// Deterministic rule map (NOT an LLM) — keeps the two-script feature
// reviewable and reproducible. [sourcing-pipeline-design.md §7, D4]
//
// IMPORTANT: this is ~95%+ correct, not a perfect 1:1 bijection.
// A few cases are genuinely ambiguous (e/э, Cyrillic е→e/ye, loanword
// ц/ы, ng boundary, ъ/ь). Those are NOT guessed silently — they are
// returned as `flags` so the human review gate can spot-check (G1/G4).
// ============================================================

export type Script = 'latin' | 'cyrillic' | 'mixed' | 'empty';

export interface TranslitResult {
  output: string;
  flags: string[]; // human-readable notes for ambiguous decisions
}

// All apostrophe-like glyphs users actually type, folded to one sentinel.
const APOS = /[\u02BB\u02BC\u2018\u2019\u0027\u0060\u00B4]/g;
const S = '\u02BC'; // internal sentinel for any apostrophe
const OKINA = '\u02BB'; // ʻ — official okina, used in oʻ / gʻ output
const TUTUQ = '\u02BC'; // ʼ — tutuq belgisi, used for ъ output

const LAT_VOWELS = new Set(['a', 'e', 'i', 'o', 'u']);
const CYR_VOWELS = new Set(['а', 'е', 'ё', 'и', 'о', 'у', 'ў', 'э', 'ю', 'я', 'ы']);

// Latin → Cyrillic, longest-match-first. (e and y handled separately.)
const LAT_RULES: [string, string][] = [
  ['o' + S, 'ў'], ['g' + S, 'ғ'],
  ['sh', 'ш'], ['ch', 'ч'], ['ts', 'ц'],
  ['yo', 'ё'], ['yu', 'ю'], ['ya', 'я'], ['ye', 'е'], ['yi', 'йи'],
  ['a', 'а'], ['b', 'б'], ['d', 'д'], ['f', 'ф'], ['g', 'г'], ['h', 'ҳ'],
  ['i', 'и'], ['j', 'ж'], ['k', 'к'], ['l', 'л'], ['m', 'м'], ['n', 'н'],
  ['o', 'о'], ['p', 'п'], ['q', 'қ'], ['r', 'р'], ['s', 'с'], ['t', 'т'],
  ['u', 'у'], ['v', 'в'], ['x', 'х'], ['y', 'й'], ['z', 'з'], ['c', 'к'],
  [S, 'ъ'],
];

// Cyrillic → Latin (single chars; е handled separately for ye/e).
const CYR_MAP: Record<string, string> = {
  а: 'a', б: 'b', в: 'v', г: 'g', ғ: 'g' + OKINA, д: 'd', ё: 'yo', ж: 'j',
  з: 'z', и: 'i', й: 'y', к: 'k', қ: 'q', л: 'l', м: 'm', н: 'n', о: 'o',
  ў: 'o' + OKINA, п: 'p', р: 'r', с: 's', т: 't', у: 'u', ф: 'f', х: 'x',
  ҳ: 'h', ц: 'ts', ч: 'ch', ш: 'sh', ъ: TUTUQ, ь: '', э: 'e', ю: 'yu',
  я: 'ya', ы: 'i',
};

const isWordToken = (t: string) => /[\p{L}\u02BC]/u.test(t);
const tokenize = (s: string) => s.match(/[\p{L}\u02BC]+|[^\p{L}\u02BC]+/gu) ?? [];

type CaseKind = 'lower' | 'upper' | 'title';
function caseOf(word: string): CaseKind {
  const hasLetters = /\p{L}/u.test(word);
  if (hasLetters && word === word.toUpperCase() && word !== word.toLowerCase() && word.length > 1) return 'upper';
  if (/^\p{Lu}/u.test(word)) return 'title';
  return 'lower';
}
function applyCase(out: string, kind: CaseKind): string {
  if (kind === 'upper') return out.toUpperCase();
  if (kind === 'title') return out.charAt(0).toUpperCase() + out.slice(1);
  return out;
}

function latinWordToCyr(word: string, flags: string[]): string {
  const kind = caseOf(word);
  const w = word.toLowerCase(); // apostrophes already normalized to S upstream
  let out = '';
  let i = 0;
  while (i < w.length) {
    // context 'e' → э (word-initial) | е (otherwise)
    if (w[i] === 'e') {
      if (i === 0) { out += 'э'; flags.push(`word-initial 'e'→э in "${word}" (could be е)`); }
      else out += 'е';
      i += 1;
      continue;
    }
    let matched = false;
    for (const [lat, cyr] of LAT_RULES) {
      if (w.startsWith(lat, i)) {
        out += cyr;
        if (lat === 'ts') flags.push(`'ts'→ц in "${word}" (loanword check)`);
        if (lat === 'c') flags.push(`bare 'c'→к in "${word}" (uncommon — verify)`);
        i += lat.length;
        matched = true;
        break;
      }
    }
    if (!matched) { out += w[i]; i += 1; } // pass through unknown char
  }
  return applyCase(out, kind);
}

function cyrWordToLatin(word: string, flags: string[]): string {
  const kind = caseOf(word);
  const w = word.toLowerCase();
  let out = '';
  for (let i = 0; i < w.length; i++) {
    const ch = w[i];
    if (ch === 'е') {
      const prev = w[i - 1];
      const atStart = i === 0;
      if (atStart || (prev && CYR_VOWELS.has(prev))) {
        out += 'ye';
        flags.push(`'е'→ye in "${word}" (could be e)`);
      } else out += 'e';
      continue;
    }
    if (ch === 'ц') flags.push(`'ц'→ts in "${word}" (loanword)`);
    if (ch === 'ы') flags.push(`'ы'→i in "${word}" (loanword)`);
    if (ch === 'ь') flags.push(`soft sign dropped in "${word}"`);
    out += ch in CYR_MAP ? CYR_MAP[ch] : ch;
  }
  return applyCase(out, kind);
}

export function detectScript(text: string): Script {
  if (!text || !text.trim()) return 'empty';
  const cyr = (text.match(/[\u0400-\u04FF]/g) ?? []).length;
  const lat = (text.match(/[A-Za-z]/g) ?? []).length;
  if (cyr > 0 && lat === 0) return 'cyrillic';
  if (lat > 0 && cyr === 0) return 'latin';
  if (cyr > 0 && lat > 0) return 'mixed';
  return 'empty';
}

export function latinToCyrillic(text: string): TranslitResult {
  const flags: string[] = [];
  const out = tokenize(text.replace(APOS, S))
    .map((t) => (isWordToken(t) ? latinWordToCyr(t, flags) : t))
    .join('');
  return { output: out, flags };
}

export function cyrillicToLatin(text: string): TranslitResult {
  const flags: string[] = [];
  const out = tokenize(text.replace(APOS, S))
    .map((t) => (isWordToken(t) ? cyrWordToLatin(t, flags) : t))
    .join('');
  return { output: out, flags };
}

/**
 * Backfill helper. Given a legacy text_uzbek value of either script,
 * return BOTH scripts with Cyrillic as canonical (D4).
 *  - cyrillic source → canonical = source, latin = derived
 *  - latin source    → canonical = derived, latin = source
 */
export function deriveBothScripts(text: string): {
  sourceScript: Script;
  cyrillic: string;
  latin: string;
  flags: string[];
} {
  const sourceScript = detectScript(text);
  if (sourceScript === 'cyrillic') {
    const { output, flags } = cyrillicToLatin(text);
    return { sourceScript, cyrillic: text, latin: output, flags };
  }
  if (sourceScript === 'latin') {
    const { output, flags } = latinToCyrillic(text);
    return { sourceScript, cyrillic: output, latin: text, flags };
  }
  // mixed / empty → no safe automatic call; flag for the human gate
  return {
    sourceScript,
    cyrillic: '',
    latin: '',
    flags: [`source script is "${sourceScript}" — needs manual handling, not auto-transliterated`],
  };
}
