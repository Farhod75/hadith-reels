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
