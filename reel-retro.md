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

## R150-R153 - Sahih al-Bukhari #6570 - 2026-10-27

**Shipped:** EN, RU, UZ, TJ - TG / IG / YT Shorts / TikTok

The second reel of the Tawheed arc, produced 2026-10-14 and held thirteen days
for the operator's 2-3 week spacing from #6423. Nothing was generated, rendered
or paid for on publish day except one re-render; the whole set cost zero in
paid API.

**Caught before publish**

- **RU was sitting on the bed YouTube Content ID claimed.**
  `aswati-Steady-Motivation.mp3` is the bed that blocked #3540 EN globally, and
  the RU leg had been rendered on it on 2026-10-14, before that was known.
  `audit-assets.py --check` blocked it - the first real case the rights field
  and its single gate have caught since they were built two days earlier. Had
  the gate not existed, the second blocked video of the month would have gone
  up. Re-rendered on `aswati-Victory-March.mp3`.
- **The bed's DURATION mattered and was measured.** `pick-nasheed.py`'s third
  choice, `aswati-Morning-Serenity`, is 46.3s against a 47.0s reel and would
  have looped by one second. The recommendation ranks by usage, not by length.
- **A suspicion about the Uzbek kalima was wrong, and checking is what settled
  it.** `text_uzbek_cyrillic` reads «Ла илаҳа иллаллоҳ» and OPEN_ITEMS quotes
  «Ла илоҳа иллаллоҳ» from another source, so the row looked defective. The
  project's own corrected ZAD Aqeedah material uses «илаҳа» throughout - it
  transliterates the Arabic *ilāha*, while «илоҳ» is the separate Uzbek noun
  the same book uses in «Аллоҳдан ўзга ҳақ илоҳ йўқ». Nothing to change. This
  would have become a correction task handed to the operator on an unchecked
  premise, which is the specific failure of 2026-10-26.
- **`text_display` is not a column.** The first run of the new caption script
  selected it and Supabase refused the query. `/api/reels` computes it per
  language (P108); a script has to read `text_russian` /
  `text_uzbek_cyrillic` / `text_tajik` directly.
- **The Whisper helper failed twice while reporting a clean finish** (P304):
  once on a space-containing path flattened through
  `Start-Process -ArgumentList`, which is P302 in a different disguise and
  written by the author of P302; once because ffmpeg is not on the system PATH
  and the render script adds it itself, so a detached helper never sees it.
  Both runs printed `=== DONE` over an empty output directory.

**Escaped to publish**

- Nothing in the content. The risk carried into publication is recorded below
  rather than hidden: two of the eight narrated blocks were read back by the
  assistant rather than by the operator.

**Carried risk, stated**

- **The UZ and TJ morals were recovered from audio by Whisper and
  reconstructed by the assistant**, then confirmed by the operator on the
  strength of listening to the reels. Transcript coverage was checked against
  the audio duration first - 13.92s of 13.95s for UZ, 10.84s of 10.92s for TJ -
  so nothing was truncated, and the two shakiest tokens were named explicitly
  when the reconstruction was put up for confirmation rather than buried in a
  paragraph. Still: this is the one text in the set that passed through the
  assistant's reading before the operator's.
- **All four titles were written fresh.** `draft.txt`'s C block is the TITLE,
  only S and M reach TTS, and the file had been overwritten, so no recording of
  the original exists anywhere. Nothing had been published, so there was no
  artefact to stay consistent with. Written under the generator's own rule from
  `route.ts`: at most 8 words, drawn from the matn, naming no benefit.

**Root causes**

- **`draft.txt` is one mutable file for a pipeline that holds reels for weeks.**
  #6570 was rendered on the 14th and published on the 27th; the next set's
  generation overwrote the only copy of its text on the 15th (P246). Reels
  rendered from 2026-10-15 onward archive their own text beside each mp3, so
  this is closed for everything after #6570 - but the hold, not the overwrite,
  is what made it bite, and the arc has one more reel to come.
- **The caption body could only be built by the admin** (P305). Seventy lines
  of template string inside a React component meant that losing the component's
  inputs meant losing the caption, and that the only fallbacks were
  re-generating the blocks - P245 re-attributed the moral in 7 of 8 generations,
  on rule 25's own test case - or hand-applying the quote rules on the very reel
  P236 names as the case that would have been the third and fourth
  hand-correction of nested guillemets. Extracted to `lib/caption.ts`.
- **A reserved row number goes stale the moment another set posts.** This
  section's own note reserved R134-R137, corrected itself to R138-R141, and both
  were wrong by publish day. Read the frontier; reserve nothing.
- **The pipeline doc still says to add the Aswati courtesy credit** for any
  `aswati-*` bed. P301 showed those beds are user-upload remixes and the
  licence requires no attribution, so the credit asserts a provenance known to
  be false. It was omitted on all four legs here and on #3540 before that, which
  means the doc has now been overridden twice by judgement instead of once by an
  edit. Recorded in OPEN_ITEMS.

**What the set did not need**

The subtitle validator was skipped on the RU re-render, deliberately and with
the render's own `[skip]` notice: it compares the SRT against `draft.txt`'s S
and M blocks, which are precisely what was lost. Reconstructing them from the
SRT to feed them back would have compared the SRT against itself. P211 matched
the narration fingerprint and kept the reviewed SRT, so the picture, narration
and burned subtitles are byte-identical to the leg reviewed on 2026-10-14 and
only the music moved.

---

## R154-R157 - Sahih al-Bukhari #3559 - 2026-10-28

**Shipped:** EN, RU, UZ, TJ - TG / IG / YT Shorts / TikTok. EN and RU replaced
posts deleted the same day.

**Caught before publish**

- **The matn was under the wrong number.** The row cited Bukhari #3559 and
  stored «إِنَّ مِنْ أَحَبِّكُمْ إِلَيَّ», which is authentic Bukhari from the same
  narrator at 3759, 3760; reference 3559 carries «إِنَّ مِنْ خِيَارِكُمْ». Caught
  because the operator said «Старайся сравнивать с оригиналом арабским» - an
  instruction, not a gate. Settled by opening both sunnah.com pages and the
  local mirror.
- The 2026-10-27 screening note in the tracker, which described a source page
  that does not exist and asserted a comparison nobody had made.
- The `love` tag, residue of the superseded wording, still in the row and in all
  four captions after the matn was fixed.
- TJ moral opened «чун қарзе» - "like a debt" - a comparison absent from the
  matn. The only linter finding across four languages (P111 r14).
- EN subtitle cue 6 read `place` for `placed`. The subtitle validator caught
  this one.
- RU subtitle cues 1 and 5 read «доблагословит». Caught by reading; the
  validator scored similarity 1.000 and reported nothing.
- All four renders failed the P194/P286 scene-budget gate on the first attempt
  because `-FitScenes` was omitted - and the previous render's own
  `render.json` recorded `fitScenes: true`.

**Escaped to publish**

- EN and RU had shipped earlier the same day on the wrong matn, four platforms
  each. Eight posts deleted and replaced; their view counts are gone. The words
  were in the narration and the burned subtitles, so no caption edit could have
  reached them - this is the first set where a published reel had to be
  withdrawn for an integrity defect rather than kept as a presentation one.

