@AGENTS.md
# CLAUDE.md — HadithReels
# Context file for Claude Code
# github.com/Farhod75/hadith-reels

## What this project does
HadithReels creates short animated video reels based on authentic
(sahih) hadiths from the hadith_library Supabase table (shared with
hadith-verifier). Each reel includes:
- Arabic text + translation
- AI-generated story behind the hadith (Claude)
- AI-generated moral lesson
- Text-to-Speech narration (ElevenLabs)
- Animated Remotion composition
- Export as MP4 for Instagram/TikTok/Telegram

## Audience segments
- Adults: formal tone, dark elegant themes, scholarly language
- Kids (6-14): simple language, bright colorful themes, fun facts

## Languages
- Arabic (ar) — primary
- Uzbek (uz)
- Russian (ru)
- Tajik (tj) — uses Persian/Farsi voices as fallback

## Tech stack
- Next.js 14 + TypeScript + Tailwind CSS
- Remotion (video composition + export)
- Anthropic Claude Sonnet (claude-sonnet-4-6)
- ElevenLabs (TTS — multilingual voices)
- Supabase (SHARED with hadith-verifier)
- Vercel (hosting)
- Stripe (monetization — Free/Pro/Team)

## Shared infrastructure
- Supabase: same project as hadith-verifier
  - Tables used: hadith_library, hadith_reels, reel_history, search_history
  - RLS disabled on all tables
  - Always use SUPABASE_SERVICE_ROLE_KEY server-side
- ElevenLabs: same API key as hadith-verifier
- Anthropic: same API key as hadith-verifier

## Project structure
hadith-reels/
├── app/
│   ├── page.tsx               — main UI (Browse|Create|MyReels|History)
│   ├── layout.tsx
│   └── api/
│       ├── generate-reel/     — Claude AI content generation
│       ├── tts/               — ElevenLabs proxy (same as hadith-verifier)
│       ├── reels/             — Supabase CRUD for hadith_reels
│       └── search/            — hadith_library search by tag/keyword
├── components/
│   ├── TTSPlayer.tsx          — same as hadith-verifier
│   ├── ReelCard.tsx           — reel preview card
│   ├── AudienceToggle.tsx     — Adults/Kids toggle
│   ├── ThemePicker.tsx        — visual theme selector
│   └── VoicePicker.tsx        — voice/reciter selector
├── remotion/
│   ├── HadithReel.tsx         — adults composition
│   ├── KidsReel.tsx           — kids composition
│   └── index.ts               — composition registry
├── lib/
│   ├── voices.ts              — voice matrix (all 4 langs × 2 audiences)
│   ├── themes.ts              — theme definitions
│   └── supabase.ts            — shared Supabase client
├── CLAUDE.md                  — this file
├── CHANGELOG.md
├── FEATURES.md
└── README.md

## Monetization tiers
- Free: 3 reel exports/month, 720p, watermark
- Pro ($4.99/mo): unlimited HD, no watermark, all themes, all voices
- Family ($9.99/mo): Pro + Kids content unlocked
- Team ($19/mo): 5 users, custom logo, bulk export

## Run commands
npm run dev -- -p 3002   (3000=other app, 3001=hadith-verifier)
vercel --prod --force

## Vercel env var best practice (Windows PowerShell)
# Add to Production + Preview only (Development uses .env.local)
# Selecting all 3 causes "Development cannot be combined" error

vercel env add KEY_NAME production
vercel env add KEY_NAME preview
# Development reads from .env.local automatically — no need to add via CLI

## Vercel deployment notes
- Use: vercel env add KEY production then vercel env add KEY preview (separately)
- Never select Development via CLI — use .env.local for local dev
- Quick deploy: vercel --prod --force
- Quick link new project: vercel --yes

## Build status
- Deployment URL: https://hadith-reels-553rlrbpd-farhod75s-projects.vercel.app
- Status: scaffold deployed, UI in progress
