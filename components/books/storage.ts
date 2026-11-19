// components/books/storage.ts - what the reader keeps in the browser (localStorage).
// Nothing here leaves the device: no account, no server copy. Every read and write is
// wrapped, because storage can be full, disabled or absent (private mode).

export interface ReaderSettings { size: number; line: number; theme: 'light' | 'sepia' | 'dark'; font: 'serif' | 'sans' }
export interface Mark { vol: number; sec: number; idx: number; excerpt: string; note: string; at: number }
export interface Position { vol: number; sec: number; idx: number; at: number }

export const DEFAULT_SETTINGS: ReaderSettings = { size: 19, line: 1.75, theme: 'sepia', font: 'serif' }

const SETTINGS_KEY = 'hr-books-settings'
const marksKey = (book: string, lang: string) => `hr-books-marks:${book}:${lang}`
const posKey = (book: string, lang: string) => `hr-books-pos:${book}:${lang}`

function get<T>(key: string, fallback: T): T {
  try {
    const v = window.localStorage.getItem(key)
    return v ? { ...fallback, ...JSON.parse(v) } : fallback
  } catch { return fallback }
}
function getArr<T>(key: string): T[] {
  try {
    const v = window.localStorage.getItem(key)
    const a = v ? JSON.parse(v) : []
    return Array.isArray(a) ? a : []
  } catch { return [] }
}
function set(key: string, value: unknown) {
  try { window.localStorage.setItem(key, JSON.stringify(value)) } catch { /* storage unavailable */ }
}

export const loadSettings = () => get<ReaderSettings>(SETTINGS_KEY, DEFAULT_SETTINGS)
export const saveSettings = (s: ReaderSettings) => set(SETTINGS_KEY, s)

export const loadMarks = (book: string, lang: string) => getArr<Mark>(marksKey(book, lang))
export const saveMarks = (book: string, lang: string, m: Mark[]) => set(marksKey(book, lang), m)

export function loadPosition(book: string, lang: string): Position | null {
  try {
    const v = window.localStorage.getItem(posKey(book, lang))
    return v ? JSON.parse(v) as Position : null
  } catch { return null }
}
export const savePosition = (book: string, lang: string, p: Position) => set(posKey(book, lang), p)
