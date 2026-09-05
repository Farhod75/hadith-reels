// P150 — localised reference line.
//
// WHY. The caption's reference read `📖 Jami at-Tirmidhi #1956, Abu Dharr` —
// Latin, on a Cyrillic caption, on every RU/UZ/TJ reel. Some readers read only
// their own language; a Latin string in the middle of a Tajik caption is a
// foreign object to them.
//
// BOTH FORMS FOR THE COLLECTION, one for the narrator. The collection name plus
// the hadith number is the CITATION — it is what someone types to check the
// hadith independently, so the Latin form has to survive. The narrator is not
// part of that lookup, so it is localised only and the line stays readable.
//
//   📖 Ҷомеъи Тирмизӣ (Jami at-Tirmidhi) №1956, Абӯзарр
//
// UNMAPPED NAMES FALL BACK to their English form rather than vanishing. A new
// collection or narrator appearing in the library should look wrong in the
// caption, not disappear from it.

export type Forms = { ru: string; uz: string; tj: string }

export const COLLECTIONS: Record<string, Forms> = {
  'Sahih al-Bukhari': { ru: 'Сахих аль-Бухари',  uz: 'Саҳиҳ ал-Бухорий',  tj: 'Саҳеҳи Бухорӣ' },
  'Sahih Muslim':     { ru: 'Сахих Муслим',      uz: 'Саҳиҳ Муслим',      tj: 'Саҳеҳи Муслим' },
  'Jami at-Tirmidhi': { ru: 'Джами ат-Тирмизи',  uz: 'Жомеъ ат-Термизий', tj: 'Ҷомеъи Тирмизӣ' },
  'Sunan Abu Dawud':  { ru: 'Сунан Абу Дауд',    uz: 'Сунан Абу Довуд',   tj: 'Сунани Абӯдовуд' },
  'Sunan an-Nasai':   { ru: 'Сунан ан-Насаи',    uz: 'Сунан ан-Насоий',   tj: 'Сунани Насоӣ' },
  'Sunan Ibn Majah':  { ru: 'Сунан Ибн Маджа',   uz: 'Сунан Ибн Можа',    tj: 'Сунани Ибни Моҷа' },
  'Musnad Ahmad':     { ru: 'Муснад Ахмад',      uz: 'Муснад Аҳмад',      tj: 'Муснади Аҳмад' },
}

// Narrators present in the library. Tajik drops the "ibn" to the izafet form
// (Абӯмусои Ашъарӣ, Ҷобир ибни Абдуллоҳ) — that is normal Tajik usage, not an
// inconsistency with the Uzbek forms.
export const NARRATORS: Record<string, Forms> = {
  'Abu Hurairah':          { ru: 'Абу Хурайра',            uz: 'Абу Ҳурайра',           tj: 'Абӯҳурайра' },
  'Abu Huraira':           { ru: 'Абу Хурайра',            uz: 'Абу Ҳурайра',           tj: 'Абӯҳурайра' },
  'Anas ibn Malik':        { ru: 'Анас ибн Малик',         uz: 'Анас ибн Молик',        tj: 'Анас ибни Молик' },
  'Abdullah ibn Amr':      { ru: 'Абдуллах ибн Амр',       uz: 'Абдуллоҳ ибн Амр',      tj: 'Абдуллоҳ ибни Амр' },
  'Abdullah ibn Masud':    { ru: 'Абдуллах ибн Масуд',     uz: 'Абдуллоҳ ибн Масъуд',   tj: 'Абдуллоҳ ибни Масъуд' },
  'Abu Dharr':             { ru: 'Абу Зарр',               uz: 'Абу Зарр',              tj: 'Абӯзарр' },
  'Abu Darda':             { ru: 'Абу ад-Дарда',           uz: 'Абу Дардо',             tj: 'Абӯдардо' },
  'Abu Said al-Khudri':    { ru: 'Абу Саид аль-Худри',     uz: 'Абу Саид ал-Худрий',    tj: 'Абӯсаиди Худрӣ' },
  'Abu Musa al-Ashari':    { ru: 'Абу Муса аль-Ашари',     uz: 'Абу Мусо ал-Ашарий',    tj: 'Абӯмусои Ашъарӣ' },
  'Abu Malik al-Ashari':   { ru: 'Абу Малик аль-Ашари',    uz: 'Абу Молик ал-Ашарий',   tj: 'Абӯмолики Ашъарӣ' },
  'Aisha':                 { ru: 'Аиша',                   uz: 'Оиша',                  tj: 'Оиша' },
  'Ibn Umar':              { ru: 'Ибн Умар',               uz: 'Ибн Умар',              tj: 'Ибни Умар' },
  'Ibn Abbas':             { ru: 'Ибн Аббас',              uz: 'Ибн Аббос',             tj: 'Ибни Аббос' },
  'Umar ibn al-Khattab':   { ru: 'Умар ибн аль-Хаттаб',    uz: 'Умар ибн Хаттоб',       tj: 'Умар ибни Хаттоб' },
  'Uthman ibn Affan':      { ru: 'Усман ибн Аффан',        uz: 'Усмон ибн Аффон',       tj: 'Усмон ибни Аффон' },
  'Jabir ibn Abdullah':    { ru: 'Джабир ибн Абдуллах',    uz: 'Жобир ибн Абдуллоҳ',    tj: 'Ҷобир ибни Абдуллоҳ' },
  'Muadh ibn Jabal':       { ru: 'Муаз ибн Джабаль',       uz: 'Муоз ибн Жабал',        tj: 'Муоз ибни Ҷабал' },
  'Suhaib':                { ru: 'Сухайб',                 uz: 'Суҳайб',                tj: 'Суҳайб' },
  "Nu'man ibn Bashir":     { ru: 'Нуман ибн Башир',        uz: 'Нўъмон ибн Башир',      tj: 'Нӯъмон ибни Башир' },
  'Adiy ibn Hatim':        { ru: 'Адий ибн Хатим',         uz: 'Адий ибн Ҳотим',        tj: 'Адӣ ибни Ҳотим' },
  'Salman al-Farisi':      { ru: 'Сальман аль-Фариси',     uz: 'Салмон ал-Форисий',     tj: 'Салмони Форсӣ' },
  'Jubayr ibn Mutim':      { ru: 'Джубайр ибн Мутим',      uz: 'Жубайр ибн Мутъим',     tj: 'Ҷубайр ибни Мутъим' },
  "Mu'awiyah ibn Jahimah": { ru: 'Муавия ибн Джахима',     uz: 'Муовия ибн Жоҳима',     tj: 'Муовия ибни Ҷоҳима' },
}

/**
 * Reference line for a caption.
 *
 * EN returns the plain form. Other languages return the localised collection
 * with the Latin name in parentheses, so the citation stays verifiable, and
 * `№` rather than `#`, which is the numeral sign those languages use.
 */
export function buildRef(
  collection: string,
  hadithNumber: string | number | null | undefined,
  narrator: string,
  lang: string,
): string {
  const num = hadithNumber ? ` ${lang === 'en' ? '#' : '№'}${hadithNumber}` : ''
  if (lang === 'en' || lang === 'ar') {
    return `${collection}${num}, ${narrator}`
  }
  const c = (COLLECTIONS[collection] as any)?.[lang] as string | undefined
  const n = (NARRATORS[narrator] as any)?.[lang] as string | undefined
  const coll = c ? `${c} (${collection})` : collection
  return `${coll}${num}, ${n || narrator}`
}
