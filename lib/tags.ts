// P150 — canonical hashtag vocabulary.
//
// WHY THIS EXISTS. The caption's hashtags were the library's `tags` column,
// English, appended to Cyrillic body text on every RU/UZ/TJ reel. The operator
// searches in his own language first, and so does the audience — an Uzbek
// speaker looking for hadith content searches «ҳадис», not #hadith.
//
// BOTH sets ship, not one. Hashtags are free and each is a separate discovery
// path: the localised tags reach the actual audience, the English ones stay
// findable by anyone browsing globally. Dropping either costs reach for nothing.
//
// TWO PROBLEMS SOLVED TOGETHER. The library vocabulary had ~100 tags with heavy
// duplication — prayer/salah, charity/sadaqah/giving, knowledge/ilm/learning/
// education, forgiveness/repentance/tawbah, blessing/blessings, good deeds/
// good-deeds. Translating those separately would have multiplied the mess by
// four. So raw tags map onto CANONICAL concepts first, then each concept
// carries its four forms.
//
// A THIRD OF THESE ARE NOT TRANSLATIONS. salah, dua, sadaqah, iman, sabr,
// shukr, taqwa, tawbah, ilm, jannah, akhirah, ibadah, dhikr, barakah, deen are
// Arabic loanwords that already exist in Russian, Uzbek and Tajik Islamic
// vocabulary. They are transliterated, not translated, and they are the terms
// the audience actually uses.
//
// UNMAPPED TAGS FALL BACK to their English form. That is deliberate: a new tag
// appearing in the library should not silently vanish from captions. It is also
// why scripts/audit-tags.ts exists — the fallback is correct and invisible, so
// nothing reported the 53 tags that were using it (P182).

export type TagForms = { en: string; ru: string; uz: string; tj: string }

// Raw library tag -> canonical key. Lowercased at lookup.
export const TAG_CANONICAL: Record<string, string> = {
  // prayer
  prayer: 'salah', salah: 'salah', fajr: 'fajr', asr: 'asr',
  // charity
  charity: 'sadaqah', sadaqah: 'sadaqah', giving: 'sadaqah',
  generosity: 'sadaqah', gift: 'sadaqah',
  // knowledge
  knowledge: 'ilm', ilm: 'ilm', learning: 'ilm', education: 'ilm',
  // repentance
  forgiveness: 'forgiveness', repentance: 'tawbah', tawbah: 'tawbah',
  sins: 'sins', expiation: 'forgiveness',
  // patience & gratitude
  patience: 'sabr', sabr: 'sabr', gratitude: 'shukr', shukr: 'shukr',
  hamd: 'shukr', contentment: 'qanaah', qanaah: 'qanaah',
  // fasting
  fasting: 'sawm', sawm: 'sawm',
  // faith
  faith: 'iman', iman: 'iman', islam: 'islam', kufr: 'kufr',
  taqwa: 'taqwa', certainty: 'iman', believer: 'iman', deen: 'deen',
  // supplication
  dua: 'dua', supplication: 'dua', asking: 'dua', dhikr: 'dhikr',
  // worship
  worship: 'ibadah', ibadah: 'ibadah', quran: 'quran',
  // family
  family: 'family', parents: 'parents', mother: 'mother', father: 'father',
  children: 'children', marriage: 'marriage', husband: 'marriage',
  kinship: 'family', brotherhood: 'brotherhood',
  // character
  character: 'akhlaq', akhlaq: 'akhlaq', kindness: 'kindness',
  respect: 'respect', mercy: 'mercy', compassion: 'mercy', love: 'love',
  sincerity: 'sincerity', intentions: 'sincerity', speech: 'speech',
  smile: 'kindness', help: 'help', harm: 'harm',
  // hereafter
  paradise: 'jannah', jannah: 'jannah', akhirah: 'akhirah',
  afterlife: 'akhirah', qiyamah: 'qiyamah', 'judgment-day': 'qiyamah',
  accountability: 'qiyamah', intercession: 'akhirah',
  // hajj
  hajj: 'hajj', pilgrimage: 'hajj', mabrur: 'hajj',
  // deeds & blessing
  deeds: 'deeds', 'good deeds': 'deeds', 'good-deeds': 'deeds',
  reward: 'reward', blessing: 'barakah', blessings: 'barakah',
  blessed: 'barakah', barakah: 'barakah',
  // misc
  allah: 'allah', wealth: 'wealth', health: 'health', heart: 'heart',
  hope: 'hope', light: 'light', animals: 'animals', food: 'food',
  jihad: 'jihad', legacy: 'legacy', closeness: 'closeness', bala: 'bala',

  // ── 2026-09-29 audit ────────────────────────────────────────────────
  // P150 mapped ~100 distinct library tags; the column is now at ~150 and
  // nothing kept the vocabulary current. 53 values were reaching captions
  // unmapped, each emitting only its English form and losing the localised
  // half that P150 exists to provide — #maruf shipped bare in the RU and TJ
  // captions of Muslim #1005. These 24 fold onto concepts that already carry
  // four forms, so they need no new vocabulary.
  sujud: 'salah', prostration: 'salah',
  'sadaqah-jariyah': 'sadaqah',
  teaching: 'ilm', scholar: 'ilm',
  praise: 'shukr', thanks: 'shukr',
  ramadan: 'sawm',
  muslim: 'islam', pillar: 'islam', pillars: 'islam', religion: 'deen',
  remembrance: 'dhikr',
  spouse: 'marriage', wife: 'marriage',
  'silatur-rahim': 'family',
  companionship: 'brotherhood', friendship: 'brotherhood',
  virtue: 'akhlaq',
  intention: 'sincerity', niyyah: 'sincerity',
  tongue: 'speech',
  umrah: 'hajj',
  trial: 'bala',

  // ── 2026-09-30: concepts, not aliases (P182, second half) ──
  // These recur. The one-off descriptive tags in the same audit were removed
  // from the library instead of translated — growing the vocabulary to chase
  // single-row tags is what made this drift in the first place.
  kabair: 'kabair', 'major-sins': 'kabair', majorsins: 'kabair',
  warning: 'kabair',            // #6857 is the major-sins hadith
  shirk: 'shirk', polytheism: 'shirk', idolatry: 'shirk',
  zakat: 'zakat',
  riba: 'riba', usury: 'riba',
  fitna: 'fitna',
  tahara: 'tahara', purity: 'tahara', clean: 'tahara',
  death: 'death',
  neighbor: 'neighbor', neighbour: 'neighbor',
  prophet: 'prophet',
  orphan: 'orphan', orphans: 'orphan',
  women: 'women',
}

