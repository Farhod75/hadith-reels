// app/books/[book]/[lang]/page.tsx - the volumes of one book in one language.
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { BOOKS, BOOKS_UI, canRead, loadCatalog, pickUi } from '@/lib/books'
import ResumeLink from '@/components/books/ResumeLink'

export const dynamic = 'force-dynamic'

type Params = Promise<{ book: string; lang: string }>

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { book, lang } = await params
  const b = BOOKS[book]
  if (!b) return {}
  return { title: `${b.title[pickUi(lang)]} · Hadith Reels`, robots: b.public ? undefined : { index: false, follow: false } }
}

export default async function BookVolumes({ params }: { params: Params }) {
  const { book, lang } = await params
  const b = BOOKS[book]
  if (!b || !b.langs.includes(lang as never) || !(await canRead(book))) notFound()
  const cat = await loadCatalog(book)
  const vols = cat?.languages.find(l => l.lang === lang)?.volumes ?? []
  const ui = pickUi(lang)
  const t = BOOKS_UI[ui]

  return (
    <main lang={ui === 'tj' ? 'tg' : ui} className="min-h-screen bg-stone-50">
      <div className="max-w-3xl mx-auto px-4 py-6">
        <nav className="mb-6"><Link href={`/books?lang=${ui}`} className="text-sm text-indigo-700 hover:underline">{t.back}</Link></nav>
        <h1 className="text-2xl font-bold text-gray-900">{b.title[ui]}</h1>
        <p className="text-sm text-gray-500 mb-4">{b.author[ui]}</p>
        {!b.public && <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">🔒 {t.closed}</p>}
        <ResumeLink book={book} lang={lang} label={t.continue} />
        <ol className="space-y-2 mt-4">
          {vols.map(v => (
            <li key={v.volume}>
              <Link href={`/books/${book}/${lang}/${v.volume}`}
                className="flex items-center justify-between gap-3 bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-indigo-300">
                <span><span className="text-gray-400 mr-2">{t.volume} {v.volume}.</span>
                  <span className="font-semibold text-gray-900">{v.title}</span></span>
                <span className="text-xs text-gray-400 whitespace-nowrap">{v.sections} {t.sections}</span>
              </Link>
            </li>
          ))}
        </ol>
      </div>
    </main>
  )
}
