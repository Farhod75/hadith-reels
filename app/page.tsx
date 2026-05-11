'use client'

import { useState, useEffect } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────
type Lang = 'en' | 'uz' | 'ar' | 'ru'
type Grade = 'sahih' | 'hasan' | 'daif' | 'all'
type Tab = 'browse' | 'generate' | 'my_reels'

interface Reel {
  id: string
  title: string
  hadith_text: string
  hadith_arabic?: string
  narrator: string
  collection: string
  hadith_number?: string
  grade: string
  style: 'adults' | 'kids'
  lang: Lang
  audio_url?: string
  created_at: string
  status: 'ready' | 'generating' | 'error'
}

// ─── Constants ────────────────────────────────────────────────────────────────
const LANG_LABELS: Record<Lang, string> = {
  en: '🇬🇧 English',
  uz: '🇺🇿 Uzbek',
  ar: '🇸🇦 Arabic',
  ru: '🇷🇺 Russian',
}

const GRADE_COLORS: Record<string, string> = {
  sahih: 'bg-green-100 text-green-700 border-green-200',
  hasan: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  daif:  'bg-red-100 text-red-700 border-red-200',
}

const STYLE_INFO = {
  adults: { icon: '📖', label: 'Adults', desc: 'Elegant calligraphy style' },
  kids:   { icon: '🌟', label: 'Kids',   desc: 'Colorful, animated style' },
}

// ─── Sample data (replace with Supabase fetch) ────────────────────────────────
const SAMPLE_REELS: Reel[] = [
  {
    id: '1',
    title: 'Kindness to Neighbors',
    hadith_text: 'The Messenger of Allah ﷺ said: "Whoever believes in Allah and the Last Day, let him be kind to his neighbor."',
    hadith_arabic: 'مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيُحْسِنْ إِلَى جَارِهِ',
    narrator: 'Abu Shuraih Al-Adawi',
    collection: 'Sahih al-Bukhari',
    hadith_number: '6019',
    grade: 'sahih',
    style: 'adults',
    lang: 'en',
    created_at: new Date().toISOString(),
    status: 'ready',
  },
  {
    id: '2',
    title: 'Smile is Sadaqah',
    hadith_text: 'The Prophet ﷺ said: "Your smile for your brother is charity."',
    hadith_arabic: 'تَبَسُّمُكَ فِي وَجْهِ أَخِيكَ لَكَ صَدَقَةٌ',
    narrator: 'Abu Dharr',
    collection: 'Jami at-Tirmidhi',
    hadith_number: '1956',
    grade: 'sahih',
    style: 'kids',
    lang: 'en',
    created_at: new Date().toISOString(),
    status: 'ready',
  },
  {
    id: '3',
    title: 'Cleanliness is Half of Faith',
    hadith_text: 'The Prophet ﷺ said: "Cleanliness is half of faith."',
    hadith_arabic: 'الطُّهُورُ شَطْرُ الْإِيمَانِ',
    narrator: 'Abu Malik al-Ashari',
    collection: 'Sahih Muslim',
    hadith_number: '223',
    grade: 'sahih',
    style: 'kids',
    lang: 'en',
    created_at: new Date().toISOString(),
    status: 'ready',
  },
]

// ─── Components ───────────────────────────────────────────────────────────────
function GradeBadge({ grade }: { grade: string }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${GRADE_COLORS[grade] ?? 'bg-gray-100 text-gray-600 border-gray-200'}`}>
      {grade}
    </span>
  )
}

function StyleBadge({ style }: { style: 'adults' | 'kids' }) {
  const info = STYLE_INFO[style]
  return (
    <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100 font-medium">
      {info.icon} {info.label}
    </span>
  )
}

function ReelCard({ reel }: { reel: Reel }) {
  const [copied, setCopied] = useState(false)

  function copyText() {
    navigator.clipboard.writeText(reel.hadith_text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:border-emerald-200 hover:shadow-sm transition-all">
      {/* Arabic text */}
      {reel.hadith_arabic && (
        <div className="text-lg text-right leading-loose text-gray-800 mb-3 p-3 bg-amber-50 rounded-lg border border-amber-100" dir="rtl">
          {reel.hadith_arabic}
        </div>
      )}

      {/* English text */}
      <p className="text-sm text-gray-700 leading-relaxed mb-3">{reel.hadith_text}</p>

      {/* Meta row */}
      <div className="flex items-center gap-2 flex-wrap mb-3">
        <GradeBadge grade={reel.grade} />
        <StyleBadge style={reel.style} />
        <span className="text-xs text-gray-400">{reel.collection}</span>
        {reel.hadith_number && <span className="text-xs text-gray-400">#{reel.hadith_number}</span>}
        <span className="text-xs text-gray-400 ml-auto">{reel.narrator}</span>
      </div>

      {/* Actions */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={copyText}
          className="text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors"
        >
          {copied ? '✓ Copied' : 'Copy text'}
        </button>
        <a
          href={`https://sunnah.com/${reel.collection.toLowerCase().replace(/\s+/g, '-')}:${reel.hadith_number}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
        >
          View source ↗
        </a>
        <a
          href={`https://hadithverifier.com`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs px-3 py-1.5 rounded-lg border border-amber-200 text-amber-700 hover:bg-amber-50 transition-colors ml-auto"
        >
          🔍 Verify
        </a>
      </div>
    </div>
  )
}

