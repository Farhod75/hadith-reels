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