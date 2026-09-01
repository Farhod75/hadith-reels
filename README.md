# Hadith Reels

A production pipeline for short-form Islamic video, publishing authenticated
hadith in four languages to four platforms. Every hadith is verified against
Tier-1 sources; every reel is reviewed by a human before it is published.

**Channel:** @SahihHadithReels — Telegram · YouTube Shorts · Instagram · TikTok
**GitHub:** https://github.com/Farhod75/hadith-reels
**Sister project:** [hadith-verifier](https://github.com/Farhod75/hadith-verifier) — shares the Supabase library

---

## What this is

Not a web app with a video feature. A **content pipeline** with a web admin
attached. The Next.js app generates and stages text; PowerShell and Python do
the rendering; the human decides what ships.

**57 reels published** from 15 hadiths, across EN / RU / UZ / TJ.

Two production lanes:

| Lane | Visual | Subtitles | Used for |
|---|---|---|---|
| **Adults** | Kling-generated scenes, MODE B (no faces) | EN, RU, AR only | general audience |
| **Kids** | lip-synced mascot (lamb), fal VEED Fabric | none | children |

---

## The hard rules

These are not preferences. They constrain every part of the system.

- **No reel publishes without human review.** No agent posts to a channel.
- **Never depict** the Prophet ﷺ, any prophet, angels, Allah, or named Sahaba —
  in generated imagery, scene prompts, or any visual asset.
- **Every hadith verified** against Tier-1 sources: sunnah.com, Dorar, HadeethEnc.
  No fabricated attributions, no unnamed scholarly authority.
- **The matn is the reference.** Generated text is checked against the stored
  Arabic-derived translation, not against itself.

The pipeline automates the mechanical work around human review. It does not
automate the review.

---

## Quick start

```bash
git clone https://github.com/Farhod75/hadith-reels
cd hadith-reels
npm install
npm run dev          # http://localhost:3002
```

Admin UI is at `/admin`.

### Environment

Create `.env.local` in the repo root with:

| Key | Used for |
|---|---|
| `ANTHROPIC_API_KEY` | reel text generation |
| `NEXT_PUBLIC_SUPABASE_URL` | hadith library (shared with hadith-verifier) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | " |
| `SUPABASE_SERVICE_ROLE_KEY` | " |
| `ELEVENLABS_API_KEY` | narration (`eleven_v3`) |
| `FAL_KEY` | Kling video, VEED Fabric lip-sync, FLUX stills |
| `TELEGRAM_BOT_TOKEN` | channel posting |

### Also required on PATH

`ffmpeg`, `ffprobe`, `python`, and `whisper` (`pip install openai-whisper`) for
subtitle generation on EN/RU/AR.

---

## Producing a reel

**Read [`reel-creation-pipeline.md`](reel-creation-pipeline.md) first.** It has a
per-language E2E checklist for each lane, in order, with the steps that have
historically cost a re-render marked. The order matters more than the commands.

Abbreviated, for the kids lane:

1. `/admin` → pick hadith, language, mascot → **Generate**
2. Review the four blocks (story / moral / context / caption) against the
   recurring-defect table
3. Pull the matn from Supabase — `text_uzbek_cyrillic` for UZ
4. Sync `draft.txt`, then lint:
   ```powershell
   python scripts\lint-content.py draft.txt --lang ru --matn "<matn>"
   ```
5. Generate narration per block, listen to both
6. Render:
   ```powershell
   .\make-kids-reel.ps1 -Lang ru -Slug bukhari-6446 -Mascot boy -Nasheed vocal-nasheed-07.mp3
   ```
7. Watch it, then publish TG → IG → YT → TikTok

The adults lane adds scene generation (stills → animate → review → stage) and a
subtitle review checkpoint. Both are in the pipeline doc.

---

## Layout

```
app/
  admin/                        generation + narration UI
  api/
    generate-reel/route.ts      Claude → story/moral/context/caption
    generate-video/route.ts
    render-reel/route.ts
    tts/route.ts                ElevenLabs, VOICE_MAP lives here
    reels/route.ts
    search/route.ts             hadith library search
    admin/verify/route.ts
    telegram/post/route.ts
remotion/                       HadithReel + KidsReel compositions
make-kids-reel.ps1              kids lane: concat → chunk → Fabric → render
render-reel.ps1                 adults lane: narration → subtitles → scenes → merge
render-mascot-reel.ps1          mascot spine assembly
scripts/
  generate-image.ps1            FLUX stills for review
  generate-scene.ps1            Kling video, -Resume for timed-out jobs
  generate-talking-clip.py      fal VEED Fabric lip-sync
  lint-content.py               8 deterministic pre-TTS checks
  stt-validate.py               subtitle validation
  split-narration.py            chunk at silence boundaries
  audit-assets.py               asset registry gate
  source-*.py / promote-*.py    library sourcing (Stage 0–5)
agents/
  reel-producing/               text pipeline + eval corpus
  tts-validating/
  stt-validating/
```

---

## Voices

All ElevenLabs `eleven_v3`. OpenAI is fully retired from this pipeline.

| | Adults | Kids (girl) | Kids (boy) |
|---|---|---|---|
| EN | James | Danielle | Eric |
| RU | Marat | Arabella Calm & Mature | Maxim Calm & Neutral |
| UZ | Opa Johann | Mini | George |
| TJ | Meisam | Katherine Polished | — |

`app/api/tts/route.ts`'s `VOICE_MAP` is the source of truth. This table is a
summary and will drift.

---

## Quality gates

**Pre-push hook** (`.githooks/pre-push`, requires `core.hooksPath = .githooks`)
classifies changed files and runs only the matching checks — TypeScript,
PowerShell, Python, JSON. Read the `📊 Classification` line it prints; a code
change reported as `Doc=1` is a classifier defect.

**`lint-content.py`** runs 8 deterministic checks before narration: missing or
duplicated blocks, divine name and its grammatical case, unnamed authority,
seerah sourcing, simile against the matn, inversion. A clean run means those
eight passed — not that the text is right.

**Asset registry** (`assets/asset-registry.json` + `scripts/audit-assets.py`)
blocks both render scripts if an asset is unregistered.

**`fix_patterns.md`** is the accumulated defect catalogue — 139 patterns, one
global sequence shared with hadith-verifier. Every fix ships with its pattern
block in the same commit.

A rule learned repeatedly here: **a gate must be proven capable of failing.**
Break it deliberately, confirm it blocks, restore it.

---

## Documentation

| File | What it holds |
|---|---|
| [`reel-creation-pipeline.md`](reel-creation-pipeline.md) | E2E checklists, both lanes, recurring defects |
| [`reel-tracker.md`](reel-tracker.md) | every reel shipped, with what went wrong |
| [`fix_patterns.md`](fix_patterns.md) | 139 defect patterns |
| [`QA_STANDARDS_AGENT_RULES.md`](QA_STANDARDS_AGENT_RULES.md) | agent rules, CI, git, project overrides |
| [`agent-fleet-roadmap.md`](agent-fleet-roadmap.md) | 13 planned agents, 2 built |
| [`animated-reel-scene-prompts.md`](animated-reel-scene-prompts.md) | scene prompt spec, religious guardrails |

---

## Tech

Next.js 16 · React 19 · TypeScript · Tailwind 4 · Remotion 4 · Supabase ·
Anthropic Claude · ElevenLabs · fal.ai (Kling, VEED Fabric, FLUX) · Whisper ·
FFmpeg · PowerShell · Python · Playwright · Vercel

---

## Author

Farhod Elbekov — [github.com/Farhod75](https://github.com/Farhod75)
ISTQB CT-AI & CTFL certified SDET / AI QA Engineer, Charlotte NC

Built as sadaqah jariyah. Free, no ads, no monetisation.
