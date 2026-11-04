'use client'

import { useState, useEffect, useRef } from 'react'
import { UI } from '@/lib/ui-strings'
import { TAG_CANONICAL, TAG_FORMS } from '@/lib/tags'
import { COLLECTIONS, NARRATORS } from '@/lib/refs'

// ─── Types ────────────────────────────────────────────────────────────────────
// P360: no 'ar'. AR is out of scope (P118) - nothing in the library is an Arabic
// translation to show, so the AR toggle displayed the ENGLISH text and Listen read it
// in English (the AR voice is a placeholder English voice). The Arabic matn is on
// every card regardless.
type Lang  = 'en' | 'uz' | 'ru' | 'tj'
type Grade = 'sahih' | 'hasan' | 'all'
type Tab   = 'browse' | 'watch'

interface Hadith {
  id: string
  text_arabic?: string
  text_english: string
  text_uzbek?: string
  text_russian?: string
  text_tajik?: string
  text_display?: string
  narrator: string
  collection: string
  hadith_number?: string
  grade: string
  tags?: string[]
  source_url?: string
}

interface PublishedReel {
  id: string
  title: string
  platform: 'youtube' | 'instagram' | 'tiktok' | 'telegram'
  embed_url?: string
  thumbnail?: string
  hadith_text: string
  style: 'adults' | 'kids'
  lang: Lang
  published_at: string
}

// ─── Constants ────────────────────────────────────────────────────────────────
const GRADE_COLORS: Record<string, string> = {
  sahih: 'bg-green-100 text-green-700 border-green-200',
  hasan: 'bg-yellow-100 text-yellow-700 border-yellow-200',
}

const LANGS: { code: Lang; flag: string; label: string }[] = [
  { code: 'en', flag: '🇬🇧', label: 'EN' },
  { code: 'uz', flag: '🇺🇿', label: 'UZ' },
  { code: 'ru', flag: '🇷🇺', label: 'RU' },
  { code: 'tj', flag: '🇹🇯', label: 'TJ' },
]

// P363: names and tags in the chosen language. English is the stored form;
// lib/refs.ts and lib/tags.ts carry the RU / UZ / TJ forms the captions already
// use. Anything without a form stays as stored rather than being guessed.
function localName(table: Record<string, { ru: string; uz: string; tj: string }>, name: string, lang: Lang) {
  return lang === 'en' ? name : (table[name]?.[lang] ?? name)
}
function localTag(tag: string, lang: Lang) {
  if (lang === 'en') return tag          // the stored tags ARE English; keep their detail
  const canon = TAG_CANONICAL[tag] ?? tag
  return TAG_FORMS[canon]?.[lang] ?? tag
}

// ─── TTS Button ───────────────────────────────────────────────────────────────
// P361: on the deployed site /api/tts needs an admin session (P353) and has no
// voice key, so "Listen" fell back to the browser's own robotic voice - Russian
// for Uzbek. Until a hadith has stored narration it offers no Listen there at
// all; on localhost (the operator's dev server) it narrates as before.
function isLocalHost() {
  if (typeof window === 'undefined') return false
  return ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname)
}

// P362: stored narration - each published set's story.mp3 (narrator + matn, in the
// voice chosen for that language), copied to Supabase Storage by
// scripts/publish-narration.py. index.json maps library id -> lang -> file.
const NARRATION_BASE =
  `${process.env.NEXT_PUBLIC_SUPABASE_URL ?? ''}/storage/v1/object/public/narration`
type NarrationIndex = Record<string, Partial<Record<Lang, { path: string }>>>

