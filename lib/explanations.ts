// lib/explanations.ts
// P387: the hadith explanation page - what a named scholar or source says about a
// hadith, carried verbatim with credit. Nothing on that page is written by us or
// by a model: the files under content/explanations/ come from
// scripts/fetch-explanation.py and scripts/lib/test_fetch_explanation.py checks
// every text field against the raw source bytes stored beside them.
//
// Page structure follows the Zad Academy hadith lessons: the matn, word meanings,
// the explanation, the lessons drawn from it - and the occasion (sabab al-wurud)
// only when a cited source records one.

import COLLECTION_SLUGS from '@/content/explanations/collections.json'
import EXPLAINED from '@/content/explanations/index.json'

export type SiteLang = 'en' | 'ru' | 'uz' | 'tj'

export interface CommentaryLang {
  url: string
  raw: string
  raw_sha256: string
  title: string
  hadeeth: string            // the source's full text of the hadith, translated by the source
  explanation: string
  lessons: string[]
  word_meanings: unknown[]
  attribution: string
  grade: string
}

export interface Commentary {
  source: string
  source_id: string
  publisher: string
  licence: string
  fetched_at: string
  references_ar: string
  langs: Partial<Record<SiteLang | 'ar', CommentaryLang>>
}

// P389: an event around the hadith, from its own source entry, sahih/hasan only.
export interface RelatedEventLang {
  url: string; raw: string; raw_sha256: string
  title: string; hadeeth: string; attribution: string; grade: string
}
export interface RelatedEvent {
  source: string; source_id: string; publisher: string; fetched_at: string
  see_also: string           // a modern book as a map (title, page) - never quoted
  langs: Partial<Record<SiteLang | 'ar', RelatedEventLang>>
}

export interface Occasion { source: string; url: string; text: Partial<Record<SiteLang, string>> }

export interface Explanation {
  schema: number
  slug: string
  library_id: string
  collection: string
  hadith_number: string
  library_is_excerpt?: boolean   // the reel narrated part of a longer hadith
  occasion: Occasion | null
  related_events?: RelatedEvent[]
  commentaries: Commentary[]
}

const SLUGS = COLLECTION_SLUGS as Record<string, string>
const BY_SLUG: Record<string, string> = Object.fromEntries(
  Object.entries(SLUGS).map(([name, slug]) => [slug, name]))

/** 'muslim' -> 'Sahih Muslim'; unknown -> undefined */
export function collectionFromSlug(slug: string): string | undefined {
  return BY_SLUG[slug.toLowerCase()]
}

/** The public path of a hadith's page, or undefined for an unmapped collection. */
export function hadithPagePath(collection: string, number: string | undefined, lang?: SiteLang) {
  const c = SLUGS[collection]
  if (!c || !number) return undefined
  return `/hadith/${c}/${encodeURIComponent(number)}${lang ? `?lang=${lang}` : ''}`
}

const EXPLAINED_SET = new Set(EXPLAINED as string[])

/** True when content/explanations/ holds an explanation for this hadith. */
export function hasExplanation(collection: string, number: string | undefined) {
  const c = SLUGS[collection]
  return !!c && !!number && EXPLAINED_SET.has(`${c}-${number}`)
}