**Root causes**

- No gate compares a row's Arabic to its own `source_url`. `matn_screened_at`
  was set on 2026-09-05 and meant only that a row had been looked at.
- **The local mirror's `id` was used as the hadith reference number.** It is
  not: in this region the mirror runs 162 behind sunnah.com, so entry 3597
  is 3759, 3760. The lookup returned genuine, correctly-narrated text under the
  wrong citation, which is why no content check could fire - the matn was real,
  the narrator matched, the grade was right and the chapter was adjacent.
- The screening note recorded the key it had resolved, "idInBook 3597", and
  then wrote its findings as facts about `bukhari:3559`. Right about every word
  it quoted, wrong about which hadith they belong to.
- The approved UZ blocks existed only in the conversation and were lost when the
  context compacted, because the draft file is written at render time rather
  than at approval time.
- `stt-validate` has nothing to compare the expanded honorific against: the
  draft holds `ﷺ`, the route expands it, Whisper transcribes the expansion.
- `-FitScenes` is still opt-in for behaviour that should be asserted. Second
  set in a row, and this time the answer was already on disk.

**Prevention landed**

- P306-P310 and a P306 addendum.
- Draft files for all four languages, written at approval time rather than
  before the render, each verified against the matn stored in the database.
- Telegram publishing automated: `sendVideo` on the route, one command in
  `scripts/post-telegram.py`.
- The tracker's #3559 note replaced with what the page actually says, and the
  missing `b6570` scene row added while there.

**Prevention deferred**

- The matn-vs-source gate. In OPEN_ITEMS under "Blocks content".
- Honorific expansion in `stt-validate`. In OPEN_ITEMS under "Blocks content".
- `-FitScenes` asserted rather than opt-in. Open since R138-R141.
- Generating the caption-blocks spec from the draft files is NOT landed. A
  one-off script in `out/` did it for this set; making it the standing path in
  `build-caption.ts` is open. Said plainly because writing it down as landed is
  the exact move P306's addendum is about.
- `TELEGRAM_ALERT_BOT_TOKEN` and `TELEGRAM_CHANNEL_CHAT_ID`, blocked on an
  interactive `vercel login`.

**Operator corrections of the assistant: 4**

1. «Старайся сравнивать с оригиналом арабским» - which is what surfaced the
   wrong matn. Without it this set would have shipped four languages on it.
2. RU matn word order: «лучше среди вас по нраву».
3. «И так подробно что я смотрю и где?» - a status report that buried the one
   thing he needed under everything that had happened.
4. The UZ singular against a plural predicate, «энг суюклиси», caught on the
   superseded attempt earlier the same day.

**The finding:** nothing here was fabricated and nothing was sloppy. A genuine
Bukhari matn, from the right companion, carefully read and accurately
summarised, sat under the wrong number because one identifier was resolved in
the wrong scheme. Every downstream check passed because every downstream check
was looking at real text. That is the dangerous shape: not a wrong answer, but a
right answer to the wrong question, wearing all the marks of diligence.

Said against the assistant as much as the pipeline. The first diagnosis of this
set - that the wording came from Jabir and Abu Tha'laba in Ahmad and
at-Tirmidhi, truncated, with the wrong companion attached - was wrong, and was
stated confidently enough to move the operator toward deleting eight posts on a
severity the facts did not support. A citation-only fix to 3759 was available
the whole time, because the narrator was already right. Three sources had been
checked and the one record that would have settled it, the mirror entry the
screening note itself named, was not opened until afterwards. Checking three
sources is not the same as checking the right one.

## R158-R161 - Sahih al-Bukhari #5185 - 2026-10-29

Four legs, four platforms each, no reruns. The set that followed #3559 and was
produced in the same session that found CI had been red for a week.

**What the set was for.** "Treat women well, for they were created from a rib"
is a hadith whose point is routinely inverted in the retelling: the rib becomes
a claim about what women ARE, when in the text it is the REASON given for a
command that opens and closes the passage. Every language block was built to
keep that shape - command, reason, command - and the seerah block says so
explicitly, because a reader who meets this hadith as a description rather than
an instruction has been given the opposite of it.

**Imagery: the rule held against my own first instinct.** Asked for scenes, the
obvious move is figures. animated-reel-scene-prompts.md line 70 says the default
is NO FIGURES AT ALL, and depicting women was declined on that basis. What
replaced it came out better than the obvious version: an almond branch under
early-spring snow that straightens slightly as the sun takes the snow off it -
the operator's idea - which is the matn's own argument in one image. Nothing in
the four scenes depicts a person.

**What actually went wrong, in order of cost.**

1. **The RU subtitle pass, five findings.** One inverted the meaning: the draft
   said straightened force breaks, rather than what is straightened BY force.
   Two participles drifted feminine, turning a sentence about the rib into a
   sentence about a woman. And the closing guillemet sat after our moral, which
   silently attributed our words to the Prophet. That last one is now P316.
   None of this was caught by a gate; it was caught by reading.
2. **The EN moral echoed the story's last line**, so a burned subtitle cue read
   "So treat women well. Treat women well." P315. The S and M blocks are linted
   separately and the seam between them is read by nothing.
3. **I spelled out the UZ honorific** after being told, in this project, twice
   before, that the glyph is right for all four languages - it is at R041 and
   R044. Then I corrected myself a second time, because my first correction
   claimed the glyph would shorten the narration. It does not: cleanForTTS
   expands it before the request, so 48.17s against 47.13s.
4. **The Telegram publish timed out mid-upload** on 7.0 MB and left the outcome
   unknown. The wrong move was available and tempting - run it again - and would
   have put a second copy of the reel in the channel. P318 records the read-only
   way to settle it: a no-op markup edit tells you whether a message id exists
   without sending anything. Exactly one existed, 171.
5. **The post script could not print Tajik** on a cp1252 console and died before
   sending. P317, fixed in the closing commit rather than left to an environment
   variable, because a script whose job is to print a non-Latin caption does not
   get to depend on the console it is run from.

**The honest note on sequencing.** This set sat half-finished for hours while CI
was diagnosed, and the TJ leg was approved only at the end of the evening. That
was the right order - a red CI is a defect report and HV had been quietly red
for a week behind it - but it is worth writing down that the content work
stopped, rather than pretending the two ran in parallel.

**Against the previous set.** #3559 was four legs that had to be DELETED and
replaced after publication, on a citation defect nobody could see. #5185 is four
legs that went out once. The difference is not luck: verify-matn-number.py, built
during #3559, ran over this row before a word was generated.

## R162-R165 - Jami at-Tirmidhi #1161 - 2026-10-31

Four legs, four platforms each. The first Jami at-Tirmidhi set, produced across
two days and a session that spent most of its length on the machinery behind it.

**What the set was for.** "Whichever woman dies while her husband is pleased
with her enters Paradise" is short enough to be misread as a whole account of a
marriage. The blocks keep it to what it says - his contentment as one cause - and
the UZ translation kept the hal clause ("while he is pleased") that a looser
rendering drops.

**What went wrong, in order of cost.**

