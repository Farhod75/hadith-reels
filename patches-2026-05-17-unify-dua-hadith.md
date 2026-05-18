# patches-2026-05-17-unify-dua-hadith.md
# Documentation patches: Unify dua + hadith content tracks
# Date: 2026-05-17 (Sunday morning, pre-Hajj)
# Author: Farhod Elbekov + Claude session
# Purpose: Make explicit that dua reels and hadith reels share the same
#          tracker, same pipeline, and same agent fleet — they are not
#          parallel tracks.

This file contains 3 small patches to apply to existing project docs.
Apply them in order. Each patch is a search-and-replace operation.

If applied via PowerShell, the recommended workflow is below at the bottom.
Otherwise, manual copy-paste into VS Code also works.

═══════════════════════════════════════════════════════════════════════
## PATCH 1 — agent-architecture-roadmap.md
═══════════════════════════════════════════════════════════════════════

**File:** hadith-reels/agent-architecture-roadmap.md
**Target section:** P3.1 (Database tracker), after the `CREATE TABLE reels_posted` block

### Find this exact block:

```
CREATE UNIQUE INDEX idx_no_duplicates
  ON reels_posted (hadith_collection, hadith_number, language, style);
```

### Replace with:

```
CREATE UNIQUE INDEX idx_no_duplicates
  ON reels_posted (hadith_collection, hadith_number, language, style);

-- Content type extension (added 2026-05-17 — dua series unification)
ALTER TABLE reels_posted
  ADD COLUMN content_type TEXT NOT NULL DEFAULT 'hadith';
-- valid values: 'hadith' | 'dua'

ALTER TABLE reels_posted
  ADD COLUMN dua_id BIGINT REFERENCES duas(id);
-- NULL for hadith reels; populated for dua reels

-- Separate table for dua source content (same shape as hadiths table)
CREATE TABLE duas (
  id                 BIGSERIAL PRIMARY KEY,
  source_type        TEXT NOT NULL,           -- 'quran' | 'hadith'
  source_collection  TEXT NOT NULL,           -- 'Quran' | 'Sahih al-Bukhari' | ...
  source_reference   TEXT NOT NULL,           -- '2:201' | '#6398' | ...
  arabic_text        TEXT NOT NULL,           -- pulled from Sunnah.com / Quran.com (Tier 1)
  grade              TEXT NOT NULL,           -- 'sahih' | 'hasan' (NEVER daif)
  category           TEXT NOT NULL,           -- 'paradise_protection' | 'forgiveness' | ...
  tags               TEXT[],

  -- Per-language translations (generated once via Claude, cached for reuse)
  text_en            TEXT,
  text_ru            TEXT,
  text_uz            TEXT,
  text_ar            TEXT,
  text_tj            TEXT,
  text_ar_translit   TEXT,                    -- optional transliteration

  status             TEXT DEFAULT 'identified',
                     -- 'identified' | 'researched' | 'translated' | 'audio_ready' | 'reel_made'
  added_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Duplicate prevention for duas works the same as for hadiths
CREATE UNIQUE INDEX idx_no_duplicate_duas
  ON reels_posted (dua_id, language, style)
  WHERE content_type = 'dua';
```

### Then find this block:

```
API endpoints:
- `POST /api/check-duplicate` → 200 if available, 409 if duplicate
- `POST /api/log-reel` → write a new entry (called by Publisher)
- `GET /api/coverage-gaps` → returns themes/langs that are underserved
- `GET /api/asset-usage?asset=mubarak-bg.mp3` → returns last N uses
```

### Replace with:

```
API endpoints:
- `POST /api/check-duplicate` → 200 if available, 409 if duplicate
  - Accepts: `{ content_type, hadith_collection?, hadith_number?, dua_id?, language, style }`
  - Works for both hadith and dua reels via the `content_type` discriminator
- `POST /api/log-reel` → write a new entry (called by Publisher)
- `GET /api/coverage-gaps` → returns themes/langs/content_types that are underserved
- `GET /api/asset-usage?asset=mubarak-bg.mp3` → returns last N uses
- `GET /api/duas?status=translated` → list duas ready for reel production
- `POST /api/duas` → add a new dua (after Tier 1 source verification)
```


