# reel-creation-pipeline.md
# Hadith Reels — Production Pipeline

> **Owner:** Farhod Elbekov
> **Last verified:** 2026-08-31 (voice table and concat gap corrected; kids path
> last re-verified end to end 2026-08-11 on Bukhari #8)
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
| RU | Arabella Calm & Mature | Maxim Calm & Neutral (P112) |
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

Chains: validate → concat (0.5s gap, P135) → split if over 28s → fal Fabric lip-sync at
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

## Per-language E2E checklist (kids lane)

> Written 2026-08-31 after the #6446 set. The stages above describe WHAT each
> step does; this is the ORDER, and the order is where the mistakes happen.
> Steps marked ⚠ have each cost a re-run or a re-render at least once.

Repeat 1–13 per language. EN → RU → UZ → TJ.

1. `/admin`, switch Language. ⚠ **Re-search and re-select the hadith** — the
   language switch deselects it (P108), and generating without re-selecting
   ships the previous language's caption.
2. Mascot: alternate per hadith, not per language. Check the Mascot stills table
   in the tracker for which lamb the last set used.
3. **Generate** → read all four blocks (S/M/H/C) before anything else.
4. Review against the recurring-defect list below. Read every line; the linter
   catches none of these.
5. ⚠ **Edit inline in the textareas. NEVER click Regenerate** — it replaces all
   four blocks and discards the review (P079). Per-block re-narrate exists
   (P125); full regeneration is not the way back.
6. ⚠ **Sync `draft.txt`** (repo root, gitignored, VS Code only — PowerShell file
   writes get silently reverted on this machine). This happens BEFORE TTS, not
   after. Text narrated but never linted in its final form has shipped before.
7. Pull the matn from the DB, not from the caption:
   `select text_<lang> from hadith_library where hadith_number = '<n>';`
   UZ uses `text_uzbek_cyrillic`. `hadith_number` is TEXT — quote it.
   Using the caption instead compares generated text against generated text,
   and a wrong DB row stays invisible.
8. `python scripts\lint-content.py draft.txt --lang <lang> --matn "<matn>"`
   Clean means seven checks passed, not that the text is right.
9. **Story narration**, then the moral's. Separate buttons, per block.
10. Listen to both. A TTS defect found now costs one re-narrate; found after
    Fabric it costs a paid regeneration.
11. ⚠ Render with the nasheed named explicitly — never let the picker choose:
    `.\make-kids-reel.ps1 -Lang <lang> -Slug <slug> -Mascot <boy|girl> -Nasheed <file>`
    Pick from the tracker's Nasheed usage table: least-used, and not one already
    used in this language or this set. The picker has drawn an ocean ambience
    track (R044) and an adults-lane bed (R029, R030).
12. `y` at the Fabric gate. This is the paid, irreversible step. Nothing before
    it costs money; answering N is free and the default.
13. Watch the reel, then publish: **TG → IG → YT Shorts → TikTok**, one platform
    at a time. YT "Made for kids" = Yes on the kids lane. TikTok caption is
    shortened — it truncates hard in-feed.

After the FULL set, not per reel — update every one of these tracker sections:
Active reels · Duplicate-check index · Theme coverage · Nasheed usage ·
Mascot stills · Production stats (replace the summary line, don't append a
second one) · Change log. Then one commit, `Doc=1`.

### Recurring defects — check every generation for these

| Defect | Seen on | Note |
|---|---|---|
| Attribution boundary left open after "The Prophet ﷺ said:" | R054 EN | Paraphrase inside the attributed span with no close. P101 family. Make it indirect. |
| Allah absent from the moral | R054–R057, all four first drafts | Gratitude with no object; "tell yourself" instead of thanking Allah. |
| Meaning drift the DB fix doesn't prevent | R052, R056, R057 | Corrected `text_uzbek`/`text_tajik` still produced «қаноат» in generation. The generator re-derives the shift from the concept. |
| Escalation: "good" → "wins" | Every set before P133 | Fixed, but check the title anyway. |
| Isnad verb in the story block | R055 RU | «Это передал…» belongs in H, not the narrated span. |
| Singular verb for the Prophet ﷺ | R056 UZ, R057 TJ | «деди»→«дедилар», «гуфт»→«гуфтанд». |
| Caption quote Latin against Cyrillic body | 8 occurrences | Pull `text_uzbek_cyrillic`; never transliterate by hand. |
| Divine-name case (RU) | R039, R043 | Linter checks WHICH name, not its case. Still unfixed. |
| Preposition inverting meaning (TJ) | R033 | «барои»→«дар». Invisible to every check. |

### Language-specific

- **RU** — the only language where `eleven_v3` mishandles ﷺ and «(р.а.)».
  Write BOTH honorifics out in full before TTS.
- **UZ** — consistently the longest. If the story alone exceeds 28s the chunker
  refuses to cut mid-story; the way out is `split-narration.py` on the existing
  narration (R048), not a regenerate.
- **TJ** — cleanest lane for three sets. Watch «Худо» for «Аллоҳ», and adjacent
  near-identical words («ғанӣ ғании») which slur in TTS.

### Known gaps

- Fabric has no resume-by-request-id. A TLS timeout mid-set regenerates every
  clip on re-run and pays twice (R057). P134 logged the same gap for Kling.
- The pre-push hook reports `✅ PowerShell OK` on a script with a broken
  backtick continuation that cannot execute past line 1.

---
## Per-language E2E checklist (adults lane)

> Written 2026-09-01, against `render-reel.ps1`, `scripts/generate-image.ps1`
> and `scripts/generate-scene.ps1` as they stand at `09138e0`. The kids
> checklist above is the base; this documents where adults diverges.
> Steps marked ⚠ have each cost a re-run, a re-render, or a paid regeneration.

### Steps 1–8 — identical to the kids lane

Generate → defect review → matn from the DB → `draft.txt` → lint → caption
script check → narration → listen. Same order, same gates, same recurring
defects. **Read the kids checklist above; it is not repeated here.**

Two differences only:

- **Voices** are the adults slots: EN James · RU Marat · UZ Opa Johann ·
  TJ Meisam. All `eleven_v3`.
- **No mascot.** `-Mascot` does not exist on `render-reel.ps1`.

Everything below is what the adults lane adds.

---

### Step 9 — Scene prompts

Per `animated-reel-scene-prompts.md`: hadith text → scene-prompt JSON, 3–4
beats forming an arc (journey → worship → destination → path is the proven
shape from #1520).

**MODE B is the standing setting** — no detailed faces, figures from behind, at
distance, or in silhouette. The spec presents A and B as a choice; in practice
every shipped animated reel is B, and it stays B.

Hard blocks, non-negotiable, from the spec's §2: never depict the Prophet ﷺ,
any prophet, angels, Allah, or named Sahaba. Era and clothing must match the
hadith's period.

**⚠ This JSON is the religious gate.** Approve or edit it before a single
image is generated. A bad prompt approved here becomes a paid clip and then a
published reel.

### Step 10 — Stills (cheap, reviewable)

```powershell
.\scripts\generate-image.ps1 -Name "b6446-market" -Count 3 -Prompt "<approved prompt>"
```

→ `out\refs\b6446-market-1.jpg` … `-3.jpg`. A few cents per call.

Review all three, keep the best. **Image-first exists because a still is
cheaper and far easier to judge than a video** — approve the frame, then
animate it.

For hands and the Kaaba, prefer your own photos or footage. Generators fumble
both, and the negative prompt in `generate-scene.ps1` lists deformed and fused
fingers for exactly this reason.

### Step 11 — Animate

Image-to-video, the normal path — the `-Prompt` here describes **motion**, not
the scene:

```powershell
.\scripts\generate-scene.ps1 -Name "b6446-market" -Image "out\refs\b6446-market-2.jpg" -Prompt "gentle drifting motion, light shifting warmly, cloth moving in a soft breeze"
```

Text-to-video when no still is needed — same script, omit `-Image`.

→ `out\backgrounds\new\b6446-market.mp4`. Roughly $0.35–0.50 per 5s clip.

**⚠ Kling regularly exceeds 8 minutes and has been measured at 505s and 564s.**
The poll deadline is 20 minutes (P134 — note the inline comment mislabels this
as P133). If it times out, the job usually still completes server-side:
**recover it by request id, do not regenerate.** The recovery snippet is printed
in the failure message. Regenerating pays twice.

### Step 12 — Watch every clip

The script opens it automatically. Two questions, both yours:

1. Is it reel-worthy?
2. Is it religiously appropriate — MODE B held, nothing in §2's never-depict
   list, era plausible?

A clip that fails either is discarded, not fixed in post.

> **Backlog note:** 13 generated clips are unreviewed as of 2026-09-01. Clips
> cannot be selected for a reel until watched, so that pass is a prerequisite
> for the next animated set, not a separate chore.

### Step 13 — Stage into `normalized\`

⚠ **Manual. There is no script for this** — it is an open to-do item.

Already 1080×1920:
```powershell
Copy-Item "out\backgrounds\new\<name>.mp4" "out\backgrounds\new\normalized\<name>.mp4"
```

Otherwise:
```powershell
ffmpeg -y -i "out\backgrounds\new\<name>.mp4" -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -c:v libx264 -pix_fmt yuv420p -an "out\backgrounds\new\normalized\<name>.mp4"
```

`render-reel.ps1`'s animated mode rebuilds every clip to 1080×1920 @ 30fps
before concat, so mismatched sources no longer break the stitch — the framerate
trap that made a 24fps clip flash past in one frame is fixed. Staging here is
therefore about **placement**, not correctness: `-Scenes` reads from
`normalized\` and nothing else.

### Step 14 — Render

```powershell
.\render-reel.ps1 -Style adults -Lang <lang> -Slug <slug> -Nasheed <file> -Scenes clip1.mp4,clip2.mp4,clip3.mp4,clip4.mp4
```

`-Scenes` is **ordered** — the list is the visual arc, so the order is an
editorial decision, not a formality.

Omitting `-Scenes` falls back to picking 3 clips at random. That path still
exists and is not used; every shipped animated reel names its clips.

Nasheed named explicitly, same rule as kids. Add `-Open` to play the result.

### Step 15 — Subtitle review checkpoint

**Only fires for EN, RU and AR.** `$subLangs = @('en','ru','ar')` — UZ and TJ
ship without subtitles (P078), so this gate does not exist on half the set.

Whisper transcribes the narration, then the script opens the SRT in VS Code and
blocks. Fix any grammar or transcription errors and save, then ENTER to burn
them in. Type `S` to ship without subtitles.

⚠ **This is the second human gate and the last one before burn-in.** After
ENTER the subtitles are in the video.

If an SRT already exists Whisper is skipped — so a stale SRT from an earlier run
will be reused silently. Delete it if the narration changed.

Two env fixes are baked in and should not be removed: `PYTHONIOENCODING=utf-8`
(P100 — Cyrillic crashes Whisper's own progress printer on a CP1252 console) and
the `$ErrorActionPreference` flip around the call (P083 — Whisper's harmless
FP16 warning goes to stderr and would otherwise terminate the script).

### Step 16 — Watch, then publish

Same as kids: **TG → IG → YT Shorts → TikTok**, one platform at a time.
YT "Made for kids" = **No** on this lane.

---

### Adults-lane costs, per language

| Stage | Cost |
|---|---|
| Stills, 3 variants | a few cents |
| Kling clip, 5s | ~$0.35–0.50 |
| A 4-scene reel | ~$1.50–2.00 in clips |

Scenes are per hadith, not per language — the same four clips serve all four
language versions. Generate once, reuse across the set.

### Known gaps in this lane

- No script stages clips from `new\` into `normalized\` (step 13).
- No resume-by-request-id for Kling; recovery is a hand-run snippet (P134,
  logged incomplete). Fabric has the same gap and it cost a duplicate
  generation on R057.
- `animated-reel-scene-prompts.md` still describes Kling as "not yet built" and
  the agent fleet as "deferred". Both are stale; the doc is a pre-POC plan for a
  lane that has since shipped 25 reels.

  
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

**PowerShell writing UTF-16 or BOM** — `>>` and `Out-File` default to UTF-16LE in
PS 5.1 (turns text files binary; git shows `Bin` and shell scripts stop running);
`Out-File -Encoding utf8` adds a BOM Python rejects. Use `Copy-Item`, VS Code, or
`[System.IO.File]::WriteAllText()`. Verify: `python -c "d=open('<f>','rb').read(); print(len(d), d.count(b'\x00'))"`

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