1. **The narrator, in one language of four.** Caught by ear in review: only UZ
   said Umm Salamah. I first read the documented rule (narrator in H, R055) and
   recommended removing it from UZ; the operator chose that, then reversed it
   with a better rule - the same matn through a different companion is a
   different record, so the narrator is never omitted and never generated.
   Six TTS calls to re-voice EN/RU/TJ. The rule now has a caller (P337). The
   caption table was also missing her, so three captions would have shown her
   name in Latin.
2. **The threshold clip, three times.** A forward drift into a blown-out doorway
   produced a modern facade, then a door knob - $2.24 of re-rolls on a camera
   rule already written in two places (P329).
3. **Whisper, after the re-voice.** RU came back as "Ум соляма, добудет" and
   "пророг"; EN as "Um Salama" with the last cue running 7.8 s past the voice.
   Rendered under -NoReview because the pause cannot be answered from a
   detached process; the validator named every one, the SRTs were fixed against
   the drafts and re-burned from cache before the operator saw the reels (P330,
   P211).
4. **Volume.** EN and TJ heard slightly loud. Measured before re-calibrating:
   the beds sat within 0.8 LU of each other and the voices differed by 5 dB, so
   the fix is a per-reel trim, not a registry change (P338).

**What is still wrong.** UZ runs 31.5 s against 21-23 s - the HARD RULE 6
spread, the same structural cause as #527, published as is by the operator.
Every bed in the registry is rights:unverified, Aswati included (P301).

**What carries forward.** The narrator is said in every adults reel from now on,
from the DB, refused at narration when missing. Kids lane: undecided.

## R166-R169 - Sunan Abu Dawud #4811 - 2026-10-31

**Shipped:** EN, RU, UZ, TJ - Telegram (176-179), Instagram, YouTube Shorts, TikTok.

**What the set was for.** "Whoever does not thank people does not thank Allah"
has two halves, and the operator asked for scenes in colour, not the dark register
most sets have used. The scenes follow the matn: water given, a hand on the
chest, the favours of Allah, and - the operator's call - a figure in dua at the
end, for the second half.

**Caught before publish, and who said it.**

1. **Left hands** in the water still (operator). Regenerated with right hands.
2. **Steam reading as smoke** through the centre of bread2 (operator); the bread
   scene was then dropped for the dua finale (operator).
3. **The qibla rule, said twice** (operator): it was stated on 2026-10-24 and
   lived only in chat memory. Written into the scene spec with the audience's
   bearings (P340).
4. **A Buddhist gesture** (operator). Kling 3.0 closed an ambiguous side-on pair
   of hands into pressed palms for all ten seconds. My whole-clip check looked
   for faces and the sun, not for the gesture.
5. **The sun in his hands, then "rubbed out with an eraser"** (operator). The
   prompt put the sun between the palms; a local OpenCV removal had no detail
   to recover under the blown core. FLUX 3 Edit fixed it on one call.
6. **"Why FLUX 2 and not 3?"** (operator). We are a major version behind, and the
   edit was the first time FLUX 3 was used.
7. **The -NoReview gate stopped EN and RU** (the gate, on my P339 fix): `--strict`
   was splatted letter by letter. Failed safe; P341.
8. **RU subtitles** (me, reading the SRT): "Абхурайра, добудет", and the closing
   guillemet after our moral - P316 recurring. The validator rated the first
   MEDIUM and did not see the second.

**Escaped to publish.** Nothing known.

**Root causes.** A rule kept in memory instead of the repo (3). A figure check
that tests for what a frame must not contain, but not for what the gesture
means (4). A fix verified by reading the code path instead of running it (7).
A validator that compares words, not the boundary of the Prophet's speech (8).

**Prevention landed.** P340 (prayer direction, now including the dua gesture);
P341.

**Prevention deferred.** Make an honorific near-miss ("добудет") and a moved
quotation boundary HIGH in stt-validate.py - P316 has now recurred, and both were
caught by hand. Evaluate FLUX 3 text-to-image for stills.

**Operator corrections of the assistant: 6** (items 1-6).

**The finding:** the operator's eye caught every visual defect this set; the
gates caught none of them. A gesture is content, and a still review that only
looks for faces will pass a frame that says the wrong thing.

## R170-R173 - Sahih al-Bukhari #6412 - 2026-11-01

**Shipped:** EN, RU, UZ, TJ - Telegram (180-183), Instagram, YouTube Shorts, TikTok.

Chosen and drafted unattended overnight on the operator's instruction, with the
stills; voice and clips after his approval in the morning.

**Caught before publish, and who said it.**

1. **The DB row's Russian matn** (me, comparing the four languages): "Две блага,
   которыми пренебрегают" - wrong gender, and "neglect" for maghbun, which the
   other three render as loss. Corrected in the DB on the operator's word.
2. **The time scene** (me): every palm-shadow variant drew the shadow of a human
   hand on the sand. The operator chose an hourglass; I noted it is not attested
   in the period and framed it as a timeless symbol.
3. **A face at the right edge of the sapling clip** (me, a whole-clip edge scan
   at 4 fps). Fixed free with a 12% crop instead of a $1.12 re-roll.
4. **RU subtitles** (the P342 gate, its first live catch): "добудет доволен имя
   Аллах" - HIGH, render stopped before the burn. "Добудет" for the third set
   running.
5. **Water out of the bottom of the jar** (operator). The still already showed
   it; I reported the clip as "the jar turns upright, reads as lifting it out".
   Replaced with water poured from the jar's mouth into another person's hands -
   the operator's idea, which also gave the scene a meaning ("health spent
   serving someone").
6. **The 'death' hashtag** (me raised it; operator: "причём тут смерть?") - the
   matn does not mention death. New `time` tag concept.
7. **"ими" for one man** (operator asked) - explained: the dual covers Ibn Abbas
   and his father; kept.

**Escaped to publish.** Nothing known.

**Root causes.** A clip review that checks what must not be in the frame - a
face, the sun - and not whether the action in it is physically right (5); the
same shape as the pressed palms on 4811. A library row whose Russian nobody had
read against the Arabic (1).

**Prevention landed.** P343: the scene spec's clip check now names the action
itself. P342 worked as designed.

**Prevention deferred.** Russian matn across the library is unaudited against the
Arabic for meaning; audit-library.py checks script and form, not sense.

**Operator corrections of the assistant: 2** (items 5 and 6's pushback; 7 was a
question).

**The finding:** two sets running, the defect the operator caught was the one
my check had no question for - first a gesture, now physics. The review needs to
ask what the scene is doing, not only what it must not show.

## R174-R177 - Sahih al-Bukhari #6406 - 2026-11-01

**Shipped:** EN, RU, UZ, TJ - Telegram (184-187), Instagram, YouTube Shorts, TikTok.

The first hadith taken from a Dorar query through every stage of the sourcing
pipeline - upload, translation, A/B (Sonnet 5 + GPT-6.1 Sol), the SQL gate,
promote - and on to a published reel the same day.

**Caught before publish, and who said it.**

1. **Translations checked only by me** (operator: "Переводы где проверял?"). Read
   against HadeethEnc then; the Uzbek "тарозуда" was wrong. Fixed before A/B.
