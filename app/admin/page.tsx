'use client'

import { useState, useEffect, useRef } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────
type Lang  = 'en' | 'uz' | 'ar' | 'ru' | 'tj'
type Style = 'adults' | 'kids'
type Step  = 'login' | 'pick' | 'generate' | 'preview' | 'done'

interface Hadith {
  id: string
  text_arabic?: string
  text_english: string
  text_display?: string
  narrator: string
  collection: string
  hadith_number?: string
  grade: string
  tags?: string[]
  source_url?: string
}

interface GeneratedContent {
  title: string
  story: string
  moral: string
  seerah_context: string
}

// ─── Constants ────────────────────────────────────────────────────────────────
const LANGS: { code: Lang; label: string; flag: string }[] = [
  { code: 'ar', label: 'Arabic',  flag: '🇸🇦' },
  { code: 'uz', label: 'Uzbek',   flag: '🇺🇿' },
  { code: 'ru', label: 'Russian', flag: '🇷🇺' },
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'tj', label: 'Tajik',   flag: '🇹🇯' },
]

const GRADE_COLORS: Record<string, string> = {
  sahih: 'bg-green-900/50 text-green-300 border-green-700',
  hasan: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
}

// ─── Step indicator ───────────────────────────────────────────────────────────
function StepBar({ step }: { step: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: 'pick',     label: '1. Pick hadith' },
    { key: 'generate', label: '2. Generate'    },
    { key: 'preview',  label: '3. Preview'     },
    { key: 'done',     label: '4. Done'        },
  ]
  const activeIndex = steps.findIndex(s => s.key === step)

  return (
    <div className="flex items-center gap-2 mb-6">
      {steps.map((s, i) => (
        <div key={s.key} className="flex items-center gap-2">
          <div className={`text-xs px-3 py-1 rounded-full border transition-colors ${
            i <= activeIndex
              ? 'bg-indigo-600 text-white border-indigo-500'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}>
            {s.label}
          </div>
          {i < steps.length - 1 && (
            <div className={`w-6 h-px ${i < activeIndex ? 'bg-indigo-500' : 'bg-slate-700'}`} />
          )}
        </div>
      ))}
    </div>
  )
}

// ─── TTS Preview ──────────────────────────────────────────────────────────────
function AudioPreview({ text, lang, style, label }: {
  text: string; lang: Lang; style: Style; label: string
}) {
  const [loading, setLoading]   = useState(false)
  const [playing, setPlaying]   = useState(false)
  const [audioUrl, setAudioUrl] = useState('')
  const audioRef = useRef<HTMLAudioElement | null>(null)

  async function generateAudio() {
    setLoading(true)
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.slice(0, 800), lang, style }),
      })
      if (!res.ok) throw new Error('TTS failed')
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      setAudioUrl(url)
      const audio = new Audio(url)
      audioRef.current = audio
      audio.play()
      setPlaying(true)
      audio.onended = () => setPlaying(false)
    } catch (e) {
      console.error('TTS error:', e)
      // Browser fallback
      const utt = new SpeechSynthesisUtterance(text.slice(0, 300))
      utt.lang  = lang === 'ar' ? 'ar-SA' : lang === 'ru' || lang === 'tj' ? 'ru-RU' : 'en-US'
      window.speechSynthesis.speak(utt)
      setPlaying(true)
      utt.onend = () => setPlaying(false)
    } finally {
      setLoading(false)
    }
  }

  function togglePlay() {
    if (playing) {
      audioRef.current?.pause()
      window.speechSynthesis?.cancel()
      setPlaying(false)
    } else if (audioUrl) {
      const audio = new Audio(audioUrl)
      audioRef.current = audio
      audio.play()
      setPlaying(true)
      audio.onended = () => setPlaying(false)
    } else {
      generateAudio()
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button onClick={togglePlay} disabled={loading}
        className="text-xs px-3 py-1.5 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white border border-indigo-500 transition-colors disabled:opacity-50">
        {loading ? '⌛ Loading...' : playing ? '⏸ Pause' : `▶ ${label}`}
      </button>
      {audioUrl && (
        <a href={audioUrl} download={`${label.toLowerCase().replace(/\s+/g, '-')}.mp3`}
          className="text-xs px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600 transition-colors">
          ⬇ Download MP3
        </a>
      )}
    </div>
  )
}

// ─── Main admin page ──────────────────────────────────────────────────────────
export default function AdminPage() {
  // Auth
  const [step, setStep]         = useState<Step>('login')
  const [password, setPassword] = useState('')
  const [authError, setAuthError] = useState('')
  const [authed, setAuthed]     = useState(false)

  // Hadith selection
  const [hadiths, setHadiths]   = useState<Hadith[]>([])
  const [loadingHadiths, setLoadingHadiths] = useState(false)
  const [selected, setSelected] = useState<Hadith | null>(null)
  const [searchQ, setSearchQ]   = useState('')
  const [filterGrade, setFilterGrade] = useState('all')

  // Generation config
  const [lang, setLang]         = useState<Lang>('ar')
  const [style, setStyle]       = useState<Style>('adults')

  // Generated content
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated]   = useState<GeneratedContent | null>(null)
  const [genError, setGenError]     = useState('')

  // Caption
  const [caption, setCaption]   = useState('')
  const [copiedCaption, setCopiedCaption] = useState(false)

  // ── Auth ──────────────────────────────────────────────────────────────────
  async function handleLogin() {
    setAuthError('')
    try {
      const res = await fetch('/api/admin/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (res.ok) {
        setAuthed(true)
        setStep('pick')
        fetchHadiths()
      } else {
        setAuthError('Incorrect password')
      }
    } catch {
      setAuthError('Connection error')
    }
  }

  // ── Fetch hadiths ─────────────────────────────────────────────────────────
  async function fetchHadiths() {
    setLoadingHadiths(true)
    try {
      const params = new URLSearchParams({ lang, limit: '70' })
      if (filterGrade !== 'all') params.set('grade', filterGrade)
      const res  = await fetch(`/api/reels?${params}`)
      const data = await res.json()
      setHadiths(data.reels || [])
    } catch {
      setHadiths([])
    } finally {
      setLoadingHadiths(false)
    }
  }

  useEffect(() => {
    if (authed) fetchHadiths()
  }, [filterGrade, lang])

  // ── Generate content ──────────────────────────────────────────────────────
  async function generate() {
    if (!selected) return
    setGenerating(true)
    setGenError('')
    setGenerated(null)
    try {
      const res = await fetch('/api/generate-reel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hadith_text:   selected.text_display || selected.text_english,
          hadith_arabic: selected.text_arabic,
          narrator:      selected.narrator,
          collection:    selected.collection,
          hadith_number: selected.hadith_number,
          style,
          lang,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setGenerated(data)

      // Auto-generate caption
      const tags = selected.tags?.slice(0, 8).map(t => `#${t}`).join(' ') || ''
      const langLabel = LANGS.find(l => l.code === lang)?.label || 'English'
      setCaption(
        `${data.title}\n\n${data.moral}\n\n📖 ${selected.collection}${selected.hadith_number ? ` #${selected.hadith_number}` : ''}\n👤 ${selected.narrator}\n\n🔍 Verify: hadithverifier.com\n\n${tags} #hadith #islamic #authentic #${langLabel.toLowerCase()}`
      )
      setStep('preview')
    } catch (e: any) {
      setGenError(e.message || 'Generation failed')
    } finally {
      setGenerating(false)
    }
  }

  // ── Filter hadiths ────────────────────────────────────────────────────────
  const filtered = hadiths.filter(h => {
    if (!searchQ.trim()) return true
    const q = searchQ.toLowerCase()
    return (
      (h.text_display || h.text_english).toLowerCase().includes(q) ||
      h.narrator.toLowerCase().includes(q) ||
      h.collection.toLowerCase().includes(q) ||
      h.tags?.some(t => t.includes(q))
    )
  })

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────────

  // ── LOGIN SCREEN ──────────────────────────────────────────────────────────
  if (!authed) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 w-full max-w-sm">
          <div className="text-center mb-6">
            <div className="text-4xl mb-3">🎬</div>
            <h1 className="text-white text-xl font-bold">Hadith Reels</h1>
            <p className="text-slate-400 text-sm mt-1">Admin Studio</p>
          </div>
          <div className="space-y-3">
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              placeholder="Enter admin password"
              className="w-full bg-slate-700 text-white border border-slate-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-slate-400"
              autoFocus
            />
            {authError && (
              <p className="text-red-400 text-xs text-center">{authError}</p>
            )}
            <button onClick={handleLogin}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors">
              Enter Studio
            </button>
          </div>
          <p className="text-slate-500 text-xs text-center mt-4">
            Set ADMIN_PASSWORD in Vercel env vars
          </p>
        </div>
      </div>
    )
  }

  // ── ADMIN STUDIO ──────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-900 text-white">

      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-sm">🎬</div>
          <div>
            <h1 className="text-sm font-bold text-white">Hadith Reels — Admin Studio</h1>
            <p className="text-xs text-slate-400">Create · Preview · Publish</p>
          </div>
          <a href="/" className="ml-auto text-xs text-slate-400 hover:text-white transition-colors">
            ← Public site
          </a>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-6">
        <StepBar step={step} />

        {/* ── STEP 1: PICK HADITH ─────────────────────────────────────────── */}
        {step === 'pick' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

            {/* Config panel */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 space-y-4">
              <h2 className="text-sm font-semibold text-white">Reel config</h2>

              {/* Style */}
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wide block mb-2">
                  Style
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {(['adults', 'kids'] as Style[]).map(s => (
                    <button key={s} onClick={() => setStyle(s)}
                      className={`py-2 px-3 rounded-lg text-xs border transition-colors ${
                        style === s
                          ? 'bg-indigo-600 text-white border-indigo-500'
                          : 'bg-slate-700 text-slate-300 border-slate-600 hover:bg-slate-600'
                      }`}>
                      {s === 'adults' ? '📖 Adults' : '🌟 Kids'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Language */}
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wide block mb-2">
                  Narration language
                </label>
                <div className="space-y-1">
                  {LANGS.map(l => (
                    <button key={l.code} onClick={() => setLang(l.code)}
                      className={`w-full py-2 px-3 rounded-lg text-xs border text-left transition-colors ${
                        lang === l.code
                          ? 'bg-indigo-600 text-white border-indigo-500'
                          : 'bg-slate-700 text-slate-300 border-slate-600 hover:bg-slate-600'
                      }`}>
                      {l.flag} {l.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Grade filter */}
              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wide block mb-2">
                  Grade filter
                </label>
                <div className="flex gap-1">
                  {['all', 'sahih', 'hasan'].map(g => (
                    <button key={g} onClick={() => setFilterGrade(g)}
                      className={`text-xs px-2 py-1 rounded border transition-colors ${
                        filterGrade === g
                          ? 'bg-indigo-600 text-white border-indigo-500'
                          : 'bg-slate-700 text-slate-300 border-slate-600'
                      }`}>
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Hadith list */}
            <div className="lg:col-span-2 space-y-3">
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-3">
                <input
                  type="text"
                  value={searchQ}
                  onChange={e => setSearchQ(e.target.value)}
                  placeholder="Search hadiths, tags, narrators..."
                  className="w-full bg-slate-700 text-white border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-slate-400"
                />
                <p className="text-xs text-slate-500 mt-1">{filtered.length} hadiths available</p>
              </div>

              {loadingHadiths && (
                <div className="text-center py-8 text-slate-400">
                  <div className="animate-pulse text-2xl mb-2">📚</div>
                  <p className="text-sm">Loading...</p>
                </div>
              )}

              <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
                {filtered.map(h => (
                  <div key={h.id}
                    onClick={() => setSelected(h)}
                    className={`bg-slate-800 rounded-xl border p-3 cursor-pointer transition-all ${
                      selected?.id === h.id
                        ? 'border-indigo-500 bg-indigo-900/20'
                        : 'border-slate-700 hover:border-slate-500'
                    }`}>
                    {h.text_arabic && (
                      <p className="text-right text-sm text-amber-200 mb-2 leading-loose" dir="rtl">
                        {h.text_arabic}
                      </p>
                    )}
                    <p className="text-sm text-slate-200 leading-relaxed mb-2">
                      {h.text_display || h.text_english}
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${GRADE_COLORS[h.grade] ?? 'bg-slate-700 text-slate-300 border-slate-600'}`}>
                        {h.grade}
                      </span>
                      <span className="text-xs text-slate-400">{h.collection}</span>
                      {h.hadith_number && <span className="text-xs text-slate-500">#{h.hadith_number}</span>}
                      <span className="text-xs text-slate-500 ml-auto">{h.narrator}</span>
                    </div>
                    {h.tags && h.tags.length > 0 && (
                      <div className="flex gap-1 flex-wrap mt-2">
                        {h.tags.slice(0, 5).map(t => (
                          <span key={t} className="text-xs px-1.5 py-0.5 bg-slate-700 text-slate-400 rounded">#{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Proceed button */}
              {selected && (
                <div className="bg-indigo-900/30 border border-indigo-700 rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-indigo-300 font-medium">Selected:</p>
                    <p className="text-sm text-white truncate max-w-xs">
                      {selected.collection} #{selected.hadith_number}
                    </p>
                  </div>
                  <button onClick={() => setStep('generate')}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors">
                    Generate →
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── STEP 2: GENERATE ────────────────────────────────────────────── */}
        {step === 'generate' && selected && (
          <div className="max-w-2xl mx-auto space-y-4">
            {/* Selected hadith summary */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-slate-400 uppercase tracking-wide">Selected hadith</span>
                <button onClick={() => setStep('pick')}
                  className="text-xs text-slate-400 hover:text-white">
                  ← Change
                </button>
              </div>
              {selected.text_arabic && (
                <p className="text-right text-sm text-amber-200 mb-2 leading-loose" dir="rtl">
                  {selected.text_arabic}
                </p>
              )}
              <p className="text-sm text-slate-200">{selected.text_display || selected.text_english}</p>
              <div className="flex gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded-full border ${GRADE_COLORS[selected.grade] ?? ''}`}>
                  {selected.grade}
                </span>
                <span className="text-xs text-slate-400">{selected.collection}</span>
                <span className="text-xs text-slate-400">
                  {LANGS.find(l => l.code === lang)?.flag} {LANGS.find(l => l.code === lang)?.label}
                  {' · '}{style === 'adults' ? '📖 Adults' : '🌟 Kids'}
                </span>
              </div>
            </div>

            {/* Generate button */}
            {!generating && !generated && (
              <button onClick={generate}
                className="w-full py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-base transition-colors">
                🤖 Generate story + moral + seerah context
              </button>
            )}

            {generating && (
              <div className="text-center py-8">
                <div className="text-3xl mb-3 animate-pulse">✨</div>
                <p className="text-white font-medium">Claude is generating your reel content...</p>
                <p className="text-slate-400 text-sm mt-1">Story · Moral · Seerah context · Caption</p>
              </div>
            )}

            {genError && (
              <div className="bg-red-900/30 border border-red-700 rounded-xl p-4">
                <p className="text-red-300 text-sm">{genError}</p>
                <button onClick={generate}
                  className="mt-2 text-xs px-3 py-1.5 rounded-lg bg-red-800 hover:bg-red-700 text-white">
                  Retry
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── STEP 3: PREVIEW ─────────────────────────────────────────────── */}
        {step === 'preview' && generated && selected && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

            {/* Content preview */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                Generated content
              </h2>

              {/* Title */}
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-2">🎬 Reel title</div>
                <p className="text-white font-semibold">{generated.title}</p>
              </div>

              {/* Story */}
              <div className="bg-amber-900/20 rounded-xl border border-amber-800/50 p-4">
                <div className="text-xs text-amber-400 uppercase tracking-wide mb-2">
                  📖 Story — Ar-Raheeq Al-Makhtum
                </div>
                <p className="text-amber-100 text-sm leading-relaxed" dir="auto">
                  {generated.story}
                </p>
                <div className="mt-3">
                  <AudioPreview
                    text={generated.story}
                    lang={lang}
                    style={style}
                    label="Preview story audio"
                  />
                </div>
              </div>

              {/* Moral */}
              <div className="bg-emerald-900/20 rounded-xl border border-emerald-800/50 p-4">
                <div className="text-xs text-emerald-400 uppercase tracking-wide mb-2">
                  💡 Moral lesson
                </div>
                <p className="text-emerald-100 text-sm leading-relaxed" dir="auto">
                  {generated.moral}
                </p>
                <div className="mt-3">
                  <AudioPreview
                    text={generated.moral}
                    lang={lang}
                    style={style}
                    label="Preview moral audio"
                  />
                </div>
              </div>

              {/* Seerah context */}
              {generated.seerah_context && (
                <div className="bg-blue-900/20 rounded-xl border border-blue-800/50 p-4">
                  <div className="text-xs text-blue-400 uppercase tracking-wide mb-2">
                    🕌 Historical context
                  </div>
                  <p className="text-blue-100 text-sm leading-relaxed" dir="auto">
                    {generated.seerah_context}
                  </p>
                </div>
              )}

              {/* Regenerate */}
              <button onClick={() => { setStep('generate'); setGenerated(null) }}
                className="w-full py-2 rounded-xl border border-slate-600 text-slate-400 hover:text-white hover:border-slate-400 text-sm transition-colors">
                🔄 Regenerate content
              </button>
            </div>

            {/* Caption + Actions */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                Caption + publish
              </h2>

              {/* Caption editor */}
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-2">
                  📱 Social media caption
                </div>
                <textarea
                  value={caption}
                  onChange={e => setCaption(e.target.value)}
                  rows={10}
                  className="w-full bg-slate-700 text-slate-200 border border-slate-600 rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={() => { navigator.clipboard.writeText(caption); setCopiedCaption(true); setTimeout(() => setCopiedCaption(false), 2000) }}
                  className="mt-2 w-full py-2 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white text-sm transition-colors">
                  {copiedCaption ? '✓ Copied!' : 'Copy caption'}
                </button>
              </div>

              {/* Publish links */}
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 space-y-2">
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-3">
                  📤 Publish to
                </div>
                {[
                  { label: 'Instagram Reels', url: 'https://www.instagram.com/', color: 'from-purple-600 to-pink-600' },
                  { label: 'TikTok', url: 'https://www.tiktok.com/', color: 'from-slate-800 to-slate-700' },
                  { label: 'YouTube Shorts', url: 'https://studio.youtube.com/', color: 'from-red-700 to-red-600' },
                  { label: 'Telegram Channel', url: 'https://t.me/', color: 'from-blue-700 to-blue-600' },
                ].map(platform => (
                  <a key={platform.label} href={platform.url} target="_blank" rel="noopener noreferrer"
                    className={`flex items-center justify-between w-full py-2.5 px-4 rounded-xl bg-gradient-to-r ${platform.color} text-white text-sm hover:opacity-90 transition-opacity`}>
                    <span>{platform.label}</span>
                    <span className="text-xs opacity-70">Open ↗</span>
                  </a>
                ))}
                <p className="text-xs text-slate-500 text-center mt-2">
                  Auto-posting via Buffer API coming in Phase 3
                </p>
              </div>

              {/* Mark done */}
              <button onClick={() => { setStep('done') }}
                className="w-full py-3 rounded-xl bg-green-700 hover:bg-green-600 text-white font-semibold text-sm transition-colors">
                ✅ Mark as published
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 4: DONE ────────────────────────────────────────────────── */}
        {step === 'done' && (
          <div className="max-w-md mx-auto text-center py-16">
            <div className="text-5xl mb-4">🎉</div>
            <h2 className="text-white text-xl font-bold mb-2">Reel published!</h2>
            <p className="text-slate-400 text-sm mb-8">
              Great work. The hadith has been shared with the world.
            </p>
            <button
              onClick={() => { setSelected(null); setGenerated(null); setCaption(''); setStep('pick') }}
              className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors">
              Create another reel →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
