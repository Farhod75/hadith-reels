'use client'
// "Continue" - back to where this reader stopped in this book and language.
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { loadPosition, type Position } from './storage'

export default function ResumeLink({ book, lang, label }: { book: string; lang: string; label: string }) {
  const [pos, setPos] = useState<Position | null>(null)
  useEffect(() => { setPos(loadPosition(book, lang)) }, [book, lang])
  if (!pos) return null
  return (
    <Link href={`/books/${book}/${lang}/${pos.vol}/${pos.sec}#p-${pos.idx}`} data-testid="resume"
      className="inline-block text-sm px-4 py-2 rounded-xl bg-indigo-700 text-white hover:bg-indigo-800">
      ▶ {label} · {pos.vol}.{pos.sec}
    </Link>
  )
}
