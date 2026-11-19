// app/books/page.tsx - the Books / Audiobooks section (lib/books.ts).
import type { Metadata } from 'next'
import Link from 'next/link'
import { BOOKS, BOOKS_UI, LANG_LABEL, isAdminViewer, pickUi, type UiLang } from '@/lib/books'

export const dynamic = 'force-dynamic'

type Search = Promise<{ lang?: string; tab?: string }>

export async function generateMetadata({ searchParams }: { searchParams: Search }): Promise<Metadata> {
  const ui = pickUi((await searchParams).lang)
  return { title: `${BOOKS_UI[ui].books} · Hadith Reels` }
}

const UI_LANGS: UiLang[] = ['uz', 'tj', 'ru', 'en']

export default async function BooksPage({ searchParams }: { searchParams: Search }) {
  const sp = await searchParams
  const ui = pickUi(sp.lang)
  const t = BOOKS_UI[ui]
  const tab = sp.tab === 'audio' ? 'audio' : 'read'
  const admin = await isAdminViewer()
  const books = Object.values(BOOKS).filter(b => b.public || admin)

  return (
    <main className="min-h-screen bg-stone-50">
      <div className="max-w-3xl mx-auto px-4 py-6">
        <nav className="flex items-center justify-between gap-3 mb-6">
          <Link href="/" className="text-sm text-indigo-700 hover:underline">← {t.home}</Link>
          <div className="flex gap-1">
            {UI_LANGS.map(l => (
              <Link key={l} href={`/books?lang=${l}&tab=${tab}`}
                className={`text-xs px-2.5 py-1 rounded-lg border ${l === ui
                  ? 'bg-indigo-700 text-white border-indigo-700'
                  : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}>
                {l.toUpperCase()}
              </Link>
            ))}
          </div>
        </nav>

        <div className="flex gap-2 mb-6" role="tablist">
          {(['read', 'audio'] as const).map(k => (
            <Link key={k} href={`/books?lang=${ui}&tab=${k}`} role="tab" aria-selected={tab === k}
              className={`px-4 py-2 rounded-xl text-sm font-semibold border ${tab === k
                ? 'bg-indigo-700 text-white border-indigo-700'
                : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'}`}>
              {k === 'read' ? `📖 ${t.books}` : `🎧 ${t.audio}`}
            </Link>
          ))}
        </div>

        {tab === 'audio' ? (
          <p className="text-gray-600 bg-white border border-gray-200 rounded-xl p-5">{t.audioSoon}</p>
        ) : books.length === 0 ? (
          <p className="text-gray-600 bg-white border border-gray-200 rounded-xl p-5" data-testid="no-books">{t.noBooks}</p>
        ) : (
          <ul className="space-y-3">
            {books.map(b => (
              <li key={b.slug} className="bg-white border border-gray-200 rounded-2xl p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">{b.title[ui]}</h2>
                    <p className="text-sm text-gray-500">{b.author[ui]}</p>
                  </div>
                  {!b.public && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 whitespace-nowrap">
                      🔒 {t.closed}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-700 mt-2">{b.about[ui]}</p>
                <div className="flex flex-wrap gap-2 mt-4">
                  {b.langs.map(l => (
                    <Link key={l} href={`/books/${b.slug}/${l}`}
                      className="text-sm px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-800 hover:bg-indigo-100">
                      {t.read}: {LANG_LABEL[l]}
                    </Link>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  )
}
