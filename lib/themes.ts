export const THEMES = {
  // ── Adults themes ──────────────────────────────────────
  desert_night: {
    audience: 'adults' as const,
    name: 'Desert Night',
    bg: 'linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0d1b2a 100%)',
    accent: '#f59e0b',
    text: '#fef9f0',
    subtitle: '#fbbf24',
    particle: '✦',
    emoji: '🌙',
  },
  golden_mosque: {
    audience: 'adults' as const,
    name: 'Golden Mosque',
    bg: 'linear-gradient(135deg, #1a0a00 0%, #3d1f00 50%, #1a0a00 100%)',
    accent: '#fbbf24',
    text: '#fffbeb',
    subtitle: '#fde68a',
    particle: '☽',
    emoji: '🕌',
  },
  ocean_dawn: {
    audience: 'adults' as const,
    name: 'Ocean Dawn',
    bg: 'linear-gradient(135deg, #0c1445 0%, #1e3a5f 50%, #0f2027 100%)',
    accent: '#38bdf8',
    text: '#f0f9ff',
    subtitle: '#7dd3fc',
    particle: '◆',
    emoji: '🌊',
  },
  forest: {
    audience: 'adults' as const,
    name: 'Forest',
    bg: 'linear-gradient(135deg, #052e16 0%, #14532d 50%, #052e16 100%)',
    accent: '#4ade80',
    text: '#f0fdf4',
    subtitle: '#86efac',
    particle: '❋',
    emoji: '🌿',
  },

  // ── Kids themes ────────────────────────────────────────
  rainbow_meadow: {
    audience: 'kids' as const,
    name: 'Rainbow Meadow',
    bg: 'linear-gradient(135deg, #fdf4ff 0%, #fae8ff 50%, #ede9fe 100%)',
    accent: '#a855f7',
    text: '#3b0764',
    subtitle: '#7c3aed',
    particle: '🌸',
    emoji: '🌈',
  },
  starry_sky: {
    audience: 'kids' as const,
    name: 'Starry Sky',
    bg: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%)',
    accent: '#fbbf24',
    text: '#ffffff',
    subtitle: '#fde68a',
    particle: '⭐',
    emoji: '✨',
  },
  ocean_adventure: {
    audience: 'kids' as const,
    name: 'Ocean Adventure',
    bg: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 50%, #0369a1 100%)',
    accent: '#fbbf24',
    text: '#ffffff',
    subtitle: '#fef9c3',
    particle: '🐠',
    emoji: '🌊',
  },
  garden: {
    audience: 'kids' as const,
    name: 'Garden',
    bg: 'linear-gradient(135deg, #bbf7d0 0%, #86efac 50%, #4ade80 100%)',
    accent: '#166534',
    text: '#052e16',
    subtitle: '#14532d',
    particle: '🌻',
    emoji: '🌺',
  },
}

export type ThemeKey = keyof typeof THEMES

export const ADULT_THEMES  = Object.entries(THEMES).filter(([, v]) => v.audience === 'adults').map(([k]) => k as ThemeKey)
export const KIDS_THEMES   = Object.entries(THEMES).filter(([, v]) => v.audience === 'kids').map(([k]) => k as ThemeKey)