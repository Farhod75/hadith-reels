### Talking-mascot kids lane (fal VEED Fabric 1.0)
**Status:** PoC proven (2026-06-13); `render-reel.ps1` integration pending.

- **Engine:** fal `veed/fabric-1.0` — image + audio → lip-synced talking video.
  Resolutions 480p ($0.08/s) / 720p ($0.15/s). ~30s/clip cap (stitch longer).
- **Tool:** `generate-talking-clip.py` (fal-client handles upload + queue).
  Auth via `FAL_KEY` env var.
- **Mascots:** `assets/mascot/lamb-boy-v1`, `lamb-girl-v1` — reusable,
  face-consistent (edit, don't re-roll). One face per clip → animate each
  mascot separately, compose in render.
- Drives clips from existing ElevenLabs/OpenAI TTS narrations.

### Kids talking-mascot reels — Route A (scene-baked)
**Status:** proven end-to-end (2026-06-13).

- **Render:** `render-mascot-reel.ps1` -Lang -Slug -Clips [-Nasheed|-NoMusic]
  [-Subs] [-Open]. Talking clips = spine; nasheed under voice @0.20.
- **Scene mascots:** generate the mascot *in* the scene in Nano Banana Pro,
  attaching the locked base mascot as a face reference. Keep the mascot large,
  front-facing, clear mouth; keep empty headroom (Route-A motion coupling).
- **Proven assets:** boy = moonlit mosque (night), girl = mosque garden (day).

- **Long narration:** `split-narration.py` auto-splits story+moral into
  ordered <=28s chunks at silence boundaries; each chunk -> one Fabric clip;
  render-mascot-reel.ps1 stitches them in order. One mascot + one voice per reel.

### Content linter (`scripts/lint-content.py`)

Deterministic pre-TTS checks on generated reel text. Warn-only — never blocks,
never edits. Encodes five failure modes that were previously caught only by
human review:

| Check | Catches | Origin |
|---|---|---|
| `divine-name` | "God" / "Бог" / "Худо" substituted for the pinned name. Rabb/Lord/Господь/Парвардигор correctly allowed. | P111 |
| `unnamed-authority` | "scholars say", «Учёные», «Уламолар», «Олимон» with no named source | P111, P105 |
| `seerah-source` | A seerah title named without a cited passage — including in negative claims ("neither X nor Y records...") | P115 |
| `simile` | Comparisons absent from the matn. Pass `--matn` and the hadith's own comparison downgrades to INFO. | P111 r14 |
| `inversion` | A station of closeness rendered as lowly («поинтарин», "lowest") | P111 r15 |

Usage — input is the same `S:/M:/H:/C:` blocks used when pasting drafts for review:

```powershell
python scripts\lint-content.py draft.txt --lang tj --matn "<text from hadith_library>"
```

Validated against four generations from R022–R029: caught every documented
defect (R022 EN 4 fail, R025 TJ 4 fail, R026 EN 1 fail) and produced no false
positives on the clean R029 TJ generation.

**Limits:** heuristic, not proof. A clean run means these five checks passed —
not that the text is correct. Human review remains the gate. The `inversion`
check is the weakest (word list only). Does not check translation accuracy,
isnad verbs, or anything the reel's meaning depends on.

### Subtitle validator (`scripts/stt-validate.py`)

Diffs a Whisper-generated `.srt` against the narration text it was transcribed
from. Not blind speech-to-text validation — the source text is known exactly, so
the primary method is word-level alignment, not similarity scoring.

| Check | Catches |
|---|---|
| `srt_malformed` | Unparseable cues, bad timestamps, empty text |
| `timing_overlap` / `cue_too_short` | Overlapping or sub-0.3s cues |
| `srt_exceeds_audio` | SRT longer than the narration — usually a stale file |
| `split_or_merged` | One source word became two, or vice versa |
| `unknown_word` | A word in the subtitle that is nowhere in the source |
| `capitalised_non_source` | Whisper inventing a proper noun from a common word |
| `near_miss` | Edit distance 1–2 — different word, changed meaning |
| `homoglyph` | Latin characters hiding inside Cyrillic words |
| `script_mismatch` | Latin runs in an otherwise-Cyrillic file |
| `p078_violation` | An SRT exists for a language that should skip subtitles |

Usage — run at the `render-reel.ps1` subtitle review gate:

```powershell
python scripts\stt-validate.py --srt "<...>-narration.srt" --source draft.txt --lang ru --narration "<...>-narration.mp3"
```

Offline: no API calls, no cost, deterministic. Runs only for `en`, `ru`, `ar`
per P078.

**Why alignment rather than similarity:** R027's SRT scored 0.974 whole-text
similarity while containing `благороднейших в Диянии` for `благороднейших
деяний` — a common noun split into a preposition plus a capitalised non-word.
Any threshold check passes that file. Alignment flags it three ways.

**Found in production on first real run:** `умaляет` and `знаниe` in the
published R027 subtitles, each carrying one Latin homoglyph introduced during
hand-correction on a Latin keyboard layout. They render identically on screen
and are invisible to human review by construction.

**Limits:** warn-only, never edits. An inflection error on a word appearing
elsewhere in another form is not caught (`Знание` → `Знания` passed because
`знания` occurs earlier). Does not judge translation accuracy — only fidelity to
the source.

### Asset registry and lane gate (`assets/asset-registry.json`, `scripts/audit-assets.py`)

Every reusable asset — background beds, mascot stills, scene clips — carries a
recorded classification and a lane approval. The render scripts refuse assets
not approved for the lane requesting them.

- `--check FILE --lane kids|adults` — exit 1 if unregistered, retired, or wrong
  lane. Wired into `render-reel.ps1` (Step 7) and `render-mascot-reel.ps1`
  (Step 0). This one BLOCKS, unlike the warn-only linters: it is a lookup, not
  a judgement.
- `--audit` — sweeps the folders and reports unregistered files, missing
  entries, retired-but-reachable assets, and entries no human has verified.

Classifications: `vocal`, `vocal+daf`, `ambience`, `instrumental`, `mascot`,
`mascot-reference`, `scene`. Retired assets carry `"lanes": []`.

Classification stays human. The registry records a judgement; the script only
enforces what was written. Nothing here decides whether an instrument is
permissible.

**Why it exists:** the picker crossed lanes twice on 2026-08-15 (a kids hamd
onto an adults reel, adults ambience onto a kids reel), and before that every
bed in the library was instrumental for months — approved once, reused across
26 reels, caught by a viewer rather than any gate.