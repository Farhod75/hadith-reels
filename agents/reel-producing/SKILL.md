---
name: reel-producing
description: Drives the text half of the Hadith Reels pipeline for one language — generation, defect review, matn retrieval, draft.txt, linting, nasheed selection, and a staged render command. Use this skill whenever (a) a reel set is being produced, (b) any task mentions draft.txt, lint-content.py, a hadith slug, or a language leg of a set, (c) reel-creation-pipeline.md is referenced, or (d) P101, P103, P108, P122, P125, P133 or P135 come up. Reads the four generated blocks (S/M/H/C) against the recurring-defect table, pulls the matn from the correct Supabase column, writes and lints draft.txt, picks a nasheed from the tracker's usage table with a stated reason, and assembles the render command. Stops there. Never generates narration, never answers a paid-generation gate, never publishes, never edits the tracker.
---

# Reel-producing agent

System under test: none. This agent is a producer, not a validator — the only
one in the fleet that makes something rather than checking something.

It removes the mechanical work that surrounds human review. It does not become
the review.

> **Written 2026-08-31**, after the #6446 kids set (R054–R057). The fleet had
> twelve agents and none of them produced a reel; every one validated or
> maintained, while the roadmap's finish line was an autonomous daily reel post.
> The orchestrator would have had nothing to dispatch. This agent closes that
> gap — and only the mechanical half of it, because the four defects that
> mattered on that set were all caught by a human reading or listening.

## The boundary, stated first

| Agent does | Human does |
|---|---|
| Generate the four blocks | **Review them** |
| Flag recurring defects | Decide what the flag means |
| Pull the matn from the DB | — |
| Write and lint `draft.txt` | — |
| Pick a nasheed, with reasoning | Accept or override |
| Assemble the render command | **Run it** |
| — | **Answer the Fabric/Kling gate** |
| — | Listen to narration |
| — | Watch the reel |
| — | Publish |
| — | Update the tracker |

Hard rules from `agent-fleet-roadmap.md` apply without exception: any public
reel content requires human review before posting, and no agent posts to a
channel. This agent's output is a staged command and a report, never a reel.

## Pre-task reads (mandatory)

1. **`reel-creation-pipeline.md` — the per-language E2E checklist.** That
   document IS this agent's specification. Step order, gates, per-language
   rules and the recurring-defect table all live there.
2. `reel-tracker.md` — Nasheed usage and Mascot stills tables, for step 7 and
   for the mascot rotation.
3. `fix_patterns.md` — for any P-number cited in a finding.

**Do NOT copy the defect table into this file.** Two copies drift; that is how
P118 happened, where a voice comment and its id disagreed for two months. The
table has one home.

## Inputs

- `hadith_number` — e.g. `6446`. Note `hadith_number` is TEXT in Supabase and
  must be quoted in SQL; an unquoted integer raises
  `operator does not exist: text = integer`.
- `lang` — `en | ru | uz | tj`
- `style` — `adults | kids`
- `mascot` — `boy | girl`, kids only. Rotates per hadith, not per language;
  read the last set from the tracker's Mascot stills table.

## Pipeline

### Step 1 — Generation

The four blocks come from `/admin`. Language switching deselects the hadith
(P108), so the hadith must be re-selected after any language change or the
caption ships with the previous language's text.

### Step 2 — Defect review

Check every block against the recurring-defect table in
`reel-creation-pipeline.md`. Report each hit as `{block, line, defect, note}`.

Three shapes recur across languages and deserve naming here because they are
what the linter does not catch:

**Attribution boundary.** A paraphrase placed after "The Prophet ﷺ said:" with
nothing marking where his words end. Every following sentence reads as his. Not
fabrication — attribution leaking. P101 family. The fix is to make the
attribution indirect so there is no quote to leak out of.

**Meaning drift a corrected DB row does not prevent.** On #6446, Stage 3 caught
`text_uzbek` and `text_tajik` rendering غِنَى النَّفْسِ as contentment, and both
columns were corrected before the adults set. The generator still produced
«нафснинг қаноати» and «дили ту қаноатманд бошад» afterwards, in both languages.
It re-derives the shift from the concept, not from the stored text. A corrected
library row is necessary and not sufficient.

**Allah absent from the moral.** All four first drafts on R054–R057 produced a
moral with gratitude and no object — "tell yourself", "thank your family",
"notice how that feels". The action must be directed to Allah.

### Step 2b — Independent matn comparison (A/B)

Step 2 reads the blocks against a table of known defects. It catches what has
gone wrong before. It cannot catch what has not.

So the blocks get a second, independent pass, and the passes must not share a
starting point:

