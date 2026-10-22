# Self-Upskilling Watchlist

> **Why this file exists.** ElevenLabs released v4 on 2026-09-28. It was found on
> 2026-10-03 by accident, while auditioning a Russian voice for an unrelated
> reason — six days, and only because something else was being changed. Nothing
> in this project watches the tools it is built on. Kling has been a major
> version behind since February and FLUX since last November, and neither was
> noticed at all.
>
> **Cadence: once a week.** Agent 11 (`upskilling`) owns this when it is built.
> Until then a human or the session assistant runs it. Record the date checked
> even when nothing changed — "last checked" is the value, not "last updated".

**Last checked:** 2026-10-22
**Next due:** 2026-10-29

---

## Versions in use vs available

| Tool | In use | Where it is set | Latest known | Status |
|---|---|---|---|---|
| ElevenLabs TTS | `eleven_v4` | `app/api/tts/route.ts` fallback | v4, v4 Turbo | CURRENT, re-confirmed 2026-10-22 BY PROBE — `eleven_v4` and `eleven_v4_turbo` both return audio; `eleven_v5` and `eleven_v5_turbo` both return `model_not_found`. No v5 exists (P193) |
| Kling video | `fal-ai/kling-video/v3/pro` | `scripts/generate-scene.ps1` | **Kling 4.0 — playground only** | LATEST CALLABLE VERSION, re-confirmed 2026-10-22. 4.0 is live on fal but has NO API yet — see open evals |
| FLUX stills | `fal-ai/flux-2` | `scripts/generate-image.ps1` | **FLUX 3 Image, 2026-10-01** | **BEHIND one major version** — re-confirmed 2026-10-22: FLUX 3 is callable at `blackforestlabs/flux-3/text-to-image`, $0.048 per 1 MP image. See open evals |
| Claude (generation) | `claude-sonnet-5` | `app/api/generate-reel/route.ts` | — | check model list quarterly |
| Whisper (ASR) | local `openai-whisper` | PATH | ElevenLabs **Scribe v2** | Scribe v2 PROBED 2026-10-15, verdict recorded below. Re-checked 2026-10-22: no Scribe v3 exists; latest is v2 plus a `scribe-v2-medical` variant. Nothing new to evaluate |

## How to check each, without trusting a release note

- **ElevenLabs** — probe the TTS endpoint with a candidate `model_id` and a two-word
  string. A valid id returns audio, an invalid one returns an error. The models
  endpoint needs a scope this key does not have, so probing is the reliable path.
  **Then audition on OUR OWN Cyrillic** before switching: P193 exists because v4
  fixed three Tajik words and broke an Uzbek one that had been safe for 105 reels.
- **Kling / FLUX** — fal.ai model ids are path-shaped. A new version is a new path;
  the old one keeps working. Changing either one re-rolls every scene prompt we
  have tuned, so evaluate at a SET boundary with the same prompt on both models.
- **Claude** — model string in the generation route. A model change re-rolls the
  generator's additions (P191/P195), so the eval is the four blocks, not the API.

## Open evaluations

- **Kling 4.0 — ANNOUNCED, NOT CALLABLE. Checked 2026-10-22.** Live on fal in
  the playground and fal Agent; the model page says **"API access is coming
  soon."** So `fal-ai/kling-video/v3/pro` is still the latest version we can
  actually call, and the CURRENT row above is accurate rather than behind.

  Two things to carry to the day it opens:

  1. **The path shape changes.** 4.0 is `kling/v4/image-to-video` — no
     `fal-ai/` prefix, no `kling-video` segment. `generate-scene.ps1`'s version
     handling was written around `fal-ai/kling-video/vN/...`. This is the same
     unguarded-path concern already recorded for `flux-3` below, now with a
     second instance, which makes it a shape problem rather than a one-off.
  2. **Specs worth having:** 3–30s clips (v3 tops out well below that, which is
     why `-FitScenes` exists), up to 10 keyframes, 21:9, stereo audio, 8,000-token
     prompts. 4.0 Flash has been in limited early access since 2026-09-28 and
     caps at 20s. Pricing $0.157/s at 720p, $0.235/s at 1080p — against four 10s
     clips per set that is roughly $9.40 at 1080p, about 2.7x the current
     $3.50 for a set.

  Evaluate at a SET boundary with the same prompt on both models, per the rule
  above. Do not adopt mid-set: it re-rolls every scene prompt we have tuned.

  Sources: https://fal.ai/learn/tools/what-is-kling-4-0 · https://fal.ai/models/kling/v4/image-to-video

