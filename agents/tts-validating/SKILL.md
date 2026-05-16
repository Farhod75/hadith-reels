---
name: tts-validating
description: Validates audio output from the Hadith Reels TTS route (POST /api/tts) against the P061 contract and P071 dual-provider implementation. Use this skill whenever (a) the TTS route is changed, (b) a new voice or language is added, (c) a reel is generated that will be narrated, (d) the P071 fix patterns are referenced, or (e) any task mentions ElevenLabs, OpenAI Nova, OpenAI Onyx, voice testing, narration, audio output, or pronunciation. The skill captures generated audio via Playwright, transcribes it with Whisper (local for AR/EN, OpenAI Whisper API for RU/UZ/TJ Cyrillic), and asserts five things: route returns 200 not 400, audio is not silent, recognized language matches requested lang, recognized text matches input text within similarity threshold, and the Prophet PBUH symbol has been replaced per cleanForTTS. Blocks downstream tasks if any assertion fails. Run before posting any reel to @SahihHadithReels.
---

# TTS-validating agent

System under test: `app/api/tts/route.ts` (POST `/api/tts`, accepts `{ text, lang, style }`).

This agent does not write code. It validates audio outputs and reports pass/fail with diagnostics. The orchestrator decides what to do with failures.

## When to run this agent

Run on any of these triggers:

- Changes to `app/api/tts/route.ts`, `components/TTSPlayer.tsx`, or the voice matrix env vars (`ELEVENLABS_VOICE_*`, `OPENAI_API_KEY`)
- Before posting any reel to a public channel (Telegram, Instagram, TikTok, YouTube)
- Before merging any PR that touches narration, captions, or the reel generation pipeline
- When a new language or voice is added to `VOICE_MAP`
- When `cleanForTTS()` is modified
- On-demand via orchestrator dispatch
- As a CI step tagged `@real-api` (manual `workflow_dispatch` only — never in push CI, per `AGENTS_ADDENDUM.md` Golden Rule)

## Pre-task reads (mandatory)

Before any validation run, read these files in order. Stop if any is missing.

1. `references/voice-matrix.md` — current lang × style → provider+voice mapping (P071)
2. `references/p061-tts-contract.md` — the `{text, lang, style}` request contract
3. `references/p071-cleanforTTS.md` — Prophet symbol replacement rules per language
4. `references/whisper-routing.md` — which Whisper backend to use per language
5. `references/thresholds.md` — current pass/fail thresholds (v1: all moderate)

If any of those files is missing, stop and report `setup_incomplete` — do not proceed with stale assumptions.

## Inputs

The orchestrator passes one or more test cases to this agent. Each case has:

- `text` — string to narrate (max 1000 chars per route)
- `lang` — one of `en`, `ar`, `uz`, `ru`, `tj`
- `style` — `adults` or `kids`
- `expected_provider` — `elevenlabs` or `openai` (derived from lang; agent verifies)
- `expected_voice_name` — human-readable voice name (Hijazi, Abrar, Nova, Onyx, James, Danielle) for diagnostic logging only

For routine pre-publish checks, the agent runs the baseline eval set from `evals/evals.json` (5 cases — one per language).

## Validation pipeline

For each test case, run these steps in order. Fail-fast: stop at the first failure and report which step failed.

### Step 1 — Contract guard (catches P061 regressions)

POST `{ text, lang, style }` to `/api/tts`. Record:

- HTTP status code
- Response `Content-Type` header
- Response time (ms)

**Assertions:**
- `status !== 400` — if 400, this is a P061 regression (route demanding `voiceId` again). Report `p061_regression` and stop.
- `status === 200` — any other non-200 is a different failure; report `route_error` with the status and response body.
- `Content-Type === 'audio/mpeg'` — confirms binary audio, not JSON error.

### Step 2 — Audio file sanity

Save the response body as a temp `.mp3` file. Measure:

- File size in bytes
- Duration in seconds (via `ffprobe` or `mutagen`)

**Thresholds (v1 moderate):**
- File size ≥ 10 KB — below this is empty or header-only
- Duration ≥ 1.0 second — below this is silent or truncated

Fail with `audio_too_small` or `audio_too_short` if either threshold is missed.

### Step 3 — Whisper transcription

Route to the correct Whisper backend per `references/whisper-routing.md`:

