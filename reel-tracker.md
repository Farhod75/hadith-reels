# reel-tracker.md
# Hadith Reels — Channel Content Log

> **Channel:** @SahihHadithReels
> **Tracker started:** 2026-05-16 (retroactive backfill included)
> **Owner:** Farhod Elbekov
> **Purpose:** Prevent duplicate posts, track asset reuse, content planning
> **Update protocol:** Add a new row IMMEDIATELY after each successful Telegram post

## How to use this tracker

1. **Before producing a new reel** — search the "Duplicate-check index" below for the hadith number. If it's listed and the target language already exists, pick a different hadith or different language.
2. **After posting a reel** — append a new row to "Active reels" table AND update the "Duplicate-check index". Both must stay in sync.
3. **Asset reuse check** — before picking a background nasheed or video clip set, scan the relevant columns to avoid back-to-back reuse.
4. **Reel IDs are sequential** — never reuse an ID, even if a reel is deleted. Mark deleted entries with a strikethrough and note in "Notes" column.

---

## Active reels

| Reel ID | Date | Hadith | Narrator | Grade | Theme | Tags | Lang | Style | Story Keyword | Story MP3 | Moral MP3 | Full Narration MP3 | Bg Clips Used | Bg Video Output | Nasheed | Subtitles | Output MP4 | Duration | Size | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R001 | 2026-05-12* | Jami at-Tirmidhi #3373 | Abu Hurairah | Hasan | Dua / Supplication | #dua #supplication #allah #asking #worship | RU | Adults | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | First reel posted (pre-tracker). Backfill post-Hajj. |
| R002 | 2026-05-13* | Sahih al-Bukhari #1894 | Abu Hurairah | Sahih | Fasting / Ramadan | #ramadan #fasting #forgiveness | EN | Adults | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Source: Ar-Raheeq Al-Makhtum. Backfill post-Hajj. |
| R003 | 2026-05-14* | Jami at-Tirmidhi #1956 | Abu Dharr | Hasan | Charity / Akhlaq | #smile #charity #akhlaq #brotherhood | UZ | Adults | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Smile-as-charity hadith. Source: Усваи Ҳасана. Backfill post-Hajj. |
| R004 | 2026-05-15 | Sahih al-Bukhari #1773 | Abu Hurairah | Sahih (mutafaqun alayh) | Hajj / Umrah | #hajj #umrah #expiation #pilgrimage #mabrur | TJ | Adults | umra-to-umra | umra-to-umra-narration.mp3 | umra-to-umra-moral-narration.mp3 | umra-to-umra-narration-full.mp3 | TBD (3 random of 6) | tj-adults-bg-mixed.mp4 | path-to-jannah-bg.mp3 | No (P078 — UZ/TJ Whisper Latin drift) | adults-tj-umra-reel-v2.mp4 | 50.7s | 33 MB | Source: Сарчашма: Усваи Ҳасана. Pre-Hajj pick. |
| R005 | 2026-05-16 | Sahih al-Bukhari #1520 | Aisha | Sahih | Hajj / Women's jihad | #hajj #jihad #women #pilgrimage #mabrur #virtue | RU | Adults | hajj-women | hajj-women-story-narration-ru.mp3 | hajj-women-moral-narration-ru.mp3 | hajj-women-narration-ru-full.mp3 | 3 random from out/backgrounds/new/normalized/ | ru-adults-bg-mixed.mp4 | mubarak-bg.mp3 | No (regenerate cycle, audio fixed, subs skipped to ship clean) | adults-ru-hajj-women-reel-v2.mp4 | 49.1s | 22 MB | Source: Источник: Усваи Хасана. Required 1 regenerate cycle (P079 — "Послание к Аллаха" → "Посланник Аллаха"). |

*Approximate dates for R001-R003 — confirm via Telegram channel history post-Hajj.

---

## Duplicate-check index (by hadith)

> **Use this first before producing.** If your target hadith appears here in the target language + style, do NOT duplicate.

| Hadith | Languages Posted | Styles Posted | Reel IDs |
|---|---|---|---|
| Jami at-Tirmidhi #3373 | RU | Adults | R001 |
| Sahih al-Bukhari #1894 | EN | Adults | R002 |
| Jami at-Tirmidhi #1956 | UZ | Adults | R003 |
| Sahih al-Bukhari #1773 | TJ | Adults | R004 |
| Sahih al-Bukhari #1520 | RU | Adults | R005 |

---

## Theme coverage (by category)

> **Use for content planning** — what themes is the channel light/heavy on?