function TTSButton({ text, lang, audioUrl }: { text: string; lang: Lang; audioUrl?: string }) {
  const [playing, setPlaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const [local, setLocal]     = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  useEffect(() => { setLocal(isLocalHost()) }, [])

  async function toggle() {
    if (playing) {
      audioRef.current?.pause()
      window.speechSynthesis?.cancel()
      setPlaying(false)
      return
    }
    if (audioUrl) {
      // the recorded narration: same file everywhere, no per-click cost
      const audio = new Audio(audioUrl)
      audioRef.current = audio
      audio.onended = () => setPlaying(false)
      audio.play().then(() => setPlaying(true)).catch(() => setPlaying(false))
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.slice(0, 400), lang, style: 'adults' }),
      })
      if (!res.ok) throw new Error('TTS failed')
      const blob  = await res.blob()
      const url   = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio
      audio.play()
      setPlaying(true)
      audio.onended = () => setPlaying(false)
    } catch {
      // Browser fallback
      const utt  = new SpeechSynthesisUtterance(text.slice(0, 300))
      utt.lang   = lang === 'ru' || lang === 'tj' ? 'ru-RU'
                 : lang === 'uz' ? 'ru-RU'
                 : 'en-US'
      window.speechSynthesis.speak(utt)
      setPlaying(true)
      utt.onend = () => setPlaying(false)
    } finally {
      setLoading(false)
    }
  }

  if (!audioUrl && !local) return null
  return (
    <button onClick={toggle}
      className="text-xs px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-100 transition-colors flex items-center gap-1.5">
      {loading ? '⌛' : playing ? UI[lang].pause : UI[lang].listen}
    </button>
  )
}