═══════════════════════════════════════════════════════════════════════
## PATCH 2 — reel-tracker.md
═══════════════════════════════════════════════════════════════════════

**File:** hadith-reels/reel-tracker.md
**Target section:** Active reels table header + template row

### Find this exact header row:

```
| Reel ID | Date | Hadith | Narrator | Grade | Theme | Tags | Lang | Style | Story Keyword | Story MP3 | Moral MP3 | Full Narration MP3 | Bg Clips Used | Bg Video Output | Nasheed | Subtitles | Output MP4 | Duration | Size | Notes |
```

### Replace with:

```
| Reel ID | Date | Content Type | Source | Narrator | Grade | Theme | Tags | Lang | Style | Story Keyword | Story MP3 | Moral MP3 | Full Narration MP3 | Bg Clips Used | Bg Video Output | Nasheed | Subtitles | Output MP4 | Duration | Size | Notes |
```

**Column changes:**
- Added: `Content Type` (values: `hadith` | `dua`)
- Renamed: `Hadith` → `Source` (more general — now holds either "Sahih al-Bukhari #1520" or "Sunan Abu Dawud #792 (dua)" or "Quran 2:201 (dua)")

### Then find the divider row (the |---|---|... row right after the header):

```
|---------|------|--------|----------|-------|-------|------|------|-------|---------------|-----------|-----------|---------------------|---------------|-----------------|---------|-----------|------------|----------|------|-------|
```

### Replace with:

```
|---------|------|--------------|--------|----------|-------|-------|------|------|-------|---------------|-----------|-----------|---------------------|---------------|-----------------|---------|-----------|------------|----------|------|-------|
```

### Then find the existing R001-R005 rows and update them — for each row, INSERT a new `hadith` value as the third column (after Date). Example for R001:

**Before:**
```
| R001 | 2026-05-12* | Jami at-Tirmidhi #3373 | Abu Hurairah | ...
```

**After:**
```
| R001 | 2026-05-12* | hadith | Jami at-Tirmidhi #3373 | Abu Hurairah | ...
```

**Apply the same insertion to R002, R003, R004, R005** — all are `hadith` (no dua reels exist yet).

### Then find this template row block:

```
## Template — adding new reels

When you ship a reel, copy this row to the "Active reels" table:

```markdown
| R### | YYYY-MM-DD | <Collection> #<num> | <Narrator> | <Grade> | <Theme> | #tag1 #tag2 | <Lang> | <Style> | <slug> | <slug>-story-narration-<lang>.mp3 | <slug>-moral-narration-<lang>.mp3 | <slug>-narration-<lang>-full.mp3 | clip1.mp4, clip2.mp4, clip3.mp4 | <lang>-<style>-bg-mixed.mp4 | <nasheed>.mp3 | Yes/No | <output>.mp4 | XXs | XX MB | <notes> |
```
```

### Replace with:

