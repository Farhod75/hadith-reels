---
name: stt-validating
description: Validates the Whisper-generated subtitle file (.srt) for a reel against the narration text it was transcribed from. Use this skill whenever (a) a subtitled reel is rendered, (b) render-reel.ps1 pauses at the subtitle review gate, (c) Whisper, subtitles, SRT, captions, or burned text are mentioned, (d) P078, P100 or P114 are referenced, or (e) subtitle language routing changes. Unlike blind speech-to-text validation, this agent has the SOURCE text — the story and moral the human wrote — so it performs a diff, not a guess. It asserts seven things: the SRT parses, timings are sane and inside the narration duration, the transcript matches the source within threshold, no word was garbled into a false proper noun, the script (Cyrillic/Latin) is consistent, the Prophet symbol is handled per convention, and the language was routed correctly per P078. Warn-only in v1 — it surfaces findings at the existing human review gate, never blocks or edits.
---

# STT-validating agent

System under test: the `.srt` produced by Step 5 of `render-reel.ps1`, transcribed
by Whisper from `{style}-{lang}-{slug}-narration.mp3`.

This agent does not write code and does not correct subtitles. It reports
divergences and lets the human at the review gate decide. The gate already
exists — `render-reel.ps1` pauses and opens the SRT in VS Code — so this agent
makes that pause informed rather than manual.

## Why this agent is different from tts-validating

`tts-validating` checks that audio matches the text that produced it. This agent
checks that the SUBTITLE matches the text that produced the audio. They fail
differently and neither substitutes for the other:

- TTS can pronounce a word correctly while Whisper mishears it — the audio is
  right and the subtitle is wrong.
- Both use Whisper, but this agent has the exact source text on hand. Similarity
  scoring is a fallback here, not the primary method; **word-level alignment
  against known-correct text is the primary method.**

