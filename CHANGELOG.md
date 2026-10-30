## [2026-10-30] - a write tool that could not be aimed, and a question answered the hard way

### Fixed

- **`--number` was refused for candidates, so `--commit` could only run wide
  (P325).** `derive-uzbek-latin.ts` accepts `--number` to scope a run, but a
  guard rejected it unless `--library` was also passed - leaving no way to scope
  `hadith_candidates` at all. With `--commit` the script rewrites
  `text_uzbek_latin` on every row holding Cyrillic: 12 rows on 2026-10-30, when
  exactly one (`tirmidhi #1161`) had none. The other eleven already had Latin,
  including one row at `needs_human` and three at `verified`. Since the script
  also prints `FLAGS` where Cyrillic `е` could be Latin `e` or `ye` - ambiguity
  only a reader can settle - a blanket write reverts precisely the rows a human
  had reason to correct, with no diff and no record. The guard is gone; nothing
  else changed, because `q.eq('hadith_number', number)` was already applied to
  whichever table is selected. `--number 1161 --commit` then wrote one row.

- **Workflow K named the wrong pass-B model for twelve days (P275 addendum).**
  CLAUDE.md step 4 read `B = gpt-5.6-terra` while the code, `probe-passb.py`'s
  default, P275 and OPEN_ITEMS all said `gpt-6.1-sol`. Pass B moved in `cf19813`
  on 2026-10-18 - a commit that updated CHANGELOG, fix_patterns, probe-passb and
  verify-candidates, and not CLAUDE.md. Forty-seven commits followed, six of them
  editing CLAUDE.md. Read against the script's banner the stale string looks like
  undeclared drift with step 8's calibration never run, and today it stopped a
  workflow to re-establish something the repo already knew. Step 4 now names the
  live model, says the code is the authority, and records what the staleness
  cost.

- **#6570 is no longer unverifiable, and four more rows got their book
  (P322/P327 addenda).** P322 left #6570 as the single legacy row citing a Dorar
  search query - *"not a page, not fetchable, permanently unverifiable"*, the one
  row the sweep could only ever report as SKIP. That described the tool's
  dispatch, not the world: `target_url()` builds a tohed URL only for sunnah.com
  hosts, so a bad citation made a good NUMBER uncheckable. Built that URL from
  collection+number instead and put the gate's own question to it - the stored
  matn is a contiguous 171-character run at `bukhari:6570`. `source_url` is now
  the real page, the row passes the gate, and **zero** library rows carry a
  search query as their source. The same test resolved four of the five
  HadeethEnc-cited rows (#31 MERGED at #30 per P312, #2654, #6857, Muslim
  #2628), each book re-derived from its page at write time rather than
  transcribed. #2654 is the one that justifies the two-source rule: its
  HadeethEnc breadcrumb reads «فقه الأخلاق», a thematic category, where the real
  kitab is ash-Shahadat - a single-source extractor would have stored P287's
  defect in the column built to prevent it. `book` is now filled on 71 of 72
  rows; #6871 is the one left and is open as a live P306 case, its stored matn
  being absent from `bukhari/6871` and both neighbours.

### Added

- **`scripts/backfill-book.py`, and 63 rows of the authority P287 said was
  missing (P327).** `hadith_library.book` was empty on 69 of 72 rows. P287 - a
  fabricated book and chapter that passed every check - records the cause as
  *"the `book` column is EMPTY, so the generator produced the subdivision out of
  nothing"* and says where the fact lives: *"the `book` column and a Tier 1
  page."* The mitigation that shipped was a `book-claim` WARN, which catches the
  symptom and cannot supply the fact - so for 96% of the library the generator
  still had nothing to draw on. The new script reads the book off the Tier 1
  page, reusing `verify-matn-number.py`'s URL builder and cache (the full run
  made zero network requests): **63 written, 0 failed, 6 refused.** Format is
  the page's own English title VERBATIM, never a transliteration - the source
  publishes none, and the three cells filled earlier prove the point: the one
  copied from the page still matches it, the two typed by hand disagree with
  each other. The script requires the page's two JSON-LD sources to agree, which
  is what kept a HadeethEnc thematic category («الرقائق والمواعظ») out of a
  column that means kitab. Six rows stay empty and are listed every run: five
  carry HadeethEnc numbers that must not be assumed to be sunnah's (P306), and
  #6570 still has only a Dorar search query (P322).

- **P326, a rule about method, after two parsers answered nothing.** Deciding
  whether that blanket write was safe, I captured the script's dry-run output and
  wrote a parser to compare it against the DB. v1 dropped lines beginning with
  `[` to skip the `[DRY RUN]` header and truncated `#3435`'s second riwaya
  paragraph, reporting a DIFFERS that was entirely its own parse. v2 added a
  self-check comparing parsed Cyrillic to the stored field, which refused to
  conclude - correctly, since the script prints the NORMALISED Cyrillic, so the
  two were never meant to match. One REST query answered the question: one row
  had null Latin. The rule recorded: when a tool prints a view of data that
  lives in a queryable store, query the store - a parser over the view adds a
  second place to be wrong, and its bugs read as findings about the data.

## [2026-10-29] - CI had been red for a week because the runner moved, not the code

### Fixed

- **`ubuntu-latest` migrated to Ubuntu 26.04 and took CI with it (P314).** Every
  push from #335 (2026-10-22) through #365 failed in 30-55s - 31 runs - with no
  Playwright report produced at all. Nothing in this repo had changed: on the
  failing commit, in a clean clone, `npm ci`, `npx tsc --noEmit` and
  `npm run build` all pass, and the live site serves every string the E2E suite
  asserts. GitHub began moving the `ubuntu-latest` label to Ubuntu 26.04 on
  2026-10-19 - the day of the last green run - picking the image at random per
  run until 2026-11-19. `@playwright/test` 1.60.0 has no Ubuntu 26 support, so
  `playwright install --with-deps chromium` exited 1 before any test ran.
  `runs-on` is now pinned to `ubuntu-24.04`, with the reason beside it.
- **The three GitHub actions were three majors behind.** `actions/checkout`,
  `actions/setup-node` and `actions/upload-artifact` were on v4, being force-run
  on Node 24 with a deprecation warning on every run. All three are now v7.
  CI's Node goes 20 -> 22, which is what this machine runs (v22.21.1); CI and
  local had been on different majors.
- **The Telegram post route now declares its runtime.** It reads the rendered
  `.mp4` off disk, which the edge runtime cannot do. `runtime = 'nodejs'` and
  `dynamic = 'force-dynamic'` are declared rather than inherited, so the route
  cannot be moved to a runtime that would break it at publish time.
- **"About 38 behind" was wrong in five documents (P314).** 38 is the gap
  between two mirror entries, not the offset between the mirror's `id` and
  sunnah.com's reference. The offset is 162 there and grows to 239 by Bukhari
  6446. Corrected in CHANGELOG.md, fix_patterns.md, OPEN_ITEMS.md,
  reel-retro.md and reel-tracker.md. The previous session recorded this fix as
  made; it had not been made anywhere.

### Carried in this commit, written earlier and never committed

- P311, P312 and P313, and the #5185 entries in OPEN_ITEMS.md.

## [2026-10-28] — a published matn was wrong, and Telegram learned to post itself

### Fixed

- **Library row #3559 carried a different hadith (P306).** The row named
  `Sahih al-Bukhari`, `3559`, `Abdullah ibn Amr`, `grade: sahih`,
  `authority: tier1` and `source_url: sunnah.com/bukhari:3559` — all correct —
  and stored «إِنَّ مِنْ أَحَبِّكُمْ إِلَيَّ أَحْسَنَكُمْ أَخْلَاقًا» under them. Bukhari 3559
  reads «إِنَّ مِنْ خِيَارِكُمْ أَحْسَنَكُمْ أَخْلَاقًا». The stored wording is authentic
  Bukhari from the very same narrator — it is 3759, 3760, in Kitab Fada'il Ashab
  an-Nabi — so the defect was the NUMBER, not the words. The number came from
  the local mirror, whose `id` runs 162 behind sunnah.com's reference in
  this region: mirror entry 3597 is 3759, 3760, and mirror entry 3559 is a
  hadith of Jabir entirely. Settled by opening both pages.
  `text_arabic` and all four translations replaced; `text_uzbek_latin` and the
  legacy `text_uzbek` re-derived; the `love` tag dropped, since it described the
  superseded wording. `narrator`, `collection`, `hadith_number`, `grade` and
  `source_url` untouched. `matn_verified_at` left NULL per P265 and
  `matn_screened_at` deliberately NOT refreshed — the screening that passed this
  row is what is in question.
- **Two reels were already public.** EN and RU had shipped on Telegram,
  Instagram, YouTube Shorts and TikTok. The wrong words were in the narration
  audio and the burned subtitles, so no platform could repair them by editing a
  caption. All eight posts were deleted and all four languages reproduced.
- **Subtitles, by hand.** EN cue 6 read `place` for `placed` — the validator
  caught that one. RU cues 1 and 5 read «доблагословит» for «да благословит»,
  which the validator structurally cannot catch (P308), and which scored
  similarity 1.000. Both fixed and re-rendered; the edited SRTs survived per
  P211.

### Added

- **`sendVideo` on `/api/telegram/post`.** Posts the reel itself rather than
  only its caption. Resolves `videoPath` against the repo root and refuses
  anything outside it, requires `.mp4`, enforces Telegram's 1024-character
  video-caption cap rather than truncating, and reports bytes and caption length
  back. The text-only `sendMessage` path is unchanged, so the admin studio's
  button still works.
- **`scripts/post-telegram.py`.** One command per reel, with `--dry-run`.
  Reads the caption from `out/caption-<n>-<lang>.txt`, so the posted text is the
  same text the narration and the database carry. Not wired into the render:
  human approval before every publish stands.
- **PATTERN 306—310 and a P306 addendum.** The conflated matn; an approved block
  that exists only in the conversation; the honorific outside the subtitle
  validator's reach; a render that dies with the bridge call driving it; .NET
  file APIs ignoring PowerShell's location. The addendum covers the screening
  note that described a source page which does not exist.

### Changed

- **`parse_mode: 'HTML'` removed from the Telegram route.** The captions are
  plain text; under HTML any bare `&` or `<` would have failed the send. The
  route also no longer appends `hadith.text_arabic` to a caption that already
  contains it.
- **Tracker.** R154—R157, a new `Character / Akhlaq` theme row, four nasheed
  rows, the `b3559` scene set and the missing `b6570` scene row, and stats to
  157 reels from 40 hadiths. The #3559 duplicate-check entry was rewritten: its
  2026-10-27 note was false in every material particular.

## [2026-10-27] - the caption body leaves the admin, and #6570's lost text is recovered

### Added
- **`lib/caption.ts` owns the caption body (P305).** `buildCaptionBody()`,
  `wrapMatn()` and `CAPTION_L10N` moved out of `app/admin/page.tsx` unchanged,
  comments included. The admin imports them. `npx tsc --noEmit` clean.
  Before this the only way to produce a caption was to open the admin and press
  a button, so losing the generated blocks meant losing the caption — which is
  exactly what had happened to #6570, rendered 14-15 October, held until today
  for the Tawheed arc's spacing, with `draft.txt` overwritten in between (P246).
- **`scripts/build-caption.ts`** builds a reel's captions from the library row
  plus the two generated blocks given as JSON, with no admin and no
  re-generation: `npx tsx scripts/build-caption.ts --blocks out/caption-6570.json`.
  It refuses to guess when `hadith_number` matches more than one row and prints
  the uuids instead (P147), exits 2 rather than 0 on a read it could not make
  (P093), fits the tag line with the same `fitTagLine()` the admin uses (P184),
  and reads each file back after writing it (P186).

### Fixed
- **#6570 RU was sitting on the bed YouTube Content ID claimed.**
  `aswati-Steady-Motivation.mp3` — the bed that blocked #3540 EN globally
  ("The Motion Wave", Abdullaerh Dee, Jungle Entertainment Ventures). The
  rights field and its single gate, built last session, caught their first real
  case: `audit-assets.py --check` blocks it. Re-rendered on
  `aswati-Victory-March.mp3`, recommended by `pick-nasheed.py` — 1 use overall,
  never in RU, and the previous RU reel (R147) was on `vocal-nasheed-04`, so the
  no-two-consecutive rule holds. 220s long, so it cannot loop under a 47s reel;
  the script's third choice, `aswati-Morning-Serenity`, is 46.3s and would have
  looped by a second, which is why the duration was measured. Picture,
  narration and burned subtitles unchanged — P211 matched the narration
  fingerprint and kept the SRT, so only the music moved. The rejected render is
  kept as `...-reel.rejected-steadymotivation.mp4`.
- **The Tawheed queue in OPEN_ITEMS said none of its hadiths were in the
  library.** True on 2026-10-12, read as current twice after it stopped being
  true. Checked row by row: #6423 and #6570 are library rows and have both
  shipped; #3435, Muslim #28 and Bukhari #99 return no row.
- **The #6570 tracker table reserved R134-R137, corrected once to R138-R141.**
  Both stale. The frontier is R149, so #6570 takes **R150-R153**.

### Recovered
- **#6570's text, rather than re-generated.** P245 re-attributed the moral in 7
  of 8 generations, and this reel is rule 25's own test case (P239), so
  re-generating was not an option here in particular. The matn came from the
  database in all four languages. EN and RU morals came from
  `narration.srt`. UZ and TJ morals were transcribed from `moral.mp3` with the
  project's own Whisper invocation (`--model small`, `--language uz` and `tg`)
  and checked against the audio duration — 13.92s of 13.95s for UZ, 10.84s of
  10.92s for TJ, so neither was truncated. The Uzbek moral is genuinely shorter
  than the other three and quotes the kalima where the others say "the words of
  tawheed"; that is the audio, not a transcription loss. ﷺ was restored in all
  four: `cleanForTTS()` expands it before narration, so both the SRT and the
  transcript hold the spoken words.
- **The title was written fresh for all four languages.** `draft.txt`'s C block
  is the TITLE, not a closing line, and only S and M reach TTS, so no recording
  of it exists anywhere. Written under the generator's own rule: at most 8
  words, drawn from the matn, promising nothing the matn does not.

### Checked and left alone
- **The Uzbek kalima is correct as stored.** `text_uzbek_cyrillic` reads
  «Ла илаҳа иллаллоҳ», which looks like a slip against «илоҳ». The project's
  own corrected ZAD Aqeedah course material uses «Ла илаҳа иллаллоҳ»
  throughout — it transliterates the Arabic *ilāha*, while «илоҳ» is the
  separate Uzbek noun the same book uses in «Аллоҳдан ўзга ҳақ илоҳ йўқ».
  Recorded because the suspicion would otherwise come back.
- **EN's caption fits one topic hashtag** at 1020 of Telegram's 1024, while RU,
  UZ and TJ keep four or five: `fitTagLine` drops the English hashtags first for
  the Cyrillic languages and the topic tags first for English. Noted, not
  changed.

### Also
- **P304** — a detached helper inherits none of `render-reel.ps1`'s setup. The
  Whisper job failed twice while reporting a clean finish: once because
  `-ArgumentList` as an array split the repo's space-containing path so `-File`
  received `C:\QA\Hadith` (P302 again, in a different disguise), and once
  because ffmpeg is not on the system PATH — the render script adds it itself,
  and a helper started outside it never sees that.
- **The 2026-10-26 Stage 3 run is now written down.** It covered 26 library
  rows, its report went to gitignored `out/`, and the container is gone. The
  findings — Tirmidhi #1956 UZ omitting لَكَ, and eight disagreements — now live
  in OPEN_ITEMS' Production queue, which is the only surviving record.

## [2026-10-26a] - the closing period moves outside the guillemet

### Fixed
- **`buildCaption` put the closing period inside the quotation.** Russian,
  Uzbek and Tajik typography all write «…питьё». while a question or
  exclamation mark stays inside: «Кто это?». The stored matn carries its own
  terminal period and the wrapper put it inside, so this shipped on every
  RU/UZ/TJ caption rather than on one reel. Fixed in the wrapper and not in the
  rows, for the reason P236 gives three comments above it: the matn is quoted
  as the source quotes it, and it is the WRAPPER that creates the boundary.
  Editing the stored columns would change quoted source text across many rows
  to undo something we add. `en` and `ar` are untouched - English convention
  differs, Arabic uses other quotation marks, and neither was reported. A
  trailing `..` is left alone so an ellipsis keeps its dots. Future captions
  only; everything published keeps the old form, by the operator's decision.
- **R146 carries the YouTube re-upload.** The blocked EN reel was re-uploaded
  on `vocal-nasheed-07.mp3` - a new video with a new URL, since a blocked one
  cannot be un-blocked. The Nasheed column and the usage table are deliberately
  unchanged: they count per reel, and this is a per-platform fact, with
  Telegram, Instagram and TikTok still carrying the original bed. The published
  original is kept on disk as the canonical file for those three.
- **A third stale OPEN_ITEMS entry closed.** "UZ's four published captions
  quote the pre-correction matn" - they do not, and both Telegram and Instagram
  carry edit markers showing they were corrected at the time. After the
  preflight and random-scene entries yesterday, that is three in two days.

## [2026-10-25c] - the still prompt is written down

### Added
- **`assets/still-prompts/<name>-still.json`, written by
  `generate-image.ps1`** (P250). `generate-scene.ps1` has recorded every
  image-to-video call since P215; the script that makes the STILL those clips
  are animated from recorded nothing at all, so #1903's four still prompts are
  gone - not in a sidecar, not in `animated-reel-scene-prompts.md` (a
  methodology doc, not a log), not in any transcript. Every earlier set
  survived only because the registry note happened to be written in the same
  session as the generation.
- The sidecar carries prompt, model, image size, inference steps, safety
  tolerance, request id, both timestamps, every variant with its file and url,
  and the seed when fal returns one. `chosen` is null until a human picks a
  variant - the script cannot know, and a guess would put a wrong answer where
  a blank is the honest one.
- The folder is tracked and is NOT under `out/`. A sidecar written beside the
  images in `out/refs/` would vanish on a clean checkout, which is the loss
  this prevents.

## [2026-10-25b] - the render records what it rendered, after rendering it

### Fixed
- **P249: both records were written at PICK time.** `.last-used.json` meant an
  aborted render burned the slot - a bed counted as used by a reel that does
  not exist. `<base>-render.json` is worse, because it is evidence: on
  2026-10-24 it was what established which bed a PUBLISHED reel carried, after
  a Content ID claim had been attributed to the wrong bed. A record that a
  failed run can write is not evidence, and `-ValidateOnly` was rewriting it
  while promising in its own output to write nothing - including during that
  day's checks. Both moved to STEP 7b, after the merge returns 0 and after
  P154's three checks that it produced a new file.
- Verified both ways: hashing the sidecar either side of a `-ValidateOnly` run
  shows it untouched, and a full render prints `recorded: ...` after the final
  merge with a fresh timestamp.

### Deferred
- The picker still keys `.last-used.json` by LANE, so there is no per-set or
  per-language rule and the #6570/#13 clash mechanism is live. That changes
  what the picker CHOOSES rather than when it writes, and wants its own change
  with someone watching. Recorded in OPEN_ITEMS rather than quietly half-fixed.

## [2026-10-25a] - a rights block on every bed, and a gate that reads it

### Added
- **`rights` on every audio entry** (P301): status, source, basis, doubt, and a
  `content_id` result. `verified: true` means a human listened to the file and
  has never meant licensed; before this the schema had no field that could.
  All 25 entries backfilled as `unverified` - eight aswati, eight Pixabay, nine
  with no recorded source at all. Not one bed in the library is provably clean,
  which is the honest reading rather than a pessimistic one.
- **`rights_block_reason` in `audit-assets.py`**, read by BOTH `cmd_check` and
  `cmd_list`. P168 moved retirement into the registry precisely because a rule
  living in one caller and not the other meant an asset was drawn and then
  refused, killing the render; a rights rule only the gate knew would repeat
  it. A missing block blocks, an observed Content ID claim blocks and is
  withheld from the picker's list, `contested` blocks, and `unverified` passes
  while printing a RIGHTS line on every use.
- **The Content ID check written into the pipeline** under Audio policy: build
  a test file carrying the bed and nothing else, upload unlisted, read the
  Claims tab, record the result, delete the video. Ten minutes, and the only
  check in that section that is not somebody's assurance.

### Changed
- `aswati-Steady-Motivation.mp3` is blocked and withheld from the picker - the
  one bed with a recorded claim. Live adults beds 16 -> 15. The other seven
  aswati beds stay in circulation by the operator's decision; the exposure is
  printed on every render rather than hidden.

### Fixed
- **The audio policy section claimed the library was "all Pixabay,
  royalty-free, cleared for monetised use".** That is the belief that cost a
  globally blocked reel. Corrected to point at the per-bed `rights` block.
- **A KNOWN GAP that P168 closed** - lane separation described as filename
  convention not enforced in code - was still standing in the same section. A
  doc that overstates what is unsettled costs the same as one that overstates
  what is settled: the next reader stops looking.

## [2026-10-24c] - scene clips validated in Step 0

### Changed
- **`render-reel.ps1` checks scene clips in Step 0.** They were resolved and
  registry-checked inside Step 6, which runs after Step 4 concatenates the
  narration and, on en/ru/ar, after Whisper - so a knowable failure cost a
  narration build first. The new block validates only; Step 6 keeps its own
  resolution and its own P121 gate, so the render path is unchanged and this
  can fail earlier, never differently. Problems are collected and reported
  together, matching Step 0's existing style rather than dying on the first.
- **A comma-bearing clip name is now diagnosed as P302.** `-Scenes a,b` splits
  at the PowerShell parser when typed and stays one string when passed through
  `Start-Process -ArgumentList` with `-File`. The old error printed the whole
  list as a single missing filename, which reads as six missing clips and is
  one mis-bound parameter. Tested three ways: a valid set reports `6 scene
  clip(s) resolved and registry-approved`, a mis-bound list names P302 and says
  to launch with `-Command`, and an unknown name reports as not found - all
  three before Step 4.

### Fixed
- **Two OPEN_ITEMS entries described gaps the repo had already closed**, found
  while picking work from that file. The preflight item claimed no precondition
  was checked up front, when Step 0 already carried the audio registry and the
  draft-sync gate; the random-scene item claimed that path had no registry
  gate, when P237 built one. A backlog that overstates what is missing costs
  the same as one that understates it.