- `en`, `ar` → Whisper local (`openai-whisper` Python package, model: `small` for v1)
- `ru`, `uz`, `tj` → OpenAI Whisper API (`/v1/audio/transcriptions`, model: `whisper-1`), explicit `language` parameter (`ru` for RU, `uz` for UZ, `tg` for TJ)

**Note on UZ:** Whisper's Cyrillic Uzbek training data is thin. The agent uses `language=uz` but should treat similarity scores 0.05–0.10 lower than other languages as expected baseline noise. The threshold (0.80 moderate) accounts for this; below 0.70 indicates a real recognition problem.

Record from Whisper response:
- Recognized text (`text` field)
- Detected language (`language` field)
- Language confidence — if Whisper API returns segment-level confidence, average across segments; otherwise default to 0.85 if `language` matched the request and `1 - WER` is reasonable

### Step 4 — Language match assertion

**Threshold (v1 moderate):** detected language must equal `lang` parameter AND confidence ≥ 0.75.

Special case for TJ: Whisper returns `tg` (Tajik) or sometimes `fa` (Persian) or `ru` (Russian, when Tajik is too close to Russian Cyrillic). Accept `tg` strictly; accept `fa` and `ru` with a warning. Fail only if detection is `en` or wildly unrelated.

Fail with `language_mismatch` if assertion fails. Include the detected language and confidence in the report.

### Step 5 — Text similarity assertion

Compute Levenshtein-normalized similarity between input `text` and Whisper-recognized text.

Normalization before comparison:
- Lowercase both
- Strip punctuation
- Collapse whitespace
- Remove Arabic diacritics for AR
- Normalize Cyrillic apostrophes/spacing for UZ/TJ

**Threshold (v1 moderate):** similarity ≥ 0.80.

Fail with `text_mismatch` if similarity < 0.80. Include both texts (truncated to 200 chars each) in the report so the reviewer can see what was misheard.

### Step 6 — Prophet symbol replacement assertion (P071)

The `cleanForTTS()` function in the route must replace the Prophet symbol ﷺ with a language-specific phrase before sending to the TTS provider. The recognized text must NOT contain:

- The literal Prophet symbol `ﷺ` (Unicode U+FDFA)
- The English abbreviations `PBUH`, `SAW`, `SAWS`, `pbuh`, `saw`
- The Russian transliteration `с.а.в.` or `с.а.с.`
- Any other untranslated form per `references/p071-cleanforTTS.md`

Fail with `prophet_symbol_not_replaced` if any banned string is found. This is the strictest check — the symbol must be fully replaced; partial replacement is a failure.

### Step 7 — Provider verification (sanity check)

The route doesn't return which provider was used, so the agent infers from headers and audio characteristics:

- ElevenLabs MP3 frames have a distinctive ID3v2 header structure
- OpenAI Nova/Onyx MP3 frames have a different bitrate profile (typically 32kbps mono vs ElevenLabs 64kbps)

For v1, this is informational only — agent reports `inferred_provider` but does not fail on mismatch. Mismatch becomes a hard assertion in v2 once we have 30+ real samples to calibrate the heuristic.

## Outputs

Return a structured report. Schema:

```json
{
  "agent": "tts-validating",
  "version": "v1",
  "timestamp": "ISO 8601",
  "case_id": "string",
  "request": { "text": "...", "lang": "...", "style": "..." },
  "result": "pass | fail",
  "failed_step": "step_1_contract | step_2_audio_sanity | step_3_transcription | step_4_language_match | step_5_text_similarity | step_6_prophet_symbol | null",
  "diagnostics": {
    "http_status": 200,
    "content_type": "audio/mpeg",
    "response_time_ms": 0,
    "audio_size_bytes": 0,
    "audio_duration_s": 0.0,
    "whisper_backend": "local | openai_api",
    "recognized_text": "...",
    "detected_language": "...",
    "language_confidence": 0.0,
    "text_similarity": 0.0,
    "prophet_symbol_violations": [],
    "inferred_provider": "elevenlabs | openai | unknown"
  },
  "warnings": []
}
```

If `result === "fail"`, include enough diagnostic detail that the orchestrator can decide whether to (a) retry, (b) escalate to a human, or (c) match against `fix_patterns.md` for a known issue.

## Self-validation (evals)

The agent runs its own eval set from `evals/evals.json` whenever the SKILL.md or any reference is changed. Eval cases cover:

