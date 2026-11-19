// app/books/[book]/[lang]/[vol]/[sec]/page.tsx - one reading section.
// The HTML is built from the translation Markdown by scripts/build-books.py (no raw HTML
// in the source; translator comments dropped). Reading settings, bookmarks and notes are
// kept in the reader's own browser (components/books/BookReader.tsx).
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { BOOKS, BOOKS_UI, canRead, loadManifest, loadSection, pickUi } from '@/lib/books'
import BookReader from '@/components/books/BookReader'

export const dynamic = 'force-dynamic'

type Params = Promise<{ book: string; lang: string; vol: string; sec: string }>

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { book, lang, vol } = await params
  const b = BOOKS[book]
  if (!b) return {}
  const m = await loadManifest(book, lang, Number(vol))
  return {
    title: `${m?.title ?? b.title[pickUi(lang)]} · Hadith Reels`,
    robots: b.public ? undefined : { index: false, follow: false },
  }
}

export default async function ReadSection({ params }: { params: Params }) {
  const { book, lang, vol, sec } = await params
  const b = BOOKS[book]
  if (!b || !(await canRead(book))) notFound()
  const v = Number(vol), s = Number(sec)
  const [m, section] = await Promise.all([loadManifest(book, lang, v), loadSection(book, lang, v, s)])
  if (!m || !section) notFound()
  const ui = pickUi(lang)
  const total = m.sections.length

  return (
    <BookReader
      book={book} lang={lang} vol={v} sec={s} total={total}
      bookTitle={b.title[ui]} volumeTitle={m.title} sectionTitle={section.title}
      html={section.html} footnotes={section.footnotes}
      closed={!b.public} ui={BOOKS_UI[ui]} htmlLang={ui === 'tj' ? 'tg' : ui}
    />
  )
}
