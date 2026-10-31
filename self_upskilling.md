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

**Last checked:** 2026-10-31
**Next due:** 2026-11-07

> **This date is now enforced.** `audit-docs.py` fails the push when it
> passes (P332). Before that it was a line in a file that was missed three
> times out of five recorded runs - including the run that declared FLUX 2
> current three days after FLUX 3 shipped.

---

## Versions in use vs available

| Tool | In use | Where it is set | Latest known | Status |
|---|---|---|---|---|
| ElevenLabs TTS | `eleven_v4` | `app/api/tts/route.ts` fallback | v4, v4 Turbo | CURRENT, re-confirmed 2026-10-22 BY PROBE — `eleven_v4` and `eleven_v4_turbo` both return audio; `eleven_v5` and `eleven_v5_turbo` both return `model_not_found`. No v5 exists (P193) |
| Kling video | `fal-ai/kling-video/v3/pro` | `scripts/generate-scene.ps1` | **Kling 4.0 — API NOW OPEN** | **BEHIND one major version, changed 2026-10-31.** fal has announced public API access to all customers; 30s native generation with audio, up to 15 references, 10 keyframes. The 2026-10-22 row said "coming soon" and that is no longer true. Re-fetched 2026-10-31 (run d): model page shows an API tab, endpoint id `kling/v4/image-to-video`, $0.157/s at 720p and $0.235/s at 1080p, 3-30s clips; eval still open — see open evals |
| FLUX stills | `fal-ai/flux-2` | `scripts/generate-image.ps1` | **FLUX 3 Image, 2026-10-01** | **BEHIND one major version** — re-confirmed 2026-10-22: FLUX 3 is callable at `blackforestlabs/flux-3/text-to-image`, $0.048 per 1 MP image. See open evals |
| Claude (generation) | `claude-sonnet-5` | `app/api/generate-reel/route.ts` | — | check model list quarterly |
| Playwright | `@playwright/test` **1.64.1** (pinned exact) | `package.json` | **1.64** | **CURRENT since 2026-10-31 (P333); ci.yml unpinned to `ubuntu-latest`.** Was BEHIND four minor versions. 1.61 is the release that adds Ubuntu 26.04 support** — the version that would let `.github/workflows/ci.yml` drop its `ubuntu-24.04` pin (P314). **Added to this watchlist 2026-10-31, and the omission is the finding:** CI went red for 31 consecutive runs on this toolchain while the file that exists to watch the project's tools did not list it |
| Whisper (ASR) | local `openai-whisper` | PATH | ElevenLabs **Scribe v2** | Scribe v2 PROBED 2026-10-15, verdict recorded below. Re-checked 2026-10-22: no Scribe v3 exists; latest is v2 plus a `scribe-v2-medical` variant. Nothing new to evaluate |

## Official sources

Where each tool announces change. **A source is only listed once it was
actually fetched**, with the date and what it showed; an unverified URL is
marked as such. Release notes say what shipped - the probe in the next
section says whether it works for us.

