# reel-creation-pipeline.md
# Hadith Reels — Production Pipeline

> **Owner:** Farhod Elbekov
> **Last verified:** 2026-08-11 (kids path re-verified end to end on Bukhari #8)
> **Companion docs:** `reel-tracker.md`, `fix_patterns.md`, `agent-architecture-roadmap.md`

## Two pipelines

The channel produces two kinds of reel and they share almost nothing after the
admin UI:

| | Kids | Adults |
|---|---|---|
| Visual | Talking mascot (lamb), lip-synced | Animated scenes or looped background |
| Renderer | `render-mascot-reel.ps1` | `render-reel.ps1` |
| Subtitles | None | Whisper SRT (en/ru/ar only, P078) |
| Wrapper | `make-kids-reel.ps1` — one command | None; run steps by hand |

**The kids path below is current and verified. The adults path further down is
older; treat it as a guide and verify against the scripts before relying on it.**

---

# PART 1 — KIDS REELS (current)

## Prerequisites

```powershell
cd "C:\QA\Hadith verification AI app\hadith-reels"
npm run dev -- -p 3002          # separate window
$env:FAL_KEY                     # must be ~69 chars; set permanently via
                                 # [Environment]::SetEnvironmentVariable(...,'User')
```

`make-kids-reel.ps1` validates all of this at Step 0 and fails loudly before
spending anything.

## Folder layout (P106)
out/
├── backgrounds/ nasheeds + background video (shared, never moves)
├── refs/ FLUX source stills, low-res mascot references
├── data/ candidates.json, translations, sourcing state
├── work/ CURRENT set only — {style}/{slug}/{lang}/
├── published/ archive — same shape as work/
└── _legacy/ tests and dead-convention files

assets/mascot/
├── lamb-boy-mosque-night-v3.png 4K, moonlit mosque courtyard
└── lamb-girl-garden-day-v2.png 4K, sunny mosque garden

Both mascot stills are committed. **Never let a source asset exist only inside a
rendered video** — both were lost that way once and had to be recovered by
extracting a 480p frame and regenerating at 4K in Nano Banana Pro (see P103).

## Mascot rotation

Alternate by hadith: boy → girl → boy. Voice follows the mascot (P104), so the
mascot choice determines the voice in every language.

| | girl lamb (female) | boy lamb (male) |
|---|---|---|
| EN | Danielle | Eric |
| RU | Arabella Calm & Mature | Liam Youthful |
| UZ | Mini | George |
| TJ | Katherine Polished | Liam Viral |

All ElevenLabs `eleven_v3`. OpenAI is fully retired from the TTS route.

## Step 1 — Pick and generate

`http://localhost:3002/admin` → login.

- **Style:** Kids · **Mascot:** boy or girl · **Language**
- Search by hadith number (exact), tag, narrator, collection, or text (P109)
- Pick the hadith, then Generate

**Switching language deselects the hadith** — by design (P108). Re-pick after
switching, or the caption ships with the previous language's text.

## Step 2 — Review the text (the step that catches everything)

Every content defect this project has shipped was caught by a human reading the
output. No test or gate has ever caught one. Read all three fields.

- **Fabrication** — no invented occasion, setting, or audience. Most hadith have
  no recorded occasion; "during a time when" is the softened form of the same
  fabrication (P103)
- **Narrator epithets** — "the great companion", "son of the second caliph".
  Plain name only; honorifics (ра, رضي الله عنه, розияллоҳу анҳу) are fine (P108)
- **Isnad verbs** — the Prophet ﷺ *said*; the companion *narrated*. Russian:
  сказал, never передал/рассказал (P108)
- **Grammar** — RU/UZ/TJ generations reliably contain 1-2 errors per set.
  Recent: добрость→доброту, бандани→бандага, Равикунандаи→Ривоятгари,
  столбов/столпов inconsistency
- **No seerah attribution in captions** — removed in P105. If one appears, that's
  a regression

Fields are editable textareas. Fix inline; don't regenerate — regeneration
reliably reintroduces the same errors.

## Step 3 — Generate narrations

Click Generate for Story and Moral. **The route writes both to disk
automatically** (P106):
out\work\kids{slug}{lang}\kids-{lang}-{slug}-story.mp3
out\work\kids{slug}{lang}\kids-{lang}-{slug}-moral.mp3

No download, no rename, no move. The ⬇ MP3 button still exists as a fallback.

Listen to both. `eleven_v3` varies between takes; clicking Generate again gives
a different one.

## Step 4 — One command

```powershell
.\make-kids-reel.ps1 -Lang ru -Slug bukhari-8 -Mascot girl -Nasheed ramadan-2-bg.mp3
```

Chains: validate → concat (1s gap) → split if over 28s → fal Fabric lip-sync at
720p per chunk → render. Pauses before Fabric (the only paid, irreversible step);
`-Auto` skips the pause.

**Splitting** cuts at the story/moral silence, not at maximum length. If the
story alone exceeds 28s the script stops with a clear message — shorten the text
rather than splitting by hand. RU and UZ hit this regularly; EN rarely.

Output: `out\work\kids\{slug}\{lang}\kids-{lang}-{slug}-mascot-reel.mp4`,
1080×1920.

## Step 5 — Watch

- Audio through the full length, nothing clipped
- The seam where clips join (mascot resets to the still — should land in silence)
- Nasheed audible but under the voice
- Headroom above the mascot's head stays stable (Fabric animates the whole frame,
  so objects above the head drift with head motion)

