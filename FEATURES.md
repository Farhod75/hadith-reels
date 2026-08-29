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

Two structural checks run before the five content ones (P128). They compare
blocks against each other and against the expected shape, which no per-block
check can do: `missing-block` (a dropped S/M/H/C label silently merges the
block into the previous one) and `duplicate-block` (two blocks with identical
text). Both come from the Muslim #2999 kids set, where each fired once and
neither was caught by anything automated. The missing-label case was already
detected but printed only as a quiet `note:` above "no findings" — it is now a
real Finding that sorts and counts.

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

### Library integrity audit (`scripts/audit-library.py`)

Per-language checks over `hadith_library` and `hadith_candidates`. Read-only,
warn-only, stdlib-only.

Catches defects in the SOURCE ROWS — the class `lint-content.py` structurally
cannot see, because it reads generated reel text and the generator paraphrases,
so the DB sentence never appears verbatim in `draft.txt`.

- **HIGH** — Tajik column is a copy of the Russian one (P050) · Latin homoglyph
  inside a Cyrillic word (R027) · grade outside sahih/hasan
- **WARN** — wrong okina in Uzbek, `o'` where `oʻ` (U+02BB) belongs (R024) ·
  Latin and Cyrillic mixed between the two Uzbek columns (R036) · missing or
  homepage-only source URL
- **INFO** — empty language fields, showing which rows cannot produce a full
  4-language set · long Tajik text carrying none of ӣ ӯ ҳ қ ғ ҷ

  ### Candidate translation, Stage 2 (`scripts/translate-candidates.py`)

Translates the Arabic matn of a sourced candidate into EN, RU, Uzbek Cyrillic
and Tajik. Dry-run by default; writes nothing until `--commit`.

Translates from `text_arabic` only. It refuses a candidate with no Arabic
rather than fall back to another language column (G3).

The system prompt carries the fabrication rules, not just register guidance:
add no clause, supply no attribution the matn lacks, add no comparison, add no
ranking or elevation, and emit `[UNCERTAIN: note]` rather than guess. A
translator asked only for a "reverent" register will smooth a terse matn into
something fuller — the same length-pressure failure as P116.

Per-field provenance goes to `translation_meta`: `machine`, model, source
field, timestamp. `text_uzbek_latin` is derived by `uzbek-translit.ts`, not
translated (D4: Cyrillic canonical).

    python scripts/translate-candidates.py --row 527      # dry run
    python scripts/translate-candidates.py --limit 10     # D5 batch
    python scripts/translate-candidates.py --commit

### Candidate translation, Stage 2 (`scripts/translate-candidates.py`, `scripts/derive-uzbek-latin.ts`)

Translates the Arabic matn of a sourced candidate into EN, RU, Uzbek Cyrillic
and Tajik. Dry-run by default; writes nothing until `--commit`.

Translates from `text_arabic` ONLY. It refuses a candidate with no Arabic rather
than fall back to another language column (G3). P075 built the current Tajik
library column by translating `text_uzbek` → `text_tajik`; that is a translation
of a translation, and «Неки» for «Некӣ» (R037) is what it produces. Translating
#527 from the Arabic returned «Некӣ» with U+04E3 correctly.

The system prompt carries the fabrication rules, not just register guidance: add
no clause, supply no attribution the matn lacks, add no comparison, add no
ranking or elevation, and emit `[UNCERTAIN: note]` rather than guess. A
translator asked only for a "reverent" register will smooth a terse matn into
something fuller — the same length-pressure failure as P116.

Per-field provenance goes to `translation_meta`: `machine`, model, source field,
timestamp. That is what routes a field to human review at Stage 4.

`text_uzbek_latin` is DERIVED, never translated (D4: Cyrillic canonical).
`derive-uzbek-latin.ts` calls `deriveBothScripts` in `scripts/lib/uzbek-translit.ts`,
which is tested for okina (U+02BB after o/g) vs tutuq (U+02BC elsewhere) and folds
every apostrophe variant to one result. Verified on #527: `oʻz`, `oʻqish`,
`soʻngra` all carry U+02BB — the okina defect that reached five captions did not
recur, and `audit-library.py` independently agrees.

    python scripts/translate-candidates.py --row 527      # dry run
    python scripts/translate-candidates.py --limit 10     # D5 batch
    python scripts/translate-candidates.py --commit
    npx tsx scripts/derive-uzbek-latin.ts                 # dry run
    npx tsx scripts/derive-uzbek-latin.ts --commit

Stage 3 must use a DIFFERENT model for pass B (D2) — a model may not be the sole
verifier of its own output.

### Translation verification, Stage 3 (`scripts/verify-candidates.py`)

Two independent passes over every translation: `claude-sonnet-5` and
`gpt-5.6-terra`, different companies, uncorrelated failure modes (D2). B never
sees A's output, and both get an identical prompt — a divergent prompt would
make disagreement uninterpretable.

Scope is faithfulness to the matn only: added, omitted, changed, register.
Conventions are owned by `lint-content.py` and `audit-library.py` and must be
clean first (P120). The original design's ref-exists and grade checks are not
here — those are API lookups Stage 0 already performs.

An API error counts as a disagreement: absence of a verdict is not a verdict.
A single failing language routes the whole candidate to `needs_human`, since a
row is promoted or rejected whole.

Proven in both directions on Bukhari #527: clean text passes on all four
languages, and an English translation with a planted invented action and
invented ranking is caught by both models independently at high confidence
while the other three stay clean.

    python scripts/verify-candidates.py --row 527    # dry run
    python scripts/verify-candidates.py --limit 10   # D5 calibration batch
    python scripts/verify-candidates.py --commit