// Canonical key -> the four forms. UZ and TJ are Cyrillic, matching the
// library's text_uzbek_cyrillic and text_tajik columns and the caption body.
export const TAG_FORMS: Record<string, TagForms> = {
  salah:        { en: 'prayer',      ru: 'намаз',        uz: 'намоз',        tj: 'намоз' },
  fajr:         { en: 'fajr',        ru: 'фаджр',        uz: 'бомдод',       tj: 'бомдод' },
  asr:          { en: 'asr',         ru: 'аср',          uz: 'аср',          tj: 'аср' },
  sadaqah:      { en: 'sadaqah',     ru: 'садака',       uz: 'садақа',       tj: 'садақа' },
  ilm:          { en: 'knowledge',   ru: 'знание',       uz: 'илм',          tj: 'илм' },
  forgiveness:  { en: 'forgiveness', ru: 'прощение',     uz: 'мағфират',     tj: 'бахшиш' },
  tawbah:       { en: 'tawbah',      ru: 'покаяние',     uz: 'тавба',        tj: 'тавба' },
  sins:         { en: 'sins',        ru: 'грехи',        uz: 'гуноҳлар',     tj: 'гуноҳҳо' },
  sabr:         { en: 'patience',    ru: 'терпение',     uz: 'сабр',         tj: 'сабр' },
  shukr:        { en: 'gratitude',   ru: 'благодарность', uz: 'шукр',        tj: 'шукр' },
  qanaah:       { en: 'contentment', ru: 'довольство',   uz: 'қаноат',       tj: 'қаноат' },
  sawm:         { en: 'fasting',     ru: 'пост',         uz: 'рўза',         tj: 'рӯза' },
  iman:         { en: 'iman',        ru: 'вера',         uz: 'иймон',        tj: 'имон' },
  islam:        { en: 'islam',       ru: 'ислам',        uz: 'ислом',        tj: 'ислом' },
  kufr:         { en: 'kufr',        ru: 'неверие',      uz: 'куфр',         tj: 'куфр' },
  shirk:        { en: 'shirk',       ru: 'ширк',         uz: 'ширк',         tj: 'ширк' },
  kabair:       { en: 'majorsins',   ru: 'большиегрехи', uz: 'кабирагуноҳлар', tj: 'гуноҳҳоикабира' },
  zakat:        { en: 'zakat',       ru: 'закят',        uz: 'закот',        tj: 'закот' },
  riba:         { en: 'riba',        ru: 'ростовщичество', uz: 'рибо',       tj: 'рибо' },
  fitna:        { en: 'fitna',       ru: 'фитна',        uz: 'фитна',        tj: 'фитна' },
  tahara:       { en: 'purity',      ru: 'чистота',      uz: 'таҳорат',      tj: 'таҳорат' },
  death:        { en: 'death',       ru: 'смерть',       uz: 'ўлим',         tj: 'марг' },
  neighbor:     { en: 'neighbor',    ru: 'сосед',        uz: 'қўшни',        tj: 'ҳамсоя' },
  prophet:      { en: 'prophet',     ru: 'пророк',       uz: 'пайғамбар',    tj: 'пайғамбар' },
  orphan:       { en: 'orphan',      ru: 'сирота',       uz: 'етим',         tj: 'ятим' },
  women:        { en: 'women',       ru: 'женщины',      uz: 'аёллар',       tj: 'занон' },
  taqwa:        { en: 'taqwa',       ru: 'богобоязненность', uz: 'тақво',    tj: 'тақво' },
  deen:         { en: 'deen',        ru: 'религия',      uz: 'дин',          tj: 'дин' },
  dua:          { en: 'dua',         ru: 'дуа',          uz: 'дуо',          tj: 'дуо' },
  dhikr:        { en: 'dhikr',       ru: 'зикр',         uz: 'зикр',         tj: 'зикр' },
  ibadah:       { en: 'worship',     ru: 'поклонение',   uz: 'ибодат',       tj: 'ибодат' },
  quran:        { en: 'quran',       ru: 'коран',        uz: 'қуръон',       tj: 'қуръон' },
  family:       { en: 'family',      ru: 'семья',        uz: 'оила',         tj: 'оила' },
  parents:      { en: 'parents',     ru: 'родители',     uz: 'ота-она',      tj: 'падару модар' },
  mother:       { en: 'mother',      ru: 'мать',         uz: 'она',          tj: 'модар' },
  father:       { en: 'father',      ru: 'отец',         uz: 'ота',          tj: 'падар' },
  children:     { en: 'children',    ru: 'дети',         uz: 'болалар',      tj: 'кӯдакон' },
  marriage:     { en: 'marriage',    ru: 'брак',         uz: 'никоҳ',        tj: 'никоҳ' },
  brotherhood:  { en: 'brotherhood', ru: 'братство',     uz: 'биродарлик',   tj: 'бародарӣ' },
  akhlaq:       { en: 'akhlaq',      ru: 'нравы',        uz: 'ахлоқ',        tj: 'ахлоқ' },
  kindness:     { en: 'kindness',    ru: 'доброта',      uz: 'меҳрибонлик',  tj: 'меҳрубонӣ' },
  respect:      { en: 'respect',     ru: 'уважение',     uz: 'ҳурмат',       tj: 'эҳтиром' },
  mercy:        { en: 'mercy',       ru: 'милосердие',   uz: 'раҳм',         tj: 'раҳм' },
  love:         { en: 'love',        ru: 'любовь',       uz: 'муҳаббат',     tj: 'муҳаббат' },
  sincerity:    { en: 'sincerity',   ru: 'искренность',  uz: 'ихлос',        tj: 'ихлос' },
  speech:       { en: 'speech',      ru: 'речь',         uz: 'сўз',          tj: 'сухан' },
  help:         { en: 'help',        ru: 'помощь',       uz: 'ёрдам',        tj: 'кӯмак' },
  harm:         { en: 'harm',        ru: 'вред',         uz: 'зарар',        tj: 'зарар' },
  jannah:       { en: 'jannah',      ru: 'рай',          uz: 'жаннат',       tj: 'биҳишт' },
  akhirah:      { en: 'akhirah',     ru: 'ахира',        uz: 'охират',       tj: 'охират' },
  qiyamah:      { en: 'qiyamah',     ru: 'судныйдень',   uz: 'қиёмат',       tj: 'қиёмат' },
  hajj:         { en: 'hajj',        ru: 'хадж',         uz: 'ҳаж',          tj: 'ҳаҷ' },
  deeds:        { en: 'deeds',       ru: 'дела',         uz: 'амаллар',      tj: 'амалҳо' },
  reward:       { en: 'reward',      ru: 'награда',      uz: 'ажр',          tj: 'подош' },
  barakah:      { en: 'barakah',     ru: 'баракат',      uz: 'барака',       tj: 'баракат' },
  allah:        { en: 'allah',       ru: 'аллах',        uz: 'аллоҳ',        tj: 'аллоҳ' },
  wealth:       { en: 'wealth',      ru: 'богатство',    uz: 'бойлик',       tj: 'сарват' },
  health:       { en: 'health',      ru: 'здоровье',     uz: 'соғлик',       tj: 'саломатӣ' },
  heart:        { en: 'heart',       ru: 'сердце',       uz: 'қалб',         tj: 'дил' },
  hope:         { en: 'hope',        ru: 'надежда',      uz: 'умид',         tj: 'умед' },
  light:        { en: 'light',       ru: 'свет',         uz: 'нур',          tj: 'нур' },
  animals:      { en: 'animals',     ru: 'животные',     uz: 'ҳайвонлар',    tj: 'ҳайвонот' },
  food:         { en: 'food',        ru: 'еда',          uz: 'таом',         tj: 'таом' },
  jihad:        { en: 'jihad',       ru: 'джихад',       uz: 'жиҳод',        tj: 'ҷиҳод' },
  legacy:       { en: 'legacy',      ru: 'наследие',     uz: 'мерос',        tj: 'мерос' },
  closeness:    { en: 'closeness',   ru: 'близость',     uz: 'яқинлик',      tj: 'наздикӣ' },
  bala:         { en: 'trials',      ru: 'испытания',    uz: 'синов',        tj: 'озмоиш' },
}

