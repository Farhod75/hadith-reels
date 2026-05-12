'use client'

import { useState, useEffect, useRef } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────
type Lang  = 'en' | 'uz' | 'ar' | 'ru'
type Grade = 'sahih' | 'hasan' | 'all'
type Tab   = 'browse' | 'generate' | 'my_reels'
type Style = 'adults' | 'kids'

interface Reel {
  id: string
  title: string
  hadith_text: string
  text_display?: string
  text_arabic?: string
  narrator: string
  collection: string
  hadith_number?: string
  grade: string
  tags?: string[]
  source_url?: string
  style: Style
  lang: Lang
  story?: string
  moral?: string
  seerah_context?: string
  audio_url?: string
  created_at?: string
  status: 'ready' | 'generating' | 'error'
}

// ─── Constants ────────────────────────────────────────────────────────────────
const GRADE_COLORS: Record<string, string> = {
  sahih: 'bg-green-100 text-green-700 border-green-200',
  hasan: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  daif:  'bg-red-100 text-red-700 border-red-200',
}

const LANG_LABELS: Record<Lang, string> = {
  en: '🇬🇧 EN', uz: '🇺🇿 UZ', ar: '🇸🇦 AR', ru: '🇷🇺 RU',
}

// ─── Sub-components ───────────────────────────────────────────────────────────
function GradeBadge({ grade }: { grade: string }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${GRADE_COLORS[grade] ?? 'bg-gray-100 text-gray-600 border-gray-200'}`}>
      {grade}
    </span>
  )
}

function TTSButton({ text, lang, style }: { text: string; lang: Lang; style: Style }) {
  const [playing, setPlaying]   = useState(false)
  const [loading, setLoading]   = useState(false)
  const audioRef                = useRef<HTMLAudioElement | null>(null)

  async function toggle() {
    if (playing) {
      audioRef.current?.pause()
      setPlaying(false)
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.slice(0, 500), lang, style }),
      })
      if (!res.ok) throw new Error('TTS failed')
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio
      audio.play()
      setPlaying(true)
      audio.onended = () => setPlaying(false)
    } catch {
      // Fallback to browser TTS
      const utt = new SpeechSynthesisUtterance(text.slice(0, 300))
      utt.lang = lang === 'ar' ? 'ar-SA' : lang === 'ru' ? 'ru-RU' : lang === 'uz' ? 'ru-RU' : 'en-US'
      window.speechSynthesis.speak(utt)
      setPlaying(true)
      utt.onend = () => setPlaying(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button onClick={toggle}
      className="text-xs px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-100 transition-colors flex items-center gap-1">
      {loading ? '⌛' : playing ? '⏸ Pause' : '▶ Listen'}
    </button>
  )
}

function ReelCard({ reel, lang, onExpand }: { reel: Reel; lang: Lang; onExpand: (r: Reel) => void }) {
  const [copied, setCopied] = useState(false)
  const display = reel.text_display || reel.hadith_text

  function copy() {
    navigator.clipboard.writeText(display)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-200 hover:shadow-sm transition-all">
      {/* Arabic */}
      {reel.text_arabic && (
        <div className="text-base text-right leading-loose text-gray-800 mb-3 p-3 bg-amber-50 rounded-lg border border-amber-100" dir="rtl">
          {reel.text_arabic}
        </div>
      )}
      {/* Translation */}
      <p className="text-sm text-gray-700 leading-relaxed mb-3">{display}</p>

      {/* Meta */}
      <div className="flex items-center gap-2 flex-wrap mb-3">
        <GradeBadge grade={reel.grade} />
        <span className="text-xs text-gray-400">{reel.collection}</span>
        {reel.hadith_number && <span className="text-xs text-gray-400">#{reel.hadith_number}</span>}
        <span className="text-xs text-gray-400 ml-auto">{reel.narrator}</span>
      </div>

      {/* Tags */}
      {reel.tags && reel.tags.length > 0 && (
        <div className="flex gap-1 flex-wrap mb-3">
          {reel.tags.slice(0, 4).map(tag => (
            <span key={tag} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">#{tag}</span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 flex-wrap">
        <TTSButton text={display} lang={lang} style="adults" />
        <button onClick={copy}
          className="text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors">
          {copied ? '✓ Copied' : 'Copy'}
        </button>
        <button onClick={() => onExpand(reel)}
          className="text-xs px-3 py-1.5 rounded-lg bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 transition-colors">
          🎬 Generate reel
        </button>
        {reel.source_url && (
          <a href={reel.source_url} target="_blank" rel="noopener noreferrer"
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

function GeneratePanel({ reel, lang, style, onDone }: {
  reel: Reel; lang: Lang; style: Style; onDone: (r: Reel) => void
}) {
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState<Reel | null>(null)
  const [error, setError]     = useState('')

  useEffect(() => { generate() }, [])

  async function generate() {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/generate-reel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hadith_text:    reel.text_display || reel.hadith_text,
          hadith_arabic:  reel.text_arabic,
          narrator:       reel.narrator,
          collection:     reel.collection,
          hadith_number:  reel.hadith_number,
          style,
          lang,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      const enriched: Reel = { ...reel, ...data, style, lang, status: 'ready' }
      setResult(enriched)
      onDone(enriched)
    } catch (e: any) {
      setError(e.message || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return (
    <div className="bg-white rounded-xl border border-indigo-200 p-6 text-center">
      <div className="text-2xl mb-2 animate-pulse">🎬</div>
      <p className="text-sm text-gray-500">Generating your reel story...</p>
    </div>
  )

  if (error) return (
    <div className="bg-red-50 rounded-xl border border-red-200 p-4">
      <p className="text-sm text-red-700">{error}</p>
      <button onClick={generate} className="mt-2 text-xs px-3 py-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200">
        Retry
      </button>
    </div>
  )

  if (!result) return null

  return (
    <div className="bg-white rounded-xl border border-indigo-200 p-4 space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-lg">🎬</span>
        <h3 className="font-semibold text-gray-900 text-sm">{result.title}</h3>
        <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 ml-auto">
          {style === 'kids' ? '🌟 Kids' : '📖 Adults'}
        </span>
      </div>

      {result.story && (
        <div className="bg-amber-50 rounded-lg border border-amber-100 p-3">
          <div className="text-xs font-medium text-amber-700 uppercase tracking-wide mb-1">
            📖 Story — Ar-Raheeq Al-Makhtum
          </div>
          <p className="text-sm text-amber-900 leading-relaxed" dir="auto">{result.story}</p>
          <div className="mt-2">
            <TTSButton text={result.story} lang={lang} style={style} />
          </div>
        </div>
      )}

      {result.moral && (
        <div className="bg-emerald-50 rounded-lg border border-emerald-100 p-3">
          <div className="text-xs font-medium text-emerald-700 uppercase tracking-wide mb-1">
            💡 Moral
          </div>
          <p className="text-sm text-emerald-900 leading-relaxed" dir="auto">{result.moral}</p>
          <div className="mt-2">
            <TTSButton text={result.moral} lang={lang} style={style} />
          </div>
        </div>
      )}

      {result.seerah_context && (
        <div className="bg-blue-50 rounded-lg border border-blue-100 p-3">
          <div className="text-xs font-medium text-blue-700 uppercase tracking-wide mb-1">
            🕌 Historical context
          </div>
          <p className="text-sm text-blue-900 leading-relaxed" dir="auto">{result.seerah_context}</p>
        </div>
      )}

      <div className="text-xs text-gray-400 text-center pt-1">
        Remotion video export coming soon · For now: copy the story for your reel
      </div>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function HadithReelsPage() {
  const [tab, setTab]               = useState<Tab>('browse')
  const [lang, setLang]             = useState<Lang>('en')
  const [style, setStyle]           = useState<Style>('adults')
  const [filterGrade, setFilterGrade] = useState<Grade>('all')
  const [reels, setReels]           = useState<Reel[]>([])
  const [loading, setLoading]       = useState(true)
  const [error, setError]           = useState('')
  const [myReels, setMyReels]       = useState<Reel[]>([])
  const [expandedReel, setExpandedReel] = useState<Reel | null>(null)
  const [toast, setToast]           = useState<string | null>(null)
  const [stats, setStats]           = useState({ total: 0, sahih: 0 })

  // Fetch hadiths from Supabase on mount + filter change
  useEffect(() => { fetchReels() }, [filterGrade, lang])

  async function fetchReels() {
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams({ lang, limit: '30' })
      if (filterGrade !== 'all') params.set('grade', filterGrade)
      const res  = await fetch(`/api/reels?${params}`)
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      const list = data.reels || []
      setReels(list)
      setStats({
        total: list.length,
        sahih: list.filter((r: Reel) => r.grade === 'sahih').length,
      })
    } catch (e: any) {
      setError(e.message || 'Failed to load reels')
    } finally {
      setLoading(false)
    }
  }

  function showToast(msg: string) {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  function handleReelGenerated(reel: Reel) {
    setMyReels(prev => {
      const exists = prev.find(r => r.id === reel.id)
      return exists ? prev.map(r => r.id === reel.id ? reel : r) : [reel, ...prev]
    })
    showToast('✅ Reel generated! View in My Reels tab.')
  }

  function handleExpand(reel: Reel) {
    setExpandedReel(reel)
    setTab('generate')
  }

  return (
    <div className="min-h-screen bg-gray-50 font-sans">

      {/* ── HEADER ──────────────────────────────────────────────────────────── */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-700 flex items-center justify-center text-white text-lg flex-shrink-0">
            🎬
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-semibold text-gray-900">Hadith Reels</h1>
            <p className="text-xs text-gray-500 truncate">
              Authentic hadith · EN · UZ · AR · RU
            </p>
          </div>
          {/* Stats */}
          <div className="hidden sm:flex gap-4 text-center flex-shrink-0">
            <div>
              <div className="text-lg font-semibold text-gray-900">{stats.total}</div>
              <div className="text-xs text-gray-500">Hadiths</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-green-700">{stats.sahih}</div>
              <div className="text-xs text-gray-500">Sahih</div>
            </div>
          </div>
          {/* Lang picker */}
          <div className="flex gap-1">
            {(Object.entries(LANG_LABELS) as [Lang, string][]).map(([code, label]) => (
              <button key={code} onClick={() => setLang(code)}
                className={`text-xs px-2 py-1 rounded-lg border transition-colors ${
                  lang === code
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'border-gray-200 text-gray-500 hover:bg-gray-50'
                }`}>
                {label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* ── HV CROSS-LINK BANNER ────────────────────────────────────────────── */}
      <div className="bg-amber-900/10 text-amber-800 text-xs text-center py-1.5 px-4 border-b border-amber-200/60">
        🔍 Verify any hadith before sharing at{' '}
        <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
          className="underline font-medium hover:text-amber-900">
          hadithverifier.com
        </a>
      </div>

      {/* ── TABS ────────────────────────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex gap-1 border-b border-gray-200 overflow-x-auto">
          {([
            { key: 'browse',   label: '📚 Browse hadiths' },
            { key: 'generate', label: `🎬 Generate${expandedReel ? ' reel' : ''}` },
            { key: 'my_reels', label: `⭐ My reels${myReels.length ? ` (${myReels.length})` : ''}` },
          ] as { key: Tab; label: string }[]).map(({ key, label }) => (
            <button key={key} onClick={() => setTab(key)}
              className={`px-4 py-3 text-sm whitespace-nowrap border-b-2 -mb-px transition-colors ${
                tab === key
                  ? 'border-indigo-600 text-indigo-700 font-medium'
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
            {/* Filters */}
            <div className="bg-white rounded-xl border border-gray-200 p-3 flex gap-4 flex-wrap items-center">
              {/* Grade filter */}
              <div className="flex gap-1 items-center">
                <span className="text-xs text-gray-500 mr-1">Grade:</span>
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
              </div>
              {/* Style picker */}
              <div className="flex gap-1 items-center ml-auto">
                <span className="text-xs text-gray-500 mr-1">Style:</span>
                {(['adults', 'kids'] as Style[]).map(s => (
                  <button key={s} onClick={() => setStyle(s)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                      style === s
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}>
                    {s === 'adults' ? '📖 Adults' : '🌟 Kids'}
                  </button>
                ))}
              </div>
            </div>

            {/* Loading */}
            {loading && (
              <div className="text-center py-12">
                <div className="text-3xl mb-3 animate-pulse">📚</div>
                <p className="text-sm text-gray-500">Loading hadiths...</p>
              </div>
            )}

            {/* Error */}
            {error && !loading && (
              <div className="bg-red-50 rounded-xl border border-red-200 p-4 text-center">
                <p className="text-sm text-red-700 mb-2">{error}</p>
                <button onClick={fetchReels}
                  className="text-xs px-3 py-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200">
                  Retry
                </button>
              </div>
            )}

            {/* Results */}
            {!loading && !error && reels.length === 0 && (
              <div className="text-center py-12 text-gray-400 text-sm">
                No hadiths found. Try changing the grade filter.
              </div>
            )}

            {!loading && !error && reels.length > 0 && (
              <div className="space-y-3">
                {reels.map(r => (
                  <ReelCard key={r.id} reel={{ ...r, style, lang }} lang={lang} onExpand={handleExpand} />
                ))}
              </div>
            )}
          </>
        )}

        {/* GENERATE TAB */}
        {tab === 'generate' && (
          <>
            {expandedReel ? (
              <>
                <div className="bg-white rounded-xl border border-gray-200 p-3 flex items-center gap-2">
                  <span className="text-xs text-gray-500">Generating for:</span>
                  <span className="text-xs font-medium text-gray-800 truncate">
                    {expandedReel.collection}
                    {expandedReel.hadith_number ? ` #${expandedReel.hadith_number}` : ''}
                  </span>
                  <button onClick={() => { setExpandedReel(null) }}
                    className="text-xs text-gray-400 hover:text-gray-600 ml-auto">
                    ✕ Clear
                  </button>
                </div>
                <GeneratePanel
                  reel={expandedReel}
                  lang={lang}
                  style={style}
                  onDone={handleReelGenerated}
                />
              </>
            ) : (
              <div className="text-center py-12">
                <div className="text-4xl mb-3">🎬</div>
                <p className="text-gray-500 text-sm mb-4">
                  Pick a hadith from Browse tab and click "Generate reel"
                </p>
                <button onClick={() => setTab('browse')}
                  className="text-sm px-4 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-colors">
                  Browse hadiths
                </button>
              </div>
            )}
          </>
        )}

        {/* MY REELS TAB */}
        {tab === 'my_reels' && (
          <>
            {myReels.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-3">⭐</div>
                <p className="text-gray-500 text-sm mb-4">
                  No reels generated yet this session.
                </p>
                <button onClick={() => setTab('browse')}
                  className="text-sm px-4 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700">
                  Start browsing
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {myReels.map(r => (
                  <div key={r.id} className="space-y-2">
                    <ReelCard reel={r} lang={lang} onExpand={handleExpand} />
                    {r.story && (
                      <div className="bg-amber-50 rounded-xl border border-amber-100 p-3 text-sm text-amber-900" dir="auto">
                        <div className="text-xs font-medium text-amber-700 mb-1">📖 Story</div>
                        {r.story}
                        <div className="mt-2">
                          <TTSButton text={r.story} lang={lang} style={r.style} />
                        </div>
                      </div>
                    )}
                    {r.moral && (
                      <div className="bg-emerald-50 rounded-xl border border-emerald-100 p-3 text-sm text-emerald-900" dir="auto">
                        <div className="text-xs font-medium text-emerald-700 mb-1">💡 Moral</div>
                        {r.moral}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-gray-400 pt-4 pb-8 border-t border-gray-100">
          All hadiths are authenticated (sahih/hasan only).{' '}
          <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer"
            className="text-amber-600 underline hover:text-amber-700">
            Verify any hadith →
          </a>
        </div>

      </main>

      {/* ── TOAST ───────────────────────────────────────────────────────────── */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-sm px-4 py-2.5 rounded-xl shadow-lg z-50">
          {toast}
        </div>
      )}
    </div>
  )
}
