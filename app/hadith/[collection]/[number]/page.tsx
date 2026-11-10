// app/hadith/[collection]/[number]/page.tsx
// P387: one hadith, fully - the matn, the translation the reel narrated, and what
// a named source says about it, quoted verbatim with credit. The reel's caption
// links here. Nothing on this page is generated: the explanation comes from
// content/explanations/<slug>.json (scripts/fetch-explanation.py), the hadith from
// the library row. No explanation file -> the page says so; it never fills the gap.

import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { createClient } from '@supabase/supabase-js'
import { UI } from '@/lib/ui-strings'
import { COLLECTIONS, NARRATORS } from '@/lib/refs'
import { EXPLANATIONS } from '@/lib/explanations-registry'
import { EXPLAIN_UI, collectionFromSlug, type SiteLang, type Explanation } from '@/lib/explanations'

export const dynamic = 'force-dynamic'

const LANGS: { code: SiteLang; label: string }[] = [
  { code: 'en', label: 'EN' }, { code: 'ru', label: 'RU' },
  { code: 'uz', label: 'UZ' }, { code: 'tj', label: 'TJ' },
]
const LANG_NAMES: Record<SiteLang, string> = { en: 'English', ru: 'Русский', uz: 'Ўзбекча', tj: 'Тоҷикӣ' }

interface Row {
  id: string; collection: string; hadith_number: string; narrator: string; grade: string
  text_arabic?: string; text_english?: string; text_russian?: string
  text_uzbek?: string; text_uzbek_cyrillic?: string; text_tajik?: string; source_url?: string
}

type Params = Promise<{ collection: string; number: string }>
type Search = Promise<{ lang?: string }>

function pickLang(v?: string): SiteLang {
  return (['en', 'ru', 'uz', 'tj'] as const).find(l => l === v) ?? 'en'
}

function local(table: Record<string, { ru: string; uz: string; tj: string }>, name: string, lang: SiteLang) {
  return lang === 'en' ? name : (table[name]?.[lang] ?? name)
}

// Same choice as /api/reels: UZ Cyrillic first (P169), TJ falls back to RU, marked.
function translation(row: Row, lang: SiteLang): { text: string; fallback: boolean } {
  if (lang === 'uz') return { text: row.text_uzbek_cyrillic || row.text_uzbek || row.text_english || '', fallback: false }
  if (lang === 'tj') return { text: row.text_tajik || row.text_russian || '', fallback: !row.text_tajik }
  if (lang === 'ru') return { text: row.text_russian || row.text_english || '', fallback: false }
  return { text: row.text_english || '', fallback: false }
}

async function libraryRow(explanation: Explanation | undefined, collection: string, number: string) {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !key) return null
  const sb = createClient(url, key)
  const cols = 'id, collection, hadith_number, narrator, grade, text_arabic, text_english, text_russian, text_uzbek, text_uzbek_cyrillic, text_tajik, source_url'
  const q = explanation
    ? sb.from('hadith_library').select(cols).eq('id', explanation.library_id)
    : sb.from('hadith_library').select(cols).eq('collection', collection).eq('hadith_number', number)
        .in('grade', ['sahih', 'hasan']).limit(1)
  const { data, error } = await q
  if (error || !data?.length) return null
  return data[0] as Row
}

async function load(params: Params) {
  const { collection: cslug, number } = await params
  const collection = collectionFromSlug(cslug)
  if (!collection || !/^[0-9]+[a-z]?$/.test(number)) return null
  const explanation = EXPLANATIONS[`${cslug.toLowerCase()}-${number}`]
  const row = await libraryRow(explanation, collection, number)
  if (!row && !explanation) return null
  return { collection, number, explanation, row }
}

export async function generateMetadata({ params, searchParams }: { params: Params; searchParams: Search }): Promise<Metadata> {
  const d = await load(params)
  if (!d) return { title: 'Hadith Reels' }
  const lang = pickLang((await searchParams).lang)
  const name = `${local(COLLECTIONS, d.collection, lang)} №${d.number}`
  const ex = d.explanation?.commentaries[0]?.langs[lang]?.explanation
  return {
    title: `${name} — ${EXPLAIN_UI[lang].explanation} · Hadith Reels`,
    description: ex ? ex.replace(/\s+/g, ' ').slice(0, 160) : undefined,
  }
}