- **Pass A (step 2)** — blocks against the recurring-defect table.
- **Pass B** — without reference to A's findings, reconstruct what each block
  *claims*, clause by clause, and compare it against the matn retrieved in
  step 3. Every clause in S and H must be traceable to the matn or marked as
  explanation. Anything asserted that the matn does not support is a finding,
  whether or not it appears in the defect table.

Run step 3 first when using B; the matn is B's only reference.

**Why two passes and not one better pass.** Two reviews by the same model share
the same blind spots — a term neither pass understands is missed twice, with
two confident clean reports as the output. B is not a second opinion; it is a
different *method*, anchored to an external source rather than to prior
experience. That is what makes the failure modes uncorrelated.

The evidence is on the record. Stage 3 A/B caught `text_uzbek` and `text_tajik`
rendering غِنَى النَّفْسِ as contentment before the #6446 adults set, and caught
missing clauses in EN and RU on earlier sets. It works because it compares
against the matn, not against a checklist.

**Report both.** Findings from either pass go to the human. A finding raised by
only one pass is marked `single-pass` — not downgraded, flagged as a
disagreement worth a closer read.

**What this does not fix.** A shorter, cleaner report is easier to skim. A/B
removes correlated blind spots; it does not remove the pull toward approving a
tidy diff instead of reading the text. The human gate stays a human gate.

### Step 3 — Matn retrieval

```sql
select text_<lang> from hadith_library where hadith_number = '<n>';
```

UZ uses `text_uzbek_cyrillic`. If it returns empty, fall back to `text_uzbek` —
the two-script backfill left it empty on the older 74 rows.

**Pull from the DB, not from the caption.** Using the generated caption as the
matn compares generated text against generated text; a wrong library row stays
invisible. #6446 is the case in point — two of its four columns were wrong until
Stage 3 caught them.

### Step 4 — draft.txt

Repo root, gitignored. Format:

```
S: <story>

M: <moral>

H: <hadith context>

C: <caption, including title, quote, moral, reference, verify line, hashtags>
```

**Written BEFORE narration, not after.** This is the step most often skipped,
and skipping it means the text that ships was never linted in its final form.

**VS Code only.** `Set-Content`, `Add-Content`, `Out-File` and
`WriteAllText` to repo files are silently reverted on the operator's machine —
suspected controlled-folder-access or a sync tool, root cause not yet found.

### Step 5 — Lint

```
python scripts/lint-content.py draft.txt --lang <lang> --matn "<matn>"
```

Report the output verbatim. A clean run means seven checks passed; the tool says
so itself. It is not a verdict on the text, and it caught none of the four
defects on R054–R057.

### Step 6 — Caption script check

The caption quote must be in the same script as the caption body. Latin against
Cyrillic has shipped eight times. For UZ, take the quote from
`text_uzbek_cyrillic` verbatim — never transliterate by hand.

### Step 7 — Nasheed selection

From the tracker's Nasheed usage table, pick the least-used file that is not
already used in this language recently and not used elsewhere in this set.
**State the reason.** Name it explicitly on the command line; never let the
script pick. The random picker has drawn an ocean-ambience track (R044) and an
adults-lane bed onto a kids reel (R029, R030).

### Step 8 — Render command

Kids:
```
.\make-kids-reel.ps1 -Lang <lang> -Slug <slug> -Mascot <boy|girl> -Nasheed <file>
```

Adults:
```
.\render-reel.ps1 -Style adults -Lang <lang> -Slug <slug> -Nasheed <file>
```

Assemble it. Do not run it.

### Step 9 — Stop

Output the report. The human reviews content, generates narration, listens,
answers the Fabric gate, watches the reel, publishes.

## Outputs

```json
{
  "agent": "reel-producing",
  "version": "v1",
  "timestamp": "ISO 8601",
  "case": { "hadith_number": "6446", "lang": "uz",
            "style": "kids", "mascot": "boy", "slug": "bukhari-6446" },
  "blocks": { "story": "...", "moral": "...", "context": "...", "caption": "..." },
  "findings": [
      "pass_b": {
    "unsupported_clauses": [
      { "block": "H", "clause": "...", "note": "not traceable to the matn" }
    ],
    "agreement": "both | pass_a_only | pass_b_only"
  },
    { "severity": "high | medium | info", "block": "S | M | H | C",
      "defect": "...", "pattern": "P101", "note": "..." }
  ],
  "matn": { "column": "text_uzbek_cyrillic", "value": "...", "source": "supabase" },
  "draft_written": true,
  "lint": { "fail": 0, "warn": 0, "info": 0, "output": "..." },
  "nasheed": { "file": "vocal-nasheed-02.mp3", "uses": 3,
               "last_used": "R046", "reason": "..." },
  "render_command": "...",
  "awaiting": "human content review"
}
```