```
## Template — adding new reels

When you ship a reel, copy ONE of these template rows to the "Active reels" table.
The pipeline is the same for both — only the `Content Type` and `Source` columns differ.

### Template for hadith reels:

```markdown
| R### | YYYY-MM-DD | hadith | <Collection> #<num> | <Narrator> | <Grade> | <Theme> | #tag1 #tag2 | <Lang> | <Style> | <slug> | <slug>-story-narration-<lang>.mp3 | <slug>-moral-narration-<lang>.mp3 | <slug>-narration-<lang>-full.mp3 | clip1.mp4, clip2.mp4, clip3.mp4 | <lang>-<style>-bg-mixed.mp4 | <nasheed>.mp3 | Yes/No | <output>.mp4 | XXs | XX MB | <notes> |
```

### Template for dua reels:

```markdown
| R### | YYYY-MM-DD | dua | <Quran X:Y or Hadith Collection #N> | <Narrator if hadith, "—" if Quran> | <Grade> | Dua: <category> | #dua #tag2 | <Lang> | <Style> | <slug> | <slug>-narration-<lang>.mp3 | — (no moral, or short moral) | <slug>-narration-<lang>-full.mp3 | clip1.mp4, clip2.mp4 | <lang>-<style>-bg-mixed.mp4 | <nasheed>.mp3 | Yes/No | <output>.mp4 | XXs | XX MB | <notes — cite Quran ayah or hadith number again> |
```

**Key differences for dua reels:**
- `Content Type = dua`
- `Source` = either Quran reference (`Quran 2:201`) or Hadith reference (`Sunan Abu Dawud #792`)
- `Narrator` = either the Companion who transmitted (for hadith duas) or `—` for Quran duas (since they're divine words, not narrated)
- `Theme` should start with `Dua: ` prefix to distinguish in the duplicate-check index
- `Moral MP3` may be omitted or shortened — dua reels are typically Arabic recitation + translation, no separate moral narration needed (though optional)
```

### Then find this block in the "Duplicate-check index" section:

```
## Duplicate-check index (by hadith)

> **Use this first before producing.** If your target hadith appears here in the target language + style, do NOT duplicate.

| Hadith | Languages Posted | Styles Posted | Reel IDs |
|---|---|---|---|
```

### Replace with:

```
## Duplicate-check index (by source)

> **Use this first before producing.** If your target source appears here in the target language + style, do NOT duplicate.
> Hadith reels and dua reels share this index — same source can have BOTH a hadith reel and a dua reel only if the dua is genuinely separate content (e.g., a hadith containing a dua might warrant both reels, but most won't).

| Source | Content Type | Languages Posted | Styles Posted | Reel IDs |
|---|---|---|---|---|
```

### Update each existing row in the duplicate-check index to add the Content Type column. Example:

**Before:**
```
| Jami at-Tirmidhi #3373 | RU | Adults | R001 |
```

**After:**
```
| Jami at-Tirmidhi #3373 | hadith | RU | Adults | R001 |
```

Apply to all 5 existing rows.


═══════════════════════════════════════════════════════════════════════
## PATCH 3 — reel-creation-pipeline.md
═══════════════════════════════════════════════════════════════════════

**File:** hadith-reels/reel-creation-pipeline.md
**Target section:** STEP 1 — Admin: Pick hadith + generate content

### Find this block:

```
## STEP 1 — Admin: Pick hadith + generate content
================================================================

1. Open browser: `http://localhost:3002/admin`
2. Login with ADMIN_PASSWORD
3. **Step 1 (Pick) in the admin UI:**
   - Select **Style:** Adults or Kids
   - Select **Language:** EN / UZ / AR / RU / TJ
   - Filter by tag (e.g. "hajj", "fasting") or grade (sahih/hasan)
   - Pick the hadith from the library
4. **Step 2 (Generate) in the admin UI:**
   - Click "🤖 Generate story + moral + seerah context"
   - Wait ~30 seconds for Claude
```

### Replace with:

```
## STEP 1 — Admin: Pick content (hadith OR dua) + generate
================================================================

This pipeline serves BOTH hadith reels and dua reels. The only difference is
which content source is picked in the admin. Everything from Step 2 onward
is identical.

### 1A — For hadith reels:

1. Open browser: `http://localhost:3002/admin`
2. Login with ADMIN_PASSWORD
3. **Step 1 (Pick) in the admin UI:**
   - Select **Content Type:** Hadith
   - Select **Style:** Adults or Kids
   - Select **Language:** EN / UZ / AR / RU / TJ
   - Filter by tag (e.g. "hajj", "fasting") or grade (sahih/hasan)
   - Pick the hadith from the library
4. **Step 2 (Generate) in the admin UI:**
   - Click "🤖 Generate story + moral + seerah context"
   - Wait ~30 seconds for Claude

### 1B — For dua reels:

1. Open browser: `http://localhost:3002/admin`
2. Login with ADMIN_PASSWORD
3. **Pre-flight (one-time per dua) — research source if not yet in `duas` table:**
   - Identify whether the dua is from Quran or hadith
   - For Quran: find the ayah on Quran.com (e.g. Quran 2:201)
   - For hadith: find the dua on Sunnah.com, note collection + number
   - Verify grade on Dorar.net if hadith-based (must be sahih or hasan)
   - Add to `duas` table via admin or direct INSERT
4. **Step 1 (Pick) in the admin UI:**
   - Select **Content Type:** Dua
   - Select **Style:** Adults or Kids
   - Select **Language:** EN / UZ / AR / RU / TJ
   - Filter by category (e.g. "forgiveness", "protection", "guidance")
   - Pick the dua from the duas library
5. **Step 2 (Generate) in the admin UI:**
   - Click "🤖 Generate translation + context"
   - For duas, the generator produces:
     - Translation in target language (if not already cached in `duas` table)
     - A brief context paragraph (when this dua is used, what occasions, etc.)
     - Optional: a short moral/reflection in target language
   - Wait ~30 seconds for Claude

### Why one pipeline for both:

- Same Admin UI (with a Content Type toggle)
- Same FFmpeg merge command in Step 7
- Same Telegram posting flow in Step 8
- Same `reel-tracker.md` schema
- Same duplicate-check API
- Same Auditor agent (when Phase 4 of agent fleet ships)

**The only divergence is upstream source research** — duas need Tier 1 verification
of the Arabic source + grade BEFORE the admin sees them. Hadiths are already
in the library because that was done at library-build time.

### Notes on dua reels specifically:

- Arabic recitation should be more reverent than story narration —
  consider Option B (qari partnership) from `dua-reel-series-backlog.md`
- Subtitles for dua reels: ALWAYS show the Arabic + the translation
  (P078 Whisper limitation doesn't apply — Arabic is its own line)
- Background music for dua reels: prefer contemplative (`mubarak-bg.mp3`,
  `light-of-my-heart-bg.mp3`) over upbeat options
- Caption MUST include the source citation (Quran ayah # or hadith collection #)
  — channel credibility depends on it
```


═══════════════════════════════════════════════════════════════════════
## Recommended application workflow (PowerShell)
═══════════════════════════════════════════════════════════════════════

These patches are small enough to apply by hand in VS Code (Ctrl+F → paste old → paste new),
which is what I'd actually recommend tonight given you're 2 days from Hajj.

However, if you want to apply them programmatically:

```powershell
cd "C:\QA\Hadith verification AI app\hadith-reels"

# Download this patch file from Claude session
# Then for each patch, open the target file in VS Code:
code agent-architecture-roadmap.md
code reel-tracker.md
code reel-creation-pipeline.md

# Apply the find/replace blocks manually (Ctrl+H in VS Code)
# Verify each file renders correctly in Markdown preview

# Atomic commit per file is FINE for doc updates,
# but since these 3 patches are conceptually ONE change ("unify dua + hadith tracks"),
# a single bundled commit is also fine:

git add agent-architecture-roadmap.md reel-tracker.md reel-creation-pipeline.md
git status
git commit -m "docs: unify dua + hadith content tracks across roadmap, tracker, and pipeline"
git push
```


═══════════════════════════════════════════════════════════════════════
## Honest engineering notes
═══════════════════════════════════════════════════════════════════════

**Why these specific patches:**

1. **Patch 1 (DB schema)** is the most important. If the DB design has duas as a separate
   table with FK to `reels_posted.dua_id`, then automation works correctly. Without this,
   you'd end up either (a) cramming duas into the `hadiths` table with NULL columns, or
   (b) duplicating the entire schema for "dua_reels_posted" — both bad.

2. **Patch 2 (tracker)** is the smallest but most user-facing. You'll look at this file
   often during production. Getting the columns right now saves rewrites later.

3. **Patch 3 (pipeline)** is the most operational. It tells future-you (or future Claude)
   exactly what the workflow looks like for duas vs hadiths.

**Why this is the right time to do these patches:**

- They're conceptual unifications, not new features
- They don't require any code changes (DB migration is in the FUTURE per P3.1 of roadmap)
- They're cheap insurance: if you start the dua series in 3 months without these patches,
  Future Claude will have to re-derive the unification from scratch and may get it wrong

**Why I'm NOT touching dua-reel-series-backlog.md in these patches:**

That file already has a "Integration with existing systems" section that's correct.
It anticipated this unification. Leaving it as-is keeps it focused on its job (Phase 1 planning).


═══════════════════════════════════════════════════════════════════════
## Change log
═══════════════════════════════════════════════════════════════════════

| Date | Change | By |
|---|---|---|
| 2026-05-17 | Initial patches drafted for dua + hadith unification | Farhod / Claude session |
