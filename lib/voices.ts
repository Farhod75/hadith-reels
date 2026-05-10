// ─── VOICE MATRIX ──────────────────────────────────────────
// Fill elevenLabsId as you add voices from ElevenLabs
// Adults: formal, warm, authoritative
// Kids: friendly, clear, gentle

export const VOICE_MATRIX = {
  ar: {
    adults: {
      narrator:    { id: 'hijazi',       elevenLabsId: 'fkqevZRU7Xj52dY1CTkq', name: 'Hijazi',       flag: '🇸🇦' },
      storyteller: { id: 'abrar',        elevenLabsId: 'VwC51uc4PUblWEJSPzeo',        name: 'Abrar Sabbah', flag: '🇸🇦' },
      dua:         { id: 'abu_salem',    elevenLabsId: 'G1QUjBCuRBbLbAmYlTgl',     name: 'Abu Salem',    flag: '🇰🇼' },
    },
    kids: {
      narrator:    { id: 'ar_kids',      elevenLabsId: null, name: 'Arabic Kids',   flag: '🌟' },
      storyteller: { id: 'ar_warm',      elevenLabsId: null, name: 'Arabic Warm',   flag: '🌟' },
      dua:         { id: 'ar_gentle',    elevenLabsId: null, name: 'Arabic Gentle', flag: '🌟' },
    },
  },
  uz: {
    adults: {
      narrator:    { id: 'uz_male',      elevenLabsId: null, name: 'Uzbek Male',    flag: '🇺🇿' },
      storyteller: { id: 'uz_warm',      elevenLabsId: null, name: 'Uzbek Warm',    flag: '🇺🇿' },
      dua:         { id: 'uz_calm',      elevenLabsId: null, name: 'Uzbek Calm',    flag: '🇺🇿' },
    },
    kids: {
      narrator:    { id: 'uz_young',     elevenLabsId: null, name: 'Uzbek Young',   flag: '🌟' },
      storyteller: { id: 'uz_friendly',  elevenLabsId: null, name: 'Uzbek Friendly',flag: '🌟' },
      dua:         { id: 'uz_gentle',    elevenLabsId: null, name: 'Uzbek Gentle',  flag: '🌟' },
    },
  },
  ru: {
    adults: {
      narrator:    { id: 'ru_calm',      elevenLabsId: null, name: 'Russian Calm',  flag: '🇷🇺' },
      storyteller: { id: 'ru_warm',      elevenLabsId: null, name: 'Russian Warm',  flag: '🇷🇺' },
      dua:         { id: 'ru_deep',      elevenLabsId: null, name: 'Russian Deep',  flag: '🇷🇺' },
    },
    kids: {
      narrator:    { id: 'ru_young',     elevenLabsId: null, name: 'Russian Young', flag: '🌟' },
      storyteller: { id: 'ru_fun',       elevenLabsId: null, name: 'Russian Fun',   flag: '🌟' },
      dua:         { id: 'ru_gentle',    elevenLabsId: null, name: 'Russian Gentle',flag: '🌟' },
    },
  },
  tj: {
    adults: {
      narrator:    { id: 'fa_warm',      elevenLabsId: null, name: 'Persian Warm',  flag: '🇹🇯' },
      storyteller: { id: 'fa_calm',      elevenLabsId: null, name: 'Persian Calm',  flag: '🇹🇯' },
      dua:         { id: 'fa_gentle',    elevenLabsId: null, name: 'Persian Gentle',flag: '🇹🇯' },
    },
    kids: {
      narrator:    { id: 'fa_young',     elevenLabsId: null, name: 'Persian Young', flag: '🌟' },
      storyteller: { id: 'fa_friendly',  elevenLabsId: null, name: 'Persian Friendly', flag: '🌟' },
      dua:         { id: 'fa_gentle_k',  elevenLabsId: null, name: 'Persian Gentle',flag: '🌟' },
    },
  },
}

export type Lang     = keyof typeof VOICE_MATRIX
export type Audience = 'adults' | 'kids'
export type VoiceRole = 'narrator' | 'storyteller' | 'dua'

export function getVoice(lang: Lang, audience: Audience, role: VoiceRole) {
  return VOICE_MATRIX[lang]?.[audience]?.[role] ?? null
}