// ─── Hadith Card ──────────────────────────────────────────────────────────────
function HadithCard({ hadith, lang, audioUrl }: { hadith: Hadith; lang: Lang; audioUrl?: string }) {
  const [copied, setCopied] = useState(false)
  const display = hadith.text_display || hadith.text_english

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-200 hover:shadow-sm transition-all">
      {/* Arabic */}
      {hadith.text_arabic && (
        <div className="text-base text-right leading-loose text-gray-800 mb-3 p-3 bg-amber-50 rounded-lg border border-amber-100" dir="rtl">
          {hadith.text_arabic}
        </div>
      )}

      {/* Translation */}
      <p className="text-sm text-gray-700 leading-relaxed mb-3" dir="auto">{display}</p>

      {/* Meta */}
      <div className="flex items-center gap-2 flex-wrap mb-3">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${GRADE_COLORS[hadith.grade] ?? 'bg-gray-100 text-gray-500 border-gray-200'}`}>
          {UI[lang].gradeLabel[hadith.grade as 'sahih' | 'hasan'] ?? hadith.grade}
        </span>
        <span className="text-xs text-gray-400">{localName(COLLECTIONS, hadith.collection, lang)}</span>
        {hadith.hadith_number && <span className="text-xs text-gray-400">#{hadith.hadith_number}</span>}
        <span className="text-xs text-gray-400 ml-auto">{localName(NARRATORS, hadith.narrator, lang)}</span>
      </div>

      {/* Tags */}
      {hadith.tags && hadith.tags.length > 0 && (
        <div className="flex gap-1 flex-wrap mb-3">
          {/* several English tags share one RU/UZ/TJ form (wife, husband -> marriage) */}
          {Array.from(new Set(hadith.tags.map(tag => localTag(tag, lang)))).slice(0, 5).map(tag => (
            <span key={tag} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 flex-wrap items-center">
        <TTSButton text={display} lang={lang} audioUrl={audioUrl} />
        <button
          onClick={() => { navigator.clipboard.writeText(display); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
          className="text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors">
          {copied ? UI[lang].copied : UI[lang].copy}
        </button>
        {hadith.source_url && (
          <a href={hadith.source_url} target="_blank" rel="noopener noreferrer"
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors">
            {UI[lang].source}
          </a>
        )}
        <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
          className="text-xs px-3 py-1.5 rounded-lg border border-amber-200 text-amber-700 hover:bg-amber-50 transition-colors ml-auto">
          {UI[lang].verify}
        </a>
      </div>
    </div>
  )
}
// Language-aware social links. Each platform falls back to `default` (the main
// channel) until a per-language playlist/channel URL is filled in. So links work
// today and improve as per-language content is added.
const SOCIAL_LINKS: Record<'youtube'|'instagram'|'telegram'|'tiktok', Partial<Record<Lang,string>> & { default: string }> = {
  youtube:   { default: 'https://www.youtube.com/@SahihHadithReels' },
  instagram: { default: 'https://www.instagram.com/SahihHadithReels' },
  telegram:  { default: 'https://t.me/SahihHadithReels' },
  tiktok:    { default: 'https://www.tiktok.com/@sahihhadithreels' },
}
const socialUrl = (platform: keyof typeof SOCIAL_LINKS, lang: Lang) =>
  SOCIAL_LINKS[platform][lang] ?? SOCIAL_LINKS[platform].default

function WatchTab({ lang }: { lang: Lang }) {
  return (
    <div className="space-y-4">
      {/* Coming soon card */}
      <div className="bg-gradient-to-br from-indigo-900 to-purple-900 rounded-2xl p-8 text-center text-white">
        <div className="text-5xl mb-4">🎬</div>
        <h2 className="text-xl font-bold mb-2">{UI[lang].watchTitle}</h2>
        <p className="text-indigo-200 text-sm mb-6 max-w-sm mx-auto">
          {UI[lang].watchDesc}
        </p>
        <div className="flex gap-3 justify-center flex-wrap">
          <a href={socialUrl('youtube', lang)} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors">
            ▶ YouTube
          </a>
          <a href={socialUrl('instagram', lang)} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white text-sm font-medium transition-colors">
            📸 Instagram
          </a>
          <a href={socialUrl('telegram', lang)} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium transition-colors">
            ✈️ Telegram
          </a>
          <a href={socialUrl('tiktok', lang)} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-black hover:bg-gray-900 text-white text-sm font-medium transition-colors">
            🎵 TikTok
          </a>
        </div>
      </div>

      {/* What to expect */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {/* P361: these four described the first plan for the channel - a dark style,
            a Ramadan series that was never made, five languages including Arabic.
            They now say what the reels actually are. */}
        {(['📖', '🐑', '🌍', '✅'] as const).map((icon, i) => ({ icon, ...UI[lang].tiles[i] })).map(item => (
          <div key={item.title} className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="text-2xl mb-2">{item.icon}</div>
            <div className="text-sm font-semibold text-gray-900 mb-1">{item.title}</div>
            <div className="text-xs text-gray-500">{item.desc}</div>
          </div>
        ))}
      </div>

      {/* Verify reminder */}
      <div className="bg-amber-50 rounded-xl border border-amber-200 p-4 text-center">
        <p className="text-sm text-amber-800">
          {UI[lang].reelsOnlyPre}<strong>{UI[lang].reelsOnlyStrong}</strong>{UI[lang].reelsOnlyPost}
          <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
            className="underline font-medium hover:text-amber-900">
            hadithverifier.com
          </a>
        </p>
      </div>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function HadithReelsPage() {
  const [tab, setTab]               = useState<Tab>('browse')
  const [lang, setLang]             = useState<Lang>('en')
  // P363: remember the viewer's language (a per-browser convenience only) and tell
  // the browser which language the page is in, for screen readers and translators.
  useEffect(() => {
    try {
      const saved = localStorage.getItem('hr-lang') as Lang | null
      if (saved && LANGS.some(l => l.code === saved)) setLang(saved)
    } catch { /* storage unavailable: stay on English */ }
  }, [])
  // Saved where the viewer chooses (not in an effect): under React's dev double-run an
  // effect saving `lang` wrote the initial 'en' over the restored choice.
  function chooseLang(code: Lang) {
    setLang(code)
    try { localStorage.setItem('hr-lang', code) } catch { /* ignore */ }
  }
  useEffect(() => { document.documentElement.lang = UI[lang].htmlLang }, [lang])
  const [narration, setNarration]   = useState<NarrationIndex>({})
  useEffect(() => {
    // P362: absent or unreadable index -> no stored audio, nothing breaks
    fetch(`${NARRATION_BASE}/index.json`, { cache: 'no-store' })
      .then(r => (r.ok ? r.json() : null))
      .then(j => { if (j?.items) setNarration(j.items) })
      .catch(() => {})
  }, [])
  const [filterGrade, setFilterGrade] = useState<Grade>('all')
  const [hadiths, setHadiths]       = useState<Hadith[]>([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState('')
  const [stats, setStats]           = useState({ total: 0, sahih: 0 })
  const [searchQuery, setSearchQuery] = useState('')
  const [loadingMore, setLoadingMore] = useState(false)

  const PAGE_SIZE = 40

  useEffect(() => { if (!searchQuery.trim()) fetchHadiths(0, true) }, [filterGrade, lang])

  // P089: server-side search across the whole library (debounced)
  useEffect(() => {
    const q = searchQuery.trim()
    if (!q) { fetchHadiths(0, true); return }   // empty box → normal browse
    const t = setTimeout(() => searchHadiths(q), 300)
    return () => clearTimeout(t)
  }, [searchQuery, filterGrade, lang])

  async function searchHadiths(q: string) {
    setLoading(true); setError('')
    try {
      const params = new URLSearchParams({ lang, q, limit: '100' })
      if (filterGrade !== 'all') params.set('grade', filterGrade)
      const res  = await fetch(`/api/reels?${params}`)
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setHadiths((data.reels || []) as Hadith[])
    } catch (e: any) {
      setError(e.message || UI[lang].searchFailed)
    } finally {
      setLoading(false)
    }
  }

  async function fetchHadiths(offset = 0, replace = false) {
    if (replace) { setLoading(true) } else { setLoadingMore(true) }
    setError('')
    try {
      const params = new URLSearchParams({ lang, limit: String(PAGE_SIZE), offset: String(offset) })
      if (filterGrade !== 'all') params.set('grade', filterGrade)
      const res  = await fetch(`/api/reels?${params}`)
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      const list = (data.reels || []) as Hadith[]
      setHadiths(prev => replace ? list : [...prev, ...list])
      setStats({
        total: data.total ?? list.length,
        sahih: data.sahih ?? list.filter(h => h.grade === 'sahih').length,
      })
    } catch (e: any) {
      setError(e.message || UI[lang].loadFailed)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  // P089: search is server-side now — render what the API returned
  const filtered = hadiths

  return (
    <div className="min-h-screen bg-gray-50 font-sans">

      {/* ── HEADER ──────────────────────────────────────────────────────────── */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          {/* Logo */}
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white text-xl flex-shrink-0">
            🎬
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-bold text-gray-900">Hadith Reels</h1>
            <p className="text-xs text-gray-500 truncate">
              {UI[lang].subtitle}
            </p>
          </div>

          {/* Stats */}
          <div className="hidden sm:flex gap-4 text-center flex-shrink-0">
            <div>
              <div className="text-base font-bold text-gray-900">{stats.total}</div>
              <div className="text-xs text-gray-500">{UI[lang].hadiths}</div>
            </div>
            <div>
              <div className="text-base font-bold text-green-600">{stats.sahih}</div>
              <div className="text-xs text-gray-500">{UI[lang].sahihStat}</div>
            </div>
          </div>

          {/* Lang switcher */}
          <div className="flex gap-1 flex-shrink-0">
            {LANGS.map(({ code, flag, label }) => (
              <button key={code} onClick={() => chooseLang(code)}
                className={`text-xs px-1.5 py-1 rounded-lg border transition-colors ${
                  lang === code
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'border-gray-200 text-gray-500 hover:bg-gray-50'
                }`}>
                {flag} {label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* ── HV CROSS-LINK ───────────────────────────────────────────────────── */}
      <div className="bg-amber-900/10 text-amber-800 text-xs text-center py-1.5 px-4 border-b border-amber-200/60">
        🔍 {UI[lang].verifyBanner}{' '}
        <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
          className="underline font-semibold hover:text-amber-900">
          hadithverifier.com
        </a>
      </div>

      {/* ── TABS ────────────────────────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex border-b border-gray-200">
          {([
            { key: 'browse', label: UI[lang].tabLibrary },
            { key: 'watch',  label: UI[lang].tabWatch   },
          ] as { key: Tab; label: string }[]).map(({ key, label }) => (
            <button key={key} onClick={() => setTab(key)}
              className={`px-5 py-3 text-sm border-b-2 -mb-px transition-colors ${
                tab === key
                  ? 'border-indigo-600 text-indigo-700 font-semibold'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── MAIN ────────────────────────────────────────────────────────────── */}
      <main className="max-w-3xl mx-auto px-4 py-6 space-y-4">

        {/* BROWSE TAB */}
        {tab === 'browse' && (
          <>
            {/* Search + filters */}
            <div className="bg-white rounded-xl border border-gray-200 p-3 space-y-3">
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                                placeholder={UI[lang].searchPlaceholder}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
              <div className="flex gap-2 items-center flex-wrap">
                <span className="text-xs text-gray-500">{UI[lang].grade}</span>
                {(['all', 'sahih', 'hasan'] as Grade[]).map(g => (
                  <button key={g} onClick={() => setFilterGrade(g)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                      filterGrade === g
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}>
                    {UI[lang].gradeLabel[g]}
                  </button>
                ))}
                <span className="text-xs text-gray-400 ml-auto">
                  {UI[lang].count(filtered.length)}
                </span>
              </div>
            </div>

            {/* Loading */}
            {loading && (
              <div className="text-center py-16">
                <div className="text-3xl mb-3 animate-pulse">📚</div>
                <p className="text-sm text-gray-500">{UI[lang].loading}</p>
              </div>
            )}

            {/* Error */}
            {!loading && error && (
              <div className="bg-red-50 rounded-xl border border-red-200 p-4 text-center">
                <p className="text-sm text-red-700 mb-2">{error}</p>
                <button onClick={() => fetchHadiths(0, true)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200">
                  {UI[lang].retry}
                </button>
              </div>
            )}

            {/* Empty */}
            {!loading && !error && filtered.length === 0 && (
              <div className="text-center py-16 text-gray-400">
                <div className="text-3xl mb-3">🔍</div>
                <p className="text-sm">{UI[lang].empty}</p>
              </div>
            )}

            {/* Hadith cards */}
            {!loading && !error && filtered.length > 0 && (
              <div className="space-y-3">
                {filtered.map(h => (
                  <HadithCard key={h.id} hadith={h} lang={lang}
                    audioUrl={narration[h.id]?.[lang]?.path
                      ? `${NARRATION_BASE}/${narration[h.id]?.[lang]?.path}` : undefined} />
                ))}
                {!searchQuery.trim() && hadiths.length < stats.total && (
                  <button
                    onClick={() => fetchHadiths(hadiths.length)}
                    disabled={loadingMore}
                    className="w-full py-3 rounded-xl border border-gray-200 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    {loadingMore ? UI[lang].loadingMore : UI[lang].loadMore(hadiths.length, stats.total)}
                  </button>
                )}
              </div>
            )}
          </>
        )}

        {/* WATCH TAB */}
        {tab === 'watch' && <WatchTab lang={lang} />}

        {/* Footer */}
        <div className="text-center text-xs text-gray-400 pt-4 pb-8 border-t border-gray-100">
          {UI[lang].footer}{' '}
          <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
            className="text-amber-600 underline hover:text-amber-700">
            {UI[lang].footerLink}
          </a>
        </div>

      </main>
    </div>
  )
}