- ~~**Kling 3.0**~~ — **EVALUATED AND ADOPTED 2026-10-11.** Multi-shot generation and 15s clips (2.6 Pro is capped at 10s,
  which is why `-FitScenes` exists). No known defect in 2.6 Pro drives this; it
  is simply a major version behind. Evaluate at a SET boundary, same prompt on
  both models, because a model change re-rolls every scene prompt we have tuned
  — and because P193 showed that what one model gets right is not inherited.
  **Checked 2026-10-11:** live on fal as `fal-ai/kling-video/v3/pro/image-to-video`,
  with `v3/standard` and `v3/4k` beside it. `duration` 3–15s. `multi_prompt`
  gives per-shot prompts, `elements` 1–3 reference images per character,
  `shot_type: intelligent` lets the model structure the shots. **$0.112/s audio
  off against 2.6 Pro's $0.07/s — 1.6×, and seconds of clip per reel are
  fixed by the narration, so 15s clips buy fewer cuts, not fewer seconds.** The
  eval was blocked by P214 first: the audio-off guard was scoped to `v2\.6`, so
  the v3 half would have generated audio and cost $1.68 for a clip that cannot
  be compared against a silent one.
  **VERDICT — ADOPTED.** One still (`b5027-matn-1.jpg`), one prompt, both
  models, 10s each, at the #5027 set boundary. Both returned 1080x1920, 24fps,
  10.04s, zero audio streams. **3.0 wins on light:** it cast defined
  window-pane shadow bars across the left page, physically coherent with the
  window in frame, where 2.6 gave an undifferentiated warm patch; parchment
  fibre and cloth weave are crisper too. **One regression:** 3.0 reads motion
  instructions more aggressively — “a very slow gentle push” travelled far
  further than on 2.6 — so phrase camera moves conservatively. Default switched
  in generate-scene.ps1; 2.6 Pro still reachable with -Model.
  **The larger finding was not the one under test:** BOTH models preserved real
  Arabic composited onto the still, letterforms and tashkeel intact through all
  10s at 24fps. Rendered text survives i2v animation — the project had assumed
  it would not. Method recorded under Practice below.
  Caveat on the verdict: three sampled frames per clip were compared, not
  motion. Mid-clip flicker or shimmer would not have shown.
- ~~**FLUX 2**~~ — **EVALUATED AND ADOPTED 2026-10-04.** The m2963 steps prompt
  asked for a camera at the TOP of a staircase looking DOWN — the hadith's
  instruction as camera direction. v1.1 returned six consecutive upward shots
  across two prompts and the concept was abandoned as an unbreakable model prior.
  flux-2 rendered it correctly on variants 1 AND 2 of a single call, from the
  same prompt text, with no code change — the script already accepted -Model.
  **The concept was never the problem.** Default switched in generate-image.ps1.

## Practice, not tools

- **2026-10-11 — real Arabic can be composited onto a still and survives Kling.**
  FLUX cannot write Arabic: three `b5027-page` variants came back as convincing
  gibberish, and that matters most exactly where the text is the subject. A
  near-correct ayah would be worse than an obviously decorative one, so scripture
  is never rendered by the model. The method, free per use once set up: FLUX a
  BLANK page — describe the emptiness as a STATE (“bare unmarked parchment, faint
  dry ruling lines the only marks crossing them”), per R026 — then render the real
  text with Pillow using the RAQM layout engine (HarfBuzz shaping gives correct
  joining and tashkeel; pass direction=“rtl”), perspective-warp it onto the page
  quad, and MULTIPLY it into the parchment so it absorbs instead of sitting on top.
  Amiri is the right face and comes from npm (`@fontsource/amiri`, woff2 -> ttf via
  fontTools): GitHub release downloads are not reachable from the session container
  and Windows ships no manuscript Naskh.
  **Keep the categories straight.** A page carrying a HADITH matn is a hadith
  manuscript, not a mushaf. Putting the matn on something that reads as a Quran
  conflates the two, which is the one confusion this channel cannot afford.

- **2026-10-04 — Anthropic's prompting guidance: tell the model what TO do, not
  what NOT to do.** `generate-reel/route.ts` is twenty rules, nearly all NEVER.
  This project already found the same principle independently as **R026** — on
  scene prompts, negations reinforce what they forbid, which is why absence is
  written as a state ("still and unattended") rather than as "no people". That
  finding was never carried from images across to text. Rules 17-20, added the
  same day this was read, are also negative. Rewriting the rule list in positive
  form is an open task, and a measurable one: the test is whether a generation
  comes back without the four additions.
  Source: https://claude.com/blog/best-practices-for-prompt-engineering
- Also in that guidance and not yet applied here: give the model explicit
  permission to say it does not know, rather than only forbidding invention.
  Rule 2 tells it to explain the teaching instead of constructing an incident,
  which is close — but nothing in the prompt lets a field come back empty.

