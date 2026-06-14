'use client'

import { useState, useEffect, useRef } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────
type Lang  = 'en' | 'uz' | 'ar' | 'ru' | 'tj'
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
  { code: 'ar', flag: '🇸🇦', label: 'AR' },
  { code: 'ru', flag: '🇷🇺', label: 'RU' },
  { code: 'tj', flag: '🇹🇯', label: 'TJ' },
]

// ─── TTS Button ───────────────────────────────────────────────────────────────
function TTSButton({ text, lang }: { text: string; lang: Lang }) {
  const [playing, setPlaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  async function toggle() {
    if (playing) {
      audioRef.current?.pause()
      window.speechSynthesis?.cancel()
      setPlaying(false)
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
      utt.lang   = lang === 'ar' ? 'ar-SA'
                 : lang === 'ru' || lang === 'tj' ? 'ru-RU'
                 : lang === 'uz' ? 'ru-RU'
                 : 'en-US'
      window.speechSynthesis.speak(utt)
      setPlaying(true)
      utt.onend = () => setPlaying(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button onClick={toggle}
      className="text-xs px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-100 transition-colors flex items-center gap-1.5">
      {loading ? '⌛' : playing ? '⏸ Pause' : '▶ Listen'}
    </button>
  )
}

// ─── Hadith Card ──────────────────────────────────────────────────────────────
function HadithCard({ hadith, lang }: { hadith: Hadith; lang: Lang }) {
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
          {hadith.grade}
        </span>
        <span className="text-xs text-gray-400">{hadith.collection}</span>
        {hadith.hadith_number && <span className="text-xs text-gray-400">#{hadith.hadith_number}</span>}
        <span className="text-xs text-gray-400 ml-auto">{hadith.narrator}</span>
      </div>

      {/* Tags */}
      {hadith.tags && hadith.tags.length > 0 && (
        <div className="flex gap-1 flex-wrap mb-3">
          {hadith.tags.slice(0, 5).map(tag => (
            <span key={tag} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 flex-wrap items-center">
        <TTSButton text={display} lang={lang} />
        <button
          onClick={() => { navigator.clipboard.writeText(display); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
          className="text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors">
          {copied ? '✓ Copied' : 'Copy'}
        </button>
        {hadith.source_url && (
          <a href={hadith.source_url} target="_blank" rel="noopener noreferrer"
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors">
            Source ↗
          </a>
        )}
        <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
          className="text-xs px-3 py-1.5 rounded-lg border border-amber-200 text-amber-700 hover:bg-amber-50 transition-colors ml-auto">
          🔍 Verify
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
        <h2 className="text-xl font-bold mb-2">Watch our reels</h2>
        <p className="text-indigo-200 text-sm mb-6 max-w-sm mx-auto">
          Authentic hadith reels with verified Islamic sources — new reels added regularly.
          Follow us on your favourite platform.
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
        {[
          { icon: '📖', title: 'Adults series', desc: 'Deep, scholarly hadiths with Seerah stories. Dark elegant style.' },
          { icon: '🌟', title: 'Kids series', desc: 'Simple language, fun animations. Perfect for children 6-14.' },
          { icon: '🕌', title: 'Ramadan special', desc: '30 days, 30 hadiths. Full month of authentic daily content.' },
          { icon: '🌍', title: '5 languages', desc: 'Arabic, Uzbek, Russian, English, Tajik narration.' },
        ].map(item => (
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
          All our reels use only <strong>sahih and hasan</strong> authenticated hadiths.
          Verify any hadith at{' '}
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
  const [filterGrade, setFilterGrade] = useState<Grade>('all')
  const [hadiths, setHadiths]       = useState<Hadith[]>([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState('')
  const [stats, setStats]           = useState({ total: 0, sahih: 0 })
  const [searchQuery, setSearchQuery] = useState('')
  const [loadingMore, setLoadingMore] = useState(false)

  const PAGE_SIZE = 40

  useEffect(() => { fetchHadiths(0, true) }, [filterGrade, lang])

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
      setError(e.message || 'Failed to load')
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  // Filter by search query
  const filtered = searchQuery.trim()
    ? hadiths.filter(h =>
        (h.text_display || h.text_english).toLowerCase().includes(searchQuery.toLowerCase()) ||
        h.text_arabic?.includes(searchQuery) ||
        h.tags?.some(t => t.toLowerCase().includes(searchQuery.toLowerCase())) ||
        h.narrator.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : hadiths

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
              Authentic hadith · EN · UZ · AR · RU · TJ
            </p>
          </div>

          {/* Stats */}
          <div className="hidden sm:flex gap-4 text-center flex-shrink-0">
            <div>
              <div className="text-base font-bold text-gray-900">{stats.total}</div>
              <div className="text-xs text-gray-500">Hadiths</div>
            </div>
            <div>
              <div className="text-base font-bold text-green-600">{stats.sahih}</div>
              <div className="text-xs text-gray-500">Sahih</div>
            </div>
          </div>

          {/* Lang switcher */}
          <div className="flex gap-1 flex-shrink-0">
            {LANGS.map(({ code, flag, label }) => (
              <button key={code} onClick={() => setLang(code)}
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
        🔍 Verify any hadith before sharing at{' '}
        <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
          className="underline font-semibold hover:text-amber-900">
          hadithverifier.com
        </a>
      </div>

      {/* ── TABS ────────────────────────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex border-b border-gray-200">
          {([
            { key: 'browse', label: '📚 Hadith library' },
            { key: 'watch',  label: '🎬 Watch reels'    },
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
                placeholder="Search hadiths, tags, narrators..."
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-300"
              />
              <div className="flex gap-2 items-center flex-wrap">
                <span className="text-xs text-gray-500">Grade:</span>
                {(['all', 'sahih', 'hasan'] as Grade[]).map(g => (
                  <button key={g} onClick={() => setFilterGrade(g)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                      filterGrade === g
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}>
                    {g}
                  </button>
                ))}
                <span className="text-xs text-gray-400 ml-auto">
                  {filtered.length} hadiths
                </span>
              </div>
            </div>

            {/* Loading */}
            {loading && (
              <div className="text-center py-16">
                <div className="text-3xl mb-3 animate-pulse">📚</div>
                <p className="text-sm text-gray-500">Loading authenticated hadiths...</p>
              </div>
            )}

            {/* Error */}
            {!loading && error && (
              <div className="bg-red-50 rounded-xl border border-red-200 p-4 text-center">
                <p className="text-sm text-red-700 mb-2">{error}</p>
                <button onClick={() => fetchHadiths(0, true)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200">
                  Retry
                </button>
              </div>
            )}

            {/* Empty */}
            {!loading && !error && filtered.length === 0 && (
              <div className="text-center py-16 text-gray-400">
                <div className="text-3xl mb-3">🔍</div>
                <p className="text-sm">No hadiths found. Try a different search or grade.</p>
              </div>
            )}

            {/* Hadith cards */}
            {!loading && !error && filtered.length > 0 && (
              <div className="space-y-3">
                {filtered.map(h => (
                  <HadithCard key={h.id} hadith={h} lang={lang} />
                ))}
                {!searchQuery.trim() && hadiths.length < stats.total && (
                  <button
                    onClick={() => fetchHadiths(hadiths.length)}
                    disabled={loadingMore}
                    className="w-full py-3 rounded-xl border border-gray-200 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    {loadingMore ? 'Loading…' : `Load more (${hadiths.length} of ${stats.total})`}
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
          All hadiths are sahih or hasan — authenticated from major collections.{' '}
          <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
            className="text-amber-600 underline hover:text-amber-700">
            Verify at hadithverifier.com →
          </a>
        </div>

      </main>
    </div>
  )
}
