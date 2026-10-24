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
## R090-R093 (correction) - Sahih Muslim #1005 - 2026-10-22

Not a production set. A post-publication correction, logged because the retro
is where recurrence gets counted.

**Caught before publish** - nothing; this was already live since 2026-09-24.

**Escaped to publish**

- Four kids reels carried **Jabir ibn Abdullah** where Muslim #1005 is
  **Hudhayfah ibn al-Yaman**. Jabir's wording of the same meaning is Bukhari
  6021. The matn, the number and the collection were all correct. Only the
  companion came from the other collection.

**Root causes**

- **Nothing compares the stored narrator against the cited source.** Stage 3
  checks translation against matn. `audit-library` checks fields one at a time.
  `verify-matn-source` asks whether the text appears in the collection, and it
  does. No check asks whether the narrator belongs to the hadith the citation
  points at, so a row where every field is individually correct passes
  everything.
- **The narrator check we do have asks a different question.** It compares
  against the mirror's `narrator`, which is a LEAD-IN STRING naming whoever the
  chain reaches last - so it flagged #31 and #2616, which were right, and its
  real catches needed a human to separate from its false ones.
- **A backlog line with a count in it hid four different problems.** "Five
  narrator mismatches" sat for weeks reading like one task.

**Prevention landed**

- P292 and its addendum: the three real corrections, the two non-defects
  explained, and `NARRATORS` entries so the corrected names localise instead of
  falling back to Latin inside Cyrillic captions.
- P290's `patch_library_row` was used for all three writes.

**Prevention deferred**

- A check that compares `narrator` against the cited source rather than the
  mirror's lead-in. This is the gap that let it through and it is still open.
- Caption rebuild returns the wrong lane's voice (see below). Not built.

**Operator corrections of the assistant: 2**

1. **The caption rebuild came back in the adults voice.** The instruction was
   to paste the rebuilt caption; the operator compared it to the live post and
   stopped. Live kids caption: *"Show your children that kindness itself is
   charity."* Rebuild: *"Do not wait for wealth to give charity..."* - adults
   register, and `#kids` and `#maruf` dropped from the tag line. The admin
   builds from the library row and the row does not carry the lane, so a
   rebuild for a published reel can silently change voice. Pasting it would
   have broken P222's kids-caption rule on four live posts to fix one name.
   Method changed mid-task to a single-name find/replace.
2. **"What do I need to do?"** - twice in one evening, because the assistant
   reported findings instead of giving directions.

**The finding:** the fix was one name. The assistant's first method would have
rewritten four live captions to change it, and the check that found the problem
flagged two correct rows alongside it. Both are the same error - acting on what
a tool reports without asking what the tool actually compares.

---
## R142-R145 - Jami at-Tirmidhi #2307 - 2026-10-23

**Shipped:** EN, RU, UZ, TJ - TG / IG / YT Shorts / TikTok

**Caught before publish**

- **S carried commentary in all four languages.** EN and UZ were caught by
  `lint-content`'s quote-addition check; RU was not; TJ put the word INSIDE the
  quotation, which no check caught at all (P294).
- **UZ's S gloss WAS the M block, word for word.** The narration would have
  said the same sentence twice. `check_duplicate_blocks` did not fire because
  only S's tail matched.
- **The scholars-say construction in all four languages** - "Its established
  meaning is", «Его установленный смысл», «Маънои муқарраршудаи он чунин аст».
  Fourth consecutive Tajik set. This is a fixed behaviour, not a recurrence.
- **RU's story was narrated from the pre-correction text** (R134 again). Caught
  by arithmetic: 18s against EN's 6s for the same one sentence.
- **Two RU subtitle fixes the lint passed clean**: «сказал.» introducing a
  quotation, and a dropped «к» in «обращённое к каждому».
- **EN subtitle cue 5** lowercased the divine pronoun - P282's unbuilt check.
- **The book-claim check, one day old, fired on "Book of Zuhd"** and the claim
  turned out to be TRUE. Confirmed against the mirror's chapter table rather
  than assumed, and reworded to the source's own "Chapters on Zuhd".

**Escaped to publish** - nothing known.

**Root causes**

- `lint-content` checks a block against the matn; it does not check a block
  against ANOTHER block, which is why UZ's duplicate passed.
- The draft-sync gate's 0.90 ratio tolerates an inserted word (P294).
- The admin's textarea and the generated audio can disagree, and nothing
  compares them. The new `.txt` sidecars make the check possible; nothing runs it.

**Prevention landed**

- P294 and P295 recorded; P284's lever demoted from "the fix" to "try once".
- `.txt` sidecars beside each mp3 turned RU's diagnosis from a transcription
  into a ten-second file read - P246 effectively closing.

**Prevention deferred**

- Tighten `check-draft-sync.py` to require the matn as a contiguous substring.
- Compare `story.txt` / `moral.txt` against `draft.txt` before the render. Both
  files now exist; nothing reads them together.
- Divine-pronoun casing check (P282), still not built, bit again on EN cue 5.

**Operator corrections of the assistant: 4**

1. **Slug guessed.** Used `tirmidhi-2307`; the admin derives `at-tirmidhi-2307`,
   and R118 in this very tracker is `at-tirmidhi-3895`. P283's exact subject,
   two days after writing P283.
