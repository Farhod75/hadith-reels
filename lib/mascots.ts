// Single source of truth for the kids mascot rotation.
// The still filenames must match assets/asset-registry.json exactly —
// audit-assets.py --check gates on them at render time (P117/P121/P157).

export type MascotKey = 'lamb-boy' | 'lamb-girl' | 'camel' | 'hoopoe' | 'bee'

export type MascotGender = 'boy' | 'girl'

export interface Mascot {
  key: MascotKey
  label: string
  emoji: string
  gender: MascotGender   // drives voice selection (P103/P104)
  still: string          // registry filename
}

export const MASCOTS: Mascot[] = [
  { key: 'lamb-boy',  label: 'Boy lamb · Uzbek tyubeteika', emoji: '🐑', gender: 'boy',  still: 'lamb-boy-mosque-night-v3.png' },
  { key: 'lamb-girl', label: 'Girl lamb · khan-atlas',      emoji: '🐑', gender: 'girl', still: 'lamb-girl-garden-day-v2.png' },
  { key: 'camel',     label: 'Camel · Chust doppa',         emoji: '🐪', gender: 'boy',  still: 'camel-dawn-v1.png' },
  { key: 'hoopoe',    label: 'Hoopoe · Kyrgyz kalpak',      emoji: '🐦', gender: 'boy',  still: 'hoopoe-garden-v2.png' },
  { key: 'bee',       label: 'Bee · Tajik toqi',            emoji: '🐝', gender: 'girl', still: 'bee-orchard-v1.png' },
]

export function mascotGender(key: MascotKey): MascotGender {
  const m = MASCOTS.find(x => x.key === key)
  if (!m) throw new Error(`unknown mascot: ${key}`)
  return m.gender
}