1. EN adults — short authentic hadith (sanity baseline)
2. AR adults — Arabic hadith with diacritics (Hijazi voice, diacritic-aware similarity)
3. RU adults — Russian hadith (Abrar voice, OpenAI Whisper API)
4. UZ kids — Uzbek Cyrillic hadith with Prophet symbol (Nova voice, P071 verification)
5. TJ adults — Tajik Cyrillic hadith (Onyx voice, fallback language detection)

Eval pass criteria: at least 4 of 5 cases pass for the agent to be considered green. The UZ case is the most likely to fail due to Whisper Cyrillic Uzbek limitations; we accept that as the known-flaky case for v1.

## Failure escalation paths

Each failure type has a defined escalation. The orchestrator follows this table.

| Failed step | Action | Notes |
|---|---|---|
| `step_1_contract` (status 400) | Block all downstream tasks. Match against P061. Open issue. | P061 regression — never ship. |
| `step_1_contract` (other) | Retry once. If still fails, escalate to human. | Could be transient API issue. |
| `step_2_audio_sanity` | Retry once. If still fails, check provider quota/status pages. | ElevenLabs and OpenAI status. |
| `step_3_transcription` (Whisper error) | Retry once with fallback backend (local ↔ API). | Don't fail the case for Whisper issues. |
| `step_4_language_match` | Block. Inspect voice matrix. Possible voice misassignment. | Real bug. |
| `step_5_text_similarity` | Soft-block. Surface for human review. | Could be Whisper limitation, not route bug. |
| `step_6_prophet_symbol` | **Hard block. Never publish.** Open critical issue. | P071 violation — religiously sensitive. |

## What this agent does NOT do

- Does not modify `route.ts`, `cleanForTTS()`, or the voice matrix — that's the Code agent's job
- Does not generate reels — that's the Reel-generating agent
- Does not post to social media — that's a human decision per HR-AGENTS.md
- Does not decide which voice to use — only validates that the chosen voice produced acceptable output

## Dependencies

- Python 3.10+ with `openai-whisper`, `openai`, `mutagen`, `python-Levenshtein`
- Playwright (TypeScript) with `--project=chromium` for audio capture
- `ffprobe` on PATH (ships with FFmpeg, already installed per HR project memory)
- Environment variables: `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, plus all `ELEVENLABS_VOICE_*` IDs

## Scripts

Implementation files live in `scripts/`:

- `scripts/capture-audio.ts` — Playwright script that hits `/api/tts` and saves the MP3
- `scripts/transcribe.py` — Whisper routing (local vs OpenAI API per language)
- `scripts/compare.py` — Levenshtein similarity with language-aware normalization
- `scripts/run-evals.py` — runs the full eval set from `evals/evals.json` and prints the report
- `scripts/check-prophet-symbol.py` — Step 6 banned-strings check

These are stubs in v1. The Code agent generates them in follow-up tasks once this SKILL.md is approved.

## Governance compliance

This agent must follow:

- `AGENTS_ADDENDUM.md` Golden Rule: never run as part of push CI; manual `workflow_dispatch` only (real OpenAI + ElevenLabs API calls)
- `QA_STANDARDS_ADDENDUM.md` Section 6.5: tagged `@real-api`
- `HR-AGENTS.md` Test agent rules: mocks not allowed in this agent's eval set — it explicitly tests real API behavior, by design, which is why it's gated to manual dispatch
- `CI_WORKFLOW_TEMPLATE.md` Rule 1: never added to push-triggered CI steps

## Versioning

- **v1 (current):** Whisper-based validation, moderate thresholds, 5-case eval baseline, single-shot per case
- **v2 (planned):** Provider verification (Step 7) becomes hard assertion; tightened thresholds; multi-shot for flaky cases; calibrated against 30+ real samples
- **v3 (planned):** Add pronunciation-accent matching (e.g., Hijazi-specific phoneme assertions for AR); add prosody/intonation quality scoring; integrate with A/B-comparing agent for cross-LLM verdict on narration quality

## Open questions for v2

These are intentionally deferred from v1 to keep the agent shippable today:

- How to detect TJ when Whisper labels output as `ru` instead of `tg` — current accept-with-warning is too lenient
- Whether to add a phoneme-level Arabic check for ﷺ replacement (current text-based check would miss if the replacement was spoken in transliteration)
- How to score "compassionate tone" in the audio (HV principle: AI flags, humans decide — but agent could surface a flag for human review)
- Whether to validate Uzbek Latin vs Uzbek Cyrillic separately when `lang=uz_latin` or `lang=uz_cyrillic` is passed (currently the route normalizes to `uz`)

These move into v2 once we have data to ground them.
