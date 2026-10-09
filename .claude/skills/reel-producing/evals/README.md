# reel-producing — evals

Ground truth for agent 13. Four real generations from the #6446 kids set
(R054–R057, 2026-08-31), with the defects that were found in them by hand.

## Why the split layout

Cases and expectations are in separate directories on purpose. Read a case
cold, write down what you find, then open the matching `expected/` file. The
corpus calibrates the human reviewer as well as the agent — which it cannot do
if the answers sit beside the input.

## Structure

```
cases/NNN-{lang}-{hadith}.md      the four raw blocks, as generated
expected/NNN-{lang}-{hadith}.json findings the agent must produce
```

Each expectation file has four sections:

- **`required`** — must be flagged. These decide pass/fail.
- **`optional`** — legitimate findings. Credited, never penalised. Several are
  real defects that were corrected at production but overlap with a required
  finding, or are low-severity.
- **`must_not_flag`** — text that is CORRECT. Flagging any of it is a false
  positive. This section is the reason the corpus is worth having: an agent
  that flags everything scores perfectly on `required` and is useless.
- **`out_of_scope`** — defects real enough to be in the tracker but outside
  what a text-stage agent can see. Present so a reader cross-referencing the
  tracker does not expect a finding.

## Pass criteria (v1)

- ≥ 3 of 4 cases with every `required` finding produced
- zero `must_not_flag` hits across all four cases

A false positive fails the run outright. The cost of a missed finding is that
the human catches it — which is the design. The cost of a false positive is
that the human learns to skim the report, which breaks the gate.

## Provenance, and a warning about it

`draft.txt` is gitignored and was overwritten once per language. The MP3s on
disk are the *corrected* text. The raw generations survive only in the session
transcript, so these fixtures were transcribed from it and verified line by line
against the original messages by the operator before commit.

That verification mattered and should not be skipped if fixtures are ever
reconstructed again. A fixture that misstates what the model produced makes the
eval measure the wrong thing, silently and forever.

**Standing rule from the next set on: capture the raw generation before
editing.** Paste each block into `cases/` as it comes out of `/admin`, before
touching the textareas. Then fixtures are artifacts, not transcriptions.

## What these four cases cover

| Case | Lang | Carries |
|---|---|---|
| 001 | EN | attribution boundary left open; a claim contradicting the moral; Allah absent |
| 002 | RU | isnad line in the story block; moral as self-talk; unexpanded honorifics |
| 003 | UZ | drift against a corrected DB column, with a correct S block in the same case; Latin-against-Cyrillic caption; singular verb |
| 004 | TJ | the same drift in two blocks; nafs narrowed to "his heart"; singular verb |

Case 003 is the most valuable single case. Its S block holds the matn correctly
while its H block drifts, in the same generation — so an agent cannot pass it by
pattern-matching on the word «қаноат». It has to read which claim is being made
where.

## Known gaps in the corpus

- **One hadith, one style, one mascot.** All four cases are #6446 kids boy.
  Nothing here exercises the adults lane, a different theme, or a girl mascot.
- **No clean case.** Every case contains defects. There is no fixture proving
  the agent stays silent on a generation that needs no correction, which is a
  real hole in the false-positive test.
- **No adversarial case.** Nothing tests a fabricated incident, an invented
  simile, or a divine-name substitution — all of which are in the defect table
  and none of which appeared in this set.

Fill these as sets ship, per the standing rule above.

## Running

No runner yet. v1 is read-and-compare by hand. When
`scripts/run-evals.py` exists it should assert `required` present,
`must_not_flag` absent, and report `optional` as informational only.