// The page's own words. UZ Cyrillic (P169); section names as the Zad lessons use them.
export const EXPLAIN_UI: Record<SiteLang, {
  back: string; explanation: string; words: string; lessons: string; occasion: string
  sourceOf: string; verbatim: string; references: string; original: string
  noLang: string; noExplanation: string; checkSource: string; translationFallback: string
  fullHadith: string; excerptNote: string; events: string; translationPending: string; seeAlso: string
}> = {
  en: {
    back: '← Hadith Reels',
    explanation: 'Explanation of the hadith',
    words: 'Meanings of words',
    lessons: 'Lessons from the hadith',
    occasion: 'Occasion of the hadith',
    sourceOf: 'Explanation source',
    verbatim: 'Quoted as published, without changes.',
    references: 'References of the explanation',
    original: 'Open at the source ↗',
    noLang: 'This explanation is not available in English yet. It is available in:',
    noExplanation: 'An explanation for this hadith has not been added yet. We publish only explanations quoted from named scholars and sources.',
    checkSource: 'Check the hadith ↗',
    translationFallback: 'Shown in Russian: no Tajik translation yet.',
    fullHadith: 'Full text of the hadith',
    excerptNote: 'The reel narrates part of this hadith.',
    events: 'Related events',
    translationPending: 'A translation will be added after review.',
    seeAlso: 'See also',
  },
  ru: {
    back: '← Hadith Reels',
    explanation: 'Разъяснение хадиса',
    words: 'Значение слов',
    lessons: 'Уроки хадиса',
    occasion: 'Повод хадиса',
    sourceOf: 'Источник разъяснения',
    verbatim: 'Приводится так, как опубликовано, без изменений.',
    references: 'Источники разъяснения',
    original: 'Открыть в источнике ↗',
    noLang: 'На русском это разъяснение пока недоступно. Есть на языках:',
    noExplanation: 'Разъяснение к этому хадису ещё не добавлено. Мы публикуем только разъяснения, приведённые из трудов названных учёных и источников.',
    checkSource: 'Проверить хадис ↗',
    translationFallback: 'Показано на русском: таджикского перевода пока нет.',
    fullHadith: 'Полный текст хадиса',
    excerptNote: 'В рилсе прозвучала часть этого хадиса.',
    events: 'События, связанные с хадисом',
    translationPending: 'Перевод будет добавлен после проверки.',
    seeAlso: 'См. также',
  },
  uz: {
    back: '← Hadith Reels',
    explanation: 'Ҳадиснинг шарҳи',
    words: 'Иборалар шарҳи',
    lessons: 'Ҳадисдан олинадиган сабоқлар',
    occasion: 'Ҳадиснинг айтилиш сабаби',
    sourceOf: 'Шарҳ манбаси',
    verbatim: 'Манбада қандай бўлса, ўзгаришсиз келтирилди.',
    references: 'Шарҳ манбалари',
    original: 'Манбада очиш ↗',
    noLang: 'Бу шарҳ ўзбек тилида ҳозирча йўқ. Мавжуд тиллар:',
    noExplanation: 'Бу ҳадисга шарҳ ҳали қўшилмаган. Биз фақат номи айтилган олимлар ва манбалардан келтирилган шарҳларни чоп этамиз.',
    checkSource: 'Ҳадисни текшириш ↗',
    translationFallback: 'Рус тилида кўрсатилди: тожикча таржима ҳали йўқ.',
    fullHadith: 'Ҳадиснинг тўлиқ матни',
    excerptNote: 'Рилсда бу ҳадиснинг бир қисми ўқилган.',
    events: 'Ҳадисга оид воқеалар',
    translationPending: 'Таржимаси текширувдан ўтгач қўшилади.',
    seeAlso: 'Яна қаранг',
  },
  tj: {
    back: '← Hadith Reels',
    explanation: 'Шарҳи ҳадис',
    words: 'Маънои калимаҳо',
    lessons: 'Дарсҳо аз ҳадис',
    occasion: 'Сабаби ворид шудани ҳадис',
    sourceOf: 'Манбаи шарҳ',
    verbatim: 'Чӣ тавре ки нашр шудааст, бе тағйир оварда шуд.',
    references: 'Манбаъҳои шарҳ',
    original: 'Дар манбаъ кушодан ↗',
    noLang: 'Ин шарҳ ҳоло бо забони тоҷикӣ нест. Бо ин забонҳо ҳаст:',
    noExplanation: 'Шарҳи ин ҳадис ҳоло илова нашудааст. Мо танҳо шарҳҳоеро нашр мекунем, ки аз уламо ва манбаъҳои маълум оварда шудаанд.',
    checkSource: 'Санҷидани ҳадис ↗',
    translationFallback: 'Бо забони русӣ нишон дода шуд: тарҷумаи тоҷикӣ ҳоло нест.',
    fullHadith: 'Матни пурраи ҳадис',
    excerptNote: 'Дар рилс қисмате аз ин ҳадис хонда шуд.',
    events: 'Воқеаҳои марбут ба ҳадис',
    translationPending: 'Тарҷума пас аз санҷиш илова мешавад.',
    seeAlso: 'Инчунин нигаред',
  },
}