## Step 6 — Caption and publish

Caption is generated deterministically (P106): title, hadith text in the target
language, moral, reference, verify link, filtered tags. `TAG_BLOCKLIST` removes
tags that pull the wrong audience (`date` → dating content, `hellfire` → metal).

**Known gap:** collection and narrator stay Latin inside Cyrillic captions.
Hand-correct to `📖 Сахих аль-Бухари №8, Ибн Умар` and the TJ/UZ equivalents.

Publish order: Telegram → Instagram → TikTok → YouTube Shorts. YouTube needs
title, description, and tags as separate fields, and Tags is under SHOW MORE at
the bottom of the Details page.

Then log in `reel-tracker.md` — row, duplicate-check index, theme coverage, asset
reuse, production stats.

---

# PART 2 — ADULTS REELS (older; verify before relying on)

Not re-verified in the 2026-08 sessions. The steps below reflect the last known
state; check them against `render-reel.ps1` before a run.

- **Pillar 1:** looped background video from `out/backgrounds/`
- **Pillar 2:** animated scenes — FLUX text-to-image (`generate-image.ps1`) →
  human review → Kling image-to-video (`generate-scene.ps1`) → `render-reel.ps1`
  with `-Scenes` (per-clip 1080×1920@30fps normalization)
- Subtitles via Whisper, **en/ru/ar only** — auto-skipped for uz/tj (P078)
- Voices: EN James, RU Abrar, UZ Opa Johann, TJ Meisam

**Open items on this path:** P100 (Whisper UTF-8 on Cyrillic) is session-only and
not hardened in `render-reel.ps1`. R005 likely has the P099 frozen tail.

---

## Troubleshooting

**FAL_KEY 401** — key is wrong or truncated. Real keys are ~69 chars. Use single
quotes when setting (`$env:FAL_KEY='...'`); double quotes interpolate `$`.

**ffmpeg not recognized**
```powershell
$env:PATH += ";C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
```

**File locked on move/delete** — a persistent lock survives closing media players
(antivirus or sync tool, same cause as the PowerShell silent-revert gotcha).
Copy instead of moving; delete after a reboot.

**PowerShell parse errors on a .ps1 you just edited** — check the file encoding.
Windows-1252 mangles em dashes into bytes PowerShell can't parse inside strings.
Save as UTF-8; prefer plain hyphens in PowerShell string literals.

**Repo file edits silently reverting** — never use PowerShell file APIs
(`Set-Content`, `Add-Content`, `WriteAllText`) on repo files. VS Code only.

---

## Audio policy — background beds

**Rule:** background audio must be vocal-only nasheed (voice, or voice + daf)
or non-musical ambience. No string, wind, or keyboard instruments — no lute,
oud, ney, flute, synth, or electric piano.

**Why:** a viewer raised this on the Abu Dawud #3641 EN reel (YouTube,
2026-08-13), objecting to instrumental music under hadith content. On audit,
all seven beds then in use contained instruments — the library had been
assembled from Pixabay searches in May without checking instrumentation, and
every reel since inherited it. Scholars differ on instruments generally, but
the daf has the strongest permitting position, and ambience is not music at
all. Vocal-only sidesteps a dispute this project has no need to enter.

**Current library** (`out/backgrounds/`, all Pixabay, royalty-free, cleared
for monetised use):
  vocal-nasheed-01..07.mp3   vocal-only background nasheeds
  vocal-hamd-kids-01.mp3     hamd/naat, kids lane
  light-of-my-heart-bg.mp3   vocal + daf
  path-to-jannah-bg.mp3      vocal + daf
  ambient-ocean-bg.mp3       generated (ffmpeg pink noise), mono
  ambient-ocean-stereo-bg.mp3  generated, stereo

**Retired:** the five instrumental beds are in `out/backgrounds/_instrumental/`
— out of the random picker's reach, not deleted. 26 published reels carry them;
whether to leave, re-render, or unlist is an open question for someone
qualified, not an engineering decision.

**KNOWN GAP:** render-reel.ps1 globs `out/backgrounds/*.mp3`, so it can pick
a kids-lane hamd for an adults reel or ocean for a kids reel. Lane separation
is by filename convention only and is not enforced in code.

**Rule for new beds:** listen before adding. A search term is not a
verification — "acapella nasheed" returns instrumental tracks.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-11 | Rewritten. Kids path re-verified end to end on Bukhari #8. Removed the seerah-attribution instruction (P105 violation), the manual MP3 download step (P106), the P079 "not editable" note, and the dead `<keyword>-story-narration-<lang>` convention that contradicted the naming section below it. Adults path marked unverified. |