/**
 * Dropped entirely — no form of these reaches a caption (P106).
 *
 * Not a vocabulary problem: these hashtags reach the wrong audience. #date
 * lands in dating content; #hellfire, #fire and #hell skew to metal and
 * gaming; #men pulls traffic this channel does not want. None of them are in
 * TAG_FORMS, so blocking the tag and blocking its English form are the same
 * act here.
 *
 * Applied by the CALLER, before buildTags() is reached. It lived inline in
 * app/admin/page.tsx, where nothing could check against it — which is how
 * `death` and `women` were each given four forms on 2026-09-30 while sitting
 * on it, with scripts/audit-tags.ts reporting OK (P182).
 */
export const TAG_BLOCKLIST = ['date', 'dates', 'hellfire', 'fire', 'hell', 'men']

/**
 * The ENGLISH hashtag is suppressed; the localised one still ships.
 *
 * P106 predates P150, when every tag was English and "drop the tag" and "drop
 * its English form" were the same act. They are not any more. #death and
 * #women reach true crime and fashion; #ўлим, #марг, #занон and #аёллар reach
 * neither. Blocking the concept to avoid the English tag costs the localised
 * audience the whole tag, which is backwards for a channel whose reach is
 * Uzbek, Russian and Tajik.
 *
 * Per-language suppression is the next split if Russian turns out to behave
 * like English here — #женщины is the one to watch.
 */
