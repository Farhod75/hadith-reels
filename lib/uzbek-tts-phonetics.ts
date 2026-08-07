// lib/uzbek-tts-phonetics.ts
// ============================================================
// Uzbek TTS pronunciation layer — ElevenLabs v3 inline IPA.
// Reusable: hadith-reels, idris-learning-app, seerah audiobooks.
//
// ── EMPIRICAL FINDINGS (browser-tested on eleven_v3, 2026-07) ──────────────
//  OK  ҳ and қ  — v3 pronounces these CORRECTLY out of the box. No fix needed.
//                 ("Аллоҳ таоло Қуръонда айтади" -> good)
//  BAD ж        — v3 says "dj", not a clean "j". THE one letter needing a fix.
//  FIX          — inline IPA wrapped in /slashes/ corrects it.
//  MIXED OK     — IPA for one word + Cyrillic for the rest WORKS:
//                 "/dʒannat/ оналар оёғи остида" -> correct.
//                 So we transcribe problem WORDS only, never whole sentences.
//
// ── MODEL REQUIREMENT ─────────────────────────────────────────────────────
//  Inline IPA requires model_id: 'eleven_v3'.
//  On eleven_multilingual_v2, IPA input is SILENTLY IGNORED — no error, it just
//  reads the raw characters. Silent degradation. Always assert the model.
//
// ── FORMATTING RULES (learned the hard way) ───────────────────────────────
//  1. Everything inside /slashes/ must be IPA/Latin. NEVER mix Cyrillic inside
//     the slashes — "/dʒума/" is half-IPA and produces undefined output.
//  2. Always close the slash. "/dʒamoat" (unclosed) does not work.
//  3. Include stress: ˈ before the stressed syllable. Uzbek stress is normally
//     final. This audibly improved results and is ElevenLabs' own advice.
//
// ── IPA GOTCHA (this cost us a test) ──────────────────────────────────────
//  In IPA, `j` is the "Y" sound (Uzbek й), NOT the "J" of jam.
//  The "J" of jam is `dʒ`.
//    Uzbek ж  (jannat) -> dʒ
//    Uzbek й/ё (oyogi) -> j      (so "ojogi" is CORRECT IPA for "oyogi")
//  Getting this backwards produces a wrong test input and a FALSE failure.
//
// ── REJECTED APPROACH (do not reintroduce) ────────────────────────────────
//  An earlier design respelled Cyrillic (ж->дж, ҳ->х, қ->к…) to trick a
//  Russian-phonetics engine. DISPROVEN on v3: it already says "dj", so ж->дж
//  pushes it further wrong, and ҳ/қ need no help at all.
//  Lesson: a workaround that helps a weak model can harm a stronger one.
//  Re-baseline after every model upgrade.
// ============================================================

export const REQUIRED_MODEL = 'eleven_v3'

/**
 * Problem-word lexicon: Uzbek Cyrillic -> IPA (unwrapped).
 * ONLY words v3 gets wrong belong here — in practice, ж-words.
 * Everything else stays plain Cyrillic; v3 handles it fine.
 *
 * Each entry should be ear-verified before being trusted. Unverified guesses
 * can make output worse, not better — they are marked below.
 */
export const UZBEK_IPA_LEXICON: Record<string, string> = {
  // ж words — all VERIFIED by ear on eleven_v3.
  // Stress: IPA primary-stress mark ˈ (U+02C8) goes BEFORE the stressed
  // syllable. Uzbek stress is normally final. Adding stress measurably
  // improved output — ElevenLabs' own guidance recommends it for IPA.
  'жаннат':   'dʒanˈnat',
  'жаҳаннам': 'dʒahˈannam',
  'жамоат':   'dʒamoˈat',   // IPA beats plain Cyrillic here — keep it
  'жон':      'dʒon',
  'жума':     'dʒuˈma',
  'ражаб':    'radʒˈab',
  'ҳожат':    'hodʒˈat',
  'ажр':      'adʒr',
}