## [2026-10-24b] - P301 corrected: the claim was on an Aswati bed

### Fixed
- **P301 named the wrong bed.** The YouTube Content ID block on #3540 EN was
  attributed to `vocal-nasheed-02.mp3` hours before the evidence was read. The
  leg's `render.json` says `aswati-Steady-Motivation.mp3`, the reel file has not
  been written since 01:28, and the six scene clips were each probed at `audio
  streams 0` - so the matched audio is the Aswati bed by elimination. Pattern
  rewritten, registry notes corrected on all nine affected entries.
- **The Aswati provenance does not survive its own files.** ID3 tags read with
  ffprobe: one SoundCloud rip remixed twice, one instrumental of an existing
  named nasheed, five phone voice memos from one evening, seven under
  `artist=marsadinstitute` and one under another uploader. The Content License
  on disk grants the platform's terms, not rights in the underlying recordings.
- **`lanes` left untouched on every bed.** Emptying the aswati lanes leaves the
  picker with nothing and halts production; that is the operator's decision, not
  a cleanup, and nothing in the library is provably clean to fall back to.

## [2026-10-24a] - #3540 across four languages; a claimed nasheed withdrawn (P300-P303)

### Changed
- **Jami at-Tirmidhi #3540 extended from one clause to the full three-part
  matn** in all six fields. The stored text was only the first address; the
  hadith escalates twice more, and the third - sins nearly filling the earth,
  met by forgiveness of the same measure - is the line the reel is built on.
  Arabic verbatim from the source and confirmed a contiguous substring of it;
  English is sunnah.com's published translation verbatim; Russian, Uzbek and
  Tajik are the operator's. `text_uzbek_latin` derived with
  `derive-uzbek-latin.ts`, never hand-written (D4).