- **FLUX 3 Image — NOT EVALUATED, and we are a major version behind again.**
  `blackforestlabs/flux-3/text-to-image` is live on fal; stills still go through
  `fal-ai/flux-2`. The DATES are the finding: **FLUX 3 Image launched 2026-10-01,
  three days BEFORE the 2026-10-04 check that adopted FLUX 2 and recorded it as
  CURRENT.** FLUX 3 had been reachable on fal since early access on 2026-07-23,
  with the Video API on 2026-08-04. The weekly check this file exists to institute
  missed a major version that was already shipping — the same failure the header
  describes, occurring inside the process meant to prevent it. Evaluate at a SET
  boundary: one still, same prompt, both models, per the rule above.
  Sources: https://bfl.ai/models/flux-3-video · https://fal.ai/explore/black-forest-labs

- **FLUX 3 Video as a Kling alternative — NOT EVALUATED.** Clips to 20s (Kling
  3.0 caps at 15s, 2.6 Pro at 10s), up to 4K, with OPTIONAL NATIVE AUDIO. Before
  any probe, widen P214's guard: it is scoped to `v2\.6`, so it already failed to
  cover `v3` once and would not cover a `flux-3` path either. An unguarded
  audio-on generation is a paid clip that cannot be compared against a silent one.
  Same set-boundary rule, and longer clips buy fewer CUTS, not fewer seconds,
  because seconds per reel are fixed by the narration.

- ~~**ElevenLabs Scribe v2 for UZ/TJ subtitles**~~ — **PROBED 2026-10-15.
  VERDICT: does NOT close P078, and for TJ it is WORSE than Whisper.** Six calls
  against `scribe_v2` on the ~20s #6570 moral mp3s, each language with and
  without `language_code`, since the hint could itself steer the script:

  | audio | language_code | detected | OUTPUT SCRIPT |
  |---|---|---|---|
  | UZ | `<auto>` | `eng` @ 0.29 | LATIN |
  | UZ | `uzb` | `uzb` @ 1.00 | LATIN |
  | TJ | `<auto>` | `fas` @ 0.97 | PERSO-ARABIC |
  | TJ | `tgk` | `tgk` @ 1.00 | PERSO-ARABIC |

  UZ returns Latin exactly as Whisper does, so P078's premise is unchanged. TJ is
  worse: at `language_code=tgk` and probability 1.0 it still returns PERSO-ARABIC,
  not Cyrillic — Scribe treats `tgk` as Persian orthography. That is not a
  transliteration gap but a different script, and further from the channel's
  Cyrillic than Whisper's Latin was.

  **The transcripts are ACCURATE, which leaves one opening for UZ only.** Scribe
  returned `Ixlos bilan o'z ichingdan "La ilaha illallah" deb ayt. Payg'ambar
  sallallahu alayhi vasallam shafaatidan eng baxtli bo'ladigan kishi...` — correct
  wording, and it placed the apostrophe as tutuq belgisi in `o'z` and
  `Payg'ambar`, the exact character class that broke #6423 UZ's kalima. The
  library already holds `text_uzbek_latin`. So `stt-validate.py` could compare
  Scribe's Latin output against THAT column and give UZ an automated listener for
  the first time, retiring "nothing automated hears these" for one of the two
  languages. Subtitles stay off regardless (P078 is about burn-in); this would be
  validation only. OPEN TASK, not done.

  TJ has no equivalent path: there is no `text_tajik_arabic` column, and
  transliterating Cyrillic Tajik into Perso-Arabic to compare is a research
  project, not a check. TJ stays with the human narration check as its only
  listener.

  Also measured: `<auto>` misread Uzbek as English at 0.29 confidence. If Scribe
  is ever wired in, `language_code` is mandatory, not an optimisation.

  Endpoint `POST https://api.elevenlabs.io/v1/speech-to-text`, header `xi-api-key`,
  multipart `file` + `model_id=scribe_v2` + optional `language_code` (ISO-639-1/3).
  Source: https://elevenlabs.io/docs/api-reference/speech-to-text/convert

## Log

| Date | Checked | Found |
|---|---|---|
| 2026-10-04 | ElevenLabs, Kling, FLUX, Anthropic guidance | v4 already adopted same day (P193). Kling 3.0 and FLUX 2 both behind, neither previously noticed. Anthropic positive-instruction guidance vs 20 NEVER rules. |
| 2026-10-04 | FLUX 2 evaluated | ADOPTED. Rendered on the first call a shot v1.1 refused six times. Kling 3.0 still open. |
| 2026-10-11 | Kling 3.0 | ADOPTED as `v3/pro`. Logged retroactively on 2026-10-15 — the eval happened but neither this Log nor the header date was updated, against this file's own rule that the date CHECKED is the value. |
| 2026-10-15 | ElevenLabs, Kling, FLUX, ASR alternatives | Ran 4 days overdue. ElevenLabs v4 still newest, no v5, so the v4 pronunciation watch-list rows stay validly scoped. Kling 3.0 current. **FLUX 3 Image found — shipped 2026-10-01, three days before the check that called FLUX 2 current.** New lead: Scribe v2 may close P078 for UZ/TJ; output script undocumented, needs a probe. |