2. **Whether A/B was running at all** (operator asked). Stage 3 run with both
   models; 4/4 pass/high.
3. **An Arabic narrator in the library** (the P337 gate at the narrate dry run).
   promote-candidates copied the Dorar adapter's 'أبو هريرة' where the library
   and NARRATORS key in English. Fixed in the data and closed in promote: P344.
4. **My Stage 4 script filtered on `id`** (PostgREST 400, nothing written). The
   candidates table keys on `candidate_id`; I wrote the column from memory
   instead of reading the row first. Same lesson as the guessed `al.pick()`.
5. **The finger-counting dhikr stills read as a meditation mudra** (me, before
   showing them). Replaced with prayer beads at the operator's word.
6. **The scale clip levelled out from ~6 s** (me, the P343 action check). Played
   in reverse it does the right thing: level, then the glowing left pan sinks.
   Free, instead of a re-roll.
7. **RU subtitles** (the P342 gate: 11 HIGH - lead-in, the two phrases, 'Причист').
   Hand-fixed against the draft. EN had MEDIUM only (no quotation marks, 'him'),
   fixed too.
8. **The transliteration broken at its hyphens on screen** (me, frames of the
   final RU). A line break inside the cue did nothing - render-reel's
   Split-LongCues joins a cue's lines - so the cue was split at the pause.

**Escaped to publish.** Nothing known.

**Root causes.** promote's mapping trusted that the adapter's narrator had the
library's shape (3). A column name written from memory (4). Nested quotation
marks in a matn, which the narrated-quote check cannot pair (handled by dropping
the inner pair from the narrated text only).

**Prevention landed.** P344: promote skips a candidate whose narrator is not a
NARRATORS key, visible in the dry run before the commit.

**Prevention deferred.** render-reel's Split-LongCues discards intentional line
breaks; a long transliteration still needs a hand split at a pause.

**Operator corrections of the assistant: 2** (items 1 and 2).

**The finding:** the gates did their job this set - P337 and P342 each stopped a
real defect before anything was spent or burned. What the operator still had to
catch was process: that the translations had not been checked against an
outside source, and whether the A/B step was being run.

## R178-R181 - Sahih Muslim #2747 - 2026-11-02

**Shipped:** EN, RU, UZ, TJ - Telegram (188-195, video + full text), Instagram, YouTube Shorts, TikTok.

