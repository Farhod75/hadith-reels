# Reel retro

One entry per set, written after the last platform of the last language and
before the tracker rows. Step 17 of `reel-creation-pipeline.md`.

The point is not to record that something went wrong - `fix_patterns.md` does
that. The point is to record **what had to be said out loud for it to be
caught**, so a correction that keeps recurring becomes a gate instead of a
habit.

`audit-docs.py` fails when the newest `reel-tracker.md` row has no entry here.

## Template

```
## R<nnn>-R<nnn> - <Collection> #<num> - <YYYY-MM-DD>
**Shipped:** <langs> - <platforms>
**Caught before publish**
**Escaped to publish**
**Root causes**
**Prevention landed**
**Prevention deferred**
**Operator corrections of the assistant: <n>**
**The finding:**
```

---

## R138-R141 - Sunan Abu Dawud #1488 - 2026-10-22

**Shipped:** EN, RU, UZ, TJ - TG / IG / YT Shorts / TikTok

**Caught before publish**

- UZ H block claimed «дуо китобида», the Book of Du'a. Du'a is the *bab*; the
  *kitab* is al-Witr. The DB's `book` column is empty, so the admin generated
  the attribution from nothing. Verified against sunnah.com book 8 and
  hadithunlocked before changing it. The same defect was then found in the TJ
  H block.
- UZ H and the UZ caption disagreed on the narrator - «Салмон Форсий» against
  «Салмон ал-Форисий». Same class in TJ: «Сунани Абу Довуд» against «Сунани
  Абӯдовуд».
- `draft.txt` still held the EN blocks during the RU render. `stt-validate`
  scored correct Russian subtitles at 0.291 and reported «source is latin» on
  every cue. The subtitles were right; the comparison input was wrong (P282).
- TJ `Дастонатро` narrated as `Достонатро`. Caught by the operator listening,
  not by any check (P284).

**Escaped to publish**

- The RU reel shipped without `-FitScenes` and shows roughly 2.5 of its 4
  clips. Live on four platforms. Kept rather than replaced - presentation
  defect, not integrity. See the rule below.

**Root causes**

- `-FitScenes` is opt-in for behaviour that should be asserted. Omitted twice
  in one set.
- `draft.txt` has no sync gate. Recorded as P282 and still not built; it cost a
  scare in this set.
- The admin will generate a book or chapter attribution with nothing behind it,
  and no check compares that claim against the DB's `book` column.
- Stage 3 runs on candidates. A library row corrected by hand never re-enters
  it, so hand corrections ship unverified unless someone remembers `--library`.
  The operator asked; it had not been run.

**Prevention landed**

- P283 - the slug / clip-prefix naming map, written down for the first time.
- P284 - the `tj.adults` instruction, validated by re-narration.
- P285 - `incomplete` means re-run, never adjudicate.
- P288 - `-ValidateOnly` was a no-op that performed a full render. It
  overwrote the published TJ reel locally during close-out; restored from the
  original parameters. Fixed with an early exit. Rule: never smoke-test a
  render script against a published slug.
- This file, Step 17, and the `audit-docs.py` gate behind it.
- **Integrity against presentation.** A published reel is replaced for a wrong
  matn, translation, narrator, citation or divine attribute. Pacing, cover
  frame and subtitle styling are fixed forward. Engagement is not worth
  resetting for a presentation defect.
- **After `lg`, nothing reopens but an integrity defect.** Not wording
  preference, not a synonym, not a caption/audio phrasing difference.

**Prevention deferred**

- `-Scenes` without `-FitScenes` - warn or refuse in `render-reel.ps1`.
- H-block book claim against the DB `book` column - `lint-content.py`.
- `draft.txt` sync gate - P282, still open.

**Operator corrections of the assistant: 7**

1. Captions handed over before the render and the subtitle fix - out of order.
2. Offered to edit a repo file directly, against the VS Code rule.
3. Asked whether the folder/clip naming had been recorded. The assistant
   searched two files, found nothing and reported it was recorded nowhere. The
   CHANGELOG had in fact noted it - citing a «§5b» section that exists in no
   doc and a tracker record that does not exist. A partial search reported as a
   complete one, answering a question that deserved the whole repo.
4. Asked whether A/B verification still ran. It had not been run on the
   hand-corrected rows.
5. Asked whether the four blocks were needed for verification. They were -
   P078 skips the subtitle validator for uz/tj, not `lint-content.py`.
6. Rejected an invented M-block convention that overrode a clean
   `lint-content.py` pass, and a re-render proposed after `lg` had been given.
7. Corrected the admin URL - the dev server is on 3002, not 3000.

**The finding:** six of the seven are the assistant asserting or omitting
something the repo could have answered on its own. The gap is not knowledge.
It is that nothing forces the check to run before the claim is made.

---