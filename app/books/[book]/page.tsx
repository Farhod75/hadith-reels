// app/books/[book]/page.tsx - /books/<book> goes to the book's first language.
import { notFound, redirect } from 'next/navigation'
import { BOOKS } from '@/lib/books'

export default async function BookIndex({ params }: { params: Promise<{ book: string }> }) {
  const { book } = await params
  const b = BOOKS[book]
  if (!b) notFound()
  redirect(`/books/${book}/${b.langs[0]}`)
}
