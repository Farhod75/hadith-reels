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

**Last checked:** 2026-10-04
**Next due:** 2026-10-11

---

## Versions in use vs available

| Tool | In use | Where it is set | Latest known | Status |
|---|---|---|---|---|
| ElevenLabs TTS | `eleven_v4` | `app/api/tts/route.ts` fallback | v4, v4 Turbo | CURRENT as of 2026-10-04 (P193) |
| Kling video | `fal-ai/kling-video/v2.6/pro` | `scripts/generate-scene.ps1` | **Kling 3.0** (Feb 2026) | **BEHIND — not evaluated** |
| FLUX stills | `fal-ai/flux-2` | `scripts/generate-image.ps1` | FLUX 2 | CURRENT as of 2026-10-04 |
| Claude (generation) | `claude-sonnet-5` | `app/api/generate-reel/route.ts` | — | check model list quarterly |
| Whisper | local `openai-whisper` | PATH | — | RU ASR is a standing cost (R095, R099, R107) |

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

- **Kling 3.0** — multi-shot generation and 15s clips (2.6 Pro is capped at 10s,
  which is why `-FitScenes` exists). No known defect in 2.6 Pro drives this; it
  is simply a major version behind. Evaluate at a SET boundary, same prompt on
  both models, because a model change re-rolls every scene prompt we have tuned
  — and because P193 showed that what one model gets right is not inherited.
- ~~**FLUX 2**~~ — **EVALUATED AND ADOPTED 2026-10-04.** The m2963 steps prompt
  asked for a camera at the TOP of a staircase looking DOWN — the hadith's
  instruction as camera direction. v1.1 returned six consecutive upward shots
  across two prompts and the concept was abandoned as an unbreakable model prior.
  flux-2 rendered it correctly on variants 1 AND 2 of a single call, from the
  same prompt text, with no code change — the script already accepted -Model.
  **The concept was never the problem.** Default switched in generate-image.ps1.

## Practice, not tools

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

## Log

| Date | Checked | Found |
|---|---|---|
| 2026-10-04 | ElevenLabs, Kling, FLUX, Anthropic guidance | v4 already adopted same day (P193). Kling 3.0 and FLUX 2 both behind, neither previously noticed. Anthropic positive-instruction guidance vs 20 NEVER rules. |
| 2026-10-04 | FLUX 2 evaluated | ADOPTED. Rendered on the first call a shot v1.1 refused six times. Kling 3.0 still open. |