- **قُرَاب restored in all three Cyrillic translations.** The word means nearly
  the fill of a thing, not the full fill. English kept it ("nearly as great as
  the earth"); Russian, Uzbek and Tajik had all flattened it to "filling the
  earth", which claims more than the Arabic does. Now «почти» / «қаријб» /
  «қарибан». Found by `grok-4.7` in the P299 probe - `gemini-4-argon` and
  `gpt-6.1-sol` passed all three 4/4 at HIGH confidence.
- **The measure clause corrected in UZ and RU after the operator read it back.**
  «шунга яқин» and «почти равным ей» both say the forgiveness falls SHORT
  of the sins, inverting the hadith. The near-ness belongs to the sins, not to
  the forgiveness.
- **TJ «сипас» -> «он гоҳ» / «баъд»** (P303), because the voice read it as
  «сипос» - gratitude - inside the quoted divine speech. `text_tajik` patched
  by uuid to match, 466 -> 466 chars, and the row checked letters-only against
  the narration rather than against a retyping.
- **`animated-reel-scene-prompts.md` named Kling 2.6 Pro as the current model.**
  The script default moved to 3.0 Pro on 2026-10-11. Section 6 corrected; the
  2.6 references in section 7 are left, being a record of a decision already
  taken.
- **`vocal-nasheed-02.mp3` withdrawn** (P301) to `out/backgrounds/_claimed/`
  with `lanes: []`, after a YouTube Content ID block. Not `_retired`: that holds
  beds pulled for content reasons, and this is about rights.

### Added
- **Six `t3540-*` scene clips registered and verified**, all 1080x1920 / 24fps /
  10.04s / no audio stream. A sixth was needed for the Uzbek leg: Uzbek TTS
  reads the same matn ~22% slower than English, and `-FitScenes` refused at
  11.93s per clip against 10.042s available. Measured by running the render, not
  estimated, before asking for the money. `t3540-light-push.mp4` is a P293
  camera push-in on a frame the generator would not animate (delta 0.83 -> 10.01).
  The Tajik leg reused all six at 9.689s and cost nothing.

### Fixed
- **P300** - a file transfer reported success and left the previous version in
  place; the corrected translations were written from the stale file and the
  write verified itself correctly against it.
- **P301** - `verified` on an audio entry means a human listened, never that the
  bed is licensed, and the schema has no licence field at all.
- **P302** - a comma-separated `-Scenes` list passed through `Start-Process
  -ArgumentList` with `-File` bound as a single string; the log said "stitching
  1 ordered scene clips" and reported six present files as one missing one.
- **P303** - `TTS_INSTRUCTIONS` has been dead code since P102, so a
  mispronunciation can only be fixed in the text, and a word inside the matn
  quote drags the library row and the caption with it.
- **A stale `draft.txt` blocked the EN render through my own P297 gate**, whose
  advice was backwards: the draft was stale, not the audio. Re-synced byte for
  byte from the narration sidecars, twice, rather than retyped.

### Verified
- `verify-matn-source` 1.00 FOUND on the extended Arabic; `audit-library --row
  3540 --strict` 0 high, 0 warn, 0 info; grade uncontested across Shakir,
  al-Albani, Bashar Awad and Zubair Ali Zai, with at-Tirmidhi's gharib note
  recorded as a description of the isnad's singularity rather than a weakening.
- `check-draft-sync` clean on every leg before its render. Six RU subtitle
  corrections against English's two, all caught by `stt-validate`, including a
  P298 divine-pronoun cue; cue 1 left lowercase deliberately, the Prophet's
  pronoun being the distinction P298 hands to a human.

### Published
- EN, RU, UZ, TJ to Telegram, Instagram, YouTube Shorts and TikTok, one language
  fully published before the next was begun. Spend on the set: $7.44.

## [2026-10-23f] - a model probe, and what four verifiers missed (P299)

### Added
- **`scripts/probe-models.py`** (P299) - measures a model as a Stage 3 pass
  before it is trusted as one. Imports `SYSTEM`, `user_msg` and `_parse` from
  `verify-candidates.py`, so the numbers are anchored to the gate's own prompt
  rather than to a second copy that would drift. Writes only to `out/`, touches
  no row, decides nothing (G1). Four runs per model per language by default
  (P272). `--from-json` scores proposed text before it is written, which is
  P264's shape applied to model selection. Every vendor is reached through
  Abacus RouteLLM, which is OpenAI-compatible, so adding a candidate is a model
  id rather than an integration.

### Measured
- 64 calls over #3540's four translations, on text the operator had already
  reviewed. `gemini-4-argon` 16/16 pass; `gpt-6.1-sol` 16/16 pass (the
  incumbent, as the control); `grok-4.7` 7 fail and 4 transport errors;
  `qwen3.8-max` 8/16 unparseable - it answers in prose, which is a format
  failure, not a capability one.
- **`gemini-4-argon` is cleared as pass B** for whenever the translator moves
  off Anthropic. A third company, and indistinguishable from the incumbent
  across 16 calls. `verify-candidates.py` was not modified.
- **The unanimous pass was wrong.** Our English read "whatever you have done"
  for عَلَى مَا كَانَ فِيكَ - "for whatever was IN you", a state, not a deed.
  Both clean models passed it at HIGH confidence; only `grok-4.7` named it, and
  it correctly PASSED the Tajik, which renders the phrase literally. grok is
  still not usable as pass B - it failed the Russian 4/4 on an idiom that
  carries the meaning - which is the point of the entry: sensitivity and
  gate-fitness came apart for the first time.
- Report preserved at `out/model-probe-calibration-3540-short.{txt,json}`.

### Removed
- **Jami at-Tirmidhi #1899 deleted from `hadith_library`** (72 → 71 rows).
  at-Tirmidhi records the mawquf version as أصح while Shakir and al-Albani
  grade the marfu' sahih. That is a contested grade, and the #5486 precedent
  says a channel publishing only sahih and hasan cannot carry one. Never used
  for a reel. Deleted by uuid under the P290 rule, with a snapshot taken first
  at `out/deleted-1899-20261024T000631Z.json`.

### Noted
- `#6871` was proposed as a candidate twice in one session before
  `fix_patterns.md` and `OPEN_ITEMS.md` were read, both of which already record
  it as #2654's twin and #2654 as published. Nothing in code enforces that
  list - selection reads `list-library.py`, which knows nothing about it.

## [2026-10-23e] - two gates from the backlog (P297, P298)

### Added
- **`check_narration()`** in `check-draft-sync.py` (P297), wired into
  `render-reel.ps1` Step 0. Compares the narrated `story.txt` / `moral.txt`
  against `draft.txt`'s S and M blocks and refuses the render when they differ.
  This is the defect that hit Tirmidhi #2307's Russian and R134 before it, both
  times caught by arithmetic rather than by anything automated. Older sets have
  no sidecars and are noted and skipped.
- **`check_divine_pronoun_case()`** in `stt-validate.py` (P298), MEDIUM. Counts
  capitalised divine pronouns in the source against the subtitles and names the
  cues holding the lowercase form. It does not decide which pronoun refers to
  whom - that is the judgement `restore-srt-casing.py` correctly refuses - it
  only reports that one went missing. `en` and `ru`; uz/tj have no subtitles
  under P078.

Both regression-tested against the exact text that shipped: the narration gate
fails a mismatched draft and passes the live Tajik sidecars; the pronoun gate
fires on the reconstructed pre-fix cue 5 and is clean on the corrected SRT.

## [2026-10-23d] - the draft-sync gate requires the matn contiguously (P294)

### Fixed
- **`scripts/check-draft-sync.py`**: the matn must now appear as a CONTIGUOUS
  substring of the S block. An insertion is reported as its own class - every
  letter present, in order, with text wedged between - rather than as a generic
  mismatch. The 0.90 ratio is kept only to describe how far off a stale draft
  is; it no longer decides.

  Regression tested against the exact Tajik S block that shipped: caught, and
  named as an insertion. The corrected S block passes.

### Corrected
- **P294's claim about that gate was wrong and is now measured.** It said the
  gate would have passed «яъне» at 0.94. The number was never run. Measured:
  0.788, so the old gate would have caught that row. The threshold was a real
  hole on longer matns - a one-word insertion scores >= 0.90 on nine of the
  twelve longest Tajik rows, because the longer the matn the more an insertion
  disappears into the ratio, which is backwards. P294, the R145 tracker note
  and the [2026-10-23b] entry all corrected.

## [2026-10-23c] - Tirmidhi #3540 re-translated (P296)

### Fixed
- **Jami at-Tirmidhi #3540**, RU, UZ and TJ re-translated by the operator after
  both models failed all three independently: «عَلَى مَا كَانَ فِيكَ» and
  «وَلَا أُبَالِي» were missing or narrowed. EN was corrected in the same pass once
  the other three made it the only narrow one. All four scored before writing;
  written by id with `patch_library_row`. The «Мен(га)» parenthetical went with
  the rewrite. `derive-uzbek-latin --number 3540 --commit` reported 1 row,
  confirmed against a 72-row snapshot. Row audits clean.

### Adjudicated
- A failed the Tajik on verb tense while passing non-past renderings in the
  other three languages in the same response. Operator ruled the Tajik stands:
  غَفَرْتُ in a conditional promise carries an assured future sense, and
  «ҳар чӣ дар ту бошад» is concessive rather than a tense error. Recorded per
  P177 - disagreement is the output, and the human gate decides it.

### Corrected
- The assistant attributed the shifting model flags to P280 without
  establishing it. The observation stands; the classification does not.

## [2026-10-23b] - #2307 shipped in four languages (R142-R145, P294-P295)

### Shipped
- **R142-R145 — Jami at-Tirmidhi #2307, adults**, all four platforms each.
  Scene arc: a toy cradle with a faceless straw doll, autumn leaves, a sinking
  sun, an empty mat with a walking stick. Infancy to old age; nothing on screen
  depicts death, because the matn says remember it.

### Found
- **P294 — words added INSIDE the quotation.** The generator appended
  commentary to S in all four languages. Three put it after the closing quote;
  Tajik put «яъне» inside it, which is speech attributed to the Prophet ﷺ that
  he did not say. `lint-content` returned 0 findings. The assistant also
  claimed the day-old draft-sync gate would have passed it at 0.94 - that
  number was never run, and the real figure is 0.788, so that gate would in
  fact have caught this row. The hole was real on longer matns: a one-word
  insertion scores >= 0.90 on nine of the twelve longest Tajik rows.
  Corrected in P294; the gate now requires the matn as a contiguous substring.
- **P295 — the TTS instruction lever worked once and not twice.** P284's
  word-level example fixed `дастон`; the identical fix for `яки` did nothing.
  The edit was reverted rather than left as an instruction that lies. M was
  reworded to «ҳар кадоми мо» instead — legitimate because M is the channel
  speaking, and unavailable in S where the words are the Prophet's ﷺ.

### Notes
- The `book-claim` check added yesterday fired on "Book of Zuhd" and the claim
  was TRUE. Confirmed against the mirror's chapter table — chapterId 36 is
  كتاب الزهد — and reworded to the source's own "Chapters on Zuhd". A check that
  asks you to confirm is working when the confirmation passes.
- RU's story was narrated from the pre-correction text (R134 again), caught by
  arithmetic: 18s against EN's 6s for the same single sentence. The `.txt`
  sidecars now written beside each mp3 made it a file read instead of a
  transcription — P246 effectively closing.
- The scholars-say construction appeared in **all four languages** of one
  hadith. It is a fixed behaviour of the generator, not a recurrence.

## [2026-10-23] - #2307 scene clips registered; motion added in post (P293)

### Added
- **Four scene clips for Jami at-Tirmidhi #2307**, registered in
  `assets/asset-registry.json`, all `verified: true` after the operator watched
  them end to end: `t2307-cradle`, `t2307-leaves`, `t2307-dusk`,
  `t2307-mat-push`.

  The arc is the operator's: a toy cradle with a faceless straw doll, autumn
  leaves, a sinking sun, and an empty mat with a walking stick beside it -
  infancy to old age, with nothing on screen depicting death. The matn says
  *remember* it.

### Fixed
- **`t2307-mat` was a near-frozen frame** out of Kling, twice - frame deltas
  0.83 then 1.34 on a paid re-roll, against 5.05 for the quietest clip that
  worked. Motion added in ffmpeg instead: a 7% push-in, delta 10.99. The
  unmodified original is kept alongside and the registry entry records the
  deltas, the filter and the fact that the motion is not the model's (P293).

## [2026-10-22j] - narrator map entries for the corrected names (P292)

### Fixed
- **`lib/refs.ts`**: added `Hudhayfah ibn al-Yaman` and `Abu Shuraih al-Adawi`
  to `NARRATORS`. `buildRef()` falls back to the stored Latin when a name is
  absent, so without these every Cyrillic caption would have carried a Latin
  name inside a Cyrillic reference line - wrong, and silent, because a fallback
  is not an error. `Abu Dharr` was already mapped.

  Verified through `buildRef` in all four languages; the Latin parenthetical
  that P150 requires is intact.

## [2026-10-22i] - the narrator backlog worked through (P292)

### Fixed
- **Muslim #1005** narrator: Jabir ibn Abdullah -> **Hudhayfah ibn al-Yaman**.
  *Every act of goodness is charity* is Jabir's in **Bukhari 6021**; Muslim 1005
  is Hudhayfah's. The matn and number were Muslim's, the narrator was Bukhari's.
- **Bukhari #6018** (the "honour his neighbour" row) -> **#6019, Abu Shuraih
  al-Adawi**, source_url updated. Our matn is `فَلْيُكْرِمْ جَارَهُ`, which is 6019.
  6018 is Abu Hurairah and says *do not harm* his neighbour. Never produced, so
  no caption carried it.
- **Tirmidhi #1987** narrator: Mu'adh ibn Jabal -> **Abu Dharr**, matching
  `tirmidhi:1987`'s own isnad. Classically both carry it; the citation decides.

All three written with `patch_library_row` (P290), by id. All three audit clean.

### Not defects, closed
- **#31** - Al-Ahnaf bin Qais is the sub-narrator; Abu Bakra is the companion
  and ours is right. The mirror's `narrator` is a lead-in string, not a
  companion field, so this class recurs by design.
- **#2616, both rows** - `locate()` matched them to a Ka'b bin Ujrah hadith
  about unjust rulers. Ours (Mu'adh ibn Jabal) is right.

### Needs doing
- **R090-R093's captions are live with "Jabir ibn Abdullah"** and need editing
  to Hudhayfah ibn al-Yaman on TG / IG / YT. TikTok captions are frozen after
  7 days (P277) and this set is from 2026-09-24.

### Note
R082-R085 were verified by transcribing the published audio - the narrated text
is not on disk (P246) and #6018 had two candidate rows. They shipped "speak good
or stay silent", the correctly-cited row. Nothing to correct there.

## [2026-10-22h] - the health route is live; step 4 points at it again

### Changed
- **`CLAUDE.md` step 4** goes back to `curl -s .../api/health | jq`, now that
  the route exists. Verified live: `{"status":"ok","db":"reachable","ms":197}`,
  and `/api/test` returns 404.
- **OPEN_ITEMS**: the health route and the debug endpoint are closed; the
  absence of a pre-commit hook is recorded as a deliberate decision rather than
  an accident. Everything gates at push, and a pre-commit running that suite
  would tax every commit for a check the push already makes.

### Note
The HV side is `hadith-verifier` `71e5f00` (P291) - the route, the removal, and
the pattern. The P sequence stays global across both repos; HR holds the
frontier at P290.

## [2026-10-22g] - #1469 fixed; a write that hit a second hadith (P290)

### Fixed
- **Bukhari #1469** «сабр(дан)» -> «сабрдан» in all three Uzbek fields,
  verified before writing: A=pass/high, B=pass/high on all four languages.
- **A second row, written by mistake and restored.** The PATCH was keyed on
  `hadith_number=eq.1469`, which matched TWO rows carrying different hadiths,
  and PostgREST updated both. Row `833a2647…` («مَنْ يَتَصَبَّرْ يُصَبِّرْهُ اللَّهُ»)
  took on the other row's Uzbek text. Restored from a 72-row snapshot taken
  earlier for the P269 guard, with the Cyrillic rebuilt via `latinToCyrillic`
  (no flags). Both rows verified correct afterwards; `audit-library --row 1469`
  is clean.

### Added
- **`patch_library_row()`** in `audit-library.py` (P290). Requires a uuid,
  filters on `id`, and raises unless exactly one row comes back. Write by id;
  the number identifies a hadith to a reader, not a row to a database.

### Found, needs a decision
- **Tirmidhi #3540 fails Stage 3 in three languages, independently, on both
  models** - and not because of the parenthesis fix, which is orthogonal. The
  stored RU, UZ and TJ all omit «وَلَا أُبَالِي» ("and I do not mind") and
  «عَلَى مَا كَانَ فِيكَ» ("whatever is in you"). EN carries both and passes.
  The «Мен(га)» fix is therefore HELD: the row needs three re-translations, not
  a bracket removal, and that is a content decision.
- #2616 and #6018 share the duplicate-number trap and both sit in the
  narrator-mismatch backlog - the next thing anyone would fix by number.

## [2026-10-22f] - the pre-flight was checking a route that never existed

### Fixed
- **`CLAUDE.md` step 4** ran `curl -s https://hadithverifier.com/api/health`
  against a route that has never existed in `hadith-verifier`. There is no
  `app/api/health` anywhere in that repo and nothing in it references the path.
  Probed 2026-10-22: `/` returns 200, `/api/health` returns 404. So the session
  pre-flight has reported a failing upstream on every session since the
  checklist was written, and the failure was the checklist.

  Now probes the site root for a status code, with a comment saying plainly
  what that does and does not prove - the deployment is serving; Supabase
  reachability is untested.

### Found, decision open
- **Build a real `/api/health`?** Confirming Supabase is reachable is what the
  pre-flight actually wants to know, and the root-200 check does not give it.
  Recorded in OPEN_ITEMS rather than built: a new public endpoint on a live
  site is the operator's call, not a cleanup.
- **`/api/test` is a public debug endpoint on the live site.** Returns
  `hasSlack` and `slackStart`, the first 30 characters of `SLACK_WEBHOOK_URL`.
  Thirty characters stops short of the token - `https://hooks.slack.com/services/`
  is 33 - so no credential is exposed, but it confirms to any caller that a
  webhook is configured and it is reachable without auth. Delete, gate or keep
  deliberately.

## [2026-10-22e] - #2307 repaired; a check for parenthetical alternates (P289)

### Fixed
- **Jami at-Tirmidhi #2307**, three defects in one row that `audit-library.py`
  passed at 0 findings:
  - UZ «бузовкисини» -> «бузувчисини». Not a word; P268 cannot see it because
    every letter is legal and the shape is not an enumerated orphan suffix.
  - TJ «Сабабкунандаи» (*causer*) -> «Қатъкунандаи» (*cutter-off*), operator's
    choice from three options. هَاذِم is the destroyer; the old text asserted
    the opposite role.
  - TJ «марг(мург)ро» -> «маргро». A parenthetical alternate in a published
    field, where «мург» means *bird*.

  Verified BEFORE writing per P266 - scored with `verify-candidates.py
  --from-json`, A=pass/high and B=pass/high on all four languages, and only
  then written. Previous values kept in `out/2307-before.json`. The Latin was
  re-derived with `--library --number 2307 --commit`, which reported `rows: 1`,
  confirmed against a 72-row before-snapshot. No repeat of P269.

  #2307 has never been produced, so no published caption carried any of this.

### Added
- **`audit-library.py` `embedded-alternate`** (P289, WARN). A parenthesis
  touching a word character on either side is an unresolved alternate; one
  standing free between spaces is a translator's gloss and is not flagged. The
  library separates cleanly on that rule - 13 fields hold a parenthesis, 5 are
  embedded, all 5 are defects, none of the other 8 is.

### Found, needs a language decision
- **Tirmidhi #3540** - «сен **Мен(га)** дуо қилиб»
- **Bukhari #1469** - «Ҳеч кимга **сабр(дан)** яхшироқ»

  Both in `text_uzbek`, `text_uzbek_cyrillic` and `text_uzbek_latin`. #3540 was
  one of the five malformed-token rows repaired on 2026-10-18 and this survived
  that repair, because the repair was looking for a different shape. Left for
  the operator: which reading is meant is a wording judgement, not a defect
  with one mechanical answer.

## [2026-10-22d] - weekly tool check run (Kling 4.0 announced, no API)

### Checked
- **ElevenLabs TTS - CURRENT, by probe rather than release note.** `eleven_v4`
  and `eleven_v4_turbo` both return audio; `eleven_v5` and `eleven_v5_turbo`
  both return `model_not_found`. No v5 exists.
- **Kling 4.0 - ANNOUNCED, NOT CALLABLE.** Live on fal in the playground and
  fal Agent; the model page says API access is coming soon. So
  `fal-ai/kling-video/v3/pro` is still the latest version we can call, and that
  row is accurate rather than behind. Two things recorded for the day it opens:
  the path shape drops the `fal-ai/` prefix entirely (`kling/v4/image-to-video`),
  which is the SECOND instance of the unguarded-path concern already noted for
  `flux-3` and therefore a shape problem rather than a one-off; and at $0.235/s
  for 1080p a four-clip set runs about $9.40 against today's $3.50.
- **FLUX - still BEHIND one major version.** FLUX 3 is callable at
  `blackforestlabs/flux-3/text-to-image`, $0.048 per 1 MP image. Status
  unchanged, now with an endpoint and a price attached to it.
- **ASR - nothing new.** No Scribe v3; the latest is v2 plus a
  `scribe-v2-medical` variant. The 2026-10-15 verdict stands.

Next due 2026-10-29.

## [2026-10-22c] - OPEN_ITEMS reconciled; the draft.txt sync gate built (P282)

### Added
- **`scripts/check-draft-sync.py`** - P282's gate, finally built, and wired
  into `render-reel.ps1` Step 0 ahead of the `-ValidateOnly` exit so the smoke
  test covers it. It does NOT compare against the admin's generated blocks:
  those live in React state and never reach disk. It compares against the
  LIBRARY ROW, which is what the blocks were built from. Two checks - the
  writing system of the S block, and a letters-only comparison against
  `text_<lang>` reported as a ratio.

  The second is the one that matters. A draft holding another language is loud
  and harmless; a stale draft in the RIGHT language is quiet and scored 0.958
  while a whole clause differed. Comparing against the database rather than a
  threshold on the SRT is what separates them.

  Verified four ways against a draft holding the Tajik blocks: `tj` passes on
  an exact quote, `uz` and `ru` fail on the matn at 0.324 and 0.137, `en` fails
  on the writing system before it reaches the database. End to end through
  `render-reel.ps1`: TJ passes and exits, UZ dies before TTS.

### Changed
- **`OPEN_ITEMS.md` reconciled.** It was written 2026-10-18 and went four days
  while nine commits landed, so it still listed #2999, #6009, #527 and #6857 as
  open - all four closed between `350d71b` and `58a10ff`. New dated section
  reconciled against `git log` and this file, marking what closed and what was
  added. The stale per-item lines are marked in place rather than deleted, per
  that file's own rule.

### Found
- **No `pre-commit` hook exists.** `core.hooksPath` is `.githooks` and it holds
  exactly one file, `pre-push`. Every check runs at push time; nothing gates a
  commit. Recorded in OPEN_ITEMS as a decision to take, not a defect to fix.
- The assistant had told the operator no hooks were installed at all, having
  looked only in `.git/hooks`. Third partial search reported as a complete one
  in a single session, after the P283 naming question and the `-ValidateOnly`
  incident.

## [2026-10-22b] - #1488 EN/UZ/TJ shipped; the set's gates built (P283-P287)

### Added
- **`reel-retro.md`** and **Step 17 - Retro** in the pipeline. One entry per
  set, written after the last platform and before the tracker rows. It records
  what had to be said out loud before a defect was caught - corrections of the
  assistant included - so a recurring correction becomes a gate instead of
  being re-explained every session.
- **`audit-docs.py` `check_retro`**: fails when the newest `reel-tracker.md`
  row has no `reel-retro.md` entry. Verified both ways - DRIFT before the rows
  existed, OK after.
- **`lint-content.py` `book-claim`** (P287): WARN when the H block names a book
  or chapter of the collection. Re-ran against both #1488 drafts; both fire.
  Header count moved from CONTENT (5) to (6).
- **`render-reel.ps1`** (P286): refuses when `-Scenes` is passed without
  `-FitScenes` and the arithmetic says clips would actually be dropped. It does
  not second-guess a deliberate full-length render.

### Fixed
- **`render-reel.ps1` `-ValidateOnly`** (P288): was declared in `param()` and
  referenced nowhere else, so the flag documented as "run step 0 and exit"
  performed a full render. Used as a pre-commit smoke test it overwrote the
  published TJ reel locally with three random clips; restored by re-rendering
  with the original parameters. Now exits after the Step 0 checks.
- **`app/api/tts/route.ts`**, `tj.adults`: word-level example pronunciation for
  дастон / дастонат / дастонаш (P284). `Дастонатро` narrated as `Достонатро` -
  your stories for your hands - sentence-initially only, the position P087
  recorded for Uzbek ҳ. Validated by re-narrating the moral alone. The Cyrillic
  was NOT respelled; PATTERN 95 rejects that approach.

### Shipped
- **R139 EN, R140 UZ, R141 TJ - Sunan Abu Dawud #1488, adults.** All four
  platforms each. R138 (RU) shipped earlier the same day.
- All four languages A/B verified against the LIBRARY row (`--library`) after
  the operator asked whether Stage 3 still ran on hand-corrected rows. It had
  not been. A=pass / B=pass at high confidence on all four. TJ first returned
  A=error with an empty body; re-ran unchanged and it passed (P285).

### Found
- **A fabricated book attribution in two languages** (P287). UZ «дуо китобида»
  and TJ «китоби дуо» - the Book of Du'a. Du'a is the *bab*; the *kitab* is
  al-Witr. The library row's `book` column is EMPTY, so both were generated out
  of nothing, and every existing check passed them clean.
- **This CHANGELOG's own 2026-10-22 entry cites references that do not exist**
  (P283): a «§5b collection prefix» section present in no doc, and a tracker
  record of the slug/clip naming split that the tracker does not contain. The
  convention is now written down, in P283 and pipeline Step 11.

### Not built
- `draft.txt` sync gate (P282). It cost a scare in this set - `stt-validate`
  scored correct Russian subtitles at 0.291 because the draft still held the EN
  blocks.

### Notes
- **Integrity against presentation**, settled here: a published reel is
  replaced for a wrong matn, translation, narrator, citation or divine
  attribute; pacing, cover frame and subtitle styling are fixed forward. R138
  (RU) is live showing roughly 2.5 of its 4 clips and was deliberately kept.
- **After `lg`, nothing reopens but an integrity defect.** Not wording
  preference, not a synonym, not a caption/audio phrasing difference.

## [2026-10-22] - Sunan Abu Dawud #1488 RU shipped; a path bug and two gate gaps (P281-P282)

### Fixed
- **`scripts/generate-scene.ps1`**: `$promptDir` is now absolute
  (`Join-Path $repo ...`). It was relative, and `[System.IO.File]::WriteAllText`
  resolves relative paths against `[Environment]::CurrentDirectory`, which
  `Set-Location` does not update - so the sidecar was written to wherever the
  shell started. Introduced by P255's BOM fix; hidden for weeks because the
  shell usually started in the repo (P281).

### Shipped
- **R138 - Sunan Abu Dawud #1488, RU, adults.** 22.95s, 3.74 MB, 1080x1920,
  four new Kling v3 Pro clips (`ad1488-mat/raised/night/dawn`), nasheed
  `aswati-Peaceful-Contemplation.mp3`, subtitles burned. Live on TG/IG/YT/TikTok.
- Stage 3 blocked this row before production: `حَيِيٌّ` was rendered "Kind"/«Добрый»
  in EN and RU, losing the حيي/يستحيي echo the hadith is built on, and UZ/TJ
  added supplication the matn does not state. All four re-translated, 8/8 after.
- Four clips registered in `assets/asset-registry.json`, `verified: true` after
  the operator watched them. All probe 10.04s / 1080x1920 / 24fps / audio:0.

### Found, not built
- **`draft.txt` has no sync gate** (P282). `stt-validate` scored subtitles
  against a stale draft at 0.958 while a whole clause differed, and the H block
  still carried «побуждающими Его» - a theological error already fixed in the
  admin, and H becomes the caption.
- **Divine-pronoun casing is unchecked** (P282). Whisper returned «раб его» /
  «проси его»; the casing restorer correctly declined, and `lint-content.py`
  checks which divine name is used, not the case of a pronoun referring to Him.

### Notes
- The scene-prompt JSON was revised at the religious gate before any spend:
  close-ups of hands were replaced after the pipeline doc's warning that
  generators fumble hands, and the arc was re-cut to bookend on the prayer mat.
  Scenes 2 and 3 depict two different anonymous people, a man and a woman,
  both silhouetted - `عَبْدِهِ` is generic.
- A dawn still with a vertical shaft of light descending onto the mat was
  rejected as reading like a depicted response.
- Slug is `sunan-abu-dawud-1488` (admin derivation), clips are `ad1488-*`
  (§5b collection prefix). The two conventions differ and the tracker already
  records that inconsistency.

## [2026-10-19] - the disagreement backlog re-read under Sol (P280)

### Fixed
- **#13**: the added qualifier "true believer" removed from all four languages
  («истинно», «ҳақиқий», «ҳақиқӣ», and English's "truly"). `لاَ يُؤْمِنُ أَحَدُكُمْ`
  is flat; the qualifier is the classical نفي الكمال softening, which is
  commentary and not the matn.
- **#2759**: `عز وجل` restored in RU, UZ and TJ; UZ «кечаги гуноҳкор» (which
  reads as *yesterday's* sinner) replaced, restoring the day/night symmetry;
  UZ «очур» (opens) put back to «чўзади» (extends) for `يَبْسُطُ يَدَهُ`; RU clause
  structure restored so the sinner repents rather than Allah accepting.
- Both verified 8/8 before the write. Latin re-derived, audit 0 high 0 warn.

### Resolved by the model swap
- **#2628** is now a clean 8/8 under Sol. It was a disagreement only because
  terra was pass B. The swap paid for itself on the first batch.

### Measured
- Of the eight open disagreements: 1 resolved by the swap, 2 were real, 5 were
  **A flagging Tajik while passing the identical issue in Uzbek** (P280). On
  #2963 A listed the same defect against the Uzbek and still passed it. The
  verdicts move by language inside one response; the issue lists are sound.

### Notes
- Third P108 instance in two days: the re-translation broke two things that
  were already correct in the row it replaced.
- The «очур»/«чўзади» swap passed both models and was caught by the operator
  reading it. A model comparison let a weaker verb through; a speaker did not.

## [2026-10-18i] - pre-gate backlog closed

### Fixed
- **Sahih al-Bukhari #1417 (EN)**: "Protect yourself" -> "Protect
  yourselves". `اتَّقُوا` is a plural imperative; both models flagged it, same
  reason, `agreement=fail` rather than a split. Verified 8/8 before the write.
- Its matn is COMPLETE - the mirror's quoted portion matches the stored 41
  characters exactly. The first pre-gate row that was not truncated.
- `text_arabic` untouched, so `matn_screened_at` stands; EN-only change, so no
  Latin re-derive.

### Closed
- **The pre-gate backlog (P278).** All ten hadiths published before the gate
  existed are now checked: 7 carried a defect, 3 were clean (Abu Dawud #3641,
  Abu Dawud #1479, Muslim #482).
- #1417's captions stand: singular-for-plural is a grammatical error, not a
  false statement of what was said - incomplete, not incorrect.

### Notes
- Narrator checked against the mirror isnad: stored "Adiy ibn Hatim" vs the
  mirror's "Adi ibn Hatim" - a romanisation variant, not a mismatch.
- No new P-number for #1417: one word is a fix, not a pattern.

## [2026-10-18h] - the pre-gate sweep, and Bukhari #1 (P277-P279)

### Fixed
- **Sahih al-Bukhari #1**: matn 34 -> 199 chars. The stored row was the opening
  phrase only; restored `وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى` and the hijra clause.
  All four translations re-done: every one had lost `إِنَّمَا`'s restrictive
  force ("only"), and three carried an invented verb where the Arabic is a
  nominal sentence. Verified 8/8 before the write; Latin re-derived; mirror
  re-screened FOUND 1.00 on the new text.

### Measured
- **Pre-gate sweep (P278).** R042 (2026-08-25) is the first reel gated before
  production. Of 134 tracked reels, 38 predate it, covering 10 hadith.
  **7 of those 10 carried a defect**; the three clean are Abu Dawud #3641,
  Abu Dawud #1479 and Muslim #482. Bukhari #1417 (EN) is now the only pre-gate
  row still open.

### Ruled
- P261 extended: where "one complete admonition" and "the complete narration"
  differ, take the NARRATION. #1 is the first case where they diverged.
- Published captions on TikTok: the platform freezes them after 7 days (P277).
  The 2026-10-17 rule is amended to "incorrect gets fixed where the platform
  allows, pinned-comment correction where it does not." Both #527 Tajik reels
  carry a pinned correction.

### Notes
- The #1 re-translation reproduced the Russian defect it was meant to fix
  (P108), and the assistant's own proposed Russian was worse than the text it
  replaced - Russian has no present-tense copula, so the verb is grammatical
  necessity, not interpolation. A third model's wording was adopted.
- **#1 has no Tier 1 confirmation** - mirror only, as sunnah.com and Dorar were
  unreachable from this session. Owed.

## [2026-10-18g] - last two A/B fails closed (P276)

### Fixed
- #6857 RU: «ростовщичество» -> «поедание ростовщического дохода» for
  وَأَكْلُ الرِّبَا. The same Russian sentence already rendered the identical
  construction correctly one item later («поедание имущества сироты»).
- #527 TJ: «беҳтарин» (best) -> «маҳбубтар» (most beloved) for
  أَحَبُّ إِلَى اللَّهِ. EN, RU and UZ all carried beloved-ness; TJ alone did not.
- Both verified with `--from-json` before the write. #6857 now 8/8.

### Ruled
- **A dialogue matn keeps its speech attributions (قال / قلت) in every
  language.** From purpose.md: fabricated hadith circulate as free-floating
  aphorisms, so the stripped form is the shape the channel exists to counter.
- **Not retrofitted into #527**, which is published across eight reels. Errors
  are corrected in shipped content; a one-hour-old style ruling is not.
- Published captions: #6857 RU is incomplete, not incorrect -> stands.
  #527 TJ is incorrect -> R037 and R041 captions need «беҳтарин» ->
  «маҳбубтар» on all four platforms.

### Measured, not built
- 11 of 72 rows have a speech verb in `text_arabic`; only #527 fails to carry
  it through. A library check is not worth the pattern-maintenance burden.
- The probe itself produced a false positive on #463 in all three languages,
  including **U+04AF written for U+04EF** - the P262 substitution, committed
  inside a check (P276).

### Proposed
- Lint the checks' own regexes against `ALPHABETS`: a pattern containing a
  letter outside its target alphabet can never match. Would have caught it.

## [2026-10-18f] - pass B: gpt-5.6-terra -> gpt-6.1-sol (P275)

### Changed
- `verify-candidates.py`: `MODEL_B = 'gpt-6.1-sol'` (was `gpt-5.6-terra`),
  docstring updated with the measurement behind it.
- `probe-passb.py`: `DEFAULT_MODEL` follows, so the probe tests what is live.

### Measured
- `probe-passb.py` against 4 candidates, 4 runs each, 128 calls:
  - all four models: 4/4 on every genuine faithfulness defect (invented
    action, invented ranking, invented simile, dual->singular change).
  - **gpt-6-luna DISQUALIFIED** - false-failed CLEAN Russian 4 of 4.
  - gpt-5.6-terra - false-failed clean Russian 1 of 4; never named the lost
    U+04E3 in the Tajik case (0 of 4).
  - gpt-6.1-sol, gpt-6-astra - no false failures; named the diacritic 4/4.
- Smoke-tested live on #6009: with sol as B, RU and TJ agree clean where
  terra failed both.

### Corrected
- **P273 was wrong** and is marked as such in place. The Uzbek probe case
  («Аллоҳ»->«Худо») tests a CONVENTION, not faithfulness: `lint-content.py`
  catches it deterministically at FAIL (`DIVINE_SUBSTITUTES`), P120 puts
  conventions outside Stage 3, no library row has ever contained it, and
  `verify-candidates.py`'s docstring (lines 15-23) already documented the
  behaviour with the correct explanation. Every candidate model does the same
  thing, and terra is the only one that catches it at all.

### Notes
- This probe cannot separate sol from astra - identical in every cell. Sol
  chosen as current-generation with independent (n=1) evidence behind it.
- No row re-verification is implied: the rows gated under terra were gated on
  faithfulness classes where terra scored 4/4.

## [2026-10-18e] - terra fails the pass-B probe on Uzbek (P273-P274)

### Measured
- `probe-passb.py --model gpt-5.6-terra`, 4 consecutive runs:
  - **uz planted: PASSED 2 of 4.** The planted defect is «Аллоҳ» -> «Худо»
    (R025 divine-name substitution). terra is blind to it half the time.
  - ru clean: FAILED 1 of 4 - noisy on clean Russian.
  - en, tj: consistent across all four runs.
  - **Run 1 alone was a clean sweep.** A single pass would have certified
    terra in all four languages.

### Ruled
- **terra does not gate Uzbek.** A 50% miss rate on the divine-name class is
  false confidence, not a weak gate.
- No model decision on a single pass. N runs, spread reported. This retires
  the reading of Sol's 4/4 falsification result as a calibration - it was one
  sample and is now re-opened.

### Notes
- The Tajik probe case plants TWO defects (invented simile + lost U+04E3) and
  scores one verdict. terra reported the simile 4/4 and the diacritic 0/4, so
  its clean Tajik score tests nothing about the orthography class (P274).
- Same flaw in Stage 3's `agreement`, which is computed from verdicts: two
  models can "agree" on fail for different reasons. #6009 is a live example.
- P272's entry corrected: `probe-passb.py` already documented run-to-run
  non-determinism. The new part is that it applies at the issue level.

## [2026-10-18d] - #6009 closed; two findings about the gate itself (P271-P272)

### Fixed
- #6009: RU «держал его зубами, пока не выбрался» -> «взял его в рот»
  (بِفِيهِ is *mouth*, and the Arabic does not narrate climbing out);
  TJ «бархоста» removed (an action absent from the matn); UZ closing line
  restored the Arabic image - «Ҳўл жигарли ҳар бир жонзотга [қилинган
  яхшиликда] ажр бордир» for فِي كُلِّ ذَاتِ كَبِدٍ رَطْبَةٍ أَجْرٌ, which UZ alone
  had generalised away while EN, RU and TJ all kept it.
- The interpretive gloss is now bracketed in RU and UZ, matching the
  convention TJ was already using («[некӣ ба]»).
- `text_arabic` untouched, so `matn_screened_at` (2026-09-05) stands.

### Ruled (Stage 4)
- The "kindness done to" gloss: KEPT, bracketed. Cutting it would let the
  Uzbek read as the reward going to the animal.
- `ﷺ` after "O Messenger of Allah" in EN: KEPT. A convention, and P120 puts
  conventions in `lint-content.py`, not Stage 3.
- "Tongue out" for يَلْهَثُ: KEPT in all three languages.

### Notes
- An earlier claim here that the tongue-out renderings were additions was
  WITHDRAWN and is now a recorded disagreement, not a defect: يلهث carries
  tongue-protrusion lexically, model B holds otherwise, and P177 says that
  split is the output.
- Bracketing a gloss does NOT clear the Stage 3 finding - the models score
  content, not typography (P271). All three rulings will re-fire on every
  future run; there is no waiver mechanism. NOT BUILT.
- Stage 3 is not reproducible at the issue level (P272): A flagged the Uzbek
  tongue-out on the second run and not the first, with that sentence
  unchanged between them. A single run is a sample. This blocks reading the
  pending terra calibration from one pass.
- `audit-library.py`: 0 high, 0 warn, 4 info.

## [2026-10-18c] - #2999 closed; a check for malformed Cyrillic tokens (P268-P270)

### Fixed
- #2999: 126 -> 210 chars. Restored `وَلَيْسَ ذَاكَ لِأَحَدٍ إِلَّا لِلْمُؤْمِنِ` and
  `فَكَانَ خَيْرًا لَهُ` after BOTH `شَكَرَ` and `صَبَرَ`. Confirmed against Dorar
  (al-Arna'ut: إسناده صحيح على شرط مسلم) and the mirror at idInBook=7314.
  Re-translated, scored 8/8 with `--from-json` BEFORE apply, re-screened.
- Five malformed Uzbek Cyrillic tokens, all in live rows: #4250 `ёъқ`->`йўқ`,
  #2699 `ёъл`/`ёълни`->`йўл`/`йўлни`, #38 `туца`->`тутса`, #3540
  `юбора-ман`->`юбораман`, #2734 `банд аси`->`бандаси`.

### Added
- `check_malformed_tokens` in `audit-library.py` (P268). Four orthographic
  impossibilities - `ёъ`, `ц` in a matn, a hyphen before a personal ending, a
  bound morpheme standing alone. No dictionary, no model call. Measured against
  the library before being written: 6 hits, 6 real, 0 false positives. A fifth
  rule returned 0 and was dropped rather than shipped unexercised. WARN on
  first outing.

### Notes
- `audit-library.py`: 6 warn -> 0 warn. 0 high, 4 info.
- `derive-uzbek-latin.ts --row` is silently ignored and writes the whole
  library (P269). No damage - the transform is deterministic and all 72 rows
  were proven byte-identical - but the flag is not a safety device.
- Stage 4 unchanged: `matn_verified_at` stays null on every row (P265).
- Open, needs an Uzbek reader: #2307 «Лаззатлар бузовкисини», likely a garbling
  of «лаззатларни бузувчини». Every token is a possible word, so no mechanical
  check can reach it.

## [2026-10-18b] - VOWEL 0 library-wide; #1151 was a constructed sentence (P267)

### Fixed
- #223: `الطَّهُورُ` -> `الطُّهُورُ`. One codepoint; sunnah.com/muslim:223
  prints damma. Length unchanged.
- #463: `انْتُقِصَ` (passive) -> `انتَقَصَ` (active). Two codepoints; Dorar
  prints fatha on both the ta and the qaf and gives the grammar - the verb is
  active, its subject is `شيءٌ`. Length unchanged.
- #82: restored `إِنَّ` and the accusative `تَرْكَ` it governs, matching the
  cited source. NOT originally a defect - without `إنّ` the nominative was
  correct, and whoever shortened the row had adjusted the grammar properly.
  Fixed anyway so it stops flagging forever: a permanent false alarm teaches
  people to skim the report.
- #1151: 86 -> 363 chars. The stored line welded `يُضَاعَفُ` directly onto
  `إِلَّا الصَّوْمَ`, removing `الحسنة عشر أمثالها إلى سبعمائة ضعف` and
  `قال الله عز وجل` - a grammatical sentence that appears in no narration, and
  the loss of the divine-speech attribution that makes it a hadith qudsi.
  Confirmed against Dorar and the mirror.

### Notes
- VOWEL discrepancies across the library: 3 -> 0. EXACT 32 -> 34.
- The three excerpt rows resolved to three severities, and the contiguity
  score did not predict the order: #1151 (0.58) worst, #2999 (0.47) internally
  clipped and STILL OPEN, #5971 (0.56) fine.
- FIRST use of verify-before-write (P266): #1151 scored 8/8 with --from-json
  before --apply. In that window the Uzbek was caught rendering خلوف as
  «оғиз қокисининг ҳиди» - not a word, and inconsistent with #1894's
  «оғиз ҳиди». Corrected, re-verified, then applied.
- The NFC trap caught a second time, in the probes written to guard against
  it. Fix: probe on the consonant skeleton, which is immune to mark order by
  construction.

## [2026-10-18] - verify-before-write and the narrator check (P266)

### Added
- `verify-candidates.py --from-json [PATH]`: score proposed translations
  against the matn WITHOUT writing them to the row first. Closes P264 - a
  library re-translation no longer has to overwrite a shipped row to be
  checked. Refuses --commit, defaults to out/candidate-translations.json,
  honours --row. Reproduces the database run's verdicts for #6009.
- Narrator comparison in `audit-diacritics.py`. verify-matn-source.py's limit
  2 says it checks the text only, not the narrator; #3104 stored a plausible
  matn under the wrong one and nothing automated could see it. The mirror
  entry is already located, so the check is nearly free. 11 unit cases.

### Fixed
- Two false positives in the narrator matcher, found on its first run and
  fixed before the output was read as findings: `Hurairah`/`Hurayrah` (ai/ay),
  and a regex that replaced a backtick with a SPACE, splitting ``Mut`im`` into
  'mut' + 'im' and destroying the match. Apostrophes and backticks mark a
  hamza or ayn inside a word; they are not separators. 7 findings -> 5.

### Notes
- No narrator misattribution found in the library. The five survivors are
  multi-chain or companion-vs-immediate-narrator cases (#31, #1987, #6018,
  #1005, #2616) and need a human reading, not a fix.
- The mirror's narrator field holds the IMMEDIATE narrator; our column holds
  the COMPANION. That is a systematic source of benign mismatch - #31 is
  exactly that and is almost certainly correct as stored.

## [2026-10-17h] - matn_screened_at vs matn_verified_at standard set (P265)

### Changed
- STANDARD SET. matn_screened_at = audit-diacritics EXACT against the mirror,
  found by verify-matn-source, citation and narrator confirmed - reproducible
  by machine, no Arabic needed. matn_verified_at = a person who reads Arabic
  compared the matn to the cited source. Nobody on the project reads Arabic, so
  that column stays NULL until a reader reviews. P151 had defined the verified
  stamp as human Arabic reading, which nobody could perform; the stamp was
  therefore being applied on grounds never written down. P265.
- The five repaired rows (#8, #1520, #5185, #1894, #1773) are now
  matn_screened_at = 2026-10-18, matn_verified_at = NULL.

### Corrected
- Two claims made earlier today and checked wrong. (1) The two columns were NOT
  conflated: 48 screened, 21 verified, only 3 carry both, and #5185 was
  verified without ever being screened. (2) translate-candidates.py should NOT
  clear matn_screened_at - that path changes translations, and screening is
  about the Arabic.

### Known issues
- STALE SCREENING STAMPS. matn_screened_at records that text matched the mirror
  on a date, with nothing linking the stamp to the text it screened. #8, #1520
  and #1894 each carried a 2026-09-05 screening for Arabic replaced this
  morning. No script writes text_arabic, so there is no code path to patch: the
  fix is to store a hash of the screened text and flag any row whose current
  text does not match it. NOT BUILT.
- The other 21 matn_verified_at rows are unreviewed under the new standard.

### Notes
- A second model reader was calibrated rather than trusted: given four rows,
  two of them historical known-bad values from P142 and unlabelled, both traps
  being authentic famous sayings on the wrong reference. It caught both,
  including a narrator error that was never hinted at, and passed both
  controls. Agreement on easy cases is free; the adversarial test is what the
  reliance rests on.

## [2026-10-17g] - #6009 partially fixed, verify-before-write gap, caption rule

### Changed
- #6009: matn was already correct and complete (mirror 5781, offset 228). The
  two defects the sweep named are fixed in all four languages - يأكل الثرى is
  now 'eating the moist earth' rather than 'licking mud', and فشكر الله له is
  'Allah thanked him' rather than 'accepted' or 'was pleased'. Softening a
  divine act was the serious one.
- CAPTION RULE, set by the operator: a published caption whose text is
  INCOMPLETE is left as it stands - a partial quotation of a sahih hadith,
  correctly attributed, is not a fabrication, and editing live posts across
  four platforms carries its own risk. A caption whose text is INCORRECT is
  corrected. Under that rule #8, #5185, #1894 and #1773 stay as published, and
  #1520's four posts are corrected: they carried لَكُنَّ, a wrong word, with
  '(for women)' built on top of it.

### Known issues
- #6009 OPEN. The re-translation introduced new defects while fixing the old
  ones: ﷺ inserted in the English, three additions in the Russian (climbing
  out, 'teeth' for بفيه, 'tongue out' for يلهث), 'moist liver' dropped from the
  Uzbek, «бархоста» added in the Tajik. Needs one more pass with the operator
  on RU/UZ/TJ. matn_verified_at is null so the row cannot pass Stage 4.
- P264: there is no way to Stage-3 a library re-translation before writing it.
  verify-candidates.py --library reads the DATABASE, so a shipped row must pass
  through an unverified state to be checked. Fix would be a --from-json mode
  that scores the proposed text without touching the row. Not yet built.

## [2026-10-17f] - Bukhari #1773 translations corrected, P263

### Fixed
- #1773's matn was already correct and complete - no SQL. The translations
  inserted 'sins' where لما بينهما says only 'for what is between them', and
  'next/subsequent' umrah where the Arabic says العمرة إلى العمرة. The stored
  English had also dropped إلى العمرة entirely, reading 'Umra is an expiation'
  with no 'to Umra'. Re-translated; Uzbek and Tajik supplied by the operator
  verbatim. Stage 3 8/8 pass - #1773 comes off the DISAGREE list. P263.

### Notes
- A Stage 3 'disagree' is not always a disagreement. Here A and B objected to
  the SAME insertion ('sins') in DIFFERENT columns, which aggregates to a split
  verdict while nothing is actually in dispute. Read what the models said
  before invoking P177. The remaining disagreements from the sweep should be
  re-read this way.
- Per-language attention is uneven: «следующей» in Russian is the same addition
  as «навбатӣ» in Tajik, and both models passed the Russian. A clean verdict on
  one column is not evidence the same defect is absent from a sibling.
- Re-translation improved English and Russian and REGRESSED Uzbek and Tajik
  (a larger gloss, an unbracketed 'sins', and كفارة with one ф). The P108
  shape: regenerating is a re-roll with its own defects, not a fix.
- check_out_of_alphabet (P262) ran on the operator's text as its first real
  input: zero findings.
- OPEN: مبرور now reads four ways - EN 'the accepted Hajj', RU «мабрур»
  transliterated, UZ «мақбул», TJ «мақбул». Russian is the odd one out.

## [2026-10-17e] - Bukhari #1894 restored, out-of-alphabet check added, P262

### Added
- `check_out_of_alphabet` in audit-library.py: a Cyrillic letter that is not in
  the target language's alphabet. HOMOGLYPHS (R027) only catches LATIN
  intruders and TJ_LETTERS only checks that Tajik letters are PRESENT, so a
  wrong Cyrillic letter passes both - verified by reading the script, not
  assumed. The dangerous pair is Uzbek ў (U+045E) against Tajik ӯ (U+04EF):
  same shape, and the two columns sit beside each other in every row.
  Unit-checked on four cases; library-wide scan returns zero findings over 72
  rows. WARN on first outing, per the precedent check_ha_formulas records. P262.

### Fixed
- Bukhari #1894 stored 18 characters - 'Fasting is a shield' - where the matn
  continues through restraint of speech, the reply when provoked, the oath, the
  musk simile and 'fasting is for Me, and I shall reward it'. 18 -> 370 chars,
  the largest restoration so far. All four translations stopped at the same two
  words, so the row was internally consistent and Stage 3 had nothing to catch.
- #1894 Tajik: «бехудагӣ» (absent-mindedness) for يرفث, which is obscene
  speech. Both models failed it unanimously - a defect, not a disagreement.
- #1894 Uzbek: «оғиз ҳидини» put the accusative on the sentence's subject.
  Grammar, which Stage 3 cannot see by design (P120).
- A hand-edit of mine typed ү (U+04AF) for ӯ (U+04EF) in the Tajik. Caught by
  reading the output back before signing, and by nothing else - which is why
  the check above now exists.

### Notes
- The mirror's idInBook=1894 is a different hadith; ours sits at 1826, offset
  68, and our own #1903 sits at 1835 with the same offset - the citation was
  confirmed from internal data before any source was fetched.

## [2026-10-17d] - Bukhari #5185 restored, extent convention set, P261

### Fixed
- Bukhari #5185 stored 32 characters - the opening imperative of the hadith -
  with the rib simile, which is its whole substance, cut off. All four
  translations read 'Treat women well.' and stopped, so the row was internally
  consistent and Stage 3 had nothing to catch. The row was STAMPED
  matn_verified_at on 2026-09-05; that is the third verified row found holding
  defective content. 32 -> 225 chars, re-translated, Latin re-derived, Stage 3
  8/8 pass. P261.

### Changed
- CONVENTION, set by the operator: text_arabic holds ONE COMPLETE admonition
  from the cited narration, never a clipped one. Where a narration carries two
  (bukhari:5185 pairs a neighbour clause with the women/rib passage), store the
  one the row is about, in full, and let the citation locate it. This also
  governs the excerpt rows #2999, #1151 and #5971.
- #5185 Uzbek: «васият қилинглар» aimed the counsel at women via the dative
  -га, where the Arabic aims it at the listener about women; EN, RU and TJ all
  read it the second way. Corrected to «нисбатан яхши муомалада бўлинглар».
  Flagged independently by model B and by the operator, then re-verified from
  scratch - a correction to the text, not a disagreement settled by preferring
  a model (P177).

### Notes
- #5185 was surfaced by three independent structural checks with no model
  judgement involved: en/ar ratio 0.53, a 0.67 partial from
  verify-matn-source.py, and the A/B sweep.

## [2026-10-17c] - audit-diacritics.py, first verify-matn-source run, P260

### Added
- `scripts/audit-diacritics.py`. Nothing compared our stored vowel marks
  against a source: Stage 3 asks whether the translation matches the matn, and
  verify-matn-source.py normalises diacritics away by design, so #1520's
  damma-for-kasra was invisible to both. This matches on the consonantal
  skeleton, then compares marks within the located span, and classifies the
  result so the noise separates from the signal: EXACT 32, PUNCTUATION 5,
  ORTHOGRAPHIC 19, VOWEL 3, LETTER 0, NOT FOUND 13 over 72 rows. P260.
- Ran `verify-matn-source.py --mirror` for the first time since it was written:
  66 found, 3 partial, 3 missing. The 3 missing are all Musnad Ahmad, which the
  mirror README says is incomplete for chapters 8-30. Partial: #1899, #2616,
  #5185. Excerpt flags (matn scattered, not contiguous): #2999, #1151, #5971.

### Fixed
- Three bugs in audit-diacritics.py, each found by reading the SHAPE of its own
  output rather than the content. It reported 56 differences, then 36, then 3.
  (1) combining-mark order: our DB is NFC, the mirror is not, so every letter
  carrying both shadda and fatha mismatched. (2) failed alignment fell back to
  comparing against the isnad, giving 'first diff at char 0' across half the
  library. (3) the span ended at the last consonant, clipping the final i'rab
  vowel off the mirror side - 31 of 36 VOWEL hits, all at the last character.

### Notes
- The three VOWEL rows (#463 passive/active, #223 tahur/tuhur, #82
  nominative/accusative) are a worklist, not verdicts. The mirror is a
  third-party scrape (P145); they need a Tier-1 source the way #1520 got one.
- Not wired into the pre-push gate yet: --strict would block every push until
  those three are resolved.

## [2026-10-17b] - Bukhari #1520 diacritic + matn, empty Uzbek Latin backfill, P259

### Fixed
- Bukhari #1520 stored `lakunna` (kaf with damma, 'for you women') where the
  source reads `lakinna` (kaf with kasra, 'but'), and the matn was cut to the
  tail of the answer - Aisha's question and the opening 'la' were missing. The
  two defects concealed each other and all four translations compensated with a
  '(for women)' gloss. Matn restored to 130 chars, re-translated from it, Latin
  re-derived. Stage 3: 8/8 pass, and all four glosses disappeared untouched.
  Verified against sunnah.com/bukhari:1520 and the local mirror. P259.
- Six library row-writes had Uzbek Cyrillic with a COMPLETELY EMPTY Latin and
  legacy column: #463, #1899, #3104, #2616 (two rows, duplicate number) and a
  stale Latin on #6446. This is the P160 symptom, never backfilled. All derived
  and verified in step.
- #82's legacy `text_uzbek` held CYRILLIC, a P097 violation in a column the app
  reads. Re-derived.

### Added
- P259's detector: a parenthetical gloss in a translation can be load-bearing,
  supplying context a truncated matn no longer carries. 9 of 72 rows carry one;
  the signal is a gloss supplying CONTENT, not a grammatical particle. Ranked
  queue: #1521, #1773, #1894.

### Corrected
- P257's extent heuristic: a high en/ar ratio means LOOK HERE, not THIS IS
  TRUNCATED. #1520 ran 3.02 because of an explanatory parenthetical, not missing
  content. It is a sort order for attention, not a verdict.

## [2026-10-17] - Bukhari #8 matn restored, P258 silent-write fix

### Fixed
- `--apply` reported writing four columns of Bukhari #8 to `hadith_library` and
  wrote none of them. `apply_from_json()` was candidates-only by design and said
  so in its docstring, but `main()` dropped `args.library` instead of refusing
  it, so the write aimed a library id at `hadith_candidates` and matched no row.
  PostgREST answers an unmatched PATCH with 200 and `[]`, so nothing raised.
  `sb_patch` now fails on an empty representation, which closes the class, and
  `apply_from_json` honours `--library`, clearing `matn_verified_at` per P151.
  This is the P177 integrity path, so the no-op landed where it cost most. P258.

### Changed
- Bukhari #8 `text_arabic` restored from 31 chars to the full matn (184), matn
  only and no isnad, per the convention every one of the 22 human-verified rows
  follows. Verified against two independent sources that agree: sunnah.com's
  bukhari:8, which is the row's own cited `source_url`, and the local
  hadith-json mirror at idInBook=8. Both give the ending as Hajj BEFORE fasting
  Ramadan - the reverse of the order all four translations carried.
- #8 re-translated from the corrected Arabic; Uzbek Latin and the legacy column
  re-derived. Three translator interpolations were removed before apply, each
  flagged by a model and each absent from the Arabic: a bracketed noun in RU, an
  intensifier on iqam as-salah in UZ, and 'true' deity plus 'month of' in TJ.
  Stage 3 re-run after the edits: 8/8 pass, zero disagreement.

### Corrected
- P257 overstated its selector claim. A default `--library` run skips the rows a
  human has STAMPED, not 'the rows that have shipped': 13 of 36 used rows are
  stamped, 23 are null. The 13 skipped include #1903 and #527, which both carry
  real defects.

### Added
- P257: the gate cannot see EXTENT either. Rows with shorter Arabic than #8
  passed (#1894 at 18 chars, #1005 at 24, #1479 at 28) because their
  translations are equally short. A character count on `text_arabic` is a cheap
  independent signal the models cannot supply.

## [2026-10-16] — Per-bed nasheed gain, publishing procedure, P249-P251

### Fixed
- All 17 scene-prompt sidecars carried a UTF-8 BOM and the pre-push JSON gate
  had been blocking every push, with the repo 34 commits ahead of origin.
  `generate-scene.ps1` wrote them with `Set-Content -Encoding UTF8`; P186 had
  already fixed the same idiom in `render-reel.ps1` and this writer was left
  behind. BOMs stripped, writer switched to `WriteAllText`. P255.
- Cyrillic from piped child processes arrived as mojibake, so the RU/UZ/TJ
  Whisper cues and stt-lint findings were unreadable in the console. P100 set
  `PYTHONIOENCODING` on the child; PowerShell decodes piped bytes with
  `[Console]::OutputEncoding` (CP437 on PS 5.1), which nothing set. Now saved,
  set to UTF-8 and restored around both piped calls in `render-reel.ps1`. P252.
- The eight `aswati-*` beds sat under-audible in the mix. The adults mix is one
  level for every bed (narration 1.4 / nasheed 0.12, P171) and the masters are
  not one loudness: measured -13.35 to -20.22 LUFS against `light-of-my-heart-bg`
  at -13.38, the bed 0.12 was tuned on. Added an optional `gain` to the
  registry's audio entries; `render-reel.ps1` multiplies 0.12 by it and records
  `nasheedVol` in the sidecar. Absent means 1.0, so no other bed changes. Derived
  per track rather than applied as one bump - Gentle-Reflection needed 2.20,
  Rising-Hope 1.00. P251.
- Mix volume is formatted with InvariantCulture before reaching the filter graph;
  a comma-decimal locale would have emitted `volume=0,2640`.

### Changed
- First Stage 3 A/B run over the shipped library (P257). 34 rows, 35 verdicts,
  19 pass / 4 fail / 12 disagree — 46% not clean, behind 137 published reels.
  Findings separate into real fidelity defects, a TRUNCATED stored matn (#8,
  visible to viewers because the caption prints text_arabic), and structural
  isnad noise. Split-matn rows (#6018) pass by construction and the gate cannot
  see them. Dry runs only; 16 rows queued in OPEN_ITEMS.
- `**Commit:**` retired from the fix-pattern template (P256, operator's call).
  69 of 186 patterns carried it, P46-P156 with 18 internal gaps, filled with a
  sha rather than the commit message the template specified. The commit is
  derivable with `git log -S`. No backfill.
- `CLAUDE.md`: recorded the scripted-Python write path as verified working,
  with its four-part verification requirement attached — assert anchors are
  unique, write nothing on a miss, prove byte counts and line endings, read
  back. VS Code remains the rule for hand edits.
- `fix_patterns.md` — P256: the `**Commit:**` field stopped at P156 because
  atomic commits made it unfillable, and no check reads it, so 99 patterns
  omitted it silently. The sha is derivable with `git log -S`.
- `CLAUDE.md`: two operator rules that existed only in chat are now in the
  repo — push when a set closes without asking, and search previous chats
  before reconstructing a convention. Both were broken on 2026-10-16; the first
  is why 35 commits sat unpushed behind a failing gate.
- Corrected the stale OPEN_ITEMS claim that Stage 3 pass B has no OpenAI
  credits. It ran twice tonight. Recorded that `verify-candidates.py --library`
  exists and had never been used, that most library rows predate the sourcing
  pipeline and have never been A/B verified, and that #1903's first ever run
  failed UZ and TJ on both models.
- `fix_patterns.md` — P254: ↻ Rebuild from blocks re-derives the caption from
  the blocks but takes the matn from `selected`, a snapshot captured at row
  selection, so a mid-session DB correction is invisible to it.
- `reel-creation-pipeline.md` Step 9 — minimum four clips per reel, because the
  clips are posted individually on Instagram.
- Three stale instructions in `reel-creation-pipeline.md` corrected, each a
  workaround that outlived its defect: Instagram "phone only, WhatsApp it to
  yourself" (laptop upload has worked for months), "collection and narrator stay
  Latin, hand-correct to Cyrillic" (superseded by P150, and it made the assistant
  tell the operator to delete a correct citation), and "`-Scenes` reads from
  `normalized` and nothing else" (superseded by P217). A registration warning was
  also added to Step 13, closing the gap that blocked #1903 EN. P253.

### Added
- `reel-creation-pipeline.md` — `Publishing — all four platforms`: the order,
  the fields each platform needs, the YT and TikTok metadata shape, and the
  per-platform traps MOVED out of the kids Step 6 so both lanes read one copy.
  Records that none of it is automated and why: the Telegram route is
  `sendMessage`, no tokens sit in either `.env.local`, IG is behind the Facebook
  appeal.
- `fix_patterns.md` — P249 (the nasheed picker keeps one slot per lane and
  writes it before the render succeeds), P250 (the FLUX still prompt is recorded
  nowhere and #1903's four are lost), P251.
- `reel-tracker.md` — R134, Bukhari #1903 EN, with the duplicate-check,
  theme, asset-reuse and stats updates.

## [2026-10-16]

### Fixed
- **The cadence check read the wrong part of the tracker (P248).** The daily
  email reported the newest reel row as 2026-10-11 (R122-R125), 5 days old,
  while R133 is dated 2026-10-15 — and the same email quoted "133 reels", which
  only the Active reels table can produce. The check lived in the task's prompt
  under an instruction to tail the file; the table is near the top and a tail
  lands in the Change log. `audit-docs.py` now computes it in `cadence_line()`
  from the rows it already parses, and the task quotes the script instead of
  recomputing. P247 had moved the sibling check into this script the day before
  and left this one behind — the same scoped-to-the-symptom shape as P237 and
  P242.

## [2026-10-15]

### Fixed
- **Scribe v2 probed for UZ/TJ — does NOT close P078.** Six `scribe_v2` calls on
  the #6570 moral mp3s: UZ returns LATIN with or without `language_code` (same as
  Whisper), and TJ returns PERSO-ARABIC even at `language_code=tgk` with
  probability 1.0 — a different script, not a transliteration gap, and further
  from the channel's Cyrillic than Whisper was. No release note documents output
  script, which is the only thing that decides it, so it had to be probed. The
  transcripts are accurate, so one opening remains for UZ alone: compare Scribe's
  Latin against the existing `text_uzbek_latin` column in `stt-validate.py` and
  give UZ its first automated listener. Recorded as an open task in
  `self_upskilling.md`; subtitles stay off either way.

- **A daily check ran for two weeks and reported to nobody (P247).** HV's
  `CLAUDE.md` cached the shared P-frontier at "P186 as of 2026-10-01" and was
  sixty patterns stale by 2026-10-15. The daily Doc drift task names that exact
  comparison as step 3 of its prompt and reported SUCCEEDED throughout, because
  the comparison was agent judgement producing prose rather than a script
  producing an exit code, and the task has no notification destination while its
  sibling job digest emails itself. `scripts/audit-docs.py` now carries
  `check_sibling_frontier()`, which FAILS on a P-number in the sibling's
  CLAUDE.md above HV's own top and below HR's frontier — the signature of a
  cached frontier. The run duration (5.3s) looked like an early bail and was not:
  `audit-docs.py` takes 0.23s and a clean run is one line by design.
  The task's prompt now also emails its report every run with the verdict in the
  subject line, because `update_trigger` cannot set a notifications field and a
  finding with no addressee is not a finding.

- **A verifier agreed with a source it could not read (P246).**
  `restore-srt-casing.py` printed "nothing to restore - the SRT already matches
  the source" while comparing an English SRT against a Cyrillic `draft.txt` left
  by the next day's generation. Zero words could match, so zero changed, and the
  empty result was reported as agreement; `stt-validate.py` correctly flagged the
  same pair at similarity 0.126. A language guard now compares writing systems
  and word coverage (`MIN_COVERAGE = 0.40`) and exits 2 rather than agreeing.
  Separately, `app/api/tts/route.ts` now archives the narrated text as
  `{style}-{lang}-{slug}-{section}.txt` beside each mp3, because `draft.txt` is
  overwritten by every generation and #6570 UZ/TJ — which ship without
  subtitles (P078) — lost their reviewed wording to it, leaving only audio.

- **`hadith_library` — three rows corrected at source.** `#6570.text_english`
  disagreed with its own narrator field (“Abu Hurayrah” against “Abu Hurairah”,
  49 uses across the repo and no variant); `#13.text_russian` lacked the
  completeness qualifier the other three languages carry; `#13.text_uzbek_*`
  read «ўз учун» where Uzbek needs «ўзи учун». All read back after the UPDATE.

### Documented
- **Pronunciation watch-list updated (P193), stale since 2026-10-04.** New
  ACTIVE row: TJ «бародарат» voiced «бародорат» on **v4** (R133, #13 TJ),
  worked around with the analytic «бародари худ», which sidesteps the suffix.
  It fits the documented class rather than extending it — stem Cyrillic a → o,
  the same grapheme-to-phoneme behaviour as «Марде»→«Мардэ» and
  «атри»→«отри». The v4 ACTIVE list now holds two entries.
  The UZ apostrophe case from R128 was deliberately NOT added to that table:
  `'` is the LETTER tutuq belgisi, so the model voiced correctly what it was
  handed and no model change fixes it. Recorded in the UZ text-prep notes
  instead, citing P097.
- **`reel-creation-pipeline.md` contradicted itself on the TTS model for 11
  days.** Two lines claimed "All ElevenLabs `eleven_v3`" while the watch-list in
  the SAME file named `eleven_v4` current since 2026-10-04, and the route's
  default is `eleven_v4` with `ELEVENLABS_MODEL` unset in every env file. Both
  corrected to name the route's default. The drift mattered because the
  watch-list is scoped to a model (P193): a reader trusting those two lines
  would have read every v4 row as inapplicable and every "NOT NEEDED on v4"
  row as live — exactly inverting the list.
- **Bukhari #13 shipped in four languages (R130-R133)** — “None of you truly
  believes until he loves for his brother what he loves for himself.” Shortest
  adults reels to date (18.9-25.6s), and the first built on REUSED scene clips
  rather than bespoke ones. #6570's reserved row IDs shift to R134-R137: the
  tracker's rule is rows go in after posting, and #6570 publishes ~2026-10-27.
- **`restore-srt-casing.py` introduced a casing error (P243).** It reads all of
  `draft.txt`, including the non-narrated H and C blocks, and does not expand
  ﷺ. A sentence-initial «Его» in H became the “source spelling” for the
  mid-sentence «его» in the ﷺ expansion, so a correct subtitle was rewritten to
  read as Allah being blessed rather than the Prophet ﷺ. The linter could not
  see it: its check fires on words absent from the source, and this one was
  present in the other case. NOT FIXED — reverted by hand at the review pause.
- **Five library rows found unusable in one morning (P244).** `Musnad Ahmad
  #7936` is wrong on narrator, grade, extent and wording, and all four of its
  translations invent the apodosis its truncated مَن conditional is missing —
  which is why it read as complete and was recommended for production twice.
  `Muslim #223` and `#2699` are partial extent. `Tirmidhi #2616` and `Bukhari
  #1469` each exist as two rows under one number, #2616's with different grades.
- **Rule 17 loses seven of eight (P245).** Across #6570 and #13 the moral
  re-attributed in seven generations; #6570 RU's «условие» and #13 TJ's «шарт»
  are the same word reached for independently. Both Uzbek instances escalated to
  attributing the claim to Allah — including once when rule 17 had been named in
  the watch list beforehand. With P239's finding on rule 25, the register of a
  rule is no longer a plausible variable; `proposed-rules-positive-form.md`
  stays on hold.

- **`app/admin/page.tsx` — the title had no editor, so Rebuild reverted it
  (P242).** P238 gave the caption a ↻ Rebuild from blocks control. The caption
  derives from title as well as story/moral/seerah, but title was a read-only
  `<p>` while the other three were textareas wired to `updateField`. Rebuild
  therefore could not pick up a corrected title and silently restored the
  generated one - a field that worked fine before P238. Found on Bukhari #13,
  where the generated title was clickbait and the correction would not stick.
  Title is now a textarea bound to `updateField('title')`.

## [2026-10-14]

### Fixed
- **`render-reel.ps1` — `-FitScenes` had no ceiling guard (P240).** It computes
  an equal share of the narration per clip and assumes the source can supply it.
  `-t` trims, it cannot stretch, so when the share exceeds the clip length every
  clip comes back at its own length and the background is SHORT of the audio -
  and `-stream_loop -1` on the merge wraps to clip 1 rather than failing. #6570
  UZ asked 10.644s of 10.042s clips, got 50.16s of background against 53.22s of
  audio, and replayed the opening lamp for its last 3.0s with no error anywhere.
  EN, RU and TJ were all under the ceiling and passed. Guard now measures the
  shortest picked clip and Dies, naming how many clips are needed.
- **`render-reel.ps1` — P237's own gate called a `--section` that does not exist
  (P241).** It passed `--section clips`; `audit-assets.py` offers only
  `{audio,mascots,scenes}`. argparse exits 2, the gate Dies - every random-mode
  render broken from the moment the fix landed, invisible because every recent
  set passes explicit `-Scenes`. Corrected in conversation when written and
  never corrected on disk.
- **`hadith_library.text_english` #6570 — two spellings of the narrator in one
  row (P241).** `Abu Hurairah` opening, `Abu Hurayrah` inside the quoted speech,
  against a narrator field reading `Abu Hurairah` and 49 uses across the repo
  with no variant. Normalized, not corrected - هُرَيرة is genuinely an *ay*
  diphthong and RU/UZ/TJ all use that form - but EN's text and EN's own narrator
  field have to agree, and `text_english` is the EN caption's first paragraph.

### Added
- **`assets/asset-registry.json` — five Bukhari #6570 scenes registered**
  (`b6570-lamp`, `-ink`, `-kalima`, `-plain`, `-garden`), all adults, all
  verified by frame inspection. Notes record the near-duplication of
  `b6570-plain` with `b6423-plain` (same beat, different ground) so the choice
  between them stays deliberate, and that the kalima survives Kling to 9.5s.

### Documented
- **Rule 25 lost 3-of-4 on its first clean test (P239).** Written as a TEST
  rather than a wording blocklist precisely because rules 23/24 were walked
  around within a day. EN held; RU, UZ and TJ all supplied a contrast the matn
  does not draw, two of them near-verbatim repeats of the same language's #6423
  defect. The clause passes the grounding test honestly - "not merely with the
  tongue" is a fair gloss of خالصًا - so what is missing is not grounding but
  that خالصًا says what the deed IS and not what it is NOT. The fifteen-rule
  positive-form rewrite stays on hold: rule 25 is both positive and a test, and
  neither property saved it.
- **`app/admin/page.tsx` — the caption never re-derived from edited blocks
  (P238).** The story/moral/seerah textareas are bound to `generated`, so an
  operator correction lands in state immediately; the caption was built once
  inside `generate()` and never again. The screen showed a corrected moral with a
  caption underneath still carrying the rejected wording. Twice on consecutive
  reels — #6423 caught by eye before posting, #6570 caught because the character
  count did not move after an edit. It was identified the first time and not
  built, so it was paid for twice. The builder is now `buildCaption(data)`,
  called from generate and from a "↻ Rebuild from blocks" control. Deliberately a
  button, not a `useEffect`: the caption box is hand-tuned (quote nesting per
  P236, a trimmed line to clear Telegram's 1024) and a reactive rebuild would
  discard that silently.
- **`render-reel.ps1` — the third asset input had no registry gate (P237).**
  `-Scenes` clips were gated by P121 and the nasheed by P168; the RANDOM path —
  glob `normalized\*.mp4`, draw three — never was. An unregistered or RETIRED
  clip could reach a reel by sitting in the folder. Each earlier gate was added
  to the path that had just failed, and neither asked which other inputs reached
  the same output. It stayed unnoticed for the same reason it is low-risk: every
  recent set passes explicit `-Scenes`, so the ungated path is never exercised —
  which reads as safety and is absence of evidence. The draw now comes FROM the
  approved list rather than being checked after the fact (checking after a pick
  invites re-rolling around a rejection), and present-but-unapproved clips are
  named on screen. A no-op today: 70 clips on disk, all 70 approved. It is a
  guard against drift, not a repair.
- **`app/admin/page.tsx` — the caption wrapper nested identical guillemets
  (P236).** P180 taught the builder to skip the `«…»` wrapper when a matn BEGINS
  with `«`. A matn carrying `«` INSIDE it is the other half of the same problem
  and P180 does not see it: wrapping gives `«… «kalima» …»`, which Russian,
  Uzbek and Tajik typography all read as broken. It hit #6423 in Russian, was
  hand-corrected, hit in Uzbek an hour later, was hand-corrected again, and
  #6570 would have been the third and fourth — four hand-corrections of one
  defect, because each looked like a formatting slip in a reel rather than a
  property of the builder. The wrapper now demotes the inner pair to `„…“`, the
  second-level convention in all three Cyrillic languages here. The fix belongs
  in the builder, not the rows: the matn is quoted as the source quotes it, and
  it is the wrapper that creates the second level.
- **Tajik kalima spelled two ways across one arc.** #6423 shipped
  `«ло илоҳа илаллоҳ»` (spaced, but missing the gemination `إلّا`'s shadda
  requires); #6570 carried `«Лоилоҳа иллаллоҳ»` (geminated, first two words run
  together). Each wrong differently, neither matching the other, in a
  three-reel arc built on that kalima. Both now `«Ло илоҳа иллаллоҳ»`.
  Uzbek was consistent across both; only Tajik drifted. The #6423 reels are
  published and were NOT re-rendered for one letter — the library row is
  corrected so nothing built from it repeats the spelling. Found by P235's
  step 3a on its first use.

## [2026-10-13]

### Fixed
- **`app/api/generate-reel/route.ts` — the model was asked to hand-serialize text
  it does not control (P232).** The Russian generation for Bukhari #6423 returned
  content that was correct in every way and would not parse: the matn carries
  straight double quotes (`говорящий: "Нет божества, кроме Аллаха"`), and copying
  them verbatim into a JSON string value closes the string early. The model obeyed
  rule 2 and P153 exactly — quote the matn as it stands — and the format it was
  told to write could not carry what the rules required it to put inside. English
  passed only because its matn happens to use guillemets; UZ and TJ share Russian
  typography, so this was two generations from presenting as a language bug rather
  than an encoding one. Replaced with an `emit_reel` tool schema and forced
  `tool_choice`; the handler reads `tool_use.input` and `JSON.parse` is gone from
  the route. The prompt's "Respond ONLY with valid JSON" line went in the same edit
  — stale and misleading once the tool is forced. P140's rule holds one block type
  over: find the block, never index by position.
- **`app/api/generate-reel/route.ts` — the parse error named a symptom and no cause
  (P231).** `Failed to parse AI response` was the entire operator-facing message;
  the raw text went to `console.error`, into a dev-server terminal that had since
  been closed, leaving an orphaned process whose output was unrecoverable. Finding
  the cause cost a hunt across three windows and a second paid generation purely to
  reproduce evidence that had already been produced twice. The error now carries
  `stop_reason` and the character count — `max_tokens` means truncation (P144 one
  stage later), anything else means non-JSON — and the full text is persisted to
  `out/last-parse-failure.txt` instead of a console. `end_turn, 929 chars` ruled
  out the leading hypothesis in one glance; the persisted file gave P232 in the
  next.
- **`render-reel.ps1` — the P201 sidecar had never once been written (P228).**
  `[System.IO.File]::WriteAllText` with a relative path resolves against
  `[Environment]::CurrentDirectory`, which PowerShell does not update on
  `Set-Location`. Every reel since P201 rendered, reported success and left no
  `{base}-render.json`, so the tracker's Nasheed column and the asset-reuse audit
  had been filled from memory. Path now built with `Resolve-Path`; the success
  line is printed and the catch prints the real exception instead of a bare
  "could not record". Verified on #6423 EN and RU.
- **`render-reel.ps1` — `-FitScenes` measured the narration before its own pad
  (P229).** The fit arithmetic divided the RAW narration across the clips while
  P143 pads the audio 1s at the tail, so the background ended a second early and
  the final scene was clipped — on a reel whose last frame is the reason the scenes
  are ordered as they are. `$tailPad = 1.0` is now one named constant used by the
  fit arithmetic, `apad=pad_dur=` and the final `-t`. #6423 RU: 27.18s for 26.18s
  of narration, 4 clips at 6.795s.
- **`scripts/lib/source_dorar.py` — the source appends punctuation the matn does
  not contain (P230).** Dorar returns every matn with an orphan ` . .` appended,
  which rode into the library and from there into the caption via P153 — the one
  element of this project that exists to be externally verified was shipping with
  characters the source does not have. `_TRAIL_DOTS` now collapses trailing ASCII
  and Arabic full stops. Rows already in the library carry the artefact until
  re-pulled; #6423 was corrected by hand before its captions went out.

### Added
- **`scripts/composite-matn.py`** — puts real Arabic onto a blank FLUX page.
  FLUX cannot write Arabic: three `b5027-page` variants came back as convincing
  gibberish, which matters most exactly where the text IS the subject. The method
  (blank page described as a STATE per R026, Pillow + RAQM/HarfBuzz with
  `direction="rtl"` and `language="ar"`, perspective warp, multiply blend so the
  ink absorbs into the fibre) was worked out for #5027 and left unscripted in
  prose, so the next reel needing it would have rebuilt it from a paragraph. Now a
  script with `--probe` for checking the quad before committing to a render.
- **Four Kling scenes registered for Bukhari #6423** — `b6423-gate`,
  `b6423-kalima`, `b6423-plain`, `b6423-ash-v2`. The ash scene is a re-roll: v1
  kindled a fire in a hearth meant to be dead (51 -> 1346 pixels above brightness
  230, peaking at pure white) because the prompt said "cool light creeping across
  the settled ash" and Kling read that as licence to put light *in* it. R026 again,
  one layer down: describing what should be absent invites it.

### Changed
- **`scripts/list-library.py` — the four-language side-by-side read, one stage
  earlier, and now required (P235).** P233 and P234 were both found on the same
  day by printing the Arabic and all four translations of one row together and
  reading down the column — and by nothing else. No gate produces either:
  `lint-content.py` checks one text at a time and passed all four, Stage 3 scores
  each language separately against the Arabic, `stt-validate.py` compares the
  subtitle to the draft rather than the draft to the matn, and per-language human
  review is exactly the view in which a four-language addition looks like four
  correct translations. The read already existed as `--row`, but only against
  `hadith_library` — after promotion, which is after the point where a defect is
  cheap. `--candidates` runs it against `hadith_candidates` and also prints
  `status`, `verify_agreement` and `review_reason`. Workflow I gains step 3a
  requiring it before the sign-off, naming both signatures: a clause in SOME
  languages and not others, and — the counter-intuitive one — a clause in ALL of
  them that is not in the Arabic. Unanimity is not corroboration; four
  generations agreeing on something absent from the source is the signature of a
  move the model makes in every language, which is how P233 survived rules
  written the day before.
- **`scripts/translate-candidates.py` — `--apply` erased a decision and a
  provenance record (P234).** A reviewed file carrying ONE corrected Tajik field
  on Bukhari #3435 also wrote `translation_meta = {}` and `status = 'translated'`,
  because both lines assumed the reviewed JSON describes the whole row. It
  describes the fields a human corrected. The status loss is the serious one:
  #3435 rests at `needs_human` by ruling, not because work is outstanding — the
  على ما كان من العمل clause is genuinely ambiguous (P224/P225) — and
  `translated` left it reading as eligible for Stage 3 and promotion, the one
  outcome three sessions of work on that clause exist to prevent. Same family as
  P151 from the other side: a column recording a HUMAN JUDGEMENT treated as one
  recording PIPELINE POSITION. `--apply` now reads the row first, merges
  `translation_meta` instead of replacing it, keeps a `TERMINAL_STATUS`
  (`needs_human`/`rejected`/`promoted`) and says so, and refuses to write if the
  read fails. #3435 restored by hand.
- **Bukhari #3435 Tajik — dropped the بحق interpolation.** «ҳеҷ маъбуде ба
  ҳақ нест ҷуз Аллоҳ» → «ҳеҷ маъбуде нест ҷуз Аллоҳ». Orthodox as grammar,
  still an interpolation, and the other three languages omit it. OPEN_ITEMS had
  attributed this to the UZBEK, which was already clean — the Tajik is where it
  actually sat, and it would have shipped. Note corrected.
- **`app/api/generate-reel/route.ts` — rule 25, stated as a test rather than a
  blocklist (P233).** Bukhari #6423 supplied a contrast the matn does not draw in
  ALL FOUR languages (`а не как пустые слова на устах`, `фақат тил билан айтишга
  эмас, балки`, `на танҳо бо забон, балки` twice) — one day after rules 23 and 24
  were added for exactly that family. Neither rule was broken as written: rule 24
  forbids a *forward* purpose clause and what arrived was a *backward* exclusion;
  rule 23 forbids "this hadith shows" and what arrived was `Маънои муқарраршудаи
  он`. Same move, different wording. It is the third instance — P212 supplied a
  WARRANT, rule 24's failure supplied a PURPOSE, this supplied an EXCLUSION — and
  each time the response was a new rule naming the new wording, which held until
  the next wording. An enumerated prohibition is a blocklist over natural language
  and has no edge. Rule 25 generalises rule 22's approach, which has held: take
  each clause of the moral and seerah_context, point at the words in the matn it
  comes from, delete it if you cannot. A test does not care which costume the
  addition arrives in. Also notes the second-order cost — naming the exclusion
  plants it, so a reel about sincerity ends up teaching the shape of insincerity
  (R026 at content level). NOT YET VERIFIED; the test is #6570, 2–3 weeks out.
- **Rule 16 amended — tense and mood (P233).** Three of four languages rendered
  `حَرَّمَ اللهُ عليه النَّارَ` (Allah *forbade* him the Fire) as a promise — `ваъда`,
  `ваъда қилган`, `ваъдаи`. A completed statement turned into a pledge moves the
  thing from done to pending. No numbered rule covered it; the moral field
  description has said "do not add a promise the matn does not make" the whole
  time, in prose. P226 unfixed for this one constraint.
- **Subtitle style** — `FontSize` 18 -> 14, `MarginV` 80 -> 55, so the burned-in
  line stops competing with the kalima in frame.

## [2026-10-12]

### Fixed
- **Generator rules 23 and 24 — the constraint was in the wrong register
  (P226).** The two defects that ran through #5027 in three of four languages
  each were already forbidden, but only inside the prose description of the
  `moral` field — never in the numbered ABSOLUTE CONTENT RULES. Every rule in
  that list held on the same set, same call, same model. A field description
  shapes a field; the rule list is the constraint set. Both promoted to
  numbered rules. NOT YET VERIFIED — a prompt change is only proven by
  generating, and the free test is Sahih Muslim #1631, next in the queue.
- **`scripts/verify-candidates.py` — one transient failure discarded eight
  paid calls (P223).** Stage 3 makes 8 provider calls per row; `incomplete`
  is per-language and rolls up, and neither pass had any retry. So a single
  momentary 429 on one language threw away that row's other seven calls and
  returned it unchecked — 5 scattered 429s cost 3 of 5 rows on the first
  funded run. Both passes now share one transport with 4 attempts and
  2s/5s/12s backoff, honouring `Retry-After`. Crucially it does NOT retry
  `insufficient_quota` / `credit_balance_exhausted`: same status code as a
  burst, opposite problem, and the one 429 that needs a human not a wait.
  Errors now carry the response body too — `urllib` renders every 429 as
  “Too Many Requests”, which is exactly why an exhausted balance was
  indistinguishable from a rate limit until the request was re-issued by hand.
- **CORRECTION — Stage 3 A/B verify was called unbuilt and is not (P221).**
  `scripts/verify-candidates.py` has been on disk since 2026-09-05,
  `probe-passb.py` beside it, and CLAUDE.md:516 documents Workflow K in eight
  steps. The claim reached P220's status line, OPEN_ITEMS and a commit message,
  and came with a recommendation to BUILD it — which would have paid to rebuild
  an owned stage, the cost P218 exists to prevent. An absence claim needs the
  same evidence as a presence claim; CLAUDE.md's workflow list is where to look.
- **`scripts/verify-candidates.py:345` — a display string ended a paid run
  (P222).** `agreement()` has returned four values since P152; the per-language
  renderer knew three and raised `KeyError: 'incomplete'` on the first row of
  the first run, after both paid passes had completed. Only reachable when a
  provider call fails, which is why five weeks of clean runs never hit it.
  Fourth value named and the lookup made non-fatal.
- **Stage 3 then ran: pass B has no OpenAI credits.** HTTP 429 on all 20 calls,
  `probe-passb.py` quoting “You have no credits remaining”. All 5 rows came back
  `incomplete` and the footer refused to send them to Stage 4 — P152's design
  behaving exactly as written. Pass A completed all 20 and flagged Bukhari
  #6570 RU/UZ on نفسه (“his own self”, not “heart”), catching this session's own
  consistency edit to the Russian on the first completed run.
- **`scripts/translate-candidates.py` — `--apply` shipped text nobody had
  read (P219).** P177 made the reviewed JSON the shipped text by removing the
  second generation, but the artifact is a fixed path with no owner. A
  redundant dry run left running detached finished mid-review, rewrote that
  path, and `--apply` wrote rows never read — Muslim #28 with its
  `[UNCERTAIN]` marker still in it, and a third Tajik wording of the «face of
  Allah» clause on Bukhari #6423. `--apply` now recomputes the signed digest
  and refuses on any mismatch. Also: `--apply` wrote without `--commit`
  although `--commit`'s help text promises otherwise, and demanded
  ANTHROPIC_API_KEY for a path that makes no model calls. Both corrected.
- **Workflow I step 6 documented the pre-P177 path.** It said “`--commit`
  writes and sets `status='translated'`” and never mentioned `--apply`, so the
  written procedure was the very one P177 was added to stop — P218's shape,
  three days on. Rewritten to review → `--sign` → `--apply --commit`, with the
  duplicated “7. 7.” numbering fixed.
- **Four translation-fidelity defects in the Tawheed batch (P220).** Bukhari
  #3435 Uzbek made admission to Paradise conditional on deeds where the matn
  says it is granted whatever they were; #3435 Tajik carried the same
  ambiguity; #6423 Uzbek reversed the direction of “the Fire was forbidden to
  him” and used the imperative; #6570 Uzbek and Tajik rendered حرص with a word
  that reads as greed in both, of a Companion being praised. Corrected in the
  reviewed JSON and shipped from there, then verified field-by-field in the DB.
  No automated check would have caught any of them.

### Added
- **`--sign` on `scripts/translate-candidates.py` (P219).** Records the
  sha256 of every `candidate_id` + proposed text to
  `out/candidate-translations.reviewed.json`. `--apply` refuses without it and
  refuses on a mismatch, printing both digests and the signing time; the
  signature is consumed on a successful apply so it can never cover a later
  file. Order-independent, so re-sorting is not a change and one character is.
- **Three Tawheed hadiths translated into EN/RU/UZ/TJ and Uzbek Latin
  derived** — Bukhari #3435, #6423, #6570, all at `status='translated'`.
  Muslim #28 held back on its `[UNCERTAIN]` marker; #99 and #6938 held as
  variants.

## [2026-10-11]

### Fixed
- **`scripts/generate-scene.ps1` — the audio-off guard was scoped to the model
  it was written for (P214).** `if ($Model -match 'v2\.6') { $payload['generate_audio'] = $false }`
  — correct while 2.6 Pro was the only model ever passed, and silently absent
  for any other. Found while preparing the Kling 3.0 evaluation, which is the
  first `-Model` this script has ever been given that is not 2.6: the v3 half
  would have billed $1.68 instead of $1.12 and come back with a generated audio
  track, which is not comparable to a silent clip. Audio-off is unconditional
  now and the one model that rejects the field (2.1 Master) is named instead,
  so a match that FAILS leaves the safe state in place. Verified against seven
  model ids, including a hypothetical v4.

### Added
- **`scripts/generate-scene.ps1` now records every scene prompt (P215).** The
  Kling 3.0 evaluation asks for “the same prompt through both models” and could
  not be run against ANY of the 64 registered scenes: no clip's motion prompt
  was ever stored. They were typed into a chat window and lost. `Write-Sidecar`
  writes name, model, mode, duration, the verbatim prompt, the input still,
  negative_prompt, generate_audio as actually sent, request_id and the
  completion facts to `assets/scene-prompts/<name>.json`.
  Written at SUBMIT, because the charge happens there and a 20-minute timeout
  (P137) ends the run before a file exists — a timed-out job still has its
  prompt for `-Resume`. The writer MERGES: a `-Resume` run carries no `-Prompt`,
  and an unconditional write would blank the record on the one path that exists
  to recover a paid job. Records go in `assets/scene-prompts/` rather than
  beside the clip because `/out/` is gitignored wholesale and git will not
  descend into an ignored directory to re-include a file — a sidecar there
  would be unversioned, the same loss on a slower clock.
  Verified by pulling the function out of the script with the PowerShell AST
  and driving all three call shapes: 17 checks.
  **The 64 clips made before today stay unreproducible** — their prompts are
  gone, recorded in P215 so no future eval plans around them.

### Changed
- **`-Duration` accepts '15'** (`generate-scene.ps1`). Kling 3.0 takes 3–15s
  where 2.6 Pro caps at 10 — and that cap is why `-FitScenes` can only ever
  trim. 2.6 rejects 15 at the API, at no charge.
- **The cost table in the script header** gains Kling 3.0 Pro: $0.112/s audio
  off, $0.168/s audio on, against 2.6 Pro's $0.07/s. 3.0 is 1.6× the
  per-second rate, which is an adoption cost and not a saving: seconds of clip
  per reel are fixed by the narration, so longer clips mean fewer cuts, not
  fewer seconds.

### Fixed
- **`generate-scene.ps1` told Kling to suppress text while handing it a still
  made of text (P216).** The negative prompt is a constant containing `text,
  watermark` — correct for every MODE B background, and directly against the
  intent for `b5027-matn`, whose whole subject was the composited matn. The
  Arabic survived both models anyway, which is evidence about that run and not
  about the instruction; a longer duration or a heavier camera move could erase
  it, and the failure would have looked like a model problem rather than a
  prompt we wrote. New `-KeepText` switch drops `text, watermark` when the input
  carries text on purpose. Found by reading the P215 sidecar of a clip that had
  already succeeded — the record paying for itself the day it shipped.

### Changed
- **Kling 3.0 Pro is the default in `generate-scene.ps1`.** Evaluated against
  2.6 Pro the way FLUX 2 was (P198): one still, one prompt, both models, 10s
  each, at the #5027 set boundary. Both returned 1080×1920 / 24fps / 10.04s with
  zero audio streams. 3.0 casts defined window-pane shadow bars physically
  coherent with the window in frame where 2.6 gives an undifferentiated warm
  patch, and resolves parchment fibre and cloth weave more crisply. Regression
  worth knowing: 3.0 reads motion instructions more aggressively — “a very slow
  gentle push” travelled much further than on 2.6 — so phrase camera moves
  conservatively. 2.6 Pro stays reachable via `-Model`. The watchlist item, open
  since February, is CLOSED.
  Verdict caveat recorded in `self_upskilling.md`: three sampled frames per clip
  were compared, not motion.

### Added
- **Real Arabic can be composited onto a still and survives Kling animation** —
  the finding the evaluation was not looking for. Both models held the matn,
  letterforms and tashkeel intact, through all 10s. FLUX cannot write Arabic
  (three `b5027-page` variants returned convincing gibberish, which matters most
  where the text IS the subject), so the method renders it instead: FLUX a blank
  page, render real text with Pillow + RAQM (HarfBuzz shaping, `direction=”rtl”`),
  perspective-warp onto the page quad, multiply into the parchment. Amiri comes
  from npm (`@fontsource/amiri`, woff2 → ttf via fontTools) because GitHub release
  downloads are unreachable from the session container and Windows ships no
  manuscript Naskh. Recorded under Practice in `self_upskilling.md`.
  **A page carrying a hadith matn is a hadith manuscript, not a mushaf** — the
  distinction the method depends on.
- **`assets/scene-prompts/` has its first two records** (P215), written at submit
  by the real pipeline: `b5027-matn.json` and `b5027-matn-v3.json`. Both show
  `generate_audio: false`, including the v3 call — **P214 verified in production**
  on exactly the clip that would otherwise have carried a generated soundtrack.
  `resolution` is null in both: ffprobe was not on PATH in the detached process,
  and the sidecar correctly recorded the absence rather than inventing a value.
- **`b5027-matn-v3.mp4` registered** as scene 1 of Sahih al-Bukhari #5027 — first
  clip on Kling 3.0 and first with real Arabic text.

### Verified
- **Kling 3.0 is live on fal as `fal-ai/kling-video/v3/pro/image-to-video`**,
  with `v3/standard` and `v3/4k` variants alongside it. Confirmed from the fal
  model page before any spend, per the rule against inventing commands. Schema
  differences that matter to the evaluation: `duration` is 3–15 (2.6: 5 or
  10); `multi_prompt` takes per-shot prompts each with its own duration;
  `elements` carries 1–3 reference images per character for consistency;
  `shot_type: intelligent` lets the model structure the shots itself; and there
  is no `aspect_ratio` field, which the payload still sends — harmless in
  image-to-video, where the start frame sets the aspect, but it is an unknown
  key and worth watching for a 422.

## [2026-10-10]

### Added
- **`scripts/check-parser-agreement.py`** — asserts that `lint-content.py`
  and `stt-validate.py` read a draft the same way. Written INSTEAD of the
  step-4 shared block parser that was on record: merging the two refactors
  working scripts to serve a v2 agent nobody is building, while this answers
  the question the merge was for. They agree on the shipped draft and on five
  adversarial inputs; both already open with utf-8-sig, so the BOM trap is
  covered in both.
  Carries `--self-test`, because after those six runs the DISAGREE branch had
  never executed — the same weakness as P210, where a threshold never checked
  against a known-different input was a number and not a gate. The self-test
  fires the failure path on three kinds of difference and confirms silence on
  identical input.
- **`evals/RUN-2026-10-10.md`** — all four reel-producing cases re-run COLD
  on a different model, one subagent each, given the blocks, the matn and the
  three shapes the skill names, and nothing else. Required findings: 001 3/3,
  002 3/3, 004 4/4, 003 1/3 — 3 of 4, which is the v1 bar, with zero genuine
  false positives.
  **Recorded as NOT a pass.** The harness was not constant: the TJ prompt
  mentioned the plural-verb convention and the UZ prompt did not, which is
  exactly one of the two findings 003 missed. It also supplied three defect
  shapes where the real agent reads the full table in
  `reel-creation-pipeline.md`. The run measures something narrower than the
  question, so the agent's v1 status is still unestablished.
  003's other miss was a confident exclusion, not an oversight: it examined
  the H drift and declined it as "standard scholarly gloss, framed as
  explanation". The framing is right and the conclusion wrong — H states the
  narrowed reading AS the hadith's meaning. Same shape as the 10-09 run's 002
  miss.

### Changed
- **eval corpus** — `attribution_boundary_open` was required on case 001 only,
  although 001, 002 and 004 all leave the boundary open. That taught the
  boundary matters in English and not elsewhere, the reverse of the truth for
  UZ and TJ, which have no subtitle pass. Now required on all three, and added
  to 003's `must_not_flag` — 003 is the only case that CLOSES its quotation, so
  the corpus tests the distinction rather than the presence of a long story
  block. Both cold runs behaved correctly on it.
- **two `must_not_flag` entries narrowed.** Both scoped themselves to the
  qanaah-drift axis in their notes but covered whole sentences in their loci,
  so a cold run flagging non-matn wording inside an attributed frame
  («Асл» inserted, «балки» dropped) would have been scored a false positive —
  which fails a run outright. The finding is real and now credited as
  `optional/non_verbatim_inside_attribution`; it shipped for real on R121,
  where the Tajik S block re-translated the hadith while C quoted the row.
- **P213 — `check_companion_honorific` in `lint-content.py`.** Flags an
  abbreviated companion honorific left in a NARRATED block. `cleanForTTS`
  expands every written form of the Prophet's honorific and no companion
  honorific at all, so the draft's "(RA)" reached ElevenLabs raw on R118 and
  was voiced as the truncated "radiyallah". Deliberately a check rather than
  an expansion: (RA) is gender-neutral in writing and gendered in speech, so
  only the draft knows whether it is *anhu* or *anha*. S and M only — H and C
  are read, where the abbreviation is correct.
  Verified four ways: the real R118 defect flags, the spelled-out form does
  not, an abbreviation confined to H and C does not, and the Russian
  «(р.а.)» flags. Two of the first four fixtures had silently failed to write
  (an emoji surrogate pair aborted the loop) and their file-not-found results
  were read as passes — recorded in P213, since it is the same shape as the
  gates it sits among.
- **R118-R121 — Jami at-Tirmidhi #3895**, the best of you is best to his
  family, EN/UZ/RU/TJ, adults. Fills Family / Marriage, which the tracker had
  as partially covered with marriage itself uncovered.
  Scene set `t3895`: one evening in one house — the hearth where the meal was
  made, the mat laid for six, the shared platter, the lit window seen from the
  yard. MODE B with no figures, on a hadith whose whole meaning is a
  relationship between people who cannot be shown.
  Era decision: a Tajik dastarkhan with plov was proposed and declined as
  Central Asian and roughly a millennium after the Hijaz. Composition kept,
  contents made 7th-century tharid — the same read for the target audience
  without the anachronism.
  No lamp is named anywhere in the house prompt and its source stays out of
  frame, against the b2654 and b6446 prior where a named lamp produced shrines.

### Fixed
- **P211** — `render-reel.ps1` skipped Whisper whenever an SRT existed, a bare
  `Test-Path`. After a per-block re-narration (P125) the previous run's
  transcript was kept and the new audio never transcribed. On this set the
  stale SRT read "Ravya Allah" while the re-narrated audio correctly said
  "may Allah be pleased with her" — that would have been burned in,
  contradicting its own soundtrack, on the exact phrase being corrected.
  mtime cannot express the staleness: `restore-srt-casing.py` rewrites the SRT
  after Whisper, so the stale file was NEWER than the audio it failed to
  describe. Replaced with a sidecar fingerprint of the source mp3s, which also
  preserves the operator's hand-edits across a re-run — the reason the cache
  exists at all.
- **P212** — rule 3 ("the moral must be practical AND directed to Allah")
  was being satisfied by inventing a divine warrant. Four languages, one
  hadith, four for four: "Allah has entrusted their care to you",
  "бу Аллоҳнинг амри", "Который возложил на человека…", "аз роҳҳои
  ба даст овардани ризои Аллоҳ". All sound teaching; none in the matn.
  Rule 3 was producing rule 16 violations. The rule now states that DIRECTED
  TO Allah means the action is addressed to Him, gives the compliant forms,
  and requires the matn to carry any claim about what Allah commanded,
  entrusted or categorised. Unverified against a fresh generation — the next
  set is the test.

### Notes
- The Uzbek library row was corrected before production: both scripts read
  «энг яхшиларингиз», plural, against a singular خيركم, colliding with
  their own singular «оиласига». `audit-library` returned 0 findings before
  and after, which is exactly what it says of itself. The correction then
  HELD through generation — the #6446 drift, where a fixed column was
  re-derived from the concept, did not recur.
- The Tajik S block re-translated the hadith instead of using `text_tajik`,
  while its own C block quoted the row correctly: one reel, two renderings.
  It also carried the gloss in a new form — a parenthetical «аҳли (оилаи) худ»
  inside the quotation.
- The Russian leg was the first ever measured by a working divergence gate,
  and the read still caught what the gate passed: Whisper heard the liaison in
  «Аллах и приветствует» as «Аллаха» and dropped the conjunction. 0.996
  similarity, zero findings, and still wrong. The gates narrowed what reaches
  the human; they did not replace the read.
- `cleanForTTS` expands every written form of the Prophet's honorific and no
  companion honorific at all, so "(RA)" reached ElevenLabs raw and was voiced
  as the truncated "radiyallah". It cannot simply be added to that list: the
  abbreviation is gender-neutral written and gendered spoken. Logged in
  OPEN_ITEMS as a proposed linter check, not an expansion.
### Fixed
- **P210** — `stt-validate.py`'s `similarity()` used `difflib.SequenceMatcher`
  without `autojunk=False`. On character sequences over 200, difflib discards
  every element occurring in more than 1% of the sequence — which for a
  300-900 character narration is every common letter. The ratio measured
  rare-character overlap, not text. Measured on the at-tirmidhi-3895 EN reel:
  0.6706 with autojunk, 0.9867 without, 0.2634 without against unrelated text.
  The gate was not dead but random — #1631 passed and this reel failed, and
  neither outcome carried information.
  Worse, a false divergence short-circuits `check_alignment`, so the broken
  gate was hiding the working one: three real HIGH findings on this reel
  (the draft's "(RA)" voiced as "Ravya Allah") were unreachable until the
  fix. All three surfaced immediately afterwards.

### Changed
- `scripts/pick-nasheed.py` — a tie at the top of the ranking is now named
  rather than silently resolved. On the #1631 set five beds sat at 0 uses, so
  the sort key `(0, 0, 0)` was identical for all of them and the stable sort
  handed back registry order; the same bed came back RECOMMENDED on all four
  legs and was overridden all four times. The recommendation carried no
  information — only the exclusion list changed between runs. Now prints a
  TIE banner stating how many beds share the top score and that usage cannot
  separate them, and rotates the default off a `--slug`+lane+lang hash so the
  legs of one set start from different places while each leg stays
  reproducible. Verified on tirmidhi-3895: the banner fires, EN repeats
  identically across runs, and chaining `--exclude` returns four distinct
  beds for the four languages.
  No P-number: this is a gap in a tool shipped two days ago and closed on its
  first real use, not a trap that recurs across the project.

### Added
- **R114-R117 - Sahih Muslim #1631**, the three ongoing deeds, EN/UZ/RU/TJ,
  adults. Produced 2026-10-09; the last of the sixteen posts landed after
  midnight. Fills Death / Afterlife, which the tracker had carried at zero
  coverage, and is the hadith this channel operates under.
  Scene set `m1631`: one planted estate - well, built irrigation channel,
  teaching circle, grove - made by someone now gone and still producing. Four
  FLUX 2 stills to four Kling 2.6 Pro clips, MODE B, no figures. Every obvious
  image for this hadith was already in the library (fruit tree x2, worn path
  x2, prayer mat x2, manuscript on a rahle, seven doorways, five dawn dunes),
  so the set was built around the one thing 56 registered scenes had never
  shown: a well. The circle carries no manuscript deliberately, keeping
  `ad3641-rahle` unrepeated for Bukhari #5027 later in the queue.
  Four distinct nasheed beds, none previously used anywhere.

### Fixed
- **P207** - `check_quote_addition`'s clause splitter was `(?<=[.!?])\s+`,
  which a closing quote mark defeats: `him.' Sadaqah` never splits, so the
  whole story line stayed one clause, matched the attribution-marker skip, and
  was never examined. The check was blindest on correctly punctuated input -
  precisely the #2759 defect class it was written for. Splitter lifted to
  `CLAUSE_SPLIT` and extended to allow one optional `' " » ” ’` after the
  terminator. Verified both ways: the block that slipped through now warns,
  and all four shipped #1631 drafts still return 0 fail 0 warn 0 info.
- **P208** - `render-reel.ps1`'s header documented narration inputs at
  `out\{style}-{lang}-{slug}-story.mp3`, a path that has not been correct
  since the P113 restructure; line 162 computes
  `out\work\{style}\{slug}\{lang}\`. The stale comment was trusted twice in
  one session and cost a screenshot to correct. Header now quotes the
  computed form.

### Documented
- **P209** - `core.autocrlf=true` with no `.gitattributes` means the per-file
  line-ending notes describe the INDEX, not the working tree, and
  `git checkout --` converts on the way out. Cost two failed writes and one
  reverted 204-line reformat. Detect from the bytes at read time, in the same
  operation that writes them back. `fix_patterns.md` is `w/mixed` (7583 CRLF,
  3 bare LF) and can only be appended to.

### Notes
- The same sadaqah jariyah gloss was inserted inside the attribution in EN, UZ
  and TJ - three of four languages, one hadith. RU alone did not, and RU's
  story block needed no correction at all. A per-hadith insertion recurring
  across languages is the concept pulling the generator, not a per-language
  quality gap.
- RU's moral opened "choose one of the three paths". The hadith says deeds
  cease EXCEPT FROM three; all three continue. Rules 15 and 20 at once, fixed
  by one conjunction. Worst content defect of the set.
- Rule 17 re-attribution appeared in UZ and TJ in the same set.
- All four languages rendered the singular child as plural, including the
  English draft written by hand.
- Pass B (different model, per P120) caught a regression introduced while
  fixing rule 3: the corrected English moral had dropped the supplication
  clause entirely.
- Whisper on Russian returned «пророг» - not a word - for «Пророк», plus a
  mangled narrator name and honorific. `restore-srt-casing.py` correctly left
  all three alone; it matches on case and ё, so it fixes casing, not spelling.
  Audio was clean. The subtitle pause is the only gate for this class.
## [2026-10-09]

### Added
- `scripts/pick-nasheed.py` — step 7 of the reel-producing skill, whose
  Scripts section had read “not yet implemented” since August. Recommends a bed
  and states the reason; it does not choose and does not render, because the
  renderer's own picker has drawn an ocean-ambience track onto R044 and an
  adults bed onto kids R029 and R030. Lane eligibility comes from the registry
  via `audit-assets --list`, never from the filename (P168); usage comes from
  the tracker parsed BY HEADER INDEX, since the Notes column holds prose and
  naive `|` splitting nearly overwrote R052's history once. Rows reading
  “not recorded (P201)” are skipped rather than counted as a bed.
  Verified on both lanes: kids/UZ recommends path-to-jannah-bg (4 uses, never
  in UZ) over beds with 8 and 9 uses, and `--exclude` correctly drops beds
  already assigned to other legs of the same set.
- `.claude/skills/reel-producing/evals/RUN-2026-10-09.md` — first run of the
  eval corpus since it was written on 2026-08-31. Passes v1 (3 of 4 cases with
  every required finding, zero must_not_flag hits) but the pass is provisional:
  the README's coverage table names each case's defects and was read before
  case 001, so that case was answered with the answers in hand. Discounted,
  the score is 2 of 3 — below the bar.
  The valuable result is the case 002 miss. `isnad_verb_in_story_block` was
  not overlooked; the run examined the line, decided «передал» is correct for a
  companion, and recorded it as deliberately not flagged. The verb is correct;
  the defect is that the isnad line sits inside the narrated span where it
  reads as the Prophet's ﷺ words. A known rule applied to the wrong axis,
  producing a confident exclusion rather than a silent miss.
  Two corpus defects found by running it: the README spoils the cases in the
  same file that argues for the split layout (now behind a spoiler warning),
  and `attribution_boundary_open` is required on 001 but absent from 004,
  which has the identical construction.

### Changed
- Moved `agents/{reel-producing,stt-validating,tts-validating}` to
  `.claude/skills/` (P206). Claude Code loads project skills from
  `.claude/skills/<name>/SKILL.md`; `.claude/` had hooks and settings.json and
  no skills directory, so 43KB of written skill — including a 15KB
  reel-producing SKILL.md with nine pipeline steps and a four-case eval corpus
  — had never been loaded by anything. The roadmap called reel-producing
  “SCOPED, not built”, which is why it survived: it understated what existed,
  and nobody audits a roadmap for undercounting. Roadmap corrected, and
  CLAUDE.md now states that a skill outside `.claude/skills/` does not exist.
- `hadith_library` #1899 — `text_english` and `text_russian` now render
  الوالد as FATHER, matching the Arabic, Uzbek and Tajik columns, which all
  already said father. They had said “parent” / «родителя», so the EN and RU
  reels of that hadith would have said something the Arabic beneath them does
  not — on a channel whose premise is that the translation matches the source.
  The row had been blocked for a week by a tj-no-diacritics INFO that turned
  out to be a HEURISTIC FALSE POSITIVE: the Tajik is correct and that sentence
  simply contains none of ӣүҳқғҷ. A week of being treated as suspect,
  and the thing actually wrong with the row was in two different columns that
  nothing flagged. Reviewed and recorded in the tracker so it is not re-opened.
- Renamed all three misnamed scene sets (P197): `b2628-*` -> `m2628-*` (Sahih
  Muslim), `b4248-*` -> `ij4248-*` and `b4251-*` -> `ij4251-*` (both Sunan Ibn
  Majah). 17 files across `new/` and `normalized/`, including two unregistered
  b4248 clips that would otherwise have kept the wrong prefix; 11 registry keys
  with the reason appended to each entry's notes; 18 tracker lines.
  Three tracker lines were deliberately left alone: they are prose and dated
  change-log entries that describe the defect BY its old name. A rename is not
  a find-and-replace — the filename is data, the sentence about the filename
  is history.
  Verified after: 0 misnamed, registry and disk agree, the new name passes
  `--check` and the old name is rejected.

### Added
- `scripts/audit-assets.py --names` — reconciles every scene clip name in the
  tracker against the hadith it was used for (P197). `--audit` enforces that a
  clip is registered and lane-approved, which is what P117 built it for; it has
  no opinion about whether the NAME points at the right narration.
  ELEVEN misnamed clips across THREE sets on the first run, where only one was
  known: `b2628-*` (Sahih Muslim #2628 under a Bukhari prefix, R102—R105),
  `b4248-*` (Sunan Ibn Majah #4248, R086—R089) and `b4251-*` (Sunan Ibn Majah
  #4251, R074—R077). The two Ibn Majah sets have been wrong since R074 and
  nothing noticed.
  The discriminator is the number. Reusing a scene set on a later hadith is
  intended and looks identical to a misnaming unless you compare it: same
  number with the wrong collection letter means the set was built for this
  hadith and labelled with another collection, a different number means reuse.
  That turns 16 raw mismatches into 11 defects and 5 expected reuses, and the
  reuses are listed rather than silently dropped.
- `scripts/audit-library.py` — `check_duplicate_numbers`, the first cross-row
  check in that script (P205). Three HIGH findings on its first run: Jami
  at-Tirmidhi #2616, Sahih al-Bukhari #1469 and Sahih al-Bukhari #6018 each
  have TWO rows under one number, and only #6018 was documented. The other two
  had been recorded in an earlier session and carried in OPEN_ITEMS as
  unverified because the tracker's index showed only #6018 — they were real.
  Each pair is one long narration split into clause-level rows rather than two
  different hadiths, which is a different diagnosis with the same exposure: the
  duplicate index keys on the number, so producing one clause makes the other
  read as already done. All three are now rows in that index.

### Removed
- `check_twin_wording`, written and deleted the same day (P205). It existed for
  Bukhari #2654 and #6871 — different numbers, same subject, nothing flagging
  the pair. Measured before trusting it: Jaccard scores that pair 0.16 against
  a library-wide maximum of 0.29, and containment scores it 0.56 while two
  unrelated pairs score 0.60. No threshold separates the case from the noise,
  because the relationship is semantic and the score is lexical. Shipping it
  would have added a gate that never fires and reads as coverage — the
  P119/P126/P185/P187/P189 shape, caught this time before the commit. The
  measurements are recorded in the code where the function used to be so it is
  not re-attempted from intuition, and #6871 is handled by an explicit row in
  the tracker's duplicate-check index instead.

- `scripts/restore-srt-casing.py`, called from `render-reel.ps1` after the cue
  split and before `stt-validate.py` (P200). Whisper transcribes sound, so
  capitalisation and Russian yo — properties of the text, never given to it —
  are destroyed on every en/ru reel: four of five RU findings and two of three
  EN ones on the #2759 set were this class, all corrected by hand.
  It uses no word list. A list cannot tell which «он» means Allah and would need
  maintaining; the correct text is already on disk as draft.txt. The script
  aligns the SRT to it and replaces a token only where the two are identical
  after normalising case and yo, so it cannot introduce a word Whisper did not
  hear, cannot change one word into another, and never touches timings. A form
  the source spells two ways is left alone and reported; the first word of a cue
  is never lowercased. Round-tripped against the real R111 defects: 11
  restorations, 0 ambiguous, cue-start «Ведь» correctly preserved. Punctuation
  and word-boundary errors still go to the human, which is what the pause is for.

### Fixed
- `CLAUDE.md` — the ﷺ glyph entry (P204). It had read "glyph handling is
  PER-LANGUAGE, measured 2026-08-16: EN, UZ and TJ voice the raw glyph
  correctly, RU does not". The measurement was real; the conclusion was not.
  `cleanForTTS` expands the glyph for every language and always has, so the raw
  glyph has never reached a TTS provider and RU is not a special case in the
  pipeline. The entry now says what the code does, and records what it used to
  say. The expansion is kept — every verified reel was narrated with it.
  Closes the open item filed a day earlier on the theory that v4 had invalidated
  the rule: it had been moot since before v4, and the code was never read.

## [2026-10-08]

### Added
- `OPEN_ITEMS.md` — the list of what is outstanding, and `CLAUDE.md` step 3 in
  the session-start order, which renumbers the rest (P203). fix_patterns records
  WHY a defect happened, one Status line per pattern across 200+ patterns in the
  order they occurred; that is not a list, and nothing else answered "what is
  left". Items that lived only in chat slipped twice. Three of them are
  content-integrity items, not cosmetics: `b2628` names a real and different
  Bukhari hadith across four shipped reels, Bukhari #6871 is #2654's twin and the
  duplicate index keys on number so nothing stops it being picked, and the
  Tirmidhi #1899 Tajik column has been flagged by audit-library.py every run for
  a week. An item leaves the file when it is done or when it is dropped with the
  reason written down.

### Changed
- `reel-creation-pipeline.md` — two conventions and three platform rules that
  were settled in conversation on 2026-10-05 and never written down. Step 2: the
  MORAL block is application and not quotation, so matn-bound formulas like
  `عز وجل` live in S and the caption and M names Allah plainly — their absence
  from M is correct, which had to be explained once already; and the library row
  is the source of truth for wording, so where S and `text_<lang>` differ on
  register alone, S changes, not the DB. Step 6: no `#` in a YouTube title (it
  becomes a hashtag link, so "#2759" turns into a tag), no Arabic in a TikTok
  caption (inconsistent RTL rendering in mixed-script text) with the first line
  front-loaded because TikTok collapses after about one line, and set the
  Instagram cover frame by hand because MODE B sets that open at night produce a
  near-black thumbnail.

## [2026-10-05]

### Added
- `app/api/generate-reel/route.ts` — rules 21 and 22 (P199). Rule 21 requires
  the STORY block to name the speaker: the Uzbek generation for Sahih Muslim
  #2759 came back with NO attribution anywhere in the block, from the same prompt
  that produced a correct one in the other three languages. Nothing had ever
  required it — rule 17 mentions the attribution only in passing, while
  explaining what the moral must not do. Rule 22 states that 15—21 apply with
  equal force outside English, because on this set English obeyed all of them,
  Uzbek broke 17, and Tajik broke 17 and 18.
- `scripts/lint-content.py` — `check_quote_addition`, the tenth check (P199).
  Splits the story block into clauses and scores each one's vocabulary against
  `--matn`; a clause sharing almost none of the hadith's words is an addition to
  it. Clause-level rather than sentence-level, because the #2759 addition rode in
  after an em dash inside an otherwise-faithful sentence. Verified against the
  real defective Tajik text — 1 of 5 words shared, flagged — and against the
  corrected text, clean.
- `render-reel.ps1` — per-reel `<base>-render.json` sidecar recording the
  chosen nasheed, scene list and `-FitScenes` (P201). `.last-used.json` keeps one
  value per lane and the next render overwrites it, so three of the four bed
  names from this set existed nowhere but a closed console buffer and are not
  recoverable. Written with `WriteAllText`, not `Set-Content -Encoding utf8`,
  which adds a BOM on PS 5.1 (P186).
- P199 — the rules are written in English and they hold best in English. The
  first instinct was that a rule was missing; rule 18 had forbidden exactly this
  since the #2628 set. The failure is instruction-following degrading with
  distance from the prompt's own language — and UZ and TJ, the two that broke
  the rules, are the same two P078 exempts from subtitles. Weakest generation,
  thinnest verification, same two lanes.
- P200 — Whisper transcribes sound, so everything that is only in the text
  dies. Divine-pronoun capitalisation and Russian yo are properties of the text
  and were never given to it. Four of five RU findings and two of three EN
  findings tonight were this class. OPEN, with the design recorded.
- P201 — the nasheed a render chose exists only in the console.
- P202 — a still is identified by its file suffix, never by where it sat in a
  paste. Cost one FLUX call and one Kling clip after "variant 3" in chat turned
  out not to be `-3.jpg` on disk.

### Changed
- `assets/asset-registry.json` — four m2759 clips registered and classified.
  Notes record that Kling adds a moon the still does not contain, that FLUX 2
  returned a DOUBLE door on two separate runs of the same prompt (so single-leaf
  must be stated), and that m2759-firstlight arrives close to dawn by 7s and
  should not be re-used expecting a distinct pre-dawn state.
- `reel-tracker.md` — R110—R113 (Sahih Muslim #2759, all four languages).
  113 reels / 29 hadiths / 61 adults.

## [2026-10-04]

### Changed
- `app/api/tts/route.ts` — ElevenLabs model default moved from `eleven_v3` to
  `eleven_v4`, at a set boundary, after running the audition the code comment
  beside it had been asking for since v4 appeared. Changed in the FALLBACK, not
  in `.env.local`, per P118. Tajik: v4 renders «атри», «Даре» and «Марде»
  correctly where v3 failed all three on the same voice — the defect was the
  model, so the planned TJ voice switch to a native Tajik speaker was built on a
  wrong diagnosis and is cancelled. Uzbek: v4 fixes «етим» and «Оқ», and newly
  breaks «емоқ».

### Added
- P193 — a model upgrade is a re-roll, not a cure. Word-initial Cyrillic е→э
  survived v3→v4 and moved to a word that had been safe across 105 reels, in a
  language where P078 leaves no automated listener. Every pronunciation
  watch-list entry is scoped to the model that produced it and expires when the
  model changes. Also records that `voice_settings.speed` is ignored by both v3
  and v4 (only `eleven_multilingual_v2` honours it, and m2 fails the Tajik
  accent), and that two identical requests differ by 4.7% in duration — enough
  that any judgement about pace from one clip per voice is noise.

### Unchanged
- Voices, both languages. UZ stays Opa Johann, TJ stays Meisam. Four Tajik
  voices were auditioned on the same line (Rustam, Firuz, Dilshod, Sherali) and
  the shared library's Tajik and Persian lists were reviewed in full: there is
  no aged, grave, native Tajik voice in it, and the model switch removed the
  reason to keep looking.
### Fixed
- `render-reel.ps1` — new `-FitScenes` switch (P194). Four 10s scene clips behind
  23s of narration played two and a half of them, and the closing beat never
  appeared in the reel. The background concat is built at full clip length while
  the final merge cuts to narration length, so any reel SHORTER than its scene
  set silently drops the tail. Latent for 106 reels: every previous adults reel
  ran 41–69s against 40s of scenes, so the concat was always the short side and
  `-stream_loop -1` covered it. R106 is the first reel shorter than its own scene
  set. `-FitScenes` trims each clip to narration / clip-count before the concat.
  Not the default and non-destructive — the 10s masters stay intact for the
  longer languages in the same set. Verified by measurement rather than by the
  log line: bg-mixed 40.0s → 22.93s, reel 3 clips → 4.

### Generator
- `app/api/generate-reel/route.ts` — rules 17–20 added (P195). Thirteen rules
  already forbade fabrication, and all four languages still re-attributed a
  paraphrase to him ﷺ in the moral — because rule 8 forbids speech BEYOND the
  hadith, and a paraphrase of the matn's own reason clause is not beyond it. The
  model was complying. The new rules name the behaviour instead of the category:
  the moral applies and never re-quotes; nothing inside an attribution that is
  not in the matn; a reason clause is one utterance, not a quote plus an act of
  explaining; no instruction to recite anything the matn does not contain.
  Evidence: eight generations across two sets, 8 of 8 on the first defect.
- Asked and answered: lowering temperature would make this worse, not better.
  These additions are the model's modal output, and lower temperature samples
  closer to the mode.

### Tools
- `scripts/generate-image.ps1` — default model moved from `fal-ai/flux-pro/v1.1`
  to `fal-ai/flux-2`, the first action taken from the new watchlist (P198).
  FLUX 2 shipped in Nov 2025 and nothing here noticed for eleven months.
  The test that settled it: the m2963 steps prompt asked for a camera at the top
  of a staircase looking DOWN — the hadith's own instruction as camera direction.
  v1.1 returned six consecutive upward shots across two prompts, and the concept
  was abandoned that afternoon as an unbreakable model prior. flux-2 rendered it
  correctly on variants 1 AND 2 of one call, same prompt text, no code change.
  **The concept was never the problem, and the response to a model refusing a
  prompt six times should have been to question the model.** v1.1 stays reachable
  via `-Model` for comparison when a prompt that used to work starts failing.

### Process
- `self_upskilling.md` — NEW (P198). Nothing in this project watched the tools it
  is built on. ElevenLabs shipped v4 on 2026-09-28 and it was found six days
  later by accident, while auditioning a Russian voice for an unrelated reason. A
  scan the next day found **Kling 3.0** (available since Feb 2026) and **FLUX 2**
  (Nov 2025) — neither previously noticed, FLUX being a full generation newer
  than the model that had just failed the same prompt six times. The roadmap's
  agent 11 cites this file as its watchlist source; the file had never existed.
  Weekly cadence, with a dated log and how to check each tool without trusting a
  release note.
- `CLAUDE.md` — session-start reading list rewritten as an ORDERED sequence of
  eight documents with `self_upskilling.md` at position 2, before anything that
  depends on a tool version. The order is load-bearing: a pronunciation
  watch-list is scoped to a model (P193), so reading it before knowing whether
  the model moved produces a confident wrong answer from a correct document.
- `animated-reel-scene-prompts.md` — section 5b, the clip naming convention
  (P197). `b` is Bukhari, `m` is Muslim; it had never been written down, which is
  how it was inferred backwards from one misnamed set and asserted as "b means
  background". The `b2628` → `m2628` rename remains OPEN, as does an audit check
  reconciling clip names against the tracker's hadith column.
- Recorded in the watchlist and not yet acted on: Anthropic's prompting guidance
  says to tell a model what TO do rather than what NOT to do. `generate-reel`
  is twenty rules, nearly all NEVER, four of them added today. This project
  already found the same principle independently as R026 on scene prompts and
  never carried it across to text.

### Found, not fixed
- P196 — `lint-content.py` only ever sees text a human has already corrected,
  because `draft.txt` is written after the block review. Discovered while about
  to add a mixed-script check that already exists and works: a probe on the exact
  corrupted Tajik line returns `[FAIL] mixed-script`. It never saw the word.
  Four "no findings" runs today were on text whose defects had already been
  removed by hand. The linter currently grades the proofreading instead of
  guarding the output, and the fix is to lint the generator's RAW output before
  review — which is automation item 3, for a better reason than convenience.

### Library
- Sahih Muslim #2963 — `text_arabic` was missing its final clause
  «فَهُوَ أَجْدَرُ أَنْ لَا تَزْدَرُوا نِعْمَةَ اللَّهِ», the reason the hadith
  gives for its own instruction, while all four translations carried it. Caught
  by reading the row before generating (P192's rule), corrected in the DB. Third
  library defect found this way in three sets — #2999 (missing clause in EN/RU),
  #2628 (a real word in the wrong place), #2963 (missing clause in AR) — and none
  of the three was findable by any gate, because every gate measures faithfulness
  TO the row.

### Assets
- Four `m2963-*` scene clips registered. The notes record the two failures beside
  the successes: `windows` is atmosphere only because FLUX smoothed the hadith's
  two-openings comparison into one pleasant courtyard across every variant, and
  `room` exists because the intended fourth clip — stone steps shot looking DOWN,
  the hadith's instruction as camera direction — came back as six consecutive
  upward shots across two prompts and was abandoned rather than paid for a third
  time.
- NAMING DEFECT FOUND, NOT YET FIXED: the scene-set prefix is the collection
  (`m2999` = Muslim, `b2654` = Bukhari), but Friday's Muslim #2628 set was named
  `b2628-*`, which points at a real and different hadith. Rename pending. The
  convention is written nowhere, and `audit-assets.py` gates on whether an asset
  is registered, not on whether its name matches the hadith it belongs to.

## [2026-10-03]

### Added
- R102–R105 — Sahih Muslim #2628 (the carrier of musk and the blower of
  bellows), EN/RU/UZ/TJ, adults. First set chosen from performance data rather
  than the slot cycle: #2654 broke out at 266K on Instagram and its Uzbek reel
  ran 223 on TikTok against 34 for #6857, and the difference is that #2654 names
  sins an ordinary person committed this week. Four new Kling 2.6 Pro scenes.
- `scripts/list-library.py` — what is in hadith_library and what has not
  shipped. `--row` dumps one hadith in every language in full (the read every
  reel should start with), `--sort length --min-en` makes matn length a
  SELECTION criterion rather than something discovered at render, and both
  reuse `audit-library.py`'s env and fetch so one place knows how to reach
  Supabase.
- `stt-validate.py` now runs inside `render-reel.ps1` at step 2b (P189). It had
  existed for seven weeks with no caller, documented in four places, catching
  three defects that human review had already passed. Runs unconditionally when
  there are subtitles, including under `-NoReview`. New `-Draft` parameter.
- `ELEVENLABS_MODEL` env override on the TTS route, so trying `eleven_v4` is a
  `.env.local` line and a restart rather than a commit. Default stays
  `eleven_v3`: P102 is the reason this pipeline is on ElevenLabs at all, and no
  release note can say whether a successor still renders ҳ қ ғ ж correctly.

### Changed
- RU adults voice: Marat → **Alex Bell** (`TUQNWEvVPBLzMBSVDPUA`, native
  Russian). Marat's own label was "Warm, Calm and Friendly" — a kids-lane
  register narrating adults-lane warnings. Changed in `VOICE_MAP`, not
  `.env.local`, because `.env.example` is explicit that the fallbacks are the
  source of truth and P118 shipped two reels in an American voice when a label
  and a fallback disagreed.
- `lint-content.py` simile markers widened (P191): Russian had «подобно» but
  not «подобен», Uzbek had «мисоли» but not «қиёслаб». Both reported clean on
  text containing an obvious comparison.
- `CLAUDE.md`: the 2026-10-01 claim that Claude's device file-commit is not
  affected by the write-revert problem is **wrong** and is corrected (P188). It
  returned `written` over an unchanged file three times in one session. Also
  `lint-content.py` described as five checks; it has nine.

### Fixed
- **A wrong word in the Uzbek matn of #2628** (P192). Both script columns
  rendered نَافِخُ الْكِيرِ with a word meaning *inspection*, so the published
  Uzbek read "the one who blows the inspection". Corrected in the DB; Latin
  regenerated with `derive-uzbek-latin.ts --library --number 2628 --commit`
  rather than hand-edited, which preserved okina versus tutuq (P097). No
  automated check could have caught it — a real, grammatical word in a
  well-formed sentence is invisible to a character-class check and to a
  faithfulness check alike.
- R103's reel was truncated after rendering — reported `OK … 11.7 MB`, found at
  2.25 MB with no moov atom, rejected by YouTube and TikTok (P190). The render's
  success check verifies exit code, existence and age; none of those is "is a
  playable video".

### Notes
- The generation added the same four things in all four languages (P191): an
  invented du'a instruction in M, a paraphrase attributed to him ﷺ as a
  quotation, a chapter claim in H, and a second simile on top of the matn's
  own — on a hadith whose entire content is a simile. Four languages is a
  prompt problem, not four slips.
- Tajik `атри` voiced as `отри`, the same а→о shift as `Даре`→`Доре` on R089.
  First Tajik defect with an explanation rather than a watch-list entry: Meisam
  is a Persian voice. The fix is Rustam at the next set, not a spelling
  workaround.
- Set durations 40.7 / 36.5 / 46.7 / 41.3s — a 28% spread, outside the ≤20%
  parity target, with Uzbek the outlier.
- This set confounds four changes at once: new hadith shape, new RU voice, and
  the model/voice switch pending for UZ and TJ. If it underperforms, the cause
  will not be cleanly attributable.

## [2026-10-01] — later

### Added
- `scripts/audit-docs.py`, wired into the pre-push hook (P187). Mechanical
  consistency checks on the docs: the tracker's declared totals against its own
  rows, reel IDs against the count, every shipped hadith against the
  duplicate-check index, every nasheed row against actual usage three ways,
  assets named against the registry, and any P-number cited above the frontier.
  Exits 1 on drift, 2 when a file cannot be read.
- Fourth instance of a gate with no caller, after P119, P126 and P185. The
  morning's fix for doc drift was a rule telling a future session to read the
  repo — which is the same shape as the thing P185 had just closed.

### Fixed
- `ramadan-bg.mp3` was used by five reels and its usage row listed four — R007
  missing since June. `light-of-my-heart-bg.mp3` declared seven uses, listed
  six, and was missing R094 from the set shipped the day before. Both found by
  audit-docs.py on its first run; both were planning a nasheed repeat, since
  the rotation is read off that table.

## [2026-10-01]

### Added
- R098–R101 — Sahih al-Bukhari #6857 (the seven destructive sins), EN/RU/UZ/TJ,
  adults. Second set from the full sourcing pipeline after #2654. Four new Kling
  2.6 Pro scenes, MODE B: whole -> ruined -> first rain -> restored. The moon and
  the lamp/niche were excluded at prompt time rather than regenerated away — the
  moon collides with انشقاق القمر, and #2654's lamp prompt had produced a temple
  shrine.

### Fixed
- `scripts/lint-content.py` read drafts as `utf-8` and reported `no S (STORY)
  block` on a valid file (P186). PowerShell 5.1's `Set-Content -Encoding utf8`
  writes a BOM, so line 1 arrives as `\ufeffS: ...`; U+FEFF is a format
  character, not whitespace, so `^\s*([SMHC])\s*:` cannot match it and ONLY the
  first block can ever vanish. Now `utf-8-sig`, which strips a BOM when present
  and is identical to `utf-8` when it is not. The missing-block advice told you
  to look inside the block above S, which does not exist; it now names the BOM
  when the missing block is S.
- R101's generated H block claimed the hadith sits in the Book of Wills. That is
  where the OTHER narration of it sits (#2766). Cut rather than replaced, since
  no other language's H names a chapter at all.

### Notes
- Uzbek TTS: «ейиш» and «етим» voice as «эйиш»/«этим» and were narrated as
  «йейиш»/«йетим». «етти» voices correctly as written, so this is NOT a rule
  about word-initial е. Narration spelling only — the caption keeps correct
  orthography.
- Whisper RU came back materially worse than EN for the second adults set
  running (R095 needed 11 of 13 cues corrected). Two sets is not a pattern yet;
  logged in the tracker rather than written up.

## [2026-09-30]

### Added
- `scripts/audit-tags.ts` — diffs the library's live `tags` column against
  TAG_CANONICAL and TAG_FORMS (P182). Exits 1 on a gap, 2 when the check could
  not run; the first draft returned 0 on an empty read, which would have made a
  misconfigured env look like a pass.
- Eleven tag concepts with four forms each: kabair, shirk, zakat, riba, fitna,
  tahara, death, neighbor, prophet, orphan, women.
- Telegram caption length is now known to the code (P184). A live counter in
  the admin, and `fitTagLine()` in lib/tags.ts, which drops English hashtags,
  then the language tag, then topic concepts until the caption fits — and says
  which. Nothing generated is ever trimmed: P116 makes length pressure on the
  generator a fabrication risk, and the matn is the caption's verifiability.
- `check_ha_formulas` in audit-library.py (P185) — х where Uzbek and Tajik take
  ҳ, across thirteen fixed honorific formulas. Found nothing in 70 rows; it is
  a regression guard.
- audit-library.py now runs `--strict` on every non-doc push. It already
  contained the check that would have caught Bukhari #574's okina, and never
  fired because nothing invoked the script.

### Changed
- Fifteen tags removed from `hadith_library` rather than translated. Each
  appeared on exactly one row and each was a descriptive word taken from that
  row's matn rather than a topic — `shield`, `rebirth`, `path`, `soul`, `time`,
  `wisdom` and the rest. Every affected row kept four or more tags, verified
  row by row before the update.
- The P106 tag blocklist moved from `app/admin/page.tsx` into `lib/tags.ts` and
  split in two (P183). `TAG_BLOCKLIST` still drops a tag whole; the new
  `EN_HASHTAG_BLOCKLIST` suppresses only the English hashtag. `death` and
  `women` moved to the second — written when every tag was English, the list
  had been dropping #ўлим and #занон to avoid #death.
- `source-candidates.py` no longer fetches HadeethEnc's four language payloads
  per candidate (P178). Nothing has read them since the adapter stopped
  carrying translations; the header comment still called them authoritative.

### Fixed

- Bukhari #574's `text_uzbek_latin` had an ASCII apostrophe where the okina
  belongs, regenerated from the canonical Cyrillic with derive-uzbek-latin.ts
  rather than patched by SQL — P097 distinguishes okina from tutuq and only the
  transliterator knows which a given position takes.

## [2026-09-29]

### Added
- `scripts/promote-candidates.py --tags` (P181) — tags are supplied for the
  batch being promoted, and the promoter refuses to write without either
  `--tags a,b` or an explicit `--no-tags`. It had hardcoded `[]` behind a true
  but irrelevant comment (*red_flags is a verifier concept*): candidates carry
  no theme data, so tags cannot be derived, and the promoter filled the gap
  with a plausible empty value rather than demanding one. Nothing downstream
  complains about an untagged row — it verifies, renders and publishes — so the
  2026-09-27 batch of five surfaced only when the library was queried for theme
  coverage, and patching it took three SQL attempts.
- `matn_intro_raw` and `matn_intro_stripped` on HadeethEnc candidates, with a
  reject on the latter in `upload-candidates.py` beside `citation_pending`.
  Three states: None (no intro field), True (removed from the matn), False
  (present but not removable by byte comparison, so the row must not promote).
- Regression tests for both intro shapes and for the unset flag. AR_PAYLOAD's
  intro/body asymmetry is now documented in the fixture as load-bearing rather
  than incidental — tidying the honorific into the body would have killed the
  test silently.

### Changed
- The HadeethEnc adapter writes none of their translations into the text
  columns and leaves `translation_source` NULL, closing P178 at the source. The
  `translations` parameter stays: it is still the fallback that finds
  `hadeeth_ar` when the payload was fetched in another language.
- Both offline test runners catch `Exception`, not `AssertionError` alone. An
  `AttributeError` was ending the whole run at the first test, so stale
  assertions surfaced one invocation at a time.

### Fixed
- `narrator` is no longer derived from `hadeeth_intro_ar`, and the intro is
  stripped from `text_arabic` when it is a byte-exact prefix (P179, closed).
  HadeethEnc carries no narrator-NAME field at all, so narrator is resolved
  with the citation like collection and hadith_number. The intro is often not
  an exact prefix — id 66511 has the honorific in the intro and not in the body
  — so the boundary is never inferred; that case is flagged and rejected at
  upload instead.
- The admin caption wrapped `hadithText` in « » unconditionally (P180), so a
  library row whose text already opened with « rendered as ««…»». #2654's Uzbek
  was one of them. The wrapper checks first now — the same guard is owed
  anywhere a sigil is concatenated onto a library column.
  - 53 library tags were reaching captions unmapped (P182), each emitting only
  its English form and losing the localised pair P150 exists to provide —
  «#maruf» shipped bare in the RU and TJ captions of Muslim #1005. 24 were
  synonyms of concepts already carrying four forms and are now aliases; 29 are
  new concepts needing translation and are deferred. The vocabulary still has
  no audit, so it will drift again.

## [2026-09-27]

### Added
- `scripts/translate-candidates.py --apply` (P177) — writes the reviewed
  `out/candidate-translations.json` to the DB with no model calls. Dry run and
  commit had been separate invocations, each generating fresh, so the JSON under
  review was never the JSON that shipped; three rolls on Bukhari #2654 gave three
  different Uzbek openings and re-introduced a gloss a previous roll had removed.
  Corrections now go in the reviewed JSON instead of an SQL patch after the write.
- Stage 2 prompt now pins three conventions, each from a defect the same day:
  honorifics in the target language's own form, no parenthetical glosses, and
  رسول الله as the Messenger rather than an envoy.
- `lib/refs.ts` — Abu Bakra added to NARRATORS (أبو بكرة, not Abu Bakr as-Siddiq).

### Changed
- HadeethEnc is now a discovery + Arabic + citation source, not a translation
  source (P178). Measured over seven candidates: in-house translations passed 8
  of 8 language-checks at high confidence, HadeethEnc's passed 0 of 5 in Russian
  and Uzbek. Its translations expand interpretively — one Arabic phrase split in
  two, حامل المسك rendered as a musk *seller*, and «бегуноҳ» (innocent) attached
  to قتل النفس, which changes the ruling. All five re-translated from the Arabic
  and re-verified; all five now pass on both models.

### Fixed
- The five HadeethEnc candidates carried the Arabic isnad in the `narrator`
  column and again at the head of `text_arabic` (P179), where the library holds a
  name and a matn. Stripped and re-translated. Closed at the source on
  2026-09-29; see that entry.

## [2026-09-26]

### Added
- `scripts/upload-candidates.py --from-json` (P175) — upload path for HadeethEnc
  candidates. Its own row mapping, deliberately not `to_row()`: the Dorar-search
  mapping writes `text_arabic` only and discards every translation, which is the
  one thing that makes a HadeethEnc candidate worth having. Per-language
  provenance goes into `translation_meta` rather than a scalar source field,
  because HadeethEnc carries all four languages for only part of its corpus — one
  field would lie about the rest. Rows land at `status='translated'`, so Stage 3
  verify and the human gate both stay ahead of promotion. Synthetic `auto-`
  numbers are refused at the door rather than deferring the failure to P174's
  guard at promotion, and `review_fuzzy` rows need `--allow-fuzzy` (G2:
  similarity never decides admission). First live batch: 5 of 6 inserted —
  Bukhari 2654 / 6871 / 6857 / 31 and Muslim 2628, all four languages each;
  Muslim 2759 correctly dropped as a hard duplicate of the live library.
  `text_uzbek_latin` left NULL by design — `scripts/derive-uzbek-latin.ts`
  already owns the tested transliteration (P097).

  - `translation_source` now reaches the caption (P176) — `buildTranslationCredit()`
  in `lib/refs.ts`, wired through the `/api/reels` select and the admin caption
  assembly. A separate line from the citation and a different label from the
  seerah source, so one caption never carries two lines called Источник pointing
  at different things. Emits nothing at all on in-house rows, newline included.
  Proven both ways on Bukhari #6018: NULL leaves the caption unchanged;
  'hadeethenc.com' renders «🌐 Таржима: HadeethEnc.com» in UZ and «🌐 Перевод:»
  in RU, from the label map rather than the English fallback.

## [2026-09-09]

### Added
- Five-mascot rotation for the kids lane. `camel-dawn-v1`, `hoopoe-garden-v1`
  and `bee-orchard-v1` registered in `assets/asset-registry.json` alongside the
  two lambs, all human-verified, all approved for the kids lane only. Each is a
  Qur'anic animal in regional dress with its own cap, palette and nature
  setting — deliberately not all Central Asian, since the audience is heavily
  Russian-speaking and includes Tatars, Chechens and Azerbaijanis. Driven by
  analytics read for the first time this session: kids reels draw 4–180 views
  against 1,500–4,800 for adults, and the Instagram grid had become fifteen
  near-identical lamb thumbnails. Backgrounds are nature, never mosque
  architecture. Still to generate: horse (Tatar kalfak), ant (Chechen papakha).

### Changed
- Voice selection now follows the mascot's GENDER rather than lamb identity
  (P104 generalised). No new voice slots: male mascots take Eric / Maxim /
  George / Liam Viral, female mascots Danielle / Arabella / Mini / Katherine.
- Kids captions address the parent rather than the child («Покажите детям»).
  Kids cadence set to weekly, measured on views, shares and comments over a
  two-week window.
- `assets/asset-registry.json` — registry date bumped to 2026-09-09.


## [2026-08-29
]
### Added
- `lint-content.py` structural checks (P128): `missing-block` and `duplicate-block`. Verified in both directions before shipping — clean input silent, a dropped `C:` label raises WARN, and identical S/M blocks raise FAIL — then confirmed no false positive on the real TJ #2999 draft. Check count 5 → 7.
## [2026-08-24]

### Added
- `scripts/verify-candidates.py` — Stage 3 of the sourcing pipeline. Two independent passes (`claude-sonnet-5` + `gpt-5.6-terra`) on translation faithfulness, dry-run by default. Agreement state machine unit-proven before any API spend: error-on-either-side is a disagreement, and an empty result rolls up to `disagree` rather than defaulting to pass. Proven to fail as well as pass — a planted invented action and ranking in the English was caught by both models at high confidence with the other three languages clean. Bukhari #527 now sits at `status='verified'`. Stage 4 (human gate) remains SQL by choice; live sourcing still blocked on Sunnah API issue #3675.

## [2026-08-23]
### Added
- `scripts/derive-uzbek-latin.ts` — fills `text_uzbek_latin` from the canonical Cyrillic via the tested `deriveBothScripts`, dry-run by default. Completes Stage 2 end to end: Bukhari #527 now carries all five language columns at `status='translated'` (EN 118 / RU 128 / UZ-Cyr 137 / UZ-Lat 144 / TJ 108 chars) and audits clean with zero findings. Length spread across languages is 27%, against 67% for the same hadith's shipped reels — translating each language independently from the Arabic gives more even output than paraphrasing.
- `scripts/translate-candidates.py` — Stage 2 of the sourcing pipeline. Translates a candidate's Arabic matn into EN/RU/UZ-Cyrillic/TJ with per-field provenance, dry-run by default. Validated on the seeded Bukhari #527: all four outputs reproduce the four moves of the matn with nothing added, and the Tajik came back «Некӣ» with U+04E3 — the exact defect that shipped in R037 did not recur when translating from the Arabic rather than from `text_uzbek`, which is what P075 did. Model `claude-sonnet-5`. Stage 3 must use a different model for pass B (D2): a model may not be the sole verifier of its own output.


## [2026-08-21]

### Added
- `scripts/audit-library.py` — fourth agent. Per-language integrity checks over `hadith_library` and `hadith_candidates`. Validated in both directions before shipping: fires on every real defect from the log (P050 Russian fallback, R027 homoglyph, R024 okina, R036 script mixing, daif grade, homepage-only URL), and produces zero false positives on the four legitimate short Tajik rows (Muslim 82, Tirmidhi 2396, Abu Dawud 1479, Bayhaqi 2318) that contain no Tajik-specific letters but are genuine translations. Baseline: all 69 library rows clean. Catches the defect class `lint-content.py` structurally cannot see, since it reads generated text rather than source rows.

### Fixed
- Pre-push hook was structurally blind to Python. There was no `.py` category: a Python file counted as non-doc, so the hook did not skip, ran `npx tsc --noEmit`, saw clean TypeScript and pushed. All four agents — `lint-content.py`, `stt-validate.py`, `audit-assets.py`, `audit-library.py` — had no pre-push coverage at all. Added a `Py` category that syntax-parses every changed `.py` and runs the offline `scripts/lib` suite (49 tests, ~0.2s). Proven in both directions: a deliberately broken file blocks the push, a valid one passes. Also set `core.hooksPath=.githooks`, which was unset — Git had been reading `.git/hooks/pre-push`, so the tracked hook was decorative and every fix to it lived only on one machine.
## [2026-08-15]

### Added
- `assets/asset-registry.json` and `scripts/audit-assets.py` — per-asset
  classification and lane approval, enforced as a hard gate in both render
  paths (P117). 21 of 27 entries await human verification.
- `scripts/stt-validate.py` — offline subtitle validator diffing the
  Whisper SRT against its source narration text. Word-level alignment plus
  homoglyph detection. Found two Latin homoglyphs in published R027 subtitles
  on first run.
- `scripts/lint-content.py` — warn-only content linter running five
  deterministic checks (divine name, unnamed authority, seerah source, simile
  vs matn, meaning inversion) on generated text before TTS. Encodes P105, P111
  and P115. Validated against R022–R029.

### Fixed
- Uzbek Latin orthography normalized across all 74 `hadith_library` rows: okina (U+02BB)
  in `oʻ`/`gʻ`, tutuq (U+02BC) for the glottal stop. Previously 41 rows carried ASCII `'`.
- `scripts/lib/uzbek-translit.ts`: `deriveBothScripts()` returned the raw Latin source
  unnormalized; now routed through the new exported `normalizeLatinApostrophes()` in both
  branches (P097).
- `scripts/promote-candidates.py`: legacy `text_uzbek` now filled from `text_uzbek_latin`
  rather than Cyrillic, matching the column's back-compat purpose and all 74 existing rows.

### Added
- `normalizeLatinApostrophes()` — context-based okina/tutuq folding, with 5 tests
  including a regression test for the passthrough defect.


### Fixed
- Legacy Uzbek two-script backfill applied to all 74 `hadith_library` rows —
  `text_uzbek_cyrillic` and `text_uzbek_latin` now populated (74/74, 0 failed).
  Script built 2026-06-14 (`7b1946c`), unrun until now.
- `scripts/apply-uzbek-scripts.ts`: added `--skip-source-fix` to suppress replay of
  June-era `text_uzbek` corrections on the 9 mixed rows already cleaned in production.
- `scripts/apply-uzbek-scripts.ts`: `.update()` now chains `.select('id')` and reports
  zero-row matches as failures instead of silent successes (P096).
- `scripts/apply-uzbek-scripts.ts`: dry-run preview no longer claims it will correct
  `text_uzbek` when `--skip-source-fix` is active.


## [2026-06-13] (cont.)

### Added
- **`split-narration.py`** — silence-aware narration splitter. Concats
  story+moral, then cuts into ordered <=28s chunks at natural pauses (ffmpeg
  silencedetect) so each fits fal Fabric's ~30s cap. Outputs
  out/talking/<base>-clipNN.mp3 + a ready generate/render block.
- **First real kids reel shipped:** kids-en-bukhari-6009 (girl lamb, thirsty-dog
  hadith), full chain: library → admin → split → Fabric → render-mascot-reel.
- **Hadith library:** added Sahih al-Bukhari 6009 (kindness to animals) in
  AR/EN/UZ/RU to hadith_library (TJ via RU fallback, P050).

## [2026-06-13] (continued)

### Added
- **Scene-baked mascots (Route A).** Mascots are now generated *inside* a
  scene via Nano Banana Pro using a locked mascot still as a face reference,
  so face/outfit stay consistent while the environment changes. Fabric then
  animates lamb + scene together. Assets: `assets/mascot/lamb-boy-mosque-night-v2.png`,
  `assets/mascot/lamb-girl-garden-day-v1.png`.
- **`render-mascot-reel.ps1`** — kids talking-mascot reel renderer. Talking
  clips (Fabric) are the spine; nasheed mixes under the voice at 0.20;
  optional burned subs (skipped uz/tj per P078); output
  `out/kids-{lang}-{slug}-mascot-reel.mp4`.

### Notes
- Route-A limitation: Fabric animates the whole frame, so anything directly
  above the head drifts with head motion. Mitigation: keep moon/large objects
  offset to a corner with empty headroom above the mascot. Route B
  (green-screen composite) deferred for fully-static backgrounds.

## [2026-06-13]

### Added
- **Talking-mascot kids lane (proof-of-concept proven).** New
  `generate-talking-clip.py` turns a mascot still + TTS audio into a
  lip-synced talking-mascot MP4 via fal **VEED Fabric 1.0**
  (`veed/fabric-1.0`; inputs `image_url` + `audio_url` + `resolution`;
  returns MP4 URL). Verified end-to-end at 480p:
  `assets/mascot/lamb-boy-v1.png` + `out/adults-en-bukhari-1520-moral.mp3`
  → `out/talking/test-boy.mp4`.
- **Two consistent lamb mascots** (Nano Banana Pro / Gemini): `lamb-boy-v1`
  (blue yakhtak + belbog + tyubeteika) and `lamb-girl-v1` (vibrant
  khan-atlas dress + braids), stored in tracked `assets/mascot/`.
  Generic animal mascots only — never sacred figures.
## [2026-06-11] — Animated reel pipeline + multi-platform launch

### Added (Pillar 2 — Animated reels)
- `render-reel.ps1` — automates Pillar 1 Steps 4–7 in one command; `-Scenes` mode stitches ordered animated clips with per-clip 1080×1920 @ 30fps normalization
- `generate-scene.ps1` — fal.ai Kling text-to-video AND image-to-video (animate your own photos to fix hands/Kaaba the model gets wrong)
- `generate-image.ps1` — fal.ai FLUX text-to-image (still frames for review before animating — image-first workflow)
- `animated-reel-scene-prompts.md` — scene-prompt design spec with religious guardrails ("themes not figures", MODE B = no faces, era→setting/dress map)

### Fixed
- P079 — admin story/moral/seerah now editable `<textarea>`s; fix translation errors before TTS (no regenerate cycle)
- P081 — Whisper `--max_line_width` orphaned-flag failure in render-reel.ps1
- P082 — mixed-framerate clips flashing by in animated stitch (now per-clip fps-normalized)
- Watch Reels tab — language-aware social links pointing to real `@SahihHadithReels` channels; replaced stale "coming soon" copy

### Published
- First animated reel: RU adults, Sahih al-Bukhari #1520 (women's Hajj as jihad), 4 scenes — live on Telegram + YouTube + Instagram + TikTok
- Brand identity set up on all 4 platforms (@SahihHadithReels, anonymous brand accounts)

### Process
- Documentation-discipline rule added to CLAUDE.md (both HV + HR): every fix/feature documented in-session

## [2026-05-10] — Initial deployment

### Deployed
- hadith-reels.vercel.app live on Vercel
- All env vars configured (Production + Preview)
- GitHub secrets added (ANTHROPIC, ELEVENLABS, SUPABASE)
- Build: Next.js 16.2.6 Turbopack — 0 errors

### Infrastructure
- Shared Supabase DB with hadith-verifier
- Voice matrix: AR/UZ/RU/TJ × Adults/Kids × 3 roles
- 8 themes: 4 adult + 4 kids
- Stub API routes: /api/tts, /api/reels, /api/search, /api/generate-reel
