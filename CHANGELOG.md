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