function GenerateForm({ onGenerate }: { onGenerate: (text: string, style: 'adults' | 'kids', lang: Lang) => void }) {
  const [hadithText, setHadithText] = useState('')
  const [style, setStyle]           = useState<'adults' | 'kids'>('adults')
  const [lang, setLang]             = useState<Lang>('en')
  const [loading, setLoading]       = useState(false)

  async function handleSubmit() {
    if (!hadithText.trim()) return
    setLoading(true)
    // Simulate generation — replace with real Remotion/ElevenLabs call
    await new Promise(r => setTimeout(r, 1500))
    onGenerate(hadithText, style, lang)
    setLoading(false)
    setHadithText('')
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-2">
          Hadith text
        </label>
        <textarea
          value={hadithText}
          onChange={e => setHadithText(e.target.value)}
          placeholder="Paste a verified hadith text... or search from the Browse tab"
          rows={4}
          className="w-full text-sm text-gray-800 border border-gray-200 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-300 focus:border-transparent"
        />
        <p className="text-xs text-gray-400 mt-1">
          ⚠️ Only use authenticated hadiths.{' '}
          <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer" className="text-amber-600 underline hover:text-amber-700">
            Verify first at hadithverifier.com
          </a>
        </p>
      </div>

      {/* Style selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-3">
          Reel style
        </label>
        <div className="grid grid-cols-2 gap-3">
          {(['adults', 'kids'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStyle(s)}
              className={`p-3 rounded-xl border-2 text-left transition-all ${
                style === s
                  ? 'border-emerald-500 bg-emerald-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-1">{STYLE_INFO[s].icon}</div>
              <div className="text-sm font-medium text-gray-800">{STYLE_INFO[s].label}</div>
              <div className="text-xs text-gray-500">{STYLE_INFO[s].desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Language selector */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <label className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-3">
          Narration language
        </label>
        <div className="grid grid-cols-2 gap-2">
          {(Object.entries(LANG_LABELS) as [Lang, string][]).map(([code, label]) => (
            <button
              key={code}
              onClick={() => setLang(code)}
              className={`py-2 px-3 rounded-lg text-sm border transition-colors ${
                lang === code
                  ? 'border-emerald-500 bg-emerald-50 text-emerald-700 font-medium'
                  : 'border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={!hadithText.trim() || loading}
        className="w-full py-3 rounded-xl bg-emerald-700 text-white font-medium text-sm hover:bg-emerald-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? '🎬 Generating reel...' : '🎬 Generate reel'}
      </button>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function HadithReelsPage() {
  const [tab, setTab]             = useState<Tab>('browse')
  const [filterGrade, setFilterGrade] = useState<Grade>('all')
  const [filterStyle, setFilterStyle] = useState<'all' | 'adults' | 'kids'>('all')
  const [reels, setReels]         = useState<Reel[]>(SAMPLE_REELS)
  const [myReels, setMyReels]     = useState<Reel[]>([])
  const [toast, setToast]         = useState<string | null>(null)

  function showToast(msg: string) {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  function handleGenerate(text: string, style: 'adults' | 'kids', lang: Lang) {
    const newReel: Reel = {
      id: Date.now().toString(),
      title: 'Custom reel',
      hadith_text: text,
      narrator: 'Custom',
      collection: 'Custom',
      grade: 'sahih',
      style,
      lang,
      created_at: new Date().toISOString(),
      status: 'ready',
    }
    setMyReels(prev => [newReel, ...prev])
    setTab('my_reels')
    showToast('✅ Reel generated! View in My Reels tab.')
  }

  const filteredReels = reels.filter(r => {
    if (filterGrade !== 'all' && r.grade !== filterGrade) return false
    if (filterStyle !== 'all' && r.style !== filterStyle) return false
    return true
  })

  return (
    <div className="min-h-screen bg-gray-50 font-sans">

      {/* ── HEADER ─────────────────────────────────────────────────────────── */}
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-700 flex items-center justify-center text-white text-lg flex-shrink-0">
            🎬
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-semibold text-gray-900">Hadith Reels</h1>
            <p className="text-xs text-gray-500 truncate">
              Authentic hadith · Short reels · EN · UZ · AR · RU
            </p>
          </div>
          <div className="hidden sm:flex gap-3 text-center flex-shrink-0">
            <div>
              <div className="text-lg font-semibold text-gray-900">{reels.length}</div>
              <div className="text-xs text-gray-500">Reels</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-green-700">
                {reels.filter(r => r.grade === 'sahih').length}
              </div>
              <div className="text-xs text-gray-500">Sahih</div>
            </div>
          </div>
        </div>
      </header>

      {/* ── HV CROSS-LINK BANNER ───────────────────────────────────────────── */}
      <div className="bg-amber-900/10 text-amber-800 text-xs text-center py-1.5 px-4 border-b border-amber-200/60">
        🔍 Verify any hadith before sharing at{' '}
        <a
          href="https://hadithverifier.com"
          target="_blank"
          rel="noopener noreferrer"
          className="underline font-medium hover:text-amber-900"
        >
          hadithverifier.com
        </a>
      </div>

      {/* ── TABS ───────────────────────────────────────────────────────────── */}
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex gap-1 border-b border-gray-200 overflow-x-auto">
          {([
            { key: 'browse',    label: '📚 Browse reels' },
            { key: 'generate',  label: '🎬 Generate' },
            { key: 'my_reels',  label: `⭐ My reels${myReels.length ? ` (${myReels.length})` : ''}` },
          ] as { key: Tab; label: string }[]).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-4 py-3 text-sm whitespace-nowrap border-b-2 -mb-px transition-colors ${
                tab === key
                  ? 'border-indigo-600 text-indigo-700 font-medium'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── MAIN ───────────────────────────────────────────────────────────── */}
      <main className="max-w-3xl mx-auto px-4 py-6 space-y-4">

        {/* BROWSE TAB */}
        {tab === 'browse' && (
          <>
            {/* Filters */}
            <div className="bg-white rounded-xl border border-gray-200 p-3 flex gap-3 flex-wrap items-center">
              <div className="flex gap-1">
                <span className="text-xs text-gray-500 self-center mr-1">Grade:</span>
                {(['all', 'sahih', 'hasan', 'daif'] as Grade[]).map(g => (
                  <button
                    key={g}
                    onClick={() => setFilterGrade(g)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                      filterGrade === g
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>
              <div className="flex gap-1">
                <span className="text-xs text-gray-500 self-center mr-1">Style:</span>
                {(['all', 'adults', 'kids'] as const).map(s => (
                  <button
                    key={s}
                    onClick={() => setFilterStyle(s)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                      filterStyle === s
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {s === 'adults' ? '📖 Adults' : s === 'kids' ? '🌟 Kids' : 'all'}
                  </button>
                ))}
              </div>
              <span className="text-xs text-gray-400 ml-auto">{filteredReels.length} reels</span>
            </div>

            {/* Reel cards */}
            {filteredReels.length === 0 ? (
              <div className="text-center py-12 text-gray-400 text-sm">No reels match your filters.</div>
            ) : (
              <div className="space-y-3">
                {filteredReels.map(r => <ReelCard key={r.id} reel={r} />)}
              </div>
            )}
          </>
        )}

        {/* GENERATE TAB */}
        {tab === 'generate' && (
          <GenerateForm onGenerate={handleGenerate} />
        )}

        {/* MY REELS TAB */}
        {tab === 'my_reels' && (
          <>
            {myReels.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-3">🎬</div>
                <p className="text-gray-500 text-sm mb-4">No reels generated yet.</p>
                <button
                  onClick={() => setTab('generate')}
                  className="text-sm px-4 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
                >
                  Generate your first reel
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {myReels.map(r => <ReelCard key={r.id} reel={r} />)}
              </div>
            )}
          </>
        )}

        {/* FOOTER NOTE */}
        <div className="text-center text-xs text-gray-400 pt-4 pb-8 border-t border-gray-100">
          All hadiths are sourced from authenticated collections.{' '}
          <a href="https://hadithverifier.com" target="_blank" rel="noopener noreferrer" className="text-amber-600 underline hover:text-amber-700">
            Verify any hadith →
          </a>
        </div>

      </main>

      {/* ── TOAST ──────────────────────────────────────────────────────────── */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-sm px-4 py-2.5 rounded-xl shadow-lg z-50 animate-fade-in">
          {toast}
        </div>
      )}
    </div>
  )
}