| Tool | Where to look | Last fetched | What it showed |
|---|---|---|---|
| Claude API / models | https://platform.claude.com/docs/en/release-notes/overview | 2026-10-31 (d) | Newest entry 2026-10-30: fast mode deprecated for `claude-opus-4-8`, removal 2026-11-30. No new model ids. Does not touch `claude-sonnet-5`. `docs.anthropic.com/en/release-notes` answers **302** to `platform.claude.com` - old links in this repo still work, but cite the new domain |
| Claude Code | https://code.claude.com/docs/en/hooks , https://code.claude.com/docs/en/settings | 2026-10-31 | Hook schema (event -> array of matcher groups); SessionStart stdout enters context; unknown/invalid entries are skipped (P334). Installed CLI here: 2.1.223 |
| Claude Code settings schema | https://json.schemastore.org/claude-code-settings.json | referenced 2026-10-31 | Named by the settings docs as the published schema; `.claude/settings.json` now points `$schema` at it so VS Code validates |
| Prompt practice (GenAI) | https://claude.com/blog/best-practices-for-prompt-engineering | earlier - see Practice section | Already used for the Practice section below |
| Playwright | https://playwright.dev/docs/release-notes | 2026-10-31 (d) | 1.64 still latest (re-fetched; 1.64 adds WebMCP, video fps/VP9, `--shuffle`). 1.61 adds Ubuntu 26.04; 1.62 drops Debian 11; 1.63 drops Ubuntu 20.04; 1.64 changes hidden-iframe visibility and `screen` emulation |
| GitHub runner images | https://github.com/actions/runner-images/releases , https://github.blog/changelog/2026-06-11-new-runner-images-in-public-preview/ | 2026-10-31 (d) | Newest releases 2026-10-26/28 image updates incl. Ubuntu 26.04/24.04/22.04. An `ubuntu-latest` -> 26.04 in November 2026 announcement was reported in a truncated part of the page - NOT verified verbatim. Migration tracked in actions/runner-images#14748 (P314) |
| Supabase | https://supabase.com/changelog | 2026-10-31 (d) | Newest: Postgres tz fix (Oct 30), Knowledge Base public beta (Oct 23), .NET SDK OpenTelemetry (Oct 14). Nothing affecting supabase-js usage here |
| fal (Kling, FLUX hosting) | https://blog.fal.ai/ and the model page per endpoint | 2026-10-31 (d) | Blog newest: EAGLE-4 (Oct 20), H3 Max (Sep 17, Aug 27) - nothing on Kling/FLUX. Kling v4 model page: API tab, `kling/v4/image-to-video`, $0.157/s 720p, $0.235/s 1080p |
| Black Forest Labs (FLUX) | https://bfl.ai/models/flux-3-video | earlier | FLUX 3 - see Open evaluations |
| ElevenLabs | https://elevenlabs.io/docs/api-reference/speech-to-text/convert | earlier | **Changelog index not fetched** (blocked here). Probe with a call, per the rule below - that is the operator's paid call |
| Next.js | https://nextjs.org/blog | 2026-10-31 (d) | Latest announced release 16.4 (2026-10-06); npm shows 16.4.3. **"Upcoming Next.js November Security Release" posted 2026-10-27** - we pin 16.2.6 |

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
| 2026-10-31d | npm (package.json vs `npm view`), Playwright, Claude API, Next.js, Supabase, runner images, fal/Kling | Scheduled weekly run; header dates already 2026-10-31/2026-11-07 from run c, left unchanged. **npm behind:** next 16.2.6 vs 16.4.3 (Next.js November security release announced 2026-10-27); react/react-dom 19.2.4 vs 19.3.1; typescript 5.9.3 vs 7.0.2 (major); @supabase/supabase-js 2.105.4 vs 2.118.0; @anthropic-ai/sdk 0.95.2 vs 1.3.0 (major); remotion 4.0.460 vs 4.0.539. Current: @playwright/test 1.64.1, @fal-ai/client 1.10.1. Kling 4.0 endpoint id and pricing now read off the model page. Next.js blog fetched for the first time. **Not verified:** ElevenLabs (paid probe), BFL/FLUX page, Claude Code release notes, Whisper/Scribe, `ubuntu-latest` -> 26.04 announcement (seen only in a truncated summary). |
| 2026-10-31c | Playwright (upgraded), Claude Code hooks, sources | Playwright 1.64.1 installed and CI unpinned (P333). Reading the Claude Code hooks reference to wire the index found that **this repo's hooks had never run** (P334). Official sources section added; two URLs marked unverified rather than listed as checked. |
| 2026-10-31 | Kling, FLUX, Playwright, ElevenLabs (not probed) | Ran **2 days overdue — and for the first time something said so**: `audit-docs.py` now fails the push on this file's own due date (P332). **Kling 4.0 API OPENED** since the 22nd, so the Kling row flips from current to behind. **Playwright found at 1.60.0 against 1.64, and was not on this watchlist at all** despite being the toolchain behind 31 red CI runs; 1.61 is what unpins ci.yml. FLUX 3 still outstanding since 2026-10-01 — fifteen stills were generated on flux-2 on 2026-10-30 because this file was not read. ElevenLabs not probed: the rule here is probe-don't-trust and that is a paid call, left for the operator. |
| 2026-10-04 | ElevenLabs, Kling, FLUX, Anthropic guidance | v4 already adopted same day (P193). Kling 3.0 and FLUX 2 both behind, neither previously noticed. Anthropic positive-instruction guidance vs 20 NEVER rules. |
| 2026-10-04 | FLUX 2 evaluated | ADOPTED. Rendered on the first call a shot v1.1 refused six times. Kling 3.0 still open. |
| 2026-10-11 | Kling 3.0 | ADOPTED as `v3/pro`. Logged retroactively on 2026-10-15 — the eval happened but neither this Log nor the header date was updated, against this file's own rule that the date CHECKED is the value. |
| 2026-10-15 | ElevenLabs, Kling, FLUX, ASR alternatives | Ran 4 days overdue. ElevenLabs v4 still newest, no v5, so the v4 pronunciation watch-list rows stay validly scoped. Kling 3.0 current. **FLUX 3 Image found — shipped 2026-10-01, three days before the check that called FLUX 2 current.** New lead: Scribe v2 may close P078 for UZ/TJ; output script undocumented, needs a probe. |
