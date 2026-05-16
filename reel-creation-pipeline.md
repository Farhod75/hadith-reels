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
<style>-<lang>-narration-<keyword>.mp3        — story audio only
moral-narration-<lang>-<keyword>.mp3          — moral audio only
<style>-<lang>-narration-<keyword>-full.mp3   — concatenated
<style>-<lang>-narration-<keyword>-full.srt   — Whisper subtitles
<style>-<lang>-<keyword>-reel.mp4             — final MP4
```

Where:
- `<style>` ∈ {`kids`, `adults`}
- `<lang>` ∈ {`en`, `uz`, `ar`, `ru`, `tj`}
- `<keyword>` is a short identifier of the hadith (e.g., `tabassum`, `fasting`, `prayer`)

Example complete set for UZ kids tabassum reel:
- `out/kids-uz-narration-tabassum.mp3`
- `out/moral-narration-uz-tabassum.mp3`
- `out/kids-uz-narration-tabassum-full.mp3`
- `out/kids-uz-narration-tabassum-full.srt`
- `out/kids-uz-tabassum-reel.mp4`

---

## Troubleshooting

**ffmpeg not recognized:**
```powershell
$env:PATH += ";C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
```
(Permanent fix: add to system PATH via Environment Variables UI)

**Whisper outputs Latin script for UZ/TJ:**
Known limitation. Ship Latin subtitles for now. Cyrillic conversion via substitution map is a post-Hajj task.

**Whisper says "FP16 not supported on CPU":**
Harmless warning. Uses FP32 instead. Slightly slower but accurate.

**Audio pronunciation has accent issues (UZ/TJ):**
Per P074, gpt-4o-mini-tts + instructions parameter mitigates ~80-90%. Persistent issues:
- Retry Generate button (run-to-run variance)
- Accept and ship; permanent fix is voice cloning post-Hajj
- See `hr-ppd-spec.md` for phonetic dictionary backup approach

---

## Future automation (post-Hajj)

Per `hr-agent-fleet-roadmap.md`:
- Orchestrator agent triggers daily cron at 06:00 UTC
- Picks 1 hadith from `hadith_library`
- Generates story + narrations
- TTS-validating agent verifies pronunciation
- Auto-renders MP4
- Auto-posts to Telegram via Bot API
- Logs to `hadith_reels` table

Today's manual pipeline becomes the agent's reference workflow.