2. **"What does S (replace - the gloss moves to H) mean? Give me clear paste
   text."** Labels explaining the edit instead of the edit.
3. **Asked to re-watch a reel after already saying `lg`** - "sg lg means I
   watched".
4. **Rewrote the assistant's Uzbek and Tajik M blocks** before they were used.

**The finding:** every one of the four legs needed the same two edits, and the
assistant proposed them one language at a time as if each were a discovery. The
pattern was visible after EN. Nothing in the pipeline says: when a block defect
appears in the first language of a set, expect it in the other three and say so
up front.

---

## R146-R149 - Jami at-Tirmidhi #3540 - 2026-10-24

**Shipped:** EN, RU, UZ, TJ - TG / IG / YT Shorts / TikTok

**Caught before publish**

- UZ rendered the measure clause as «шунга яқин», close to that, which makes
  the forgiveness fall SHORT of the sins and inverts the hadith. RU's «почти
  равным ей» carried the same ambiguity. The near-ness belongs to the sins:
  قُرَاب is nearly the earth's fill of them, and the forgiveness matches it.
  Both caught by the operator reading the blocks back, not by any gate.
- TJ's H block tied forgiveness to the measure of the servant's dua rather than
  to the measure of the SINS - the same inversion, one block over - and
  asserted «Маънои муқарраршудаи он», its established meaning, with no scholar
  cited. Fifth consecutive Tajik set to generate that construction.
- TTS read TJ «сипас» (then) as «сипос» (gratitude), inside quoted divine
  speech. Caught by ear.
- draft.txt was stale on both the EN and the RU legs, and the P297 gate's own
  advice was backwards on EN: it said re-narrate when the audio was correct.
- Whisper needed six hand-corrections on RU against English's two, including a
  P298 divine-pronoun cue. Cue 1 was left lowercase deliberately - the pronoun
  there is the Prophet's.
- The sixth scene clip was measured rather than estimated: the render was run
  to get 11.93s against 10.042s available before any money was spent.

**Escaped to publish**

- The EN reel was BLOCKED GLOBALLY on YouTube for its bed. Nothing in the
  pipeline reads a bed's rights, so it could not have been caught.
- The wrong diagnosis of that block - `vocal-nasheed-02.mp3` rather than
  `aswati-Steady-Motivation.mp3` - reached a pushed pattern and a registry note
  before anyone read the leg's `render.json`.

**Root causes**

- `verified: true` on an audio entry means a human listened to it. It has never
  meant licensed, and the schema has no licence field. The Aswati certificate
  licensed a remix platform's terms of service, not the recordings its users
  uploaded: ffprobe reads the eight beds as a SoundCloud rip, the instrumental
  of an existing named nasheed, and five phone voice memos from one evening.
- A conclusion drawn from the bed I expected the leg to carry rather than from
  the sidecar that records what it did carry.
- `TTS_INSTRUCTIONS` has been dead code since P102, so a mispronunciation can
  only be fixed in the text - and a word inside the matn quote drags the
  library row and the published caption with it.
- Scene clips were validated after the narration had been built.

**Prevention landed**

- P300 (a transfer that reported success and left the previous version),
  P301 (the licence covered the platform, not the recording), P302 (a comma
  list through Start-Process binds as one string), P303 (no invisible fix for a
  mispronunciation).
- Scene clips now validated in Step 0, with the comma case named as P302
  instead of reported as a missing file.
- ID3 evidence recorded on all eight aswati registry entries; the TJ voice
  watch-list extended with the v4 сипас->сипос defect.
- A Content ID smoke test was run and came back clean on the ElevenLabs trial
  bed: a bed alone on a black frame, uploaded unlisted, Claims read ten minutes
  later.

**Prevention deferred**

- A licence field on the audio schema, and a gate that refuses a bed without
  one. A field records a claim; it does not test one, so the smoke test above
  belongs beside it, not instead of it.
- The `lanes` decision on the eight aswati beds. Emptying them leaves the
  picker with nothing and halts production, and nothing in the library is
  provably clean to fall back to.

**Operator corrections of the assistant: 6**

1. **«шунга яқин» and «почти равным ей»** - the inverted measure, in two
   languages, neither flagged by a gate.
2. **«рўбарў» narrates as «рўбаро»** - caught by ear, in the UZ moral.
3. **«сипас» narrates as «сипос»** - caught by ear, in the TJ matn quote.
4. **"Where is tag?"** - the YouTube pack was handed over without the Tags
   field, three languages running.
5. **«мебахшояд» against «мебахшам»** was flagged as an inconsistency and is
   not one: S is direct speech in the first person and M speaks about Him. The
   assistant raised a grammar question in a language it does not have.
6. **Publishing order** - each language fully published before the next is
   begun, restated when the assistant moved ahead.

**The finding:** every fact in this set that was read from disk was right, and
the one taken from memory was wrong - and that one reached a pattern, a
registry note and a push. `render.json` records the bed for every leg and was
sitting there the whole time. Nothing in the pipeline says that a claim about
which asset a PUBLISHED reel carries must be read from that leg's sidecar
before it is written down. The tracker rows for this set were therefore built
column by column from `render.json`, ffprobe and the library row, which is how
the three wrong beds in the assistant's own notes were found at all.

---
