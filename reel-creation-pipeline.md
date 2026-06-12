# HR Reel Creation Pipeline

End-to-end workflow for generating a Hadith Reel from admin UI to Telegram post.

**Proven on:**
- EN adults reel — May 14, 2026 (Fasting is a shield, Sahih al-Bukhari #1894)
- UZ kids reel — May 15, 2026 (Tabassum — sadaqa, Jami at-Tirmidhi #1956)

Pipeline uses ffmpeg shell commands (NOT Remotion). Remotion compositions exist in repo but are not used in this flow.

---

## Prerequisites

**Software (one-time setup):**
- Node.js + npm (HR dev environment)
- Python 3.10+ with `openai-whisper` package: `pip install openai-whisper`
- FFmpeg installed at `C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe` (or any path; add to PATH)

**Environment:**
- HR dev server running on port 3002 (`npm run dev`)
- `.env.local` populated with `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`, `ADMIN_PASSWORD` (quoted), Supabase keys

**Assets (in `out/backgrounds/`):**
- `garden.mp4` — kids reel background
- `mosque.mp4` — adults reel background
- Nasheed audio files: `nasheed-bg-1.mp3`, `mubarak-bg.mp3`, `path-to-jannah-bg.mp3`, `light-of-my-heart-bg.mp3`, `ramadan-bg.mp3`, `ramadan-1-bg.mp3`, `ramadan-2-bg.mp3`

---

## Step 1 — Admin: generate content

1. Open `localhost:3002/admin` in Chrome (regular, not incognito — hydration warnings noisy in regular but functional)
2. Login with `ADMIN_PASSWORD` value
3. Step 1 "Pick":
   - Select **Style** (Adults / Kids)
   - Select **Language** (EN / UZ / AR / RU / TJ)
   - Find target hadith by number, tag, or text — click to select
4. Step 2 "Generate":
   - Click "Generate story + moral + seerah context"
   - Wait ~30 sec for Claude (Sonnet) to produce: title, story (with appropriate Seerah source: Ar-Raheeq for EN/AR, Усваи Ҳасана for UZ/TJ/RU), moral lesson, social caption with attribution and hashtags
5. Step 3 "Preview":
   - Click "Generate Story narration" — produces story MP3 via TTS route
   - **Right-click the audio player → "Save audio as..."** → save to `out/<style>-<lang>-narration-<keyword>.mp3` (e.g. `kids-uz-narration-tabassum.mp3`)
   - Click "Generate Moral narration" — produces moral MP3
   - Save to `out/moral-narration-<lang>-<keyword>.mp3`
   - **Manual validation step:** listen to both. If pronunciation is unacceptable, retry the Generate button (Nova has run-to-run variance — sometimes second take is better). Accept when good enough or retries exhaust patience.

---
## ⭐ Automated render (Steps 2–4 in ONE command) — Pillar 1

Once both narration MP3s are saved with the naming convention, render the whole reel with one command — no need to run Steps 2–4 manually:

```powershell
cd "C:\QA\Hadith verification AI app\hadith-reels"
.\render-reel.ps1 -Style adults -Lang ru -Slug bukhari-1520 -Open
```

This does it all: concat story+moral → Whisper subtitles (auto-skipped for uz/tj per P078) → subtitle-review checkpoint (proofread before burn-in) → random-pick 3 Kaaba bg clips (resolution-guarded) → final merge with a random local nasheed + title overlay → reports MB and resolution.

Flags: `-Nasheed <file>.mp3` (force a specific nasheed), `-NoReview` (skip the proofread pause), `-ForceNoSubs` (skip subtitles).

> Steps 2–4 below are the MANUAL commands this script automates — kept for reference/debugging. In normal use you do NOT run them by hand.

---
## Step 2 — Concatenate story + moral into one narration file

Combine the two audio files with a 1-second gap between them, so Whisper can transcribe both as one timeline.

```powershell
$env:PATH += ";C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
cd "C:\QA\Hadith verification AI app\hadith-reels"

ffmpeg -y `
  -i "out\<style>-<lang>-narration-<keyword>.mp3" `
  -i "out\moral-narration-<lang>-<keyword>.mp3" `
  -filter_complex "[0:a]apad=pad_dur=1[a0];[a0][1:a]concat=n=2:v=0:a=1[out]" `
  -map "[out]" `
  "out\<style>-<lang>-narration-<keyword>-full.mp3"
```

Verify file exists and has expected duration:
```powershell
Get-Item out\<style>-<lang>-narration-<keyword>-full.mp3 | Select-Object Name, Length
```

Expected: ~100-200 KB for ~25-35 second audio.

---

## Step 3 — Whisper subtitles

```powershell
whisper "out\<style>-<lang>-narration-<keyword>-full.mp3" `
  --model small `
  --language <lang> `
  --output_format srt `
  --output_dir "out" `
  --word_timestamps True `
  --max_line_width 35
```

Where `<lang>` is one of: `en`, `uz`, `ru`, `tj` (Whisper uses `tg` internally for Tajik, but `uz` for Tajik often works too).

**Known issue:** Whisper transcribes Uzbek and Tajik in **Latin script**, not Cyrillic, regardless of input language. Latin output is acceptable for subtitles (Uzbeks read Latin officially since 1993). Cyrillic conversion is a post-Hajj enhancement.

Verify SRT was created:
```powershell
Get-ChildItem out\<style>-<lang>-narration-<keyword>-full.srt | Select-Object Name, Length
```

---

## Step 4 — Final ffmpeg merge

Combines: looping background video + narration + nasheed background music (volume 0.25) + subtitle overlay + "Hadith Reels" title text.

```powershell
ffmpeg -y `
  -stream_loop -1 -i "out\backgrounds\<garden_or_mosque>.mp4" `
  -i "out\<style>-<lang>-narration-<keyword>-full.mp3" `
  -stream_loop -1 -i "out\backgrounds\<nasheed-file>.mp3" `
  -filter_complex "[1:a]volume=1.0[narration];[2:a]volume=0.25[music];[narration][music]amix=inputs=2:duration=first[aout]" `
  -vf "subtitles='out/<style>-<lang>-narration-<keyword>-full.srt':force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,Alignment=2,MarginV=80',drawtext=text='Hadith Reels <Kids or Adults>':fontsize=28:fontcolor=white:shadowcolor=black@0.9:shadowx=2:shadowy=2:box=1:boxcolor=black@0.4:boxborderw=8:x=(w-text_w)/2:y=30:font=Arial" `
  -map 0:v -map "[aout]" `
  -c:v libx264 -c:a aac -shortest `
  -movflags +faststart `
  "out\<style>-<lang>-<keyword>-reel.mp4"
```

**Variables to fill in per reel:**
- Background video: `garden.mp4` for kids, `mosque.mp4` for adults
- Nasheed file: pick from available list, vary per reel
- Title text: "Hadith Reels Kids" or "Hadith Reels"

Expected output: ~10MB MP4, 1080x1920 (vertical reel format from source), ~30 seconds duration.

---

## Step 5 — Manual validation

Open `out\<style>-<lang>-<keyword>-reel.mp4` in Windows Media Player or VLC. Check:

- [ ] Audio plays (story + 1s gap + moral)
- [ ] Background video visible and looping
- [ ] Nasheed music audible but quiet under narration
- [ ] Subtitles appear at correct timing
- [ ] Title overlay readable
- [ ] No visual glitches
- [ ] Duration ≤ 60 seconds (Instagram/TikTok limit; Telegram unlimited)

If any check fails, return to relevant earlier step.

---

## Step 6 — Telegram post

1. In admin Step 3, click **"Copy caption"** button — copies the auto-generated caption to clipboard
2. Open Telegram → @SahihHadithReels (or via Telegram Desktop)
3. Attach the MP4 file (drag-drop or paperclip → file)
4. Paste the caption in the message field
5. Verify caption shows: title, story, moral, attribution (collection + number + narrator + Seerah source), Verify link, hashtags
6. Post

**Cross-platform expansion (future):**
- Instagram Reels: same MP4, copy caption, manual upload
- TikTok: same MP4, modify hashtags
- YouTube Shorts: same MP4, add title and description

---

## Naming convention

All reel artifacts in `out/` follow this pattern:

```
{style}-{lang}-{slug}-story.mp3        — story audio (from admin Step 2)
{style}-{lang}-{slug}-moral.mp3        — moral audio (from admin Step 2)
{style}-{lang}-{slug}-narration.mp3    — concatenated (render-reel.ps1 makes this)
{style}-{lang}-{slug}-narration.srt    — Whisper subtitles (en/ru/ar only, per P078)
{style}-{lang}-{slug}-reel.mp4         — final MP4
```

Where:
- `{style}` ∈ {`kids`, `adults`}
- `{lang}` ∈ {`en`, `uz`, `ru`, `tj`}  (AR skipped — not quality-checkable; was: en/uz/ar/ru/tj)
- `{slug}` = collection-number, machine-dedupable (e.g. `bukhari-1520`, `tirmidhi-1956`)

Example complete set for UZ kids tabassum reel:
- `out/adults-ru-bukhari-1520-story.mp3`
- `out/adults-ru-bukhari-1520-moral.mp3`
- `out/adults-ru-bukhari-1520-narration.mp3`
- `out/adults-ru-bukhari-1520-narration.srt`
- `out/adults-ru-bukhari-1520-reel.mp4`

---

## Troubleshooting

**ffmpeg not recognized:**
```powershell
$env:PATH += ";C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
```
(Permanent fix: add to system PATH via Environment Variables UI)

**Whisper outputs Latin script for UZ/TJ (P078):**
`render-reel.ps1` AUTO-SKIPS subtitles for uz/tj — only en/ru/ar get Whisper subs. Long-term path: Claude native audio input (Candidate 7) to fix UZ/TJ transliteration.

**Whisper call fails with "usage: ... --max_line_width requires --word_timestamps" (P081):**
`--max_line_width` needs `--word_timestamps True` (they're a pair). render-reel.ps1 omits both and uses segment-level SRT (cleaner for reels). Don't half-remove paired flags.

**Generated story has a grammar error (e.g. RU "Послание→Посланник"):**
FIXED (P079) — story/moral/seerah are now EDITABLE textareas in admin Step 2. Just fix the text before generating audio; no regenerate cycle needed.

**Whisper says "FP16 not supported on CPU":**
Harmless warning. Uses FP32 instead. Slightly slower but accurate.

**Audio pronunciation has accent issues (UZ/TJ):**
Per P074, gpt-4o-mini-tts + instructions parameter mitigates ~80-90%. Persistent issues:
- Retry Generate button (run-to-run variance)
- Accept and ship; permanent fix is voice cloning post-Hajj
- See `hr-ppd-spec.md` for phonetic dictionary backup approach

---

## Future automation (Curator agent)
**Status update (2026-06-11):** the render step is now AUTOMATED — `render-reel.ps1`
turns the manual Steps 2–4 into one command (Pillar 1) and also stitches ordered
animated scenes (Pillar 2, `-Scenes`). So the agent below no longer has to reinvent
rendering; it would orchestrate the existing scripts. Remaining for a Curator agent:

Per `hr-agent-fleet-roadmap.md`:
- Orchestrator agent triggers daily cron at 06:00 UTC
- Picks 1 hadith from `hadith_library`
- Generates story + narrations
- TTS-validating agent verifies pronunciation
- Auto-renders MP4
- Auto-posts to Telegram via Bot API
- Logs to `hadith_reels` table

The render-reel.ps1 / generate-scene.ps1 / generate-image.ps1 scripts become the agent's
building blocks. See `animated-reel-scene-prompts.md` for Pillar 2 (animated) design + guardrails.