export default async function HadithPage({ params, searchParams }: { params: Params; searchParams: Search }) {
  const d = await load(params)
  if (!d) notFound()
  const lang = pickLang((await searchParams).lang)
  const t = EXPLAIN_UI[lang]
  const { row, explanation, collection, number } = d
  const tr = row ? translation(row, lang) : null
  const self = `/hadith/${(await params).collection.toLowerCase()}/${number}`

  return (
    <main lang={UI[lang].htmlLang} className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-6">
        <nav className="flex items-center justify-between gap-3 mb-6">
          <Link href="/" className="text-sm text-indigo-700 hover:underline">{t.back}</Link>
          <div className="flex gap-1">
            {LANGS.map(l => (
              <Link key={l.code} href={`${self}?lang=${l.code}`}
                className={`text-xs px-2.5 py-1 rounded-lg border ${l.code === lang
                  ? 'bg-indigo-700 text-white border-indigo-700'
                  : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}>
                {l.label}
              </Link>
            ))}
          </div>
        </nav>

        <header className="mb-4">
          <h1 className="text-xl font-bold text-gray-900">
            {local(COLLECTIONS, collection, lang)} №{number}
          </h1>
          {row && (
            <p className="text-sm text-gray-500 mt-1">
              {local(NARRATORS, row.narrator, lang)} · {UI[lang].gradeLabel[row.grade as 'sahih' | 'hasan'] ?? row.grade}
            </p>
          )}
        </header>

        {row?.text_arabic && (
          <div dir="rtl" lang="ar"
            className="text-xl leading-loose text-right text-gray-900 p-4 bg-amber-50 rounded-xl border border-amber-100 mb-3">
            {row.text_arabic}
          </div>
        )}
        {tr?.text && (
          <div className="mb-6">
            <p className="text-base text-gray-800 leading-relaxed">{tr.text}</p>
            {tr.fallback && <p className="text-xs text-gray-400 mt-1">{t.translationFallback}</p>}
          </div>
        )}

        {!explanation && (
          <p className="text-sm text-gray-600 bg-white border border-gray-200 rounded-xl p-4" data-testid="no-explanation">
            {t.noExplanation}
          </p>
        )}

        {explanation?.occasion?.text[lang] && (
          <section className="mb-6" data-testid="occasion">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">{t.occasion}</h2>
            <p className="text-gray-800 leading-relaxed whitespace-pre-line">{explanation.occasion.text[lang]}</p>
            <a href={explanation.occasion.url} target="_blank" rel="noopener noreferrer"
              className="text-xs text-indigo-700 hover:underline">{explanation.occasion.source} ↗</a>
          </section>
        )}

        {explanation?.commentaries.map(c => {
          const x = c.langs[lang]
          if (!x) {
            const have = LANGS.filter(l => c.langs[l.code])
            return (
              <p key={c.source + c.source_id} className="text-sm text-gray-600 mb-6">
                {t.noLang}{' '}
                {have.map((l, i) => (
                  <span key={l.code}>{i > 0 && ', '}
                    <Link href={`${self}?lang=${l.code}`} className="text-indigo-700 hover:underline">{LANG_NAMES[l.code]}</Link>
                  </span>
                ))}
              </p>
            )
          }
          return (
            <article key={c.source + c.source_id} className="space-y-6 mb-8" data-testid="explanation">
              {x.word_meanings.length > 0 && (
                <section>
                  <h2 className="text-lg font-semibold text-gray-900 mb-2">{t.words}</h2>
                  <ul className="space-y-1 text-gray-800">
                    {x.word_meanings.map((w, i) => {
                      const o = w as { word?: string; meaning?: string }
                      return <li key={i}><b>{o.word}</b> — {o.meaning}</li>
                    })}
                  </ul>
                </section>
              )}

              <section>
                <h2 className="text-lg font-semibold text-gray-900 mb-2">{t.explanation}</h2>
                <p className="text-gray-800 leading-relaxed whitespace-pre-line">{x.explanation}</p>
              </section>

              {x.lessons.length > 0 && (
                <section>
                  <h2 className="text-lg font-semibold text-gray-900 mb-2">{t.lessons}</h2>
                  <ol className="list-decimal ps-5 space-y-2 text-gray-800 leading-relaxed">
                    {x.lessons.map((l, i) => <li key={i}>{l}</li>)}
                  </ol>
                </section>
              )}

              <footer className="text-sm bg-white border border-gray-200 rounded-xl p-4 space-y-2" data-testid="credit">
                <p>
                  <span className="text-gray-500">{t.sourceOf}: </span>
                  <a href={x.url} target="_blank" rel="noopener noreferrer" className="text-indigo-700 hover:underline">
                    {c.publisher}, №{c.source_id}
                  </a>
                  <span className="text-gray-500"> · {t.verbatim}</span>
                </p>
                {c.references_ar && (
                  <details>
                    <summary className="cursor-pointer text-gray-500">{t.references}</summary>
                    <p dir="rtl" lang="ar" className="text-right whitespace-pre-line text-gray-700 mt-2">{c.references_ar}</p>
                  </details>
                )}
              </footer>
            </article>
          )
        })}

        <div className="flex gap-2 flex-wrap">
          {row?.source_url && (
            <a href={row.source_url} target="_blank" rel="noopener noreferrer"
              className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50">
              {UI[lang].source}
            </a>
          )}
          <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
            className="text-xs px-3 py-1.5 rounded-lg border border-amber-200 bg-white text-amber-700 hover:bg-amber-50">
            {t.checkSource}
          </a>
        </div>
      </div>
    </main>
  )
}
