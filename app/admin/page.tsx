'use client'
// app/admin/page.tsx — Hadith Reels Admin Studio
// Step 1: Pick hadith
// Step 2: Generate story (Claude)
// Step 3: Preview — listen to ElevenLabs audio, edit caption
// Step 4: Render + Publish

import { useState, useEffect, useRef } from 'react'

type Lang   = 'en' | 'uz' | 'ar' | 'ru' | 'tj'
type Style  = 'adults' | 'kids'
type Step   = 'login' | 'pick' | 'generate' | 'preview' | 'publish'

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

interface Generated {
  title:          string
  story:          string
  moral:          string
  seerah_context: string
  attribution:    string
  caption_intro:  string
  source_attribution: string
}

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

// ── Step bar ──────────────────────────────────────────────────────────────────
function StepBar({ step }: { step: Step }) {
  const steps: { key: Step; label: string }[] = [
    { key: 'pick',     label: '1. Pick'     },
    { key: 'generate', label: '2. Generate' },
    { key: 'preview',  label: '3. Preview'  },
    { key: 'publish',  label: '4. Publish'  },
  ]
  const idx = steps.findIndex(s => s.key === step)
  return (
    <div className="flex items-center gap-2 mb-6 flex-wrap">
      {steps.map((s, i) => (
        <div key={s.key} className="flex items-center gap-2">
          <div className={`text-xs px-3 py-1 rounded-full border transition-colors ${
            i <= idx
              ? 'bg-indigo-600 text-white border-indigo-500'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}>{s.label}</div>
          {i < steps.length - 1 && (
            <div className={`w-4 h-px ${i < idx ? 'bg-indigo-500' : 'bg-slate-700'}`} />
          )}
        </div>
      ))}
    </div>
  )
}

// ── Audio player ──────────────────────────────────────────────────────────────
function AudioSection({ text, lang, style, label, onAudioReady }: {
  text: string; lang: Lang; style: Style; label: string
  onAudioReady?: (url: string) => void
}) {
  const [loading, setLoading]   = useState(false)
  const [playing, setPlaying]   = useState(false)
  const [audioUrl, setAudioUrl] = useState<string>('')
  const [error, setError]       = useState('')
  const audioRef = useRef<HTMLAudioElement | null>(null)

  async function generate() {
    setLoading(true); setError('')
    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.slice(0, 800), lang }),
      })
      if (!res.ok) throw new Error(`TTS ${res.status}`)
      const blob = await res.blob()
      const url  = URL.createObjectURL(blob)
      setAudioUrl(url)
      onAudioReady?.(url)
      // Auto-play
      const audio = new Audio(url)
      audioRef.current = audio
      audio.play()
      setPlaying(true)
      audio.onended = () => setPlaying(false)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function toggle() {
    if (!audioUrl) { generate(); return }
    if (playing) {
      audioRef.current?.pause(); setPlaying(false)
    } else {
      const audio = new Audio(audioUrl)
      audioRef.current = audio
      audio.play(); setPlaying(true)
      audio.onended = () => setPlaying(false)
    }
  }

  return (
    <div className="flex items-center gap-2 flex-wrap mt-2">
      <button onClick={toggle} disabled={loading}
        className="text-xs px-3 py-1.5 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white border border-indigo-500 disabled:opacity-50 transition-colors flex items-center gap-1.5">
        {loading ? '⌛ Generating...' : playing ? '⏸ Pause' : audioUrl ? `▶ ${label}` : `🎙 Generate ${label}`}
      </button>
      {audioUrl && (
        <a href={audioUrl} download={`${label.toLowerCase().replace(/\s+/g, '-')}.mp3`}
          className="text-xs px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600 transition-colors">
          ⬇ MP3
        </a>
      )}
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function AdminPage() {
  const [step, setStep]       = useState<Step>('login')
  const [password, setPassword] = useState('')
  const [authError, setAuthError] = useState('')
  const [authed, setAuthed]   = useState(false)

  const [hadiths, setHadiths] = useState<Hadith[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<Hadith | null>(null)
  const [searchQ, setSearchQ] = useState('')
  const [filterGrade, setFilterGrade] = useState('all')

  const [lang, setLang]   = useState<Lang>('ar')
  const [style, setStyle] = useState<Style>('adults')

  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated]   = useState<Generated | null>(null)
  const [genError, setGenError]     = useState('')

  // Audio URLs for each section — passed to Remotion
  const [storyAudioUrl, setStoryAudioUrl]   = useState('')
  const [moralAudioUrl, setMoralAudioUrl]   = useState('')

  // Render state
  const [rendering, setRendering]   = useState(false)
  const [renderDone, setRenderDone] = useState(false)

  // Telegram post state
  const [posting, setPosting]     = useState(false)
  const [postDone, setPostDone]   = useState(false)
  const [postError, setPostError] = useState('')

  // Caption
  const [caption, setCaption]           = useState('')
  const [copiedCaption, setCopiedCaption] = useState(false)

  // ── Auth ───────────────────────────────────────────────────────────────────
  async function handleLogin() {
    setAuthError('')
    try {
      const res = await fetch('/api/admin/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (res.ok) { setAuthed(true); setStep('pick'); fetchHadiths() }
      else setAuthError('Incorrect password')
    } catch { setAuthError('Connection error') }
  }

  // ── Fetch hadiths ──────────────────────────────────────────────────────────
  async function fetchHadiths() {
    setLoading(true)
    try {
      const params = new URLSearchParams({ lang, limit: '70' })
      if (filterGrade !== 'all') params.set('grade', filterGrade)
      const res  = await fetch(`/api/reels?${params}`)
      const data = await res.json()
      setHadiths(data.reels || [])
    } catch { setHadiths([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { if (authed) fetchHadiths() }, [filterGrade, lang])

  // ── Generate content ───────────────────────────────────────────────────────
  async function generate() {
    if (!selected) return
    setGenerating(true); setGenError(''); setGenerated(null)
    setStoryAudioUrl(''); setMoralAudioUrl('')
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
          tags:          selected.tags,
          style, lang,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setGenerated(data)

      // Auto-generate caption
      const tags = selected.tags?.slice(0, 8).map(t => `#${t}`).join(' ') || ''
      const langLabel = LANGS.find(l => l.code === lang)?.label || 'English'
      setCaption(
        `${data.title}\n\n${data.moral}\n\n` +
        `📖 ${selected.collection}${selected.hadith_number ? ` #${selected.hadith_number}` : ''}\n` +
        `👤 ${selected.narrator}\n` +
        `${data.source_attribution || data.attribution || ''}\n\n` +
        `🔍 Verify: hadithverifier.com\n\n` +
        `${tags} #hadith #islamic #authentic #${langLabel.toLowerCase()}`
      )
      setStep('preview')
    } catch (e: any) { setGenError(e.message || 'Generation failed') }
    finally { setGenerating(false) }
  }

  // ── Trigger local Remotion render ──────────────────────────────────────────
  // Since Remotion can't run on Vercel, we give the user exact PowerShell
  // commands to run locally with the generated content as props
  function buildRenderCommand(): string {
    if (!generated || !selected) return ''
    const props = {
      hadithArabic:  selected.text_arabic || '',
      hadithText:    selected.text_display || selected.text_english,
      narrator:      selected.narrator,
      collection:    selected.collection,
      hadithNumber:  selected.hadith_number || '',
      story:         generated.story,
      moral:         generated.moral,
      seerahContext: generated.seerah_context,
      attribution:   generated.source_attribution || generated.attribution,
      lang,
      audioUrl:      storyAudioUrl || '',
      bgScene:       lang === 'ar' ? 'kaaba' : lang === 'ru' || lang === 'tj' ? 'mosque' : 'desert',
    }
    const propsJson = JSON.stringify(props).replace(/'/g, "\\'")
    const composition = style === 'kids' ? 'KidsReel' : 'HadithReel'
    const outFile = `out/${composition.toLowerCase()}-${Date.now()}.mp4`
    return `cd "C:\\QA\\Hadith verification AI app\\hadith-reels"\nnpx remotion render remotion/index.tsx ${composition} ${outFile} --props='${propsJson}'`
  }

  // ── Post to Telegram ───────────────────────────────────────────────────────
  async function postToTelegram() {
    setPosting(true); setPostError('')
    try {
      const res = await fetch('/api/telegram/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          caption,
          hadith: selected,
          generated,
          lang,
          style,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setPostDone(true)
      setStep('publish')
    } catch (e: any) { setPostError(e.message || 'Post failed') }
    finally { setPosting(false) }
  }

  // ── Filtered hadiths ───────────────────────────────────────────────────────
  const filtered = hadiths.filter(h => {
    if (!searchQ.trim()) return true
    const q = searchQ.toLowerCase()
    return (h.text_display || h.text_english).toLowerCase().includes(q) ||
      h.narrator.toLowerCase().includes(q) ||
      h.tags?.some(t => t.includes(q))
  })

  // ─────────────────────────────────────────────────────────────────────────
  // LOGIN SCREEN
  // ─────────────────────────────────────────────────────────────────────────
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
            <input type="password" value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              placeholder="Admin password"
              className="w-full bg-slate-700 text-white border border-slate-600 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-slate-400"
              autoFocus />
            {authError && <p className="text-red-400 text-xs text-center">{authError}</p>}
            <button onClick={handleLogin}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors">
              Enter Studio
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ─────────────────────────────────────────────────────────────────────────
  // ADMIN STUDIO
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <header className="bg-slate-800 border-b border-slate-700 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-sm">🎬</div>
          <div>
            <h1 className="text-sm font-bold">Hadith Reels — Admin Studio</h1>
            <p className="text-xs text-slate-400">Create · Preview · Publish</p>
          </div>
          <a href="/" className="ml-auto text-xs text-slate-400 hover:text-white">← Public site</a>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-6">
        <StepBar step={step} />

        {/* ── STEP 1: PICK HADITH ─────────────────────────────────────── */}
        {step === 'pick' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Config */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 space-y-4">
              <h2 className="text-sm font-semibold">Reel config</h2>

              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wide block mb-2">Style</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['adults','kids'] as Style[]).map(s => (
                    <button key={s} onClick={() => setStyle(s)}
                      className={`py-2 px-3 rounded-lg text-xs border transition-colors ${
                        style === s ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-slate-700 text-slate-300 border-slate-600 hover:bg-slate-600'}`}>
                      {s === 'adults' ? '📖 Adults' : '🌟 Kids'}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wide block mb-2">Language</label>
                <div className="space-y-1">
                  {LANGS.map(l => (
                    <button key={l.code} onClick={() => setLang(l.code)}
                      className={`w-full py-2 px-3 rounded-lg text-xs border text-left transition-colors ${
                        lang === l.code ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-slate-700 text-slate-300 border-slate-600 hover:bg-slate-600'}`}>
                      {l.flag} {l.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 uppercase tracking-wide block mb-2">Grade filter</label>
                <div className="flex gap-1">
                  {['all','sahih','hasan'].map(g => (
                    <button key={g} onClick={() => setFilterGrade(g)}
                      className={`text-xs px-2 py-1 rounded border transition-colors ${
                        filterGrade === g ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-slate-700 text-slate-300 border-slate-600'}`}>
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Hadith list */}
            <div className="lg:col-span-2 space-y-3">
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-3">
                <input type="text" value={searchQ}
                  onChange={e => setSearchQ(e.target.value)}
                  placeholder="Search hadiths, tags, narrators..."
                  className="w-full bg-slate-700 text-white border border-slate-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-slate-400" />
                <p className="text-xs text-slate-500 mt-1">{filtered.length} hadiths</p>
              </div>

              {loading && <div className="text-center py-8 text-slate-400 animate-pulse">📚 Loading...</div>}

              <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
                {filtered.map(h => (
                  <div key={h.id} onClick={() => setSelected(h)}
                    className={`bg-slate-800 rounded-xl border p-3 cursor-pointer transition-all ${
                      selected?.id === h.id ? 'border-indigo-500 bg-indigo-900/20' : 'border-slate-700 hover:border-slate-500'}`}>
                    {h.text_arabic && (
                      <p className="text-right text-sm text-amber-200 mb-2 leading-loose" dir="rtl">{h.text_arabic}</p>
                    )}
                    <p className="text-sm text-slate-200 leading-relaxed mb-2">{h.text_display || h.text_english}</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${GRADE_COLORS[h.grade] ?? 'bg-slate-700 text-slate-300 border-slate-600'}`}>{h.grade}</span>
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

              {selected && (
                <div className="bg-indigo-900/30 border border-indigo-700 rounded-xl p-3 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-indigo-300 font-medium">Selected:</p>
                    <p className="text-sm text-white truncate max-w-xs">{selected.collection} #{selected.hadith_number}</p>
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

        {/* ── STEP 2: GENERATE ────────────────────────────────────────── */}
        {step === 'generate' && selected && (
          <div className="max-w-2xl mx-auto space-y-4">
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-slate-400 uppercase tracking-wide">Selected hadith</span>
                <button onClick={() => setStep('pick')} className="text-xs text-slate-400 hover:text-white">← Change</button>
              </div>
              {selected.text_arabic && (
                <p className="text-right text-sm text-amber-200 mb-2 leading-loose" dir="rtl">{selected.text_arabic}</p>
              )}
              <p className="text-sm text-slate-200">{selected.text_display || selected.text_english}</p>
              <div className="flex gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded-full border ${GRADE_COLORS[selected.grade] ?? ''}`}>{selected.grade}</span>
                <span className="text-xs text-slate-400">{selected.collection}</span>
                <span className="text-xs text-slate-400">{LANGS.find(l => l.code === lang)?.flag} {LANGS.find(l => l.code === lang)?.label} · {style === 'adults' ? '📖 Adults' : '🌟 Kids'}</span>
              </div>
            </div>

            {!generating && !generated && (
              <button onClick={generate}
                className="w-full py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-base transition-colors">
                🤖 Generate story + moral + seerah context
              </button>
            )}

            {generating && (
              <div className="text-center py-8">
                <div className="text-3xl mb-3 animate-pulse">✨</div>
                <p className="text-white font-medium">Claude generating reel content...</p>
                <p className="text-slate-400 text-sm mt-1">Story · Moral · Seerah context · Caption</p>
              </div>
            )}

            {genError && (
              <div className="bg-red-900/30 border border-red-700 rounded-xl p-4">
                <p className="text-red-300 text-sm">{genError}</p>
                <button onClick={generate} className="mt-2 text-xs px-3 py-1.5 rounded-lg bg-red-800 hover:bg-red-700 text-white">Retry</button>
              </div>
            )}
          </div>
        )}

        {/* — STEP 3: PREVIEW ————————————————————————— */}
        {step === 'preview' && generated && selected && (
          <>
          <button
            onClick={() => { setStep('pick'); setGenerated(null) }}
            className="mb-4 text-sm text-slate-400 hover:text-white flex items-center gap-1"
          >
            ← Back to hadith picker
          </button>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

            {/* Content + Audio */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Generated content + Audio</h2>

              {/* Title */}
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-2">🎬 Title</div>
                <p className="text-white font-semibold" dir="auto">{generated.title}</p>
              </div>

              {/* Story + Audio */}
              <div className="bg-amber-900/20 rounded-xl border border-amber-800/50 p-4">
                <div className="text-xs text-amber-400 uppercase tracking-wide mb-2">📖 Story — {generated.source_attribution || generated.attribution}</div>
                <p className="text-amber-100 text-sm leading-relaxed" dir="auto">{generated.story}</p>
                <AudioSection
                  text={generated.story}
                  lang={lang} style={style}
                  label="Story narration"
                  onAudioReady={url => setStoryAudioUrl(url)}
                />
              </div>

              {/* Moral + Audio */}
              <div className="bg-emerald-900/20 rounded-xl border border-emerald-800/50 p-4">
                <div className="text-xs text-emerald-400 uppercase tracking-wide mb-2">💡 Moral lesson</div>
                <p className="text-emerald-100 text-sm leading-relaxed" dir="auto">{generated.moral}</p>
                <AudioSection
                  text={generated.moral}
                  lang={lang} style={style}
                  label="Moral narration"
                  onAudioReady={url => setMoralAudioUrl(url)}
                />
              </div>

              {/* Seerah context */}
              {generated.seerah_context && (
                <div className="bg-blue-900/20 rounded-xl border border-blue-800/50 p-4">
                  <div className="text-xs text-blue-400 uppercase tracking-wide mb-2">🕌 Historical context</div>
                  <p className="text-blue-100 text-sm leading-relaxed" dir="auto">{generated.seerah_context}</p>
                </div>
              )}

              {/* Regenerate */}
              <button onClick={() => { setStep('generate'); setGenerated(null) }}
                className="w-full py-2 rounded-xl border border-slate-600 text-slate-400 hover:text-white hover:border-slate-400 text-sm transition-colors">
                🔄 Regenerate
              </button>
            </div>

            {/* Caption + Render + Publish */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Caption + Render + Publish</h2>

              {/* Caption editor */}
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-2">📱 Social media caption</div>
                <textarea value={caption} onChange={e => setCaption(e.target.value)} rows={9}
                  className="w-full bg-slate-700 text-slate-200 border border-slate-600 rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                <button
                  onClick={() => { navigator.clipboard.writeText(caption); setCopiedCaption(true); setTimeout(() => setCopiedCaption(false), 2000) }}
                  className="mt-2 w-full py-2 rounded-lg bg-indigo-700 hover:bg-indigo-600 text-white text-sm transition-colors">
                  {copiedCaption ? '✓ Copied!' : 'Copy caption'}
                </button>
              </div>

              {/* Render MP4 commands */}
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-3">🎬 Render MP4 (local)</div>
                <div className="bg-slate-900 rounded-lg p-3 text-xs text-green-400 font-mono overflow-x-auto mb-3">
                  <div className="text-slate-500 mb-1"># Run in PowerShell:</div>
                  <div>cd "C:\QA\Hadith verification AI app\hadith-reels"</div>
                  <div className="mt-1 text-yellow-300">npm run remotion:{style === 'kids' ? 'kids' : 'adults'}</div>
                </div>
                <p className="text-xs text-slate-500">
                  {storyAudioUrl ? '✅ Audio generated — re-render to include narration' : '⚠️ Generate audio first for reel with narration'}
                </p>
              </div>

              {/* Telegram post */}
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-3">📤 Publish to Telegram</div>
                <p className="text-xs text-slate-500 mb-3">
                  Posts caption + hadith text to your Telegram channel.
                  For video: render MP4 locally, then upload manually.
                </p>
                <button onClick={postToTelegram} disabled={posting}
                  className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold disabled:opacity-50 transition-colors">
                  {posting ? '⏳ Posting...' : '✈️ Post to Telegram channel'}
                </button>
                {postError && <p className="text-red-400 text-xs mt-2">{postError}</p>}
              </div>

              {/* Other platforms */}
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-4 space-y-2">
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-2">📤 Other platforms</div>
                {[
                  { label: 'Instagram Reels', url: 'https://www.instagram.com/', color: 'from-purple-600 to-pink-600' },
                  { label: 'TikTok', url: 'https://www.tiktok.com/', color: 'from-slate-700 to-slate-600' },
                  { label: 'YouTube Shorts', url: 'https://studio.youtube.com/', color: 'from-red-700 to-red-600' },
                ].map(p => (
                  <a key={p.label} href={p.url} target="_blank" rel="noopener noreferrer"
                    className={`flex items-center justify-between w-full py-2 px-4 rounded-xl bg-gradient-to-r ${p.color} text-white text-sm hover:opacity-90 transition-opacity`}>
                    <span>{p.label}</span>
                    <span className="text-xs opacity-70">Open ↗</span>
                  </a>
                ))}
              </div>

              <button onClick={() => setStep('publish')}
                className="w-full py-3 rounded-xl bg-green-700 hover:bg-green-600 text-white font-semibold text-sm transition-colors">
                ✅ Mark as published
              </button>
            </div>
          </div>
        </div>
          </>
        )}

        {/* ── STEP 4: PUBLISHED ───────────────────────────────────────── */}
        {step === 'publish' && (
          <div className="max-w-md mx-auto text-center py-16">
            <div className="text-5xl mb-4">{postDone ? '🎉' : '✅'}</div>
            <h2 className="text-white text-xl font-bold mb-2">
              {postDone ? 'Posted to Telegram!' : 'Reel complete!'}
            </h2>
            <p className="text-slate-400 text-sm mb-8">
              {postDone
                ? 'Your hadith reel has been shared with the community. JazakAllahu Khairan!'
                : 'Great work. The reel is ready to share.'}
            </p>
            <button onClick={() => {
              setSelected(null); setGenerated(null); setCaption('')
              setStoryAudioUrl(''); setMoralAudioUrl('')
              setPostDone(false); setStep('pick')
            }} className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors">
              Create another reel →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
