# Open items

**What this file is for.** `fix_patterns.md` records WHY something happened and
carries a Status line at the bottom of each pattern. That is 200+ Status lines
scattered through one long file, and it is not a list of what is outstanding.
Everything else lived in chat, and chat ends. Items have slipped twice that way.

**The rule:** an item leaves this file only when it is DONE, or deliberately
dropped with the reason written here. Not when it stops being interesting.

Read at session start, step 3. Added 2026-10-08.

**Completeness.** This file was first assembled on 2026-10-08 from one
session's view, and four items from earlier sessions were missing on the first
pass — found only because the operator asked whether everything had been
carried over. Assume it is still incomplete. Add to it rather than trusting it.


---

## Blocks content — do not ship past these

**Sahih al-Bukhari #6871 must never follow #2654 without a deliberate call.**
Different number, same subject (al-kaba'ir). The duplicate index keys on the
number so nothing flags the pair, and NO automated check covers it — a
similarity check was written and removed on 2026-10-09 because the pair scores
0.16 against a library-wide maximum of 0.29 (P205). The mechanism is now a row
in the tracker's duplicate-check index. This item stays open only as a pointer
to that row.

---

## Recorded, not built

**P196 — the linter only ever sees text a human already cleaned.**

**P126 — classifier blind spots.** Partly covered.

---

## Pipeline / design

**Re-measure the rest of the pronunciation watch-list against v4.** The ﷺ
entry is CLOSED (2026-10-09): checked on v4, all languages handle it, and
`cleanForTTS` expands it before TTS anyway so the model never sees it — the
doc had been describing a per-language distinction the code does not make.
The REST of the watch-list in `reel-creation-pipeline.md` is still scoped to
whichever model measured it, and P193 says those entries expire when the
model changes. They have not been re-run since 2026-10-04.

**Generator rules in positive form.** The prompt is now 22 rules and most of
them are NEVER. R026 is that negations reinforce what they forbid, and
Anthropic's own prompting guidance says to state what the model should DO. Both
are recorded in `self_upskilling.md` under "Practice, not tools" and neither has
been applied to the generator. P199 is evidence the prose rules are the weak
layer: rule 18 existed and was broken anyway, in the two languages furthest from
the prompt's own.

**`hr-ppd-spec.md` — designed, never built.** The per-platform posting spec was
worked out in conversation and never written to the repo. The file does not
exist. Either write it or drop this item deliberately.

---

## Platforms

**Check the Instagram comment Inbox.** Business Suite showed an empty comment
queue against a post with 251 comments. Comments made before the Page was
connected never backfill, so the open question is whether comments made SINCE
the connection appear. If they do not, the Page-link hypothesis is dead and the
Graph API is the only route to comment triage — which is what Agent #15 is for,
and it is blocked behind the Facebook appeal.

## Agent fleet

**15 agents scoped. Three have a loadable SKILL.md as of 2026-10-09** —
`reel-producing` (with a four-case eval corpus), `stt-validating` and
`tts-validating`. All three existed for weeks in `agents/`, which is not a path
anything loads from; moved to `.claude/skills/` (P206). `asset-auditing` is the
one built as scripts, and it works — it is what blocked the m2759 render until
the clips were classified.

**`reel-producing` evals RUN for the first time on 2026-10-09** (record:
`.claude/skills/reel-producing/evals/RUN-2026-10-09.md`). Passes v1 on paper —
3 of 4 cases with every required finding, zero `must_not_flag` hits — but the
pass is PROVISIONAL: case 001 was answered after its defects had been read in
the README's coverage table, so discounting it gives 2 of 3, below the bar.
Re-run 001 cold to settle it.

Still open for `reel-producing`:

  - Scripts: step 7 DONE (`scripts/pick-nasheed.py`, 2026-10-09). The step 4
    S:/M:/H:/C: block parser is the remaining one, reusable from
    `lint-content.py`.
  - Step 2b pass B has NEVER been exercised — it needs a different model, and
    the run was pass A only. The A/B split the skill specifies is untested.
  - Case 004 may be missing a required `attribution_boundary_open`: it has the
    same construction as 001, which requires it.
  - The adults lane still has no E2E checklist, which the skill names as a
    precondition for driving that lane.

**The roadmap has been found incomplete three times**, each time missing the
agent for whatever had just happened: it had no agent that PRODUCES a reel until
#13 was added on 2026-08-31, having been written with an orchestrator that would
have had nothing to dispatch; #14 came after a competitor question; #15 after a
viewer objection arrived in the Instagram comments. CLAUDE.md step 8 says to
assume a fourth gap exists. That is a standing instruction, not a resolved item.

**The unbuilt agent marked Tier 1** — highest daily return of anything unbuilt
— is the one that takes a hadith number, language, style and mascot, writes the
four blocks, checks them against the recurring-defect table, pulls the matn from
the correct DB column, writes draft.txt, runs lint-content.py, picks a least-used
nasheed, assembles the render command and then STOPS. Every one of those steps
was done by hand across four languages on 2026-10-05, and the two defects that
mattered most that day — a missing attribution and commentary inside a
quotation — were caught by reading, which is the step this agent explicitly does
not replace.

**Nothing here is scheduled.** The fleet is a roadmap with dates from the
original post-Hajj plan, all of them passed. Decide whether to build the Tier 1
agent or to mark the roadmap as aspirational and stop counting against it.

---

## Assets

**Kids-lane nasheed beds.** The eight Aswati tracks registered 2026-10-05 are
ADULTS ONLY. The kids rotation is unchanged and still thin. Separate search.

**Aswati per-track licence certificates.** Eight of them, from Aswati Studio
— Account — Your licenses, into `out/backgrounds/licenses/`. Section 1 of
their licence calls these the proof; only the terms snapshot is saved so far.
Note `out/` is gitignored, so that folder is not backed up by the repo — a
copy exists on D:\licenses.

**No reel has used an Aswati bed yet.** The next set will be the first. The
reply to Al-Mutawari committed to sending him that link when it ships.

---

## Ideas, scoped but not scheduled

**HV: verify a hadith from a video or reel link.** Proposed 2026-10-09. The
reverse of the text/screenshot verifier: a lot of reels recite the hadith aloud,
and checking one today means copying it out by hand.

Build it in two phases, and the first one is mostly not speech at all:

  - **Phase 1 — caption path.** Paste a link, pull the post's CAPTION, run the
    EXISTING text verifier. No transcription, no new verdict logic. Most reels
    carry the hadith or at least the citation in the caption, so this covers
    the majority of real cases with the component that already works.
  - **Phase 2 — ASR, only if phase 1 shows demand.** For genuinely
    caption-less recitation. ARABIC FIRST: the matn is fixed and the register
    constrained, so a near-match is actual evidence. Output must read
    “possible match — confirm” and never a verdict, and the transcript must be
    shown so the human sees what it heard.

**Why not ASR-first.** Transcription is lossy and the matching that follows is
built on its output, so errors compound into the one thing HV must never emit:
a confident wrong verdict on a sound narration. The evidence is in this repo —
Whisper needed hand correction on FOUR consecutive RU sets of our own clean,
single-voice, no-background TTS audio, and UZ and TJ are where it is weakest.
A stranger's phone video with a nasheed bed is a much harder input than
anything we have fed it. The fuzzy-match step afterwards is the same problem
that defeated check_twin_wording on clean text (P205), with worse signal.

**Build it with agent #15, not beside it.** Both answer “someone posted a
hadith, is it sound” — #15 from comments, this from posts. One shared path:
candidate text -> library match -> human confirms. Two separate ones means two
places for a verdict to be wrong.

---

## Tools

**Kling 3.0 evaluation.** OPEN on `self_upskilling.md`. Run at a set boundary,
same prompt through both models, as FLUX 2 was evaluated. Watchlist next due
2026-10-11.

---

## External / blocked

**Facebook Page** — avatar, bio, cross-post toggle still unset.

**Agent #15 (comment triage), step 1: the Meta app.** BLOCKED behind the
Facebook account appeal. The account was disabled after being created and
registered as a developer the same day.

---

## Recently closed

- 2026-10-09 — Tirmidhi #1899 reviewed and cleared. The Tajik was never
  wrong; the diacritic check is a heuristic and that sentence legitimately has
  none of ӣүҳқғҷ. The actual defect was EN and RU rendering الوالد as
  “parent” against FATHER in the Arabic, Uzbek and Tajik — now aligned.

- 2026-10-09 — P197 closed. `audit-assets.py --names` built, and all three
  misnamed sets renamed: b2628->m2628, b4248->ij4248, b4251->ij4251. 17 files,
  11 registry keys, 18 tracker lines; three prose lines left alone on purpose.

- 2026-10-09 — duplicate-number check added to audit-library.py; it found
  Tirmidhi #2616 and Bukhari #1469 doubled on first run, confirming what an
  earlier session had recorded and OPEN_ITEMS carried as unverified. Both are
  now rows in the tracker's duplicate-check index.

- 2026-10-09 — P200 fixed: `scripts/restore-srt-casing.py`, wired into
  render-reel.ps1 ahead of the validator.
- 2026-10-05 — R110—R113 shipped, Sahih Muslim #2759, four languages, four
  platforms each.
- 2026-10-05 — P199 generator rules 21—22 and the `quote-addition` lint check.
- 2026-10-05 — P201 per-reel nasheed sidecar.
- 2026-10-05 — eight Aswati beds registered; adults-eligible beds 9 -> 17.
- 2026-10-04 — P198 FLUX 2 adopted as the stills default.