export const EN_HASHTAG_BLOCKLIST = ['death', 'women']

/**
 * Build the hashtag line for a caption.
 *
 * Emits BOTH the localised and the English form of each topic tag — two
 * discovery paths, and hashtags cost nothing. When lang is 'en' the two
 * collapse and only one is emitted.
 *
 * Two filters apply and they are NOT the same filter. TAG_BLOCKLIST is applied
 * by the caller and drops the tag whole. EN_HASHTAG_BLOCKLIST is applied below
 * and suppresses only the English form, leaving the localised tag to ship.
 */
export function buildTags(rawTags: string[], lang: string): string {
  const out: string[] = []
  const seen = new Set<string>()
  const push = (t: string) => {
    const tag = '#' + t.replace(/[\s-]+/g, '')
    if (!seen.has(tag)) { seen.add(tag); out.push(tag) }
  }
  for (const raw of rawTags) {
    const key = TAG_CANONICAL[raw.toLowerCase()]
    const forms = key ? TAG_FORMS[key] : undefined
    if (!forms) { push(raw); continue }   // unmapped: keep it rather than drop it
    const local = (forms as any)[lang] as string | undefined
    if (local) push(local)
    // The English form is its own discovery path and can be suppressed alone —
    // the localised tag is unaffected by what #death reaches.
    if (!EN_HASHTAG_BLOCKLIST.includes(key)) push(forms.en)
  }
  return out.join(' ')
}