/** Russian loanwords that legitimately keep /ʒ/ — never IPA-convert these. */
const ZH_LOANWORDS = new Set([
  'журнал', 'журналист', 'гараж', 'режим', 'режиссёр', 'жюри',
  'инженер', 'жанр', 'багаж', 'массаж', 'пляж', 'этаж',
])

export interface ApplyOptions {
  /** Pass the model you're about to call; throws if it can't honour IPA. */
  assertModel?: string
}

/**
 * Wrap known problem words in inline IPA, leaving everything else as Cyrillic.
 * "Жаннат оналар оёғи остида" -> "/dʒannat/ оналар оёғи остида"
 */
export function applyUzbekIPA(text: string, opts: ApplyOptions = {}): string {
  if (!text) return text

  if (opts.assertModel && opts.assertModel !== REQUIRED_MODEL) {
    throw new Error(
      `Uzbek IPA requires model '${REQUIRED_MODEL}', got '${opts.assertModel}'. ` +
      `Other models SILENTLY IGNORE IPA — the fix would vanish with no error.`
    )
  }

  return text.replace(/[\p{L}\u0400-\u04FF']+/gu, (word) => {
    const lower = word.toLowerCase()
    if (ZH_LOANWORDS.has(lower)) return word        // keep Russian /ʒ/
    const ipa = UZBEK_IPA_LEXICON[lower]
    return ipa ? `/${ipa}/` : word
  })
}

/** Which lexicon entries fired — for eval / debugging. */
export function explainIPA(text: string): Array<{ word: string; ipa: string }> {
  const hits: Array<{ word: string; ipa: string }> = []
  text.replace(/[\p{L}\u0400-\u04FF']+/gu, (w) => {
    const lower = w.toLowerCase()
    const ipa = UZBEK_IPA_LEXICON[lower]
    if (ipa && !ZH_LOANWORDS.has(lower)) hits.push({ word: w, ipa })
    return w
  })
  return hits
}

// ============================================================
// EVAL CORPUS — regression suite. Generate, LISTEN, score.
// `status` records what was actually verified, not what we hope.
// ============================================================
export interface EvalCase {
  id: string
  cyrillic: string
  expect: string
  status: 'verified-ok' | 'verified-fixed' | 'unverified'
}

export const UZBEK_TTS_EVAL: EvalCase[] = [
  // Already correct on v3 — regression canaries, must not break
  { id: 'ok-01', cyrillic: 'Аллоҳ таоло Қуръонда айтади',
    expect: 'ҳ and қ both clean', status: 'verified-ok' },
  { id: 'ok-02', cyrillic: 'Илм олиш ҳар бир мусулмонга фарздир',
    expect: 'baseline clean', status: 'unverified' },

  // The ж fix
  { id: 'j-01', cyrillic: 'Жаннат оналар оёғи остида',
    expect: 'jannat (not djannat), oyogi correct', status: 'verified-fixed' },
  { id: 'j-02', cyrillic: 'Жума куни', expect: 'juma', status: 'verified-fixed' },
  { id: 'j-03', cyrillic: 'Бу ражаб ойида', expect: 'rajab', status: 'verified-fixed' },
  { id: 'j-04', cyrillic: 'Жамоат намози', expect: 'jamoat', status: 'verified-fixed' },

  // Loanword guard — must NOT be converted
  { id: 'lw-01', cyrillic: 'журнал ўқидим',
    expect: 'zhurnal (Russian ж kept)', status: 'unverified' },

  // HIGH STAKES — always human-verified before publishing, regardless of tooling
  { id: 'hs-01', cyrillic: 'Расулуллоҳ соллаллоҳу алайҳи васаллам',
    expect: 'reverent, every ҳ sounded', status: 'unverified' },
  { id: 'hs-02', cyrillic: 'Бу ҳадис саҳиҳ, Имом Бухорий ривоят қилган',
    expect: 'clean', status: 'unverified' },
]
