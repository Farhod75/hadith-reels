## [2026-10-09]

### Added
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