## Self-validation (evals)

Ground truth from R054–R057, 2026-08-31 — four real generations with defects
found by hand and recorded in the tracker.

| Case | Must flag |
|---|---|
| 1. EN kids #6446 | attribution boundary left open after "The Prophet ﷺ said:"; "richness is already inside you" contradicting the moral; Allah absent from the moral |
| 2. RU kids #6446 | isnad line («Это передал…») placed in the story block; moral rendered as self-talk with no Allah |
| 3. UZ kids #6446 | H drifting to «нафснинг қаноати» against a corrected DB column; «деди» singular for the Prophet ﷺ; caption quote Latin against a Cyrillic body |
| 4. TJ kids #6446 | «гуфт» singular; қаноат drift in both S and H; «дилаш» where the matn says nafs |

**Pass criteria v1:** flags ≥3 of 4 cases, with no false positive on a block
that shipped unchanged.

**A known limitation, stated plainly.** On case 3 the UZ narration voiced «оз»
(few) as «ўз» (one's own), inverting the sentence. That is a TTS artefact,
audible only after generation, invisible in text. No text-stage agent catches
it. Same shape as the P112 hum that `tts-validating` cannot hear. Listening
remains a human step.

## Failure escalation

| Finding | Action |
|---|---|
| Attribution boundary open | Block. Religious defect (P101 family). |
| Fabricated detail, invented simile | Block. Never publish. |
| Divine name substituted («God», «Худо») | Block. |
| Meaning drift from the matn | Surface for review with both texts side by side. |
| Allah absent from the moral | Surface. Near-certain on a first draft. |
| Caption script mismatch | Surface. Fix from the DB column, not by hand. |
| Singular verb for the Prophet ﷺ | Surface. |
| Lint FAIL | Block until resolved. |
| Matn query returns empty | Stop. Do not proceed on a caption-derived matn. |

## What this agent does NOT do

- Does not click Generate narration. Per-block re-narrate exists (P125); the
  agent does not invoke it.
- Does not answer the Fabric or Kling confirmation. That is the paid,
  irreversible step and it is human by rule.
- Does not publish to Telegram, Instagram, YouTube or TikTok.
- Does not edit `reel-tracker.md`. Tracker updates happen after the full set.
- Does not choose the hadith. Sourcing is Stage 0.
- Does not judge audio. That is `tts-validating`.
- Does not check subtitles. That is `scripts/stt-validate.py`.
- Does not replace review. Every defect that mattered on #6446 was caught by a
  human reading the text or listening to the audio, with the linter clean in
  all four languages.

## Dependencies

- Supabase read access to `hadith_library`
- `scripts/lint-content.py`
- `reel-creation-pipeline.md` and `reel-tracker.md` present and current
- Claude API for generation

## Scripts

Not yet implemented. When built, reuse:
- the S:/M:/H:/C: block parser from `scripts/lint-content.py`
- the tracker table parser needed for step 7 — note the tracker's Notes column
  contains prose and naive `awk -F'|'` field splitting misreads rows; a
  reconstruction built on that error nearly overwrote R052's history on
  2026-08-31

## Governance

- Read-only against Supabase. Writes exactly one file, `draft.txt`, gitignored.
- Assembles but does not execute commands. No spend without a human keystroke.
- Not suitable for push CI — it calls the Claude API and is non-deterministic.
- Human approval before publish is unaffected.

## Versioning

- **v1 (current, 2026-08-31):** text pipeline only, steps 1–8, chat-driven.
  No scripts.
- **v2 (planned):** `generate-reel-draft.py` implementing steps 1–8
  programmatically, with the defect table read from
  `reel-creation-pipeline.md` rather than reimplemented.

## Open questions

- Should the agent propose corrected text for each finding, or only flag?
  Corrected blocks were provided and accepted on every finding on #6446, which
  shortens the human's task from "judge this text" to "approve this diff."
  Step 2b addresses the blind-spot half of that risk; the anchoring half
  remains open. One option not yet tried: flag first, withhold corrections
  until the human has read the blocks.
- The қаноат drift survived a corrected DB column in two languages. Is a
  per-hadith "known drift" note in `hadith_library` worth the schema change, or
  does the defect table cover it?
- Adults lane needs its own E2E checklist before this agent can drive it;
  `render-reel.ps1` has scene generation, Whisper subtitles and an
  `stt-validate` gate with no kids equivalent.