Chosen for that day's post on the operator's reading of the analytics: repentance
and forgiveness draw (Ibn Majah #4251 is the YouTube #1). Dorar query to
published reel in one day, through candidate, translation, A/B, promote and the
matn-vs-number gate.

**Caught before publish, and who said it.**

1. **TJ "маркаб"** (operator): a literal "mount" where the Tajik reader says
   "шутур". Changed in the library, A/B re-run on TJ.
2. **The saddle's Y-frames read as antlers** (me, the stills sheet), and did not
   match caravan-1. Re-rolled with short posts.
3. **The cloak and staff were not in the tree's shade, and the tree in the tree
   and return stills were two different trees** (operator). One tree description
   word for word in both prompts; picked the pair whose trunks matched.
4. **The staff stood upright in the sand** (operator). Propped on the trunk.
5. **The caravan camel slid backward from 6 s** (me, the 0.5 s review comparing
   positions): my motion prompt named the screen direction against the way the
   still faced. P348; one re-roll.
6. **RU "отчаялся найти"** (A/B model A): a word the Arabic does not have.
7. **RU lead-in garbled, EN "aired" for "erred"** (the P342 gate). Hand-fixed.
8. **UZ 64.9 s against six 10 s clips** (P240 refused the render). Slowed copies.
9. **Every caption over Telegram's 1024** (build-caption). Operator chose video +
   full text as a reply; route.ts gained `replyTo`.

**Escaped to publish.**

- **TikTok TJ: two Cyrillic letters inside the Arabic line** ("هо бها"). I typed
  the four TikTok texts by hand instead of copying them from the caption files.
  Caught by me after the operator's "d"; he was asked to edit the caption. P349.
- **RU on Telegram: the full text went as the next message, not a reply.** The
  first post run sat inside a remote call that timed out after 60 s; the process
  died after RU's video, and its message id was lost. P350.

**Operator corrections of the assistant: 5.** Items 1, 3, 4; "for today" - I had
queued #2747 after #223 although it was made for that day's post ("ты тормоз");
and "you post Telegram, did you forget?" - I handed him the Telegram text to paste.

**Root causes.** Text produced twice by hand where a file already held it (P349).
A long-running publish started in the foreground of a call with a 60 s limit, then
retried as Start-Process with an absolute path containing spaces, which never
started (P350). The session's own decisions (post today, the bot posts Telegram)
were not re-read before acting on the schedule.

**Prevention landed.** P346 (references first, foreseeable defects in the still
prompt), P348 (motion direction by the subject), P349, P350; the Telegram split
is a recorded rule.

**The finding:** the content gates held - every defect in the reel itself was
caught before publish. What escaped was in the handoff to the platforms, the one
stage still done by hand.

---

## R182-R185 - Sahih Muslim #2749 - 2026-11-03

**Shipped:** EN, RU, UZ, TJ - Telegram (196-199, one message each: every caption 641-735 chars, under 1024), Instagram, YouTube Shorts, TikTok.

The second hadith from the repentance queue, chosen at the operator's request to
start the next reel "by theme". Dorar query to published reel in one day:
candidate, translation, A/B, Stage 4, promote, matn-vs-number gate. The session
opened with the full pre-flight read, which found P351.

**Caught before publish, and who said it.**

1. **Pre-flight step 5 ran `npm run test:smoke`, a script that never existed**
   (me, running the step instead of reading it). P351.
2. **RU "удалил бы вас", TJ "Савганд ба Он ки"** (me, against the Arabic) -
   "убрал", "Он Зоте, ки" before A/B; A/B 4/4 pass/high.
3. **Tag `istighfar` is not in lib/tags.ts** (me, before promote) - the push gate
   would have refused the library. `sins` instead.
4. **"ولجاء" (Dorar) against "وجاء" (HadeethEnc)** - the matn-vs-number gate and
   the tohed page settled it: "ولجاء" sits at this number.
5. **dua still: hands shoulder-wide, palms forward - the takbir, not dua - on a
   patterned fringed rug** (me, the stills sheet). Re-rolled.
6. **people-1: sandals toes-to-camera on figures walking away; a pink bag**
   (me). people-2; the clip's feet checked on a crop.
7. **The fourth scene was a reused clip** (operator: "where is the fourth still?
   so each language gets its own cover"). A new still - and made bright and
   colourful at his request, because the other three were desert.
8. **Kling's wind died at ~3 s on footprints** (me, the frame strip). Operator:
   keep only the windy start - first 3.5 s slowed x3.
9. **UZ 40.07 s against four 10 s clips** (P240, planned before the render).
10. **RU subtitles: lead-in and honorific garbled** (P339 stopped the render).
11. **EN burned "By him in Whose Hand"** - a lowercase pronoun for Allah - with
    no quotation marks (me, reading the render log before reporting). The check
    rated it MEDIUM, and under -NoReview a MEDIUM burns. Hand-fixed and
    re-rendered before anything was shown. P352.

**Escaped to publish.** Nothing known.

**Operator corrections of the assistant: 1.** Item 7: the scene plan reused a
clip for the fourth slot, although four stills - one cover per language - had
been discussed.

**Root causes.** A check that knew about the defect (P298) was wired WARN-only
from the days a human always reviewed the subtitles; -NoReview removed the
human and left the warning with nobody to read it. And a standing need stated
in conversation (a cover per language) was not carried into the scene plan.

**Prevention landed.** P351 (pre-flight step 5 runs the real suite). P352
(divine_pronoun_case is HIGH; a test pins it).

**Prevention deferred.** `quote_missing` is still MEDIUM, and the first EN
render burned without quotation marks too - the same shape as P352, left for
the operator to decide. Scene plans: four NEW stills unless the operator says
otherwise.

**The finding:** a warning is only as good as the reader it assumes. When a
gate's reader goes away (-NoReview), every warning it raises about integrity
has to be promoted to a stop, or it becomes a burn.

## R186-R189 - Sahih al-Bukhari #38 - 2026-11-04

**Shipped:** EN, RU, UZ, TJ - Telegram (200-203, one message each: every caption 513-559 chars, under 1024). Instagram, YouTube Shorts and TikTok by the operator.

The first set from the library-wide triage (operator: reels for every library
hadith, one or two at a time, full hadiths only - long ones live on the site).
Fasting / Ramadan had one reel since May.

**Caught before publish, and who said it.**

1. **RU matn ended differently from the Arabic** (me, against the Arabic): the
   row was corrected to «...тому простятся его прежние грехи» before any draft;
   A/B on the proposal 4/4 pass/high.
2. **H block cited "the scholars explain"** - lint unnamed-authority FAIL (P111).
   Replaced with named sources: Ibn Hajar, Fath al-Bari (checked against a page
   quoting it) and the HadeethEnc commentary. An an-Nawawi attribution was dropped
   because it could not be checked.
3. **suhoor stills drew a teapot-like lamp** (operator). Re-written from
   documented early Islamic clay lamps and re-generated; the operator asked that
   every still and Kling prompt start from an internet reference.
4. **EN and RU subtitles: 'Ramaban', a garbled RU lead-in, no quotation marks,
   lowercase pronouns for Allah** - P339 stopped both renders under -NoReview,
   which is the gate working as built (P342/P352). Fixed in the cached SRTs
   (P211), strict re-validation 0 findings, re-rendered; UZ and TJ rendered
   first time.

**Escaped to publish.** Nothing known.

**Operator corrections of the assistant: 1.** Item 3: the lamp was described from
memory; a reference was needed first.

**Root causes.** A prompt for a period object written from the model's idea of
it, not from a source - the same shape as an unsourced claim in a caption.

**Prevention landed.** Stills and Kling prompts start from an internet reference
(standing rule, operator 2026-11-04). The strict subtitle gate stopped what it
was built to stop.

**Prevention deferred.** render-set renders all four languages in one pass; a
strict stop on EN or RU still lets UZ/TJ finish, which is fine, but nothing
re-runs the stopped legs - that is a manual second pass (`--langs en ru`).

**The finding:** the gates that were promoted to stops this week (P339, P352)
now catch Whisper's errors as a matter of routine. The work at the gate has
moved from noticing to fixing.

## R190-R193 - Sahih al-Bukhari #5984 - 2026-11-04

**Shipped:** EN, RU, UZ, TJ - Telegram (204-207, one message each: 397-456 chars), Instagram and Facebook together from Meta Business Suite, YouTube Shorts, TikTok. #38 (R186-R189) went to Facebook the same evening - the first two sets on the new page.

Second set from the library triage, chosen because Family / Kinship had no reel.
Page check (en.tohed.com, bukhari/5984): one hadith at the number, matn-vs-number
gate MATCH.

**Caught before publish, and who said it.**

1. **A/B disagreed on all three non-English legs** (the gate): pass A said
   'ties of kinship' is not in «قاطع». Settled from the source, not by preferring
   a model: Muslim #2556 has Sufyan's gloss «يعني قاطع رحم» and a narration with
   «قاطع رحم». Text kept; the operator approved; the H block names both.
2. **"Will not enter Paradise" needed its scholarly reading** (me): the H block
   quotes Shaykh Abdul Sattar al-Hammad (Hidayat al-Qari) - holding it lawful
   vs. knowing it is forbidden - read on the page before it was written.
3. **First morals restated the matn** (me, P315 shape) - rewritten to one action.
4. **door-1 over my door-3; meal cups read as soup pots** (operator). Meal
   re-generated from a reference (Bukhari 5638, the wooden drinking bowl) with
   small piala-like bowls.
5. **EN and RU subtitles** - 'Jubeir', 'Джубайер Ибан ... добудет', no quotation
   marks, and an EN last cue stretched to 32.0 s on a 22.7 s narration (P339
   stopped both renders). Fixed in the cached SRTs, strict re-check 0, re-rendered.

**Escaped to publish.** Nothing known.

**Operator corrections of the assistant: 2.** Item 4 (door pick, cup shape).

**Root causes.** "Cups" in a prompt is read by the model as whatever vessel it
likes; the size and shape have to be stated, from a reference, the way the lamp
was for #38.

**Prevention landed.** None new - the existing gates (A/B, P339) did their work.

**Prevention deferred.** The RU bed ran at x1.97 to reach the mix target - a
very quiet track; worth a loudness note in the registry if it recurs.

**The finding:** two models disagreeing was the useful output. The answer was
in the next hadith over, not in either model.

## R194-R197 - Sahih al-Bukhari #6675 - 2026-11-05

**Shipped:** EN, RU, UZ, TJ - Telegram (208-211, one message each: 608-688 chars), Instagram and Facebook together from Meta Business Suite, YouTube Shorts, TikTok. Listen on hadithreels.com published for all four (publish-narration).

Third set from the library triage. Page check (en.tohed.com, bukhari/6675): one
hadith at the number, matn-vs-number gate MATCH. A/B 4/4.

**Caught before publish, and who said it.**

1. **The well still, four rounds** (operator): the first rope read as a noose;
   then the bucket spilled; then the rope hung beside the bucket instead of
   holding it. well-d-2 has the rope knotted to the handle.
2. **Kling undid the knot** (operator): under the slow push-in the knot drifted
   off the handle within the first second. Re-run with a static camera and the
   knot named in the prompt; checked frame by frame, once a second (me).
3. **UZ narration 40.1 s on 10.04 s clips** (render-set stopped it): x1.06
   copies, as for #2749 (P240).
4. **EN and RU subtitles** - 'Honor' capitalised mid-sentence, no quotation
   marks; RU 'Абдулах Ибан Амар, добудет', 'со товарищей', 'лживое клятва'
   (P339 stopped both renders). Fixed in the cached SRTs, re-rendered.
5. **The top-ranked bed was 'Victory March'** (me): first by usage count, wrong
   in tone for a hadith about the major sins. Four lower-use beds chosen instead.

**Escaped to publish.** One field, by me: the TJ YouTube description I typed
for the operator had '#парents' (Cyrillic letters inside 'parents'). Flagged
with the next message; platform-texts.py had it right - the error was in my
retyping, not the generator.

**Not settled before production.** The tracker and OPEN_ITEMS said #6675 must
not follow #2654 (same subject, al-kaba'ir) without a deliberate call. The
overlap was written into OPEN_ITEMS at the #5984 close, but I find no record
that it was put to the operator as a decision before the paid A/B. 37 days and 96 reels separate
the two sets, and the operator approved every gate after - but the call was not
made as the row asked.

**Operator corrections of the assistant: 2.** Items 1 and 2.

**Root causes.** A rope and a bucket are two objects to an image model, and a
camera move is licence to separate them: the attachment has to be stated, and
the camera held still, when the attachment is the point. The TJ slip: copying a
generated field by hand instead of from the file.

**Prevention landed.** None new.

**Prevention deferred.** The 'deliberate call' rows (#6675/#2654, the Tawheed
cluster) live in prose; nothing surfaces them when a set is picked.
Candidate: the triage reads the duplicate index and prints the row next to the
candidate.

**The finding:** the gates caught everything that reached them. What slipped -
a pairing rule and a retyped hashtag - lived outside any gate.

## R198-R201 - Sahih al-Bukhari #6307 - 2026-11-05

**Shipped:** EN, RU, UZ, TJ - Telegram (212-215, one message each: 544-602 chars), Instagram and Facebook together from Meta Business Suite, YouTube Shorts, TikTok. Listen published.

From request to published in one evening. The operator sent two posts (Tirmidhi
#3462, Musnad Ahmad #22079) and asked what the library has on repentance and
dhikr. Neither post's hadith passed the Dorar gate (a lone narrator; a broken
chain) - recorded in OPEN_ITEMS. #6307 came from the repentance queue the same
query run: candidate -> our translation from the Arabic -> A/B 4/4 -> operator
approval -> library -> P319 MATCH -> set.

**Caught before publish, and who said it.**

1. **TJ 'Ба Худо савганд'** for واللهِ (me, at the side-by-side read; operator
   approved 'Ба Аллоҳ').
2. **'istighfar' is not in the tag vocabulary** (me, against lib/tags.ts) -
   dropped before the promote.
3. **The book column** - promote leaves it empty; set from the page header
   (صحيح البخاري / كتاب الدعوات), not from memory.
4. **The H block** - written from al-Hammad's commentary on the page; his
   'tark al-awla' point left out as too fine for a reel.
5. **EN and RU subtitles** - no quotation marks; RU 'Абуху Райра, добудет
   доволенным', 'по истине' (P339 stopped both). Fixed in the cached SRTs; the
   EN/RU re-render was queued to start when the UZ/TJ render finished.

**Escaped to publish.** Nothing known. The platform texts were pasted from
platform-6307.md, not retyped (the #6675 '#парents' lesson).

**Process slips (mine).** Workflow K step 2 (audit-library before A/B) was run
after the A/B dry run, not before - clean, but out of order. The A/B ran twice
because --commit re-scores; the cost was stated to the operator after the fact.
The translation step was first described as free; it calls the model, and the
operator was asked before it ran.

**Operator corrections of the assistant: 0 on this set.** Item 1 was my
proposal, his approval. His standing instruction from the #6675 close - check
the documents every time - is what this set was run against.

**Root causes.** Steps I knew from earlier sets I ran from memory of the order,
not from the workflow text; the slips were exactly where the order differs from
what I remembered.

**Prevention landed.** Reading the workflow section before each stage
(Workflows L, I, K, J were read this set before running).

**The finding:** a request that arrived as two social-media posts ended as a
reel of a different, sound hadith on the same subject - the gate turned "is this
real?" into "here is the real one".

## R202-R205 - Sahih Muslim #2734 - 2026-11-06

**Shipped:** EN, RU, UZ, TJ - Telegram (216-219, one message each: 488-530 chars), Instagram and Facebook from Meta Business Suite, YouTube Shorts, TikTok.

A set rendered on 2026-11-02/04 and held while #2747, #38, #5984, #6675 and #6307
went out first. The operator re-watched the four reels before the post.

**Caught before publish (earlier, recorded at the time).** The matn row stopped
after the food clause; the drink clause was restored from HadeethEnc 5798 and the
row re-translated and A/B'd before production (2026-11-01). The UZ bed was retired
and re-bedded on 2026-11-03. EN re-rendered on 2026-11-04 from its recorded inputs
after the P355/P356/P358 render changes - byte-identical.

**At publish.** A rendered set four days old was checked for the things that can
go stale: the TG dry run (captions present, chars under the limit), the reels
re-sent to the operator. Nothing had changed.

**Operator corrections of the assistant: 0.**

**The finding:** a held set needs one re-watch and a dry run, not a re-render;
its render sidecars (render.json per language) carried everything the close needed.

## R206-R209 - Sahih Muslim #2581 - 2026-11-06

**Shipped:** EN, RU, UZ, TJ - Telegram (220-227: captions 1196-1267 chars, so each leg is a video plus a full-text reply), Instagram and Facebook from Meta Business Suite, YouTube Shorts, TikTok.

Produced end to end while the operator was away ("доделай до конца"): stills picks, beds and the EN/RU subtitle fixes were Claude's; every paid step and the publish waited for his go.

**Caught before publish**

1. **tidy-out archived this set's drafts** during the #2734 close - set-2581.json, the caption JSON and the drafts were "not read by any tool". Moved back; P373 makes a set-<n>.json for an unpublished number mark the set as in production.
2. **UZ bed refused by the gain gate** - vocal-nasheed-04 needed x2.19 against the cap of 2; re-bedded on path-to-jannah-bg (x1.04).
3. **UZ narration (67 s) outran the six clips** - x1.15 slowed copies (-s, P240), registered from a separate spec.
4. **EN/RU subtitles** - P339 stopped both first renders: EN 'zaqa' -> 'zakah', the honorific, 'said:', quotes, last cue clamped to 58.9 s; RU lead-in, 'дирхема', 'воскресения', 'оклеветав', 'долга', quotes. Fixed in the cached SRTs, re-rendered.
5. **«муфлис» in UZ/TJ** - the operator asked whether it was checked; his explanation and HadeethEnc TJ («муфлис (фақир)») confirm it. Kept.

**Escaped to publish**

- **TikTok TJ: a Cyrillic «х» inside the Arabic matn** (`хَسَناتِه` for `حَسَناتِه`). platform-2581.md was correct; the letter changed in my chat block when I reproduced it. Caught by me after sending, flagged at once; the operator replaced the Arabic paragraph from a block that was compared with the file (cmp) before it was sent. Integrity of the Arabic text, so corrected in place.

**Root causes**

- A platform block passes through the model on its way to the chat. "Copied from the file" was true of the source, not of the output - a mixed-script paragraph is where a letter of the neighbouring script slips in.

**Prevention landed**

- From this set: a block with Arabic is compared with the file (written out and cmp'd) before it is sent, as the corrected paragraph was.

**Prevention deferred**

- A per-language YouTube cover (a script, next set): the operator wants a distinct cover for the UZ and TJ legs - a different scene and the title in that language - so the four legs do not look like one video in search. EN/RU are told apart by their burned-in subtitles.

**Operator corrections of the assistant: 1.** I said the Shorts cover changes little because the Shorts feed shows none; he pointed out that search, the home page and the channel page do show it, and four identical covers read as one video - a viewer opens one and never learns the hadith is there in his friend's language. He was right.

**The finding:** the gate that copies text from a file ends at the file; the last hop - from the model to the chat - needs its own check, and Arabic beside Cyrillic is where it fails.

## R210-R213 - Sahih Muslim #223 - 2026-11-07

**Shipped:** EN, RU, UZ, TJ - Telegram (228-231, one video message each), Instagram and Facebook from Meta Business Suite, YouTube Shorts (UZ and TJ with their own covers), TikTok.

Rendered 2026-11-02/03 and held until the operator said «публикуй #223» on 2026-11-07.

**Caught before publish**

1. **EN/RU subtitles** read against the drafts on 2026-11-06: they match.
2. **TJ YouTube cover:** make-covers.py's default scene for TJ was m223-sadaqa, which shows a hand; re-made on m223-path (`--scene tj=path`).
3. **An ambiguous «да»** at 01:27 and 12:09 followed messages that asked about a paid translation run and the publication together. I took them for the reversible one and asked for «публикуй #223» before posting; the operator wrote it at 12:11.
4. **The Telegram run did not start** the first time: `Start-Process -File` with an absolute path containing spaces. Nothing was posted; re-run with -WorkingDirectory and a relative path.

**Escaped to publish**

- **m223-sadaqa shows a hand** in all four reels (MODE B: no people). Presentation, not integrity - fixed forward, not republished. The scene was accepted at render on 2026-11-02.

**Prevention landed**

- Every platform block checked as sent with `platform-texts.py --check-sent` (P375): 15 of 15 matched the file.
- P376: covers go beside their reels (the operator's request during this set).

**Prevention deferred**

- make-covers.py cannot see a hand in a frame; the operator's eye on the cover remains the check.

**Operator corrections of the assistant: 0.** One request (P376).

**The finding:** the check after sending (P375) costs seconds per block and caught nothing this time - which is what it should do on a good day.

## R214-R217 - Sahih al-Bukhari #6114 - 2026-11-08

**Shipped:** EN, RU, UZ, TJ - Telegram (232-235, one video message each), Instagram and Facebook from Meta Business Suite, YouTube Shorts (UZ and TJ with their own covers), TikTok.

**Caught before publish**

1. **RU bed Content-ID claimed.** I picked aswati-Steady-Motivation from the lanes and the recent-use history without reading `rights.content_id`; it blocked #3540 worldwide. render-set's dry run passed; render-reel's gate refused RU mid-set. Re-rendered on vocal-nasheed-05.
2. **EN subtitles:** Whisper wrote «Hurayra» against the draft's «Hurairah», and the Prophet's words had no quotation marks - P339 stopped the burn. SRT text fixed, timings kept.
3. **RU subtitles:** Whisper garbled the opening («Абуху Райра, добудет доволенным»), wrote «селен» for «силён», and invented two cues in the silence after the narration («Редактор субтитров И. Бойкова», «Корректор А. Егорова»). Caught by the gate (srt_exceeds_audio, unknown_word, honorific_garbled); fixed by hand.
4. **A night scene** in the approved plan (scene 3) - changed to daylight before FLUX, per the operator's bright-scenes rule.
5. **well-1:** a pale shape at top left looked like a figure at thumbnail size; checked at full size - a stone post.

**Escaped to publish**

- None found.

**Root causes**

- Choosing from a list without the gate that will judge the choice (the bed).
- Whisper on short Russian narration: the opening name and the silence after the last word are where it fails.

**Prevention landed**

- P377: render-set.py runs every bed and clip through `audit-assets.py --check` before the first render, dry run included.
- Every platform block checked as sent (P375): 28 of 28 matched.

**Prevention deferred**

- The SRT fixes are still by hand; a draft-aligned subtitle text (keep Whisper's timings, take the words from the draft) would remove the class.

**Operator corrections of the assistant: 1.** «кафи дарё» -> «кафи баҳр» on the next set (#6405, TJ): «дарё» reads as a river.

**The finding:** a gate that exists only at the point of use turns a planning slip into a mid-run failure; the same check, run while planning, costs nothing.

## R218-R221 - Sahih al-Bukhari #6405 - 2026-11-09

**Shipped:** EN, RU, UZ, TJ - Telegram (236-239, one video message each), Instagram and Facebook from Meta Business Suite, YouTube Shorts (UZ and TJ with their own covers), TikTok. Rendered 2026-11-08, published 2026-11-09 in the order the operator then fixed (P385).

**Caught before publish**

1. **UZ bed gain x2.14** asked for by the gap target; render-reel.ps1 accepts at most 2 and stopped UZ mid-set after the dry run had printed the number. P384: render-set's dry run now applies the same cap.
2. **EN subtitles:** Whisper's «Subhan Allahi wa bihamdi» and «Abhurayra»; the Prophet's words without quotation marks - P339 stopped the burn twice (the second time after a stale device write had put the old SRT back).
3. **RU subtitles:** «вобихамдеги», «Абхурайра», the quote marks - fixed by hand; and «Субхана-Ллахи» broke across two lines at the hyphen. The operator caught the break; U+2011 (non-breaking hyphen) keeps it whole.
4. **TJ «кафи дарё»** -> «кафи баҳр» (operator, before narration): «дарё» reads as a river.
5. **Facebook title field gone** in Meta Business Suite's Create reel; the title block was pasted into the Facebook "Text" field and replaced with the full caption before posting (P385).

**Escaped to publish**

- None found.

**Root causes**

- A planner that does not apply the limits of the step it plans for (the gain cap).
- Repeated writes of the same staged file landing stale content on the PC - a transport fault, not a content one.
- A form that changed under a generated block (Meta).

**Prevention landed**

- P384: the dry run stops on a gain render-reel.ps1 would refuse.
- P385: platform-texts.py prints the fixed publishing sequence and no Facebook title; tests pin both.
- Every device write now goes under a unique file name and is checked by hash.

**Prevention deferred**

- The SRT fixes are still by hand (draft-aligned subtitle text would remove the class).
- Platform blocks were given from out/platform-6405.md but not run through `--check-sent` (P375) this time.
- Listen (publish-narration) not run yet - waits for the operator's yes.

**Operator corrections of the assistant: 2.** The RU hyphen break in «Субхана-Ллахи»; the publishing order, which he asked to be written down so it stops drifting.

**The finding:** generated text is only as good as the form it is pasted into - the day a platform changes its form, the generator changes too.

## R222-R225 - Sahih Muslim #2564 - 2026-11-09

**Shipped:** EN, RU, UZ, TJ - Telegram (240-243, one video message each), Instagram and Facebook from Meta Business Suite, YouTube Shorts (UZ and TJ with their own covers), TikTok - in the fixed order (P385).

**Caught before publish**

1. **Library UZ/TJ singular for a plural:** UZ «қалб ва амалларингизга», TJ «сурати шумо» for قُلُوبِكُمْ / صُوَرِكُمْ. Flagged against the Arabic; the operator chose to fix the library; written through sign -> apply, Latin re-derived, Stage 3 8/8 pass.
2. **Clip order did not follow the matn:** the first EN render showed the mat on «forms or wealth». The operator asked for the clips to match the matn ("we discussed this"); reordered well, wealth, mat, bread. Equal slots still put «hearts and deeds» on the wealth clip - a fifth clip would align it exactly.
3. **Five clips planned, four needed:** the operator asked why five for a 22-second narration; four used, one paid clip saved.
4. **First wealth still:** dark, and the coins looked modern (bimetal). Regenerated bright with hand-struck dirhams and dinars.
5. **Subtitles:** EN without quotation marks around the Prophet's words; RU «Абуху Райра добудет доволенным», «ваше сердца», «намеренье» and the closing quote after the moral - both stopped by P339, fixed against the drafts.
6. **Beds:** the picker recommended aswati-Victory-March and Focused-Determination for a hadith about the heart; calmer beds chosen.

**Escaped to publish**

- None found. The mat clip is darker than the bright-palette rule asks; kept by the operator's lg.

**Root causes**

- Equal-length scene slots cannot follow the matn's own boundaries; the order is the only lever.
- The bed picker ranks by rotation, not by mood.

**Prevention landed**

- Scene order chosen against the narration's cue times before the render (this set, by hand).

**Prevention deferred**

- Per-clip durations from the SRT cue times in render-reel.ps1, so a clip can start where the matn says what it shows.
- A mood tag on beds so the picker can skip marches for contemplative hadiths.
- Platform blocks given from out/platform-2564.md, not run through `--check-sent` (P375).

**Operator corrections of the assistant: 2.** The clip order (clips must follow the matn, already agreed); four clips, not five.

**The finding:** a scene order that ignores the words is a defect the operator has to catch every time; it belongs in the plan, checked against the cue times, before the first render.

## R226-R229 - Sahih Muslim #2588 - 2026-11-10

**Shipped:** EN, RU, UZ, TJ - Telegram (244-247, one video message each), Instagram and Facebook from Meta Business Suite, YouTube Shorts (UZ and TJ with their own covers), TikTok - in the fixed order (P385).

**Caught before publish**

1. **Clips ordered before the narration was measured:** four 10 s Kling clips, then the narrations; the last slot (third clause + moral) needed 17.5 s in EN and 18.9 s in UZ. A 0.55x slow copy was the first fix. The operator asked whether the clips had been made without measuring the narration - they had. Option A on his direction: a new bright 15 s clip, a mountain oasis, for «Allah raises him» and the moral (not always desert).
2. **The asset gate crashed on a Cyrillic note** and render-reel.ps1 read the crash as a rejection of four registered clips (P392).
3. **Clips on the wrong clause:** proportional anchors (matn:0.35, matn:0.7) put the horse (honour) on «no one humbles himself». Seen on a frame sheet of the first EN render; anchors moved to the EN/RU clause cues (matn:0.22, matn:0.55), which stretched the last slot to 20.9 s (UZ) - the oasis slow copy went from x0.78 to x0.70.
4. **Subtitles:** EN without quotation marks; RU «Абуху Райра, добудет доволенным», «пророг», «Запрощения» and the closing quote after the moral - fixed against the drafts before the burn (P339).
5. **YouTube description:** the caption's new page line was glued to the end of the moral (P394), caught in the generated block before it was sent.

**Escaped to publish**

- None found. The oasis clip plays at x0.70 with blended frames; on a slow rising shot it reads as smooth.

**Root causes**

- The clip plan was written from the hadith, not from the measured narration.
- A shared fraction of the matn cannot know where each language's clauses begin.
- platform-texts.parse() folded every line it did not know into the moral.

**Prevention landed**

- P393: reel-creation-pipeline.md Step 9 - narrate all four languages first; each clip's length is the longest language's slot; scenes follow the words, not always desert.
- P392: the asset gate prints with errors="replace".
- P394: the page line is its own field; 1 test.

**Prevention deferred**

- An anchor keyed to a subtitle cue (for example `cue:4`) so a clause boundary is exact in each language instead of one shared fraction.
- The P393 tripwire in code: generate-scene.ps1 refusing a reel whose four narrations are not on disk.

**Operator corrections of the assistant: 2.** The clips were made without measuring the narration; not every scene has to be desert.

**The finding:** the narration is the timeline - anything paid that has to fit it is ordered after it is measured.

## R230-R233 - Jami at-Tirmidhi #1987 - 2026-11-11

**Shipped:** EN, RU, UZ, TJ - Telegram (249-252, one video message each), Instagram and Facebook from Meta Business Suite, YouTube Shorts (UZ and TJ with their own covers), TikTok - in the fixed order (P385).

**Caught before publish**

1. **A clip that did not show its words:** «follow a bad deed with a good one and it will erase it» was footprints in sand that the wind should fill. Two Kling takes ($0.56 each) kept every print to the last frame. Fixed with a FLUX Kontext edit of the same still with the prints removed ($0.04), horizon matched to the pixel, and a 1 s fade timed on the gust in the second take (P402).
2. **Wrong collection prefix:** the stills and clips were generated as `b1987-*`; `b` is Bukhari, Tirmidhi is `t`. Renamed before registering.
3. **The rename emptied seven prompt sidecars** (assets/scene-prompts, untracked, so git could not restore them). Rebuilt by `generate-scene.ps1 -Resume <request_id>` for each - fal still held the jobs, nothing was charged - and the still sidecars were rewritten from a staged copy with a size and hash check (P403).
4. **Two beds refused by the rights gate:** aswati-Heartfelt-Gratitude (retired) and aswati-Steady-Motivation (Content ID claim). Swapped for Morning-Serenity (RU) and Peaceful-Contemplation (TJ). The gate did its job.
5. **Subtitles:** EN without quotation marks and «Abu Dhar»; RU «Абузар, добудет доволенным», no quotation marks, and two cues Whisper invented after the narration ended («Редактор субтитров…», «Корректор…») - fixed against the drafts before the burn (P339).

**Escaped to publish**

- None found.

**Root causes**

- An image-to-video model animates what is in its first frame; it does not take things out of it. A prompt that asks it to is asking for the opposite of what it does.
- The stills were named before the collection prefix was checked against the registry.
- An in-place rewrite of untracked provenance files, with no check on what was written.

**Prevention landed**

- P402: a clip whose meaning is an object disappearing is built as still -> edited still -> crossfade on the motion, not prompted.
- P403: untracked provenance is rewritten only through a staged copy whose size and hash are checked before and after; renames are renames, content edits are separate.

**Prevention deferred**

- A repo script for the Kontext edit (it ran as a one-off from out/explain-src/edit1987.ps1) - OPEN_ITEMS.
- generate-image.ps1 checking the `-Name` prefix against the collection of the set.

**Operator corrections of the assistant: 1.** The scene numbers on the contact sheet (1.2, 2.2) did not match anything in the folder - he could not find the files; answered with the file names.

**The finding:** when the words say something vanishes, make the vanishing out of two pictures, not one prompt.