**Grounding case (R027, Abu Dawud #3641 RU):** the narration said
`благороднейших деяний` (noblest deeds). Whisper produced
`благороднейших в Диянии` — splitting a common noun into a preposition plus a
capitalised non-word that reads as a proper noun. Similarity scoring alone would
have rated the cue ~0.92 and passed it. Word-level alignment flags it
immediately: `деяний` is in the source, `Диянии` is not in the source and is not
a word.

## When to run this agent

- At the `render-reel.ps1` subtitle review gate, before ENTER is pressed
- After any change to the Whisper invocation (model, language flag,
  `--output_dir`, `PYTHONIOENCODING`) — see P100, P114
- When a language is added to or removed from `$subLangs` (P078)
- When narration text is edited after the SRT was generated (the SRT is stale
  and the agent will say so)
- On-demand via orchestrator dispatch

Do NOT run for `uz` or `tj` — per P078 those languages skip subtitles entirely.
If invoked for them, report `not_applicable` and stop.

## Pre-task reads (mandatory)

1. `references/p078-subtitle-routing.md` — which languages get subtitles and why
2. `references/prophet-symbol-convention.md` — how the ﷺ is rendered in burned
   subtitles (symbol, spoken words, or both — see Open questions)
3. `references/proper-nouns.md` — narrator names, collection names and
   transliterations per language, so the agent does not flag correct rare words
4. `references/thresholds.md` — current pass/fail thresholds

If any file is missing, report `setup_incomplete` and stop.

## Inputs

- `srt_path` — the generated `.srt`
- `source_text` — the story + moral text the human approved, concatenated in
  narration order. In practice this is `draft.txt` (the same file
  `scripts/lint-content.py` reads), S and M blocks only.
- `narration_path` — the `.mp3` the SRT was transcribed from, for duration
- `lang` — `en`, `ru`, or `ar`
- `slug`, `style` — for the report only

**Note on source availability:** the generated text is not currently written to
disk by the admin — only the MP3s are. Until it is, `source_text` comes from
`draft.txt`, which the human saves manually. Automating that write is a
prerequisite for running this agent unattended, and is tracked separately.

## Validation pipeline

Run in order. Unlike `tts-validating`, this agent does NOT fail-fast — it runs
every check and reports all findings together, because the human is reading the
whole file anyway.

### Step 1 — SRT parse

Parse the file. Assert: at least one cue; every cue has an index, a timestamp
line, and non-empty text; indices ascend from 1 without gaps.

Fail `srt_malformed` with the offending line number.

### Step 2 — Timing sanity

For each cue: `start < end`, duration ≥ 0.3s, and no overlap with the next cue's
start. For the file: last cue's end ≤ narration duration + 0.5s tolerance.

Fail `timing_overlap`, `cue_too_short`, or `srt_exceeds_audio`. The last one
usually means the SRT is stale — generated from an earlier narration and never
regenerated after the text changed.

### Step 3 — Whole-text similarity (coarse gate)

Join all cue text, normalise (lowercase, strip punctuation, collapse whitespace,
normalise Cyrillic apostrophes), and compute Levenshtein-normalised similarity
against the normalised `source_text`.

**Threshold (v1 moderate):** ≥ 0.90. This is higher than `tts-validating`'s 0.80
because the source text is known exactly — a lower score means real divergence,
not recognition noise.

Below 0.75, report `transcript_diverged` and note that the SRT may have been
generated from different audio.

### Step 4 — Word-level alignment (the primary check)

Tokenise both texts. Align with a standard sequence diff. For every token in the
SRT that is not in the source, classify:

- **`unknown_word`** — the token does not appear anywhere in `source_text` and is
  not in `references/proper-nouns.md`. Report with the source token it replaced.
  This is the R027 case.
- **`capitalised_non_source`** — the token is capitalised mid-sentence and is not
  in the source and not a known proper noun. Highest-signal finding: Whisper
  fabricating a proper noun out of a common word is both wrong and looks
  authoritative on screen.
- **`split_or_merged`** — one source token maps to two SRT tokens or vice versa
  (`деяний` → `в Диянии`). Report both sides.
- **`near_miss`** — edit distance 1–2 from a source token (`умаляет` →
  `умоляет`). Different word, plausible mishearing, changes meaning.
- **`number_format`** — digits where the source had words or vice versa
  (`пятнадцать` → `15`). Informational only; acceptable in subtitles.

Every finding except `number_format` is surfaced. None of them block.

### Step 5 — Script consistency

Detect the dominant script of `source_text` (Cyrillic or Latin). Flag any cue
containing ≥ 3 consecutive characters of the other script.

Catches the Latin-in-Cyrillic class of defect seen in R024 and R028 captions —
different surface, same root cause: the wrong column or the wrong script reached
the output.

### Step 6 — Prophet symbol convention

`cleanForTTS()` converts ﷺ to spoken words before TTS, so Whisper transcribes
the words, not the symbol. The burned subtitle therefore shows the spoken form
unless a human edits it.

The agent asserts the file is INTERNALLY CONSISTENT with the convention in
`references/prophet-symbol-convention.md` — every occurrence rendered the same
way. Mixed forms in one file (symbol in cue 1, spoken words in cue 7) are
reported as `prophet_symbol_inconsistent`.

The convention itself is a human decision and is currently unset — see Open
questions. Until it is set, this step reports the forms found and does not
assert.

### Step 7 — Language routing (P078)

Assert `lang ∈ {en, ru, ar}`. If `uz` or `tj`, report `p078_violation`: a
subtitle file exists for a language that should have skipped subtitles. Indicates
`$subLangs` drift or a stale SRT left in the work tree from an earlier run —
`render-reel.ps1` deletes stale SRTs in the skip branch precisely to prevent
this, so a hit here means that guard failed.

## Outputs

```json
{
  "agent": "stt-validating",
  "version": "v1",
  "timestamp": "ISO 8601",
  "reel": { "style": "adults", "lang": "ru", "slug": "abudawud-3641" },
  "result": "clean | findings",
  "counts": { "high": 0, "medium": 0, "info": 0 },
  "findings": [
    {
      "severity": "high | medium | info",
      "code": "unknown_word | capitalised_non_source | split_or_merged | near_miss | number_format | timing_overlap | cue_too_short | srt_exceeds_audio | script_mismatch | prophet_symbol_inconsistent | p078_violation | srt_malformed | transcript_diverged",
      "cue_index": 11,
      "line_no": 43,
      "srt_text": "из благороднейших в Диянии.",
      "source_text": "из благороднейших деяний.",
      "note": "human-readable explanation"
    }
  ],
  "diagnostics": {
    "cue_count": 14,
    "srt_duration_s": 0.0,
    "narration_duration_s": 0.0,
    "whole_text_similarity": 0.0,
    "source_available": true
  },
  "warnings": []
}
```

`result` is `clean` only when there are zero high and zero medium findings.
**A clean result means these seven checks passed — it does not mean the
subtitles are correct.** The human still reads the file.

## Self-validation (evals)

Eval set in `evals/evals.json`, built from real SRTs already produced:

1. **R027 RU** — contains `в Диянии` (split_or_merged + capitalised_non_source),
   `умоляет` (near_miss), `Знания` (near_miss). Must find all three.
2. **R026 EN** — known clean after review. Must return zero high findings.
3. **Synthetic stale SRT** — R026's SRT against R027's narration. Must fire
   `srt_exceeds_audio` or `transcript_diverged`.
4. **Synthetic script mismatch** — a Latin cue injected into the RU SRT. Must
   fire `script_mismatch`.
5. **Synthetic P078 violation** — an SRT passed with `lang=uz`. Must fire
   `p078_violation` and stop.

Pass criteria: 5 of 5. Unlike `tts-validating`, none of these depend on Whisper
behaviour at runtime — the inputs are fixed files — so there is no known-flaky
case and the bar is total.

## Failure escalation paths

| Finding | Severity | Action |
|---|---|---|
| `capitalised_non_source` | High | Surface prominently. A fabricated proper noun in a religious reel reads as a real term and damages credibility. |
| `unknown_word`, `split_or_merged` | High | Surface with both texts side by side. |
| `near_miss` | Medium | Surface — meaning may have changed (умаляет/умоляет). |
| `script_mismatch` | Medium | Surface. Check the source column. |
| `srt_exceeds_audio`, `transcript_diverged` | High | Likely stale SRT. Recommend deleting it and re-running Step 5. |
| `p078_violation` | High | Stop. Do not review; investigate the routing. |
| `srt_malformed` | High | Stop. Nothing downstream can use the file. |
| `timing_overlap`, `cue_too_short` | Medium | Surface; usually cosmetic. |
| `number_format` | Info | Log only. |

No finding blocks in v1. The human gate in `render-reel.ps1` is the block.

## What this agent does NOT do

- Does not edit the SRT — the human edits in VS Code at the existing gate
- Does not judge translation accuracy, only transcription fidelity to the source
- Does not check the content rules (divine name, similes, attribution) — that is
  `scripts/lint-content.py`, run earlier, on the source text before TTS
- Does not validate audio — that is `tts-validating`
- Does not decide the ﷺ convention, only enforces consistency once it is set

## Dependencies

- Python 3.10+ with `python-Levenshtein`; `difflib` from stdlib for alignment
- `ffprobe` on PATH for narration duration
- No API calls. No network. Runs offline on two local files, which is why it can
  run inside the render loop without the `@real-api` gating that
  `tts-validating` requires.

## Scripts

- `scripts/stt-validate.py` — entry point; takes `--srt`, `--source`,
  `--narration`, `--lang`
- `scripts/align.py` — Step 4 tokenisation and classification
- Reuses the S:/M:/H:/C: block parser from `scripts/lint-content.py` so the two
  agents read the same `draft.txt` format

Stubs in v1. To be generated once this SKILL.md is approved.

## Governance compliance

- Safe for push CI — no API calls, no cost, deterministic on fixed inputs. This
  agent is explicitly NOT covered by the `AGENTS_ADDENDUM.md` Golden Rule, which
  gates agents that make real provider calls.
- Human approval before publish is unaffected; this agent informs that gate and
  never replaces it.

## Versioning

- **v1 (current):** offline SRT-vs-source diff, warn-only, 7 checks, 5-case eval
- **v2 (planned):** enforce the ﷺ convention once set; auto-suggest corrections
  for `near_miss` findings (suggest only — the human applies); reading-speed
  check (characters per second per cue) now that subtitle size is a known issue
- **v3 (planned):** run automatically inside `render-reel.ps1` between Whisper
  and the review pause, printing findings above the ENTER prompt

## Open questions for v2

- **The ﷺ convention is unset.** R026 EN shipped with both the symbol and the
  spoken words ("The Prophet ﷺ, peace be upon him") because the human added the
  symbol without removing the transcription. Step 6 cannot assert until a human
  decides: symbol only, words only, or both. This is a channel style decision,
  not a technical one.
- Whether `source_text` should include the H (seerah) block. Currently no — the
  seerah is not narrated in the adults reel, only story and moral are. Confirm
  this holds for every style before hardcoding it.
- Where the generated text should be written to disk so `draft.txt` stops being
  a manual step. The admin has it; the work tree does not.
- Whether `near_miss` should be severity high when the two words have opposite
  meanings (умаляет/умоляет). Requires a per-language confusable list, which
  does not exist yet.