---
name: tts-validating
description: Validates narration audio produced by the Hadith Reels TTS route (POST /api/tts) against the text that produced it. Use this skill whenever (a) app/api/tts/route.ts or VOICE_MAP changes, (b) a voice or language is added or swapped, (c) narration is generated for a reel, (d) P102, P103, P104, P112 or P118 are referenced, or (e) any task mentions ElevenLabs, voice testing, narration, pronunciation, or cleanForTTS. Transcribes the narration with local Whisper and asserts six things: the file is real audio of plausible length, the recognised language matches the request, the recognised text matches the input within threshold, the Prophet symbol was expanded to spoken words per cleanForTTS, the correct voice id was used for the language/style/mascot combination, and that voice id resolves to the voice its comment claims. Warn-only except the Prophet-symbol check, which blocks.
---

# TTS-validating agent

System under test: `app/api/tts/route.ts` (POST `/api/tts`, accepts
`{ text, lang, style, mascot, slug, section }`).

This agent does not write code and does not regenerate audio. It reports
pass/fail with diagnostics; the human at the pre-publish gate decides.

> **REVISED 2026-08-15.** The previous version of this SKILL.md was written
> before P102/P103/P104 and described a dual-provider system (ElevenLabs +
> OpenAI Nova/Onyx) with James/Danielle voices, OpenAI Whisper API routing for
> Cyrillic, and a bitrate heuristic to tell the two providers apart. **None of
> that exists.** OpenAI is fully retired from this route; every language uses
> ElevenLabs `eleven_v3`. The old spec would have had anyone implementing it
> build against a system that has not existed since June. That is the reason
> Step 7 is gone and Step 3 changed.

## What changed in the stack, and what it means here

| Was | Is | Consequence for this agent |
|---|---|---|
| ElevenLabs + OpenAI, per language | ElevenLabs `eleven_v3` only (P102, P104) | No provider inference. Old Step 7 deleted. |
| Two kids voices per language | Kids split by mascot: boy and girl (P103) | The matrix is lang × style × mascot = 25 slots, not 10. |
| Audio captured via Playwright | Route writes to `out/work/{style}/{slug}/{lang}/` (P106) | For reel validation the MP3 is already on disk. Playwright capture is only needed for synthetic cases. |
| Cyrillic needed OpenAI Whisper API | Local Whisper works with `PYTHONIOENCODING=utf-8` (P114) | No API key, no cost, offline. |

## When to run this agent

- After generating narration for a reel, before the Fabric/render spend
- After any change to `app/api/tts/route.ts`, `VOICE_MAP`, or `cleanForTTS()`
- When a voice is swapped (P112 RU kids boy, P118 RU adults)
- When a language is added
- On-demand via orchestrator dispatch

## Pre-task reads (mandatory)

1. `app/api/tts/route.ts` — VOICE_MAP is the source of truth for the matrix.
   Do NOT keep a second copy of the voice table in this skill's references; two
   copies drift, which is how P118 happened.
2. `references/cleanforTTS.md` — the Prophet-symbol phrase per language
3. `references/thresholds.md` — current pass/fail thresholds

## Inputs

Either an existing reel narration:
- `audio_path` — an MP3 under `out/work/{style}/{slug}/{lang}/`
- `source_text` — the text that produced it (the S or M block of `draft.txt`)
- `lang`, `style`, `mascot`

or a synthetic case for matrix coverage, in which case the agent POSTs to
`/api/tts` itself and saves the response.

## Validation pipeline

### Step 1 — Audio sanity

File size ≥ 10 KB; duration ≥ 1.0s via `ffprobe`. Below either is empty,
header-only, or truncated. Fail `audio_too_small` / `audio_too_short`.

### Step 2 — Transcription (local Whisper)

`whisper <file> --model small --language {lang} --output_format srt`, with
`PYTHONIOENCODING=utf-8` set on the child process.

**That env var is not optional for Cyrillic.** Whisper prints progress to
stdout; on Windows the console codec is CP1252 and Cyrillic raises
`UnicodeEncodeError` *inside transcribe.py's own progress print*, abandoning the
file. The transcription itself is fine — the crash is in display. See P100 and
P114.

UZ is the weak case: Whisper's Cyrillic Uzbek training data is thin. Treat
similarity 0.05–0.10 below other languages as expected noise; below 0.70 is a
real recognition problem.

TJ: Whisper returns `tg`, sometimes `fa` or `ru`. Accept `tg`; accept `fa`/`ru`
with a warning; fail only on `en` or something unrelated.

### Step 3 — Language match

Detected language equals the requested `lang`. Fail `language_mismatch` with
the detected value.

### Step 4 — Text similarity

Levenshtein-normalised similarity between `cleanForTTS(source_text)` and the
recognised text.

Normalise first: lowercase, strip punctuation, collapse whitespace, remove
Arabic diacritics for AR, normalise Cyrillic apostrophes for UZ/TJ.

**Threshold (v1):** ≥ 0.80. Fail `text_mismatch` with both texts truncated to
200 chars.

Note this compares against the CLEANED text, not the raw source — the audio was
made from the cleaned version, so comparing against the raw one flags the
Prophet-symbol expansion as a defect. `scripts/stt-validate.py` hit exactly that
and had to expand the symbol on both sides.

### Step 5 — Prophet symbol expansion (hard block)

`cleanForTTS()` replaces ﷺ with a spoken phrase before the text reaches
ElevenLabs. The recognised text must therefore contain the SPOKEN phrase and
must NOT contain:

- the literal ﷺ (U+FDFA)
- `PBUH`, `SAW`, `SAWS` or lowercase variants
- `с.а.в.`, `с.а.с.`
- any other untranslated form

Fail `prophet_symbol_not_replaced`. **This is the only blocking check.** A reel
that speaks an abbreviation instead of the full phrase is a religious defect,
not a quality one.

### Step 6 — Voice identity (new in this revision)

Two assertions, both cheap, both grounded in P118:

**6a — correct slot.** Given `lang`, `style` and `mascot`, read VOICE_MAP from
`route.ts` and confirm the request would resolve to the expected id. Catches the
P084/P085 class where a missing `mascot` field silently routes to the wrong
gender.

**6b — the id is the voice its comment claims.** GET
`https://api.elevenlabs.io/v1/voices/{id}` and compare the returned `name` to
the comment beside the id.

P118: `ru.adults` was labelled Abrar and resolved to *Adam — Dominant, Firm*, an
American voice, and shipped that way on R023 and R027. `ar.*` had the same
defect. **A comment cannot be wrong loudly.** This is the only check in the
fleet that validates a label against its referent, and it found two live
defects the first time it was run by hand.

Also assert every VOICE_MAP id is distinct except where sharing is deliberate
and commented — two slots resolving to the same voice is the shape P118 took.

**Note on env vars:** only `ELEVENLABS_VOICE_EN_KIDS` is set in `.env.local`.
Every other slot resolves to its hardcoded fallback, so the fallbacks ARE the
configuration. Do not dismiss a wrong fallback as unreachable.

**AR is out of scope.** Arabic reels are not produced — the operator does not
read Arabic fluently enough to review generated output, and review gates every
publish. The AR ids are placeholders pointing at an English voice and are
labelled as such. Skip AR cases; report `out_of_scope`.

## Outputs

```json
{
  "agent": "tts-validating",
  "version": "v2",
  "timestamp": "ISO 8601",
  "case": { "lang": "ru", "style": "adults", "mascot": null,
            "slug": "sunan-abu-dawud-3641" },
  "result": "pass | fail",
  "blocking_failure": "prophet_symbol_not_replaced | null",
  "findings": [
    { "severity": "high | medium | info", "code": "...", "note": "..." }
  ],
  "diagnostics": {
    "audio_size_bytes": 0,
    "audio_duration_s": 0.0,
    "recognised_text": "...",
    "detected_language": "...",
    "text_similarity": 0.0,
    "expected_voice_id": "...",
    "resolved_voice_name": "...",
    "comment_claims": "...",
    "voice_label_matches": true,
    "prophet_symbol_violations": []
  }
}
```

