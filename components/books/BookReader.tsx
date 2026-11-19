'use client'
// components/books/BookReader.tsx - the reading view for one section of a book.
// Font size, line spacing, background and font are the reader's choice; a tap on any
// paragraph offers a bookmark or a note; the place the reader stopped is remembered.
// All of it lives in this browser only (storage.ts) - no account, nothing sent anywhere.

import Link from 'next/link'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  DEFAULT_SETTINGS, loadMarks, loadSettings, saveMarks, savePosition, saveSettings,
  type Mark, type ReaderSettings,
} from './storage'

interface Props {
  book: string; lang: string; vol: number; sec: number; total: number
  bookTitle: string; volumeTitle: string; sectionTitle: string
  html: string; footnotes: { n: number; html: string }[]
  closed: boolean; ui: Record<string, string>; htmlLang: string
}

const THEMES = {
  light: { bg: '#ffffff', fg: '#1f2937', muted: '#6b7280', panel: '#f9fafb', border: '#e5e7eb', mark: '#eef2ff' },
  sepia: { bg: '#f8f1e3', fg: '#3b2f22', muted: '#8a7a63', panel: '#efe6d2', border: '#e2d5b9', mark: '#f1e2b8' },
  dark:  { bg: '#16181d', fg: '#d6d3cd', muted: '#8b8f98', panel: '#20232a', border: '#2f333c', mark: '#2b3047' },
}
const BLOCKS = 'p, h2, h3, h4, blockquote, ul, ol, table, figure'

export default function BookReader(p: Props) {
  const t = p.ui
  const [s, setS] = useState<ReaderSettings>(DEFAULT_SETTINGS)
  const [marks, setMarks] = useState<Mark[]>([])
  const [panel, setPanel] = useState<'none' | 'settings' | 'marks'>('none')
  const [sel, setSel] = useState<number | null>(null)
  const [editing, setEditing] = useState<{ idx: number; text: string } | null>(null)
  const body = useRef<HTMLDivElement>(null)
  const base = `/books/${p.book}/${p.lang}/${p.vol}`
  const th = THEMES[s.theme]

  useEffect(() => { setS(loadSettings()); setMarks(loadMarks(p.book, p.lang)) }, [p.book, p.lang])
  const update = (patch: Partial<ReaderSettings>) => setS(prev => { const n = { ...prev, ...patch }; saveSettings(n); return n })

  const here = useMemo(() => marks.filter(m => m.vol === p.vol && m.sec === p.sec), [marks, p.vol, p.sec])

  // number every block once, so a bookmark points at the same paragraph next time
  useEffect(() => {
    const root = body.current
    if (!root) return
    root.querySelectorAll<HTMLElement>(':scope > *').forEach((el, i) => {
      if (el.matches(BLOCKS)) { el.dataset.idx = String(i); if (!el.id) el.id = `p-${i}` }
    })
    const h = decodeURIComponent(window.location.hash.slice(1))
    const target = /^p-\d+$/.test(h)
      ? root.querySelector<HTMLElement>(`[data-idx="${h.slice(2)}"]`)
      : h ? document.getElementById(h) : null
    target?.scrollIntoView()
  }, [p.html])

  // show which paragraphs carry a bookmark or a note
  useEffect(() => {
    const root = body.current
    if (!root) return
    root.querySelectorAll<HTMLElement>('[data-idx]').forEach(el => {
      const m = here.find(x => x.idx === Number(el.dataset.idx))
      el.classList.toggle('bk-marked', !!m)
      el.classList.toggle('bk-selected', sel === Number(el.dataset.idx))
      el.querySelector(':scope > .bk-note')?.remove()
      if (m?.note) {
        const n = document.createElement('div')
        n.className = 'bk-note'; n.textContent = '✎ ' + m.note
        el.appendChild(n)
      }
    })
  }, [here, sel, p.html])

  // remember where the reader is: the first paragraph at the top of the screen
  useEffect(() => {
    const root = body.current
    if (!root) return
    let timer: ReturnType<typeof setTimeout> | null = null
    const onScroll = () => {
      if (timer) return
      timer = setTimeout(() => {
        timer = null
        const els = root.querySelectorAll<HTMLElement>('[data-idx]')
        for (const el of els) {
          if (el.getBoundingClientRect().bottom > 80) {
            savePosition(p.book, p.lang, { vol: p.vol, sec: p.sec, idx: Number(el.dataset.idx), at: Date.now() })
            break
          }
        }
      }, 600)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => { window.removeEventListener('scroll', onScroll); if (timer) clearTimeout(timer) }
  }, [p.book, p.lang, p.vol, p.sec, p.html])

  const onBodyClick = useCallback((e: React.MouseEvent) => {
    const target = e.target as HTMLElement
    if (target.closest('a')) return
    const el = target.closest<HTMLElement>('[data-idx]')
    setSel(el ? (sel === Number(el.dataset.idx) ? null : Number(el.dataset.idx)) : null)
  }, [sel])

  const excerptOf = (idx: number) => {
    const el = body.current?.querySelector<HTMLElement>(`[data-idx="${idx}"]`)
    const text = (el?.innerText || '').replace(/✎[\s\S]*$/, '').replace(/\s+/g, ' ').trim()
    return text.length > 140 ? text.slice(0, 140) + '…' : text
  }
  const store = (next: Mark[]) => { setMarks(next); saveMarks(p.book, p.lang, next) }
  const findMark = (idx: number) => marks.find(m => m.vol === p.vol && m.sec === p.sec && m.idx === idx)
  const toggleBookmark = (idx: number) => {
    const m = findMark(idx)
    if (m) store(marks.filter(x => x !== m))
    else store([...marks, { vol: p.vol, sec: p.sec, idx, excerpt: excerptOf(idx), note: '', at: Date.now() }])
    setSel(null)
  }
  const saveNote = () => {
    if (!editing) return
    const m = findMark(editing.idx)
    const note = editing.text.trim()
    if (m) store(marks.map(x => (x === m ? { ...x, note } : x)))
    else store([...marks, { vol: p.vol, sec: p.sec, idx: editing.idx, excerpt: excerptOf(editing.idx), note, at: Date.now() }])
    setEditing(null); setSel(null)
  }
  const removeMark = (m: Mark) => store(marks.filter(x => x !== m))

  const sorted = [...marks].sort((a, b) => a.vol - b.vol || a.sec - b.sec || a.idx - b.idx)
  const btn = { border: `1px solid ${th.border}`, background: th.panel, color: th.fg }

  return (
    <main lang={p.htmlLang} style={{ background: th.bg, color: th.fg, minHeight: '100vh' }}>
      <style>{`
        .bk-body { font-size: ${s.size}px; line-height: ${s.line}; font-family: ${s.font === 'serif'
          ? "Georgia, 'Times New Roman', 'Noto Serif', serif" : "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"}; }
        .bk-body > p, .bk-body > blockquote, .bk-body > ul, .bk-body > ol { margin: 0 0 0.9em; }
        .bk-body h2 { font-size: 1.45em; font-weight: 700; margin: 1.4em 0 0.6em; line-height: 1.3; }
        .bk-body h3 { font-size: 1.2em; font-weight: 700; margin: 1.2em 0 0.5em; line-height: 1.3; }
        .bk-body h4 { font-size: 1.05em; font-weight: 700; margin: 1em 0 0.4em; }
        .bk-body blockquote { border-left: 3px solid ${th.border}; padding-left: 0.9em; color: ${th.muted}; }
        .bk-body ul { list-style: disc; padding-left: 1.4em; } .bk-body ol { list-style: decimal; padding-left: 1.4em; }
        .bk-body table { border-collapse: collapse; font-size: 0.85em; margin: 0 0 1em; width: 100%; }
        .bk-body td, .bk-body th { border: 1px solid ${th.border}; padding: 0.3em 0.5em; vertical-align: top; }
        .bk-body img { max-width: 100%; height: auto; margin: 0.5em auto; display: block; }
        .bk-body .pdf-mark { font-family: system-ui, sans-serif; font-size: 11px; color: ${th.muted}; text-align: right;
          border-top: 1px dashed ${th.border}; margin: 1.2em 0 0.6em; padding-top: 2px; user-select: none; }
        .bk-body sup.fn a { color: #4f46e5; text-decoration: none; font-size: 0.75em; padding: 0 1px; }
        .bk-body [data-idx] { border-radius: 6px; transition: background .15s; cursor: pointer; }
        .bk-body .bk-marked { background: ${th.mark}; box-shadow: -6px 0 0 ${th.mark}, 6px 0 0 ${th.mark}; position: relative; }
        .bk-body .bk-marked::before { content: '🔖'; position: absolute; left: -1.6em; top: 0; font-size: 0.8em; }
        .bk-body .bk-selected { outline: 2px solid #6366f1; outline-offset: 3px; }
        .bk-body .bk-note { font-family: system-ui, sans-serif; font-size: 0.8em; color: ${th.muted}; margin-top: 0.3em;
          padding: 0.3em 0.6em; border-left: 3px solid #6366f1; white-space: pre-wrap; }
      `}</style>

      {/* top bar */}
      <div style={{ background: th.bg, borderBottom: `1px solid ${th.border}` }} className="sticky top-0 z-20">
        <div className="max-w-2xl mx-auto px-4 py-2 flex items-center gap-2">
          <Link href={base} className="text-sm whitespace-nowrap" style={{ color: '#4f46e5' }}>☰ {t.contents}</Link>
          <div className="flex-1 min-w-0 text-center">
            <div className="text-xs truncate" style={{ color: th.muted }}>{p.bookTitle} · {p.volumeTitle}</div>
            <div className="text-[11px]" style={{ color: th.muted }}>{p.sec} {t.of} {p.total}</div>
          </div>
          <button onClick={() => setPanel(panel === 'settings' ? 'none' : 'settings')} aria-label={t.settings}
            className="px-2.5 py-1 rounded-lg text-sm font-serif" style={btn}>Aa</button>
          <button onClick={() => setPanel(panel === 'marks' ? 'none' : 'marks')} aria-label={t.marks}
            className="px-2.5 py-1 rounded-lg text-sm" style={btn} data-testid="marks-button">🔖 {marks.length || ''}</button>
        </div>

        {panel === 'settings' && (
          <div className="max-w-2xl mx-auto px-4 pb-3 space-y-2 text-sm" data-testid="settings-panel">
            <Row label={t.fontSize}>
              <button style={btn} className="px-3 py-1 rounded-lg" onClick={() => update({ size: Math.max(14, s.size - 1) })}>A−</button>
              <span className="w-10 text-center tabular-nums">{s.size}</span>
              <button style={btn} className="px-3 py-1 rounded-lg" onClick={() => update({ size: Math.min(32, s.size + 1) })}>A+</button>
            </Row>
            <Row label={t.lineSpacing}>
              {[1.5, 1.75, 2.0].map(v => (
                <button key={v} style={{ ...btn, outline: s.line === v ? '2px solid #6366f1' : undefined }}
                  className="px-3 py-1 rounded-lg" onClick={() => update({ line: v })}>{v}</button>
              ))}
            </Row>
            <Row label={t.theme}>
              {(['light', 'sepia', 'dark'] as const).map(k => (
                <button key={k} onClick={() => update({ theme: k })} className="px-3 py-1 rounded-lg"
                  style={{ background: THEMES[k].bg, color: THEMES[k].fg, border: `1px solid ${THEMES[k].border}`,
                    outline: s.theme === k ? '2px solid #6366f1' : undefined }}>{t[k]}</button>
              ))}
            </Row>
            <Row label={t.font}>
              {(['serif', 'sans'] as const).map(k => (
                <button key={k} onClick={() => update({ font: k })} className="px-3 py-1 rounded-lg"
                  style={{ ...btn, fontFamily: k === 'serif' ? 'Georgia, serif' : 'system-ui, sans-serif',
                    outline: s.font === k ? '2px solid #6366f1' : undefined }}>{t[k]}</button>
              ))}
            </Row>
            <p className="text-xs" style={{ color: th.muted }}>{t.tapHint} · {t.saved}</p>
          </div>
        )}

        {panel === 'marks' && (
          <div className="max-w-2xl mx-auto px-4 pb-3 max-h-[60vh] overflow-y-auto" data-testid="marks-panel">
            <div className="text-sm font-semibold mb-2">{t.marks}</div>
            {sorted.length === 0 && <p className="text-sm" style={{ color: th.muted }}>{t.noMarks}</p>}
            <ul className="space-y-2">
              {sorted.map(m => (
                <li key={`${m.vol}-${m.sec}-${m.idx}`} className="rounded-lg p-2 text-sm" style={{ background: th.panel, border: `1px solid ${th.border}` }}>
                  <Link href={`/books/${p.book}/${p.lang}/${m.vol}/${m.sec}#p-${m.idx}`} onClick={() => setPanel('none')}
                    className="block" style={{ color: th.fg }}>
                    <span className="text-xs" style={{ color: th.muted }}>{t.volume} {m.vol} · {m.sec} — </span>{m.excerpt}
                  </Link>
                  {m.note && <p className="mt-1 text-xs whitespace-pre-wrap" style={{ color: th.muted }}>✎ {m.note}</p>}
                  <button onClick={() => removeMark(m)} className="mt-1 text-xs" style={{ color: '#dc2626' }}>{t.del}</button>
                </li>
              ))}
            </ul>
            <p className="text-xs mt-2" style={{ color: th.muted }}>{t.saved}</p>
          </div>
        )}
      </div>

      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-6">
        {p.closed && (
          <p className="text-xs rounded-lg px-3 py-2 mb-4" style={{ background: '#fef3c7', color: '#92400e' }}>🔒 {t.closed}</p>
        )}
        <div ref={body} className="bk-body" onClick={onBodyClick} dangerouslySetInnerHTML={{ __html: p.html }} />

        {p.footnotes.length > 0 && (
          <section className="mt-8 pt-4 text-sm" style={{ borderTop: `1px solid ${th.border}`, color: th.muted }}>
            <h2 className="font-semibold mb-2" style={{ color: th.fg }}>{t.footnotes}</h2>
            <ol className="space-y-1.5">
              {p.footnotes.map(f => (
                <li key={f.n} id={`fn-${p.sec}-${f.n}`}>
                  <a href={`#fr-${p.sec}-${f.n}`} style={{ color: '#4f46e5' }}>{f.n}.</a>{' '}
                  <span dangerouslySetInnerHTML={{ __html: f.html }} />
                </li>
              ))}
            </ol>
          </section>
        )}

        <nav className="flex items-center justify-between gap-3 mt-10 mb-16">
          {p.sec > 1
            ? <Link href={`${base}/${p.sec - 1}`} className="px-4 py-2 rounded-xl text-sm" style={btn}>{t.prev}</Link>
            : <span />}
          <span className="text-xs" style={{ color: th.muted }}>{p.sec} / {p.total}</span>
          {p.sec < p.total
            ? <Link href={`${base}/${p.sec + 1}`} className="px-4 py-2 rounded-xl text-sm" style={{ background: '#4338ca', color: '#fff' }}>{t.next}</Link>
            : <Link href={`/books/${p.book}/${p.lang}`} className="px-4 py-2 rounded-xl text-sm" style={btn}>{t.contents}</Link>}
        </nav>
      </div>

      {/* paragraph actions */}
      {sel !== null && !editing && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-30 flex gap-2 rounded-2xl px-3 py-2 shadow-lg"
          style={{ background: th.panel, border: `1px solid ${th.border}` }} data-testid="para-actions">
          <button onClick={() => toggleBookmark(sel)} className="px-3 py-1.5 rounded-lg text-sm" style={btn}>
            🔖 {findMark(sel) ? t.del : t.bookmark}
          </button>
          <button onClick={() => setEditing({ idx: sel, text: findMark(sel)?.note ?? '' })} className="px-3 py-1.5 rounded-lg text-sm" style={btn}>
            ✎ {t.note}
          </button>
          <button onClick={() => setSel(null)} className="px-2 py-1.5 rounded-lg text-sm" style={{ color: th.muted }}>✕</button>
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 z-40 flex items-end sm:items-center justify-center bg-black/40 p-3" onClick={() => setEditing(null)}>
          <div className="w-full max-w-lg rounded-2xl p-4" style={{ background: th.bg, border: `1px solid ${th.border}` }}
            onClick={e => e.stopPropagation()}>
            <p className="text-xs mb-2" style={{ color: th.muted }}>{excerptOf(editing.idx)}</p>
            <textarea autoFocus value={editing.text} onChange={e => setEditing({ ...editing, text: e.target.value })}
              placeholder={t.notePlaceholder} rows={5} className="w-full rounded-lg p-2 text-sm"
              style={{ background: th.panel, color: th.fg, border: `1px solid ${th.border}` }} data-testid="note-input" />
            <div className="flex justify-end gap-2 mt-2">
              <button onClick={() => setEditing(null)} className="px-3 py-1.5 rounded-lg text-sm" style={btn}>{t.cancel}</button>
              <button onClick={saveNote} className="px-3 py-1.5 rounded-lg text-sm" style={{ background: '#4338ca', color: '#fff' }}>{t.save}</button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="w-40 text-xs opacity-70">{label}</span>
      {children}
    </div>
  )
}
