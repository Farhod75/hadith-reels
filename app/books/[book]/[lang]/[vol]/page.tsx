// app/books/[book]/[lang]/[vol]/page.tsx - one volume's table of contents.
import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { BOOKS, BOOKS_UI, canRead, loadManifest, pickUi } from '@/lib/books'

export const dynamic = 'force-dynamic'

type Params = Promise<{ book: string; lang: string; vol: string }>

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { book } = await params
  const b = BOOKS[book]
  return b && !b.public ? { robots: { index: false, follow: false } } : {}
}

export default async function VolumeToc({ params }: { params: Params }) {
  const { book, lang, vol } = await params
  const b = BOOKS[book]
  if (!b || !(await canRead(book))) notFound()
  const m = await loadManifest(book, lang, Number(vol))
  if (!m) notFound()
  const ui = pickUi(lang)
  const t = BOOKS_UI[ui]
  const base = `/books/${book}/${lang}/${m.volume}`

  return (
    <main lang={ui === 'tj' ? 'tg' : ui} className="min-h-screen bg-stone-50">
      <div className="max-w-3xl mx-auto px-4 py-6">
        <nav className="mb-6"><Link href={`/books/${book}/${lang}`} className="text-sm text-indigo-700 hover:underline">{t.back}</Link></nav>
        <p className="text-sm text-gray-500">{b.title[ui]} · {t.volume} {m.volume}</p>
        <h1 className="text-2xl font-bold text-gray-900 mb-5">{m.title}</h1>
        <Link href={`${base}/1`} className="inline-block mb-5 text-sm px-4 py-2 rounded-xl bg-indigo-700 text-white hover:bg-indigo-800">
          📖 {t.read}
        </Link>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">{t.contents}</h2>
        <ul className="bg-white border border-gray-200 rounded-xl divide-y divide-gray-100">
          {m.toc.map(item => (
            <li key={item.id} style={{ paddingLeft: `${(item.level - 1) * 1.1 + 1}rem` }} className="pr-4 py-2">
              <Link href={`${base}/${item.section}#${item.id}`}
                className={`hover:text-indigo-700 ${item.level === 1 ? 'font-semibold text-gray-900' : 'text-gray-700 text-sm'}`}>
                {item.title}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </main>
  )
}