| Theme | Count | Reel IDs | Languages covered |
|---|---|---|---|
| Hajj / Umrah | 1 | R004 | TJ |
| Hajj / Women's jihad | 1 | R005 | RU |
| Fasting / Ramadan | 1 | R002 | EN |
| Charity / Akhlaq | 1 | R003 | UZ |
| Dua / Supplication | 1 | R001 | RU |

**Coverage gaps to consider for upcoming reels:**

- ❌ Zakat / Wealth purification — no reels yet
- ❌ Salah / Prayer — no reels yet
- ❌ Tawheed / Aqeedah basics — no reels yet
- ❌ Akhlaq / Patience / Anger management — no reels yet (smile-as-charity is the only one)
- ❌ Family / Marriage / Parents — no reels yet
- ❌ Quran recitation / Tilawah — no reels yet
- ❌ Death / Afterlife / Barzakh — no reels yet

**Language coverage gaps:**

- AR (Arabic) — 0 reels (gap!)
- Kids style — 0 reels in any language (gap!)

---

## Asset reuse audit

> **Use to avoid asset fatigue** — same nasheed/clips on consecutive reels feels lazy to viewers.

### Nasheed usage

| Nasheed | Uses | Last used | Reel IDs |
|---|---|---|---|
| path-to-jannah-bg.mp3 | 1 | 2026-05-15 (R004) | R004 |
| mubarak-bg.mp3 | 1 | 2026-05-16 (R005) | R005 |
| nasheed-bg-1.mp3 | 0 | Never | — |
| light-of-my-heart-bg.mp3 | 0 | Never | — |
| ramadan-bg.mp3 | 0 | Never | — |
| ramadan-1-bg.mp3 | 0 | Never | — |
| ramadan-2-bg.mp3 | 0 | Never | — |

### Background video clips (normalized library, 1080×1920)

| Clip | Uses | Reel IDs |
|---|---|---|
| kaaba.mp4 | TBD | TBD (R004 or R005 random pick) |
| kaaba-roof.mp4 | TBD | TBD |
| kaaba-balcony.mp4 | TBD | TBD |
| kaaba-crowd.mp4 | TBD | TBD |
| Kaaba-drone.mp4 | TBD | TBD |
| makka-tower.mp4 | TBD | TBD |

**Note:** R004 and R005 used `Get-Random -Count 3` from the library. Exact clip combinations weren't logged at production time. Future reels: log explicit clip filenames via the random-pick PowerShell output line.

### Production rule of thumb

- Don't use the same nasheed on **2 consecutive reels in the same language**
- Don't reuse the exact same 3-clip combination within **5 consecutive reels** (math: 6 clips choose 3 = 20 combos, so 1-in-20 collision is unlikely if random, but check)
- After 10 reels, rotate in 3-5 new background clips from Pexels to refresh the library

---

## Production stats

| Metric | Value |
|---|---|
| Total reels posted | 5 |
| Languages active | 4 (RU, EN, UZ, TJ) |
| Languages remaining | 1 (AR) |
| Adults reels | 5 |
| Kids reels | 0 |
| Avg duration | ~50s |
| Avg file size | ~28 MB |
| Hadiths used (unique) | 5 |
| Hadith collections used | 2 (Sahih al-Bukhari ×3, Jami at-Tirmidhi ×2) |
| Companions cited | 3 (Abu Hurairah ×3, Abu Dharr ×1, Aisha ×1) |

---

## Template — adding new reels

When you ship a reel, copy this row to the "Active reels" table:

```markdown
| R### | YYYY-MM-DD | <Collection> #<num> | <Narrator> | <Grade> | <Theme> | #tag1 #tag2 | <Lang> | <Style> | <slug> | <slug>-story-narration-<lang>.mp3 | <slug>-moral-narration-<lang>.mp3 | <slug>-narration-<lang>-full.mp3 | clip1.mp4, clip2.mp4, clip3.mp4 | <lang>-<style>-bg-mixed.mp4 | <nasheed>.mp3 | Yes/No | <output>.mp4 | XXs | XX MB | <notes> |
```

Then update:
1. **Duplicate-check index** — new row OR add lang/style to existing hadith row
2. **Theme coverage** — increment count, add reel ID
3. **Asset reuse audit** — increment nasheed counter, log clip filenames
4. **Production stats** — bump totals

---

## Related files

- `reel-creation-pipeline.md` — full 8-step production pipeline
- `fix_patterns.md` — P078 (Whisper UZ/TJ limitation), P079 (admin story not editable)
- `hr-CLAUDE.md` — project overview
- `hr-CLAUDE-append-3.md` — business model + post-Hajj roadmap

## Change log

| Date | Change | By |
|---|---|---|
| 2026-05-16 | Initial creation, 5 reels logged retroactively + tonight's | Farhod / Claude session |