## Self-validation (evals)

Five cases covering the matrix as it now stands:

1. **EN adults** — James. Baseline.
2. **RU adults** — Marat (post-P118). Must confirm the id resolves to Marat,
   not Adam. This case exists because it failed before P118.
3. **UZ kids boy** — George, text containing ﷺ. Covers the mascot split (P103)
   and the Prophet-symbol block in the hardest script.
4. **TJ kids girl** — Katherine. Covers TJ language-detection fallback.
5. **RU kids boy** — Maxim (post-P112). Regression guard on the voice swap; the
   previous voice produced an audible background hum that no automated check
   caught, only the operator's ear.

Pass criteria: 5 of 5 on Step 5 and Step 6 (both deterministic). 4 of 5 overall,
with UZ the accepted flaky case on Step 4.

**Case 5 is a known limitation, stated plainly:** the hum that caused P112 was
an artefact in otherwise-correct speech. Transcription-based validation cannot
hear it — similarity would have been high. Audio-quality assertions (noise
floor, spectral anomalies) are a v3 question. Until then, listening remains a
human step and this agent does not replace it.

## Failure escalation

| Failed step | Action |
|---|---|
| `step_5_prophet_symbol` | **Hard block. Never publish.** Religiously sensitive. |
| `step_6b_voice_label` | Block. The matrix is lying about itself (P118). |
| `step_6a_wrong_slot` | Block. Wrong-voice routing (P084/P085). |
| `step_1_audio_sanity` | Retry once, then check the ElevenLabs status page. |
| `step_2_transcription` | Retry once. If `UnicodeEncodeError`, `PYTHONIOENCODING` is not set — that is P100/P114, not a TTS defect. |
| `step_3_language_match` | Block. Likely a voice misassignment. |
| `step_4_text_similarity` | Soft-block, surface for review. May be a Whisper limitation. |

## What this agent does NOT do

- Does not modify `route.ts`, `cleanForTTS()`, or VOICE_MAP
- Does not judge audio QUALITY — hum, artefacts, prosody. See case 5.
- Does not check subtitles — that is `scripts/stt-validate.py`
- Does not check content rules — that is `scripts/lint-content.py`, run earlier
- Does not decide which voice to use, only that the chosen one was used

## Dependencies

- Python 3.10+ with `openai-whisper`, `python-Levenshtein`
- `ffprobe` on PATH
- `ELEVENLABS_API_KEY` for Step 6b only
- **No OpenAI dependency.** `OPENAI_API_KEY` is still present in `.env.local`
  but nothing in this pipeline calls it; it predates the P102/P104 migration.

## Scripts

Not yet implemented. When built, reuse:
- the S:/M:/H:/C: block parser from `scripts/lint-content.py`
- the normalisation and Prophet-symbol expansion from `scripts/stt-validate.py`
  (which already solved the compare-against-cleaned-text problem)

## Governance

- Steps 1–5 are offline and safe for push CI. Step 6b makes one ElevenLabs API
  call per distinct voice id (13 total, cacheable) — cheap but networked, so
  gate it as `@real-api` per `AGENTS_ADDENDUM.md` if run in CI.
- Human approval before publish is unaffected.

## Versioning

- **v1 (2026-06):** dual-provider, OpenAI Whisper routing, provider inference.
  Superseded — described a stack that no longer exists.
- **v2 (current, 2026-08-15):** ElevenLabs only, local Whisper, mascot split,
  voice-identity checks, AR out of scope.
- **v3 (planned):** audio-quality assertions (noise floor, spectral anomaly) to
  cover the P112 hum class; Arabic phoneme checks if AR ever comes into scope.

## Open questions

- What noise-floor metric would have caught the P112 hum without flagging normal
  room tone? Needs samples of both before a threshold can be set.
- Should Step 6b run on every invocation or once per session? 13 API calls is
  trivial but not free.
- `OPENAI_API_KEY` is unused — remove it from `.env.local`, or keep it for the
  sourcing scripts? Confirm nothing else reads it before deleting.