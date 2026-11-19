// lib/books.ts
// The /books section: book translations read on the site (and, later, audiobooks).
// Text comes from content/books/<book>/<lang>/v<NN>/ - built by scripts/build-books.py
// from the translation repo, never edited here.
//
// ACCESS: a book is readable by everyone only when BOOKS[book].public is true. Until
// then only an admin session (the /admin sign-in, lib/admin-session.ts) or `next dev`
// on localhost can open it, and every page of it is noindex. al-Bidaya stays closed
// until Darussalam (publisher of the English source) answers the permission request.

import fs from 'node:fs/promises'
import path from 'node:path'
import { cookies, headers } from 'next/headers'
import { ADMIN_COOKIE, verifySessionToken } from '@/lib/admin-session'

export type BookLang = 'uz' | 'tj' | 'ru' | 'en'
export type UiLang = BookLang

export interface BookInfo {
  slug: string
  public: boolean
  langs: BookLang[]
  title: Record<UiLang, string>
  author: Record<UiLang, string>
  about: Record<UiLang, string>
}

export const BOOKS: Record<string, BookInfo> = {
  'al-bidaya': {
    slug: 'al-bidaya',
    public: false,
    langs: ['uz', 'tj'],
    title: {
      uz: 'Ал-Бидоя ван-Ниҳоя',
      tj: 'Ал-Бидоя ва-н-Ниҳоя',
      ru: 'Аль-Бидая ва-н-Нихая',
      en: 'Al-Bidaya wan-Nihaya',
    },
    author: { uz: 'Ибн Касир', tj: 'Ибни Касир', ru: 'Ибн Касир', en: 'Ibn Kathir' },
    about: {
      uz: 'Етти китоб: яратилишдан пайғамбарлар қиссаларигача. Инглизча қисқартирилган нашрдан таржима.',
      tj: 'Ҳафт китоб: аз офариниш то қиссаҳои паёмбарон. Тарҷума аз нашри мухтасари англисӣ.',
      ru: 'Семь книг: от сотворения мира до историй пророков. Перевод с сокращённого английского издания.',
      en: 'Seven books: from the creation to the stories of the prophets. Translated from the abridged English edition.',
    },
  },
}

export const LANG_LABEL: Record<BookLang, string> = { uz: 'Ўзбекча', tj: 'Тоҷикӣ', ru: 'Русский', en: 'English' }

export const BOOKS_UI: Record<UiLang, Record<string, string>> = {
  uz: {
    settings: 'Матн созламалари', fontSize: 'Ҳарф ўлчами', lineSpacing: 'Қатор оралиғи', theme: 'Фон', light: 'Оқ', sepia: 'Сарғиш', dark: 'Тунги', font: 'Шрифт', serif: 'Китобий', sans: 'Оддий',
    bookmark: 'Хатчўп', note: 'Изоҳ', save: 'Сақлаш', cancel: 'Бекор қилиш', del: 'Ўчириш', marks: 'Хатчўплар ва изоҳлар', noMarks: 'Ҳали хатчўп йўқ. Хатбошига босинг.', notePlaceholder: 'Изоҳингизни ёзинг…', of: 'дан', tapHint: 'Хатчўп ёки изоҳ учун хатбошига босинг', saved: 'Сизнинг қурилмангизда сақланади',
    books: 'Китоблар', audio: 'Аудиокитоблар', read: 'Ўқиш', contents: 'Мундарижа', volume: 'Китоб',
    back: '← Орқага', home: 'Бош саҳифа', closed: 'Ёпиқ: фақат администратор кўради',
    soon: 'Тез орада', audioSoon: 'Аудиокитоблар тайёрланмоқда.', noBooks: 'Ҳозирча очиқ китоблар йўқ. Тез орада.',
    prev: '← Олдинги', next: 'Кейинги →', continue: 'Давом эттириш', sections: 'бўлим',
    footnotes: 'Изоҳлар', translatedFrom: 'Таржима манбаи',
  },
  tj: {
    settings: 'Танзимоти матн', fontSize: 'Андозаи ҳарф', lineSpacing: 'Фосилаи сатр', theme: 'Замина', light: 'Сафед', sepia: 'Зардча', dark: 'Шабона', font: 'Ҳуруф', serif: 'Китобӣ', sans: 'Одӣ',
    bookmark: 'Хатчӯб', note: 'Эзоҳ', save: 'Нигоҳ доштан', cancel: 'Бекор', del: 'Нест кардан', marks: 'Хатчӯбҳо ва эзоҳҳо', noMarks: 'Ҳоло хатчӯб нест. Ба сарсатр пахш кунед.', notePlaceholder: 'Эзоҳи худро нависед…', of: 'аз', tapHint: 'Барои хатчӯб ё эзоҳ ба сарсатр пахш кунед', saved: 'Дар дастгоҳи шумо нигоҳ дошта мешавад',
    books: 'Китобҳо', audio: 'Китобҳои аудиоӣ', read: 'Хондан', contents: 'Мундариҷа', volume: 'Китоб',
    back: '← Бозгашт', home: 'Саҳифаи асосӣ', closed: 'Пӯшида: танҳо маъмур мебинад',
    soon: 'Ба наздикӣ', audioSoon: 'Китобҳои аудиоӣ омода мешаванд.', noBooks: 'Ҳоло китобҳои кушода нест. Ба наздикӣ.',
    prev: '← Қаблӣ', next: 'Баъдӣ →', continue: 'Идома додан', sections: 'қисм',
    footnotes: 'Эзоҳҳо', translatedFrom: 'Манбаи тарҷума',
  },
  ru: {
    settings: 'Настройки текста', fontSize: 'Размер шрифта', lineSpacing: 'Межстрочный интервал', theme: 'Фон', light: 'Белый', sepia: 'Сепия', dark: 'Ночь', font: 'Шрифт', serif: 'Книжный', sans: 'Простой',
    bookmark: 'Закладка', note: 'Заметка', save: 'Сохранить', cancel: 'Отмена', del: 'Удалить', marks: 'Закладки и заметки', noMarks: 'Пока нет закладок. Нажмите на абзац.', notePlaceholder: 'Ваша заметка…', of: 'из', tapHint: 'Нажмите на абзац, чтобы поставить закладку или заметку', saved: 'Хранится на вашем устройстве',
    books: 'Книги', audio: 'Аудиокниги', read: 'Читать', contents: 'Оглавление', volume: 'Книга',
    back: '← Назад', home: 'Главная', closed: 'Закрыто: видит только администратор',
    soon: 'Скоро', audioSoon: 'Аудиокниги готовятся.', noBooks: 'Пока нет открытых книг. Скоро.',
    prev: '← Назад', next: 'Дальше →', continue: 'Продолжить', sections: 'частей',
    footnotes: 'Примечания', translatedFrom: 'Источник перевода',
  },
  en: {
    settings: 'Text settings', fontSize: 'Font size', lineSpacing: 'Line spacing', theme: 'Background', light: 'White', sepia: 'Sepia', dark: 'Night', font: 'Font', serif: 'Book', sans: 'Plain',
    bookmark: 'Bookmark', note: 'Note', save: 'Save', cancel: 'Cancel', del: 'Delete', marks: 'Bookmarks and notes', noMarks: 'No bookmarks yet. Tap a paragraph.', notePlaceholder: 'Your note…', of: 'of', tapHint: 'Tap a paragraph to bookmark it or add a note', saved: 'Kept on your device',
    books: 'Books', audio: 'Audiobooks', read: 'Read', contents: 'Contents', volume: 'Book',
    back: '← Back', home: 'Home', closed: 'Closed: admin only',
    soon: 'Soon', audioSoon: 'Audiobooks are being prepared.', noBooks: 'No open books yet. Coming soon.',
    prev: '← Previous', next: 'Next →', continue: 'Continue', sections: 'parts',
    footnotes: 'Notes', translatedFrom: 'Translated from',
  },
}

export function pickUi(v?: string): UiLang {
  return (['uz', 'tj', 'ru', 'en'] as const).find(l => l === v) ?? 'uz'
}

const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]', '::1'])

/** Admin session (or `next dev` on localhost) - the same rule as the admin routes. */
export async function isAdminViewer(): Promise<boolean> {
  if (process.env.NODE_ENV === 'development' && !process.env.VERCEL) {
    const host = ((await headers()).get('host') || '').split(':')[0].toLowerCase()
    if (LOCAL_HOSTS.has(host)) return true
  }
  return verifySessionToken((await cookies()).get(ADMIN_COOKIE)?.value)
}

export async function canRead(book: string): Promise<boolean> {
  const b = BOOKS[book]
  if (!b) return false
  return b.public || (await isAdminViewer())
}

const ROOT = path.join(process.cwd(), 'content', 'books')

// Book texts are not in the public repo (.gitignore). Locally they are read from
// content/books; in production from the PRIVATE Supabase Storage bucket 'books',
// with the service-role client, and only after canRead() has passed.
const BUCKET = 'books'

async function readFile(parts: string[]): Promise<Buffer | null> {
  try {
    return await fs.readFile(path.join(ROOT, ...parts))
  } catch { /* not on disk - try storage */ }
  try {
    const { supabaseAdmin } = await import('./supabase')
    const { data, error } = await supabaseAdmin.storage.from(BUCKET).download(parts.join('/'))
    if (error || !data) return null
    return Buffer.from(await data.arrayBuffer())
  } catch {
    return null
  }
}

async function readJson<T>(...parts: string[]): Promise<T | null> {
  const buf = await readFile(parts)
  if (!buf) return null
  try { return JSON.parse(buf.toString('utf-8')) as T } catch { return null }
}

export interface Catalog { book: string; languages: { lang: BookLang; volumes: { volume: number; title: string; sections: number }[] }[] }
export interface TocItem { level: number; title: string; section: number; id: string }
export interface Manifest {
  book: string; lang: BookLang; volume: number; title: string; source_file: string
  sections: { n: number; title: string }[]; toc: TocItem[]
}
export interface Section { n: number; title: string; html: string; footnotes: { n: number; html: string }[] }

const SAFE = /^[a-z0-9-]+$/

export const vdir = (v: number) => `v${String(v).padStart(2, '0')}`

export function loadCatalog(book: string) {
  if (!SAFE.test(book)) return Promise.resolve(null)
  return readJson<Catalog>(book, 'catalog.json')
}

export function loadManifest(book: string, lang: string, vol: number) {
  if (!SAFE.test(book) || !SAFE.test(lang) || !Number.isInteger(vol)) return Promise.resolve(null)
  return readJson<Manifest>(book, lang, vdir(vol), 'manifest.json')
}

export function loadSection(book: string, lang: string, vol: number, sec: number) {
  if (!SAFE.test(book) || !SAFE.test(lang) || !Number.isInteger(vol) || !Number.isInteger(sec)) return Promise.resolve(null)
  return readJson<Section>(book, lang, vdir(vol), `s${String(sec).padStart(3, '0')}.json`)
}

export async function loadAsset(book: string, lang: string, file: string): Promise<Buffer | null> {
  if (!SAFE.test(book) || !SAFE.test(lang) || !/^[A-Za-z0-9_.-]+\.(png|jpe?g)$/.test(file)) return null
  return readFile([book, lang, 'assets', file])
}
