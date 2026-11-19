// app/books/asset/[book]/[lang]/[file]/route.ts - images inside book text, behind the
// same access rule as the text itself (lib/books.ts canRead).
import { NextResponse } from 'next/server'
import { canRead, loadAsset } from '@/lib/books'

type Params = Promise<{ book: string; lang: string; file: string }>

export async function GET(_req: Request, { params }: { params: Params }) {
  const { book, lang, file } = await params
  if (!(await canRead(book))) return new NextResponse('Not found', { status: 404 })
  const buf = await loadAsset(book, lang, file)
  if (!buf) return new NextResponse('Not found', { status: 404 })
  const type = file.endsWith('.png') ? 'image/png' : 'image/jpeg'
  return new NextResponse(new Uint8Array(buf), {
    headers: { 'Content-Type': type, 'Cache-Control': 'private, max-age=3600', 'X-Robots-Tag': 'noindex' },
  })
}
