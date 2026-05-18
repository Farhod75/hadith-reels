# dua-reel-series-backlog.md
# Hadith Reels — Dua Series Content Plan

> **Author:** Farhod Elbekov + Claude session, 2026-05-17 (post-midnight)
> **Status:** BACKLOG — execution deferred to post-Hajj (target: June 2026+)
> **Project:** hadith-reels (github.com/Farhod75/hadith-reels)
> **Companion docs:** `reel-tracker.md`, `reel-creation-pipeline.md`, `agent-architecture-roadmap.md`

## What this is

A multi-year content plan for adapting authentic duas (Quran + Sahih Sunnah) into reels across all channel languages.

**Inspiration source:** Shaykh Muhammad Salih Al-Munajjid's "100 Дуа из Корана и пречистой Сунны" (Издательский дом Фаджр, 2021, ISBN 978-5-6047818-8-3). Used as a **content map only** — the book provides thematic structure and selection guidance. All actual dua content is sourced independently from public-domain primary sources.

## Why this matters

- **Content scale:** 100 duas × 5 languages (EN/RU/UZ/AR/TJ) × 2 styles (Adults/Kids) = potential 1,000 reels
- **Theological strength:** Duas are direct words taught by Allah (Quran) and the Prophet ﷺ (Sahih hadith) — strongest possible content for a "Sahih" branded channel
- **Universal relevance:** Duas address every life situation (illness, fear, gratitude, hardship, daily life) — broader audience than narrative hadith
- **Repeatability:** Audiences re-watch duas to memorize them — built-in retention loop
- **Hajj relevance:** Several duas in the source book are specifically Hajj-related, perfect for post-Hajj content burst

## Hard rules (legal + theological)

1. **Never reproduce the source book's specific translations** — they're copyrighted by Издательство Фаджр and Ibrahim Khattat
2. **Never reproduce the book's specific Cyrillic transliterations** — also copyrighted
3. **Always source duas from primary sources** (Quran, Sunnah.com, Dorar.net, HadeethEnc.com)
4. **Generate fresh translations** per language via Claude API (these are derivative works, but original to this project)
5. **Cite the original Quran ayah or hadith number** in every reel — never claim a dua's source without verification
6. **Only sahih or hasan duas** — same rule as the rest of the channel
7. **Per P049** — use language-appropriate seerah attribution where relevant (Ar-Raheeq for EN/AR, Усваи Ҳасана for UZ/RU/TJ)

## The 6 thematic categories (from book — inspiration only)

These map to natural content sub-series. Each category becomes its own "season" on the channel.

| # | Theme (RU original) | EN equivalent | Approx count | Strategic notes |
|---|---|---|---|---|
| 1 | Испрашивание у Аллаха Рая и защиты от Ада | Asking for Paradise and protection from Hell | ~5 duas | Strong opener — universal Muslim aspiration |
| 2 | Испрашивание у Аллаха прощения и милости | Asking for forgiveness and mercy | ~17 duas | Largest category — Ramadan/Laylat al-Qadr launch potential |
| 3 | Испрашивание наставления и стойкости в религии | Asking for guidance and steadfastness | ~11 duas | Daily-use duas — high engagement |
| 4 | Испрашивание блага этого мира и мира вечного | Asking for good in this world and the next | ~19 duas | Includes Quran 2:201 — most quoted dua in Islam |
| 5 | Мольба за родителей, семью и детей | Duas for parents, family, children | ~6 duas | Family-themed reel series, parent's day content |
| 6 | Испрашивание благости религии и ахирата | Asking for goodness in religion and afterlife | ~41 duas | Largest category — includes most "protective" duas |

## Workflow per dua (Path A)

For each dua selected for reel production:

### Step 1 — Source identification
- Read the book entry to identify whether it's a Quran ayah or hadith dua
- Note: the book often doesn't cite hadith numbers — need to research separately
- Verify the source via:
  - **Quran ayahs** → Quran.com (preferred — multiple translations available)
  - **Hadith duas** → Sunnah.com search by Arabic text
  - **Disputed/weak duas** → Dorar.net authentication check
  - **Cross-reference** → HadeethEnc.com for thematic context

### Step 2 — Pull Arabic source
- Take the Arabic text from the **primary source** (Quran.com or Sunnah.com), NOT from the book
- Verify it matches what's in the book (sanity check the book's accuracy)
- Note diacritics — use the fully-vowelized version for reel display

### Step 3 — Generate fresh translations via Claude
- Per language: EN, RU, UZ, AR (display + reciter), TJ
- Prompt Claude with:
  - The Arabic source
  - Target language
  - Context: this is for a children-friendly OR adults reel
  - Length constraint (per HR pipeline: short, max ~10 sec narration per scene)
- Output: short, accurate, ASD-aware where applicable for Kids style

### Step 4 — Generate transliteration (optional)
- If transliteration is needed, generate independently
- Do NOT copy the book's Cyrillic transliteration system (Қ, Ӷ, Һ characters)
- Alternative: ship Arabic-only display, skip transliteration entirely (cleaner for shorter reels)

### Step 5 — Standard reel pipeline
- Per `reel-creation-pipeline.md` Steps 1-8
- Use existing infrastructure (admin Step 1-3, FFmpeg pipeline, etc.)
- Tag in `reel-tracker.md` with theme = "Dua: [category]"

### Step 6 — Logging
- Add to `reel-tracker.md` with new reel ID
- Update duplicate-check index — track which duas have been done in which languages
- Cross-reference back to source (Quran ayah # or hadith collection #)

## Worked example — Dua #1 from the book

**Book entry (page 9, used as content map only):**
> «Аллáһумма, инни́ ас'алюка-ль-Джанната ва а'ýзу бика мина-н-Нáр(и)»
> "О, Аллах! Прошу у Тебя Рая и прибегаю к Твоей защите от Ада"

**Path A workflow:**

1. **Source identification:** This is a hadith dua. Need to research where.
2. **Research via Sunnah.com:** Search for "اللهم إني أسألك الجنة وأعوذ بك من النار"
3. **Found in:** Sunan Abu Dawud #792, Sunan Ibn Majah #910 — graded sahih by Al-Albani
4. **Pull Arabic from Sunnah.com:** `اللَّهُمَّ إِنِّي أَسْأَلُكَ الْجَنَّةَ وَأَعُوذُ بِكَ مِنَ النَّارِ`
5. **Generate fresh translations via Claude** — explicitly NOT using the book's wording. Use Claude with prompt: *"Translate this dua to [lang]. Brief, natural, suitable for a 30-second reel narration. Maintain reverence."*
6. **Render reel** per pipeline
7. **Log in tracker:** Reel ID R###, source = "Sunan Abu Dawud #792 + Sunan Ibn Majah #910", category = "Dua: Paradise/Hellfire"

## Pre-execution checklist (before starting Phase 1 post-Hajj)

- [ ] Verify Sunnah.com API or scraping policy for batch dua lookup
- [ ] Build a Supabase table `duas` with: Arabic text, source citation, theme tag, status, completion per language
- [ ] Decide on transliteration approach (display or skip — pick one and stay consistent)
- [ ] Decide on visual style for dua reels — same as hadith reels, or distinct theme?
- [ ] Audio decision: Should Arabic be recited by a qari (high quality), or by ElevenLabs Arabic voice?
- [ ] Pacing decision: 1 dua per reel, or themed compilations (3-5 duas per reel)?
- [ ] Pricing check: 1000 reels × ElevenLabs cost — does prompt caching (Idris P3.6 equivalent) apply here?

## Audio quality consideration — Arabic recitation

This is the biggest open question for the dua series:

**Option A — ElevenLabs Arabic voice (current pipeline)**
- Pros: matches existing workflow, fast iteration, cheap
- Cons: synthetic recitation of religious text feels less reverent; ASD-aware users (Idriszhon will see these) may not bond
- Risk: native Arabic speakers may critique the tajweed

**Option B — Hire/partner with a real qari**
- Pros: authentic recitation, channel credibility, listener bonding
- Cons: cost, scheduling, attribution complexity, IP
- Path: contact qaris on Telegram/Instagram who already produce free dawah content; offer attribution + cross-promotion

**Option C — Use public-domain recitations (Mishary Rashid, Sudais, etc.)**
- Pros: highest authenticity, free, well-loved voices
- Cons: their recitations may be copyrighted by the qari or their publishers — same trap as the book
- Verify: most Quran-only recitations from major qaris ARE in public domain per scholar consensus, but mixed with translations they're often re-copyrighted

**Recommendation:** Start with **Option A for Phase 1** to test channel response, then upgrade to **Option B** for Phase 2 once metrics show the series has audience traction.

## Suggested Phase 1 (post-Hajj first month)

Pick **5 duas** from Category 1 (Paradise/Hellfire) — short list, high emotional resonance, good for testing the workflow end-to-end.

| Dua # in book | Theme | Source identification needed |
|---|---|---|
| 1 | Asking Paradise/protection from Hell | Sunan Abu Dawud #792, Ibn Majah #910 |
| 2 | "Build me a house in Paradise near You" | Quran 66:11 (Asiya's dua) |
| 3 | "Join me with righteous, give me good remembrance" | Quran 26:83-85 (Ibrahim's dua) |
| 4 | "Avert from us the punishment of Hell" | Quran 25:65 |
| 5 | "Lord of Jibril, Mikail, Israfil — protect me from fire" | Hadith — needs source verification |

5 duas × 5 languages × 2 styles = up to 50 reels for Phase 1. Realistic 1-2 month production at current cadence.

## Integration with existing systems

- **reel-tracker.md:** new column or tag `series = "100 Duas"` to filter
- **agent-architecture-roadmap.md:** Auditor agent Check 1 already handles authenticity grade — applies to duas
- **fix_patterns.md:** if any duas surface new failure modes (Arabic rendering issues, etc.) log as Pxxx
- **HV cross-reference:** HV's Tier 1-3 source authority list already covers Sunnah.com, Dorar.net etc. — same sources used here

## Backlog status

- ✅ Concept documented (this file)
- ⏳ Phase 1 dua source identification (post-Hajj)
- ⏳ Supabase `duas` table schema (post-Hajj)
- ⏳ First Phase 1 reel rendered (target: June 2026)
- ⏳ Channel response evaluation (after 5 reels live)
- ⏳ Phase 2 planning (qari partnership, scale up)

## Optional — contact publisher

**Worth doing in parallel:**
- Telegram +7 (988) 428-00-66 (MAGAZINUMMA)
- Or via the publisher's contact channels
- Brief, respectful message: introduce yourself, the project, ask if they'd support free reel adaptation with full attribution
- Worst case: no response (proceed with Path A unchanged)
- Best case: explicit permission + cross-promotion + credibility boost

Sample message (RU):

> Ассаламу алейкум,
>
> Меня зовут Фарход Эльбеков. Я разработчик и владелец канала Telegram @SahihHadithReels (короткие видео с достоверными хадисами на 5 языках, включая русский) и проекта hadithverifier.com (приложение для проверки достоверности хадисов на основе ИИ).
>
> Я недавно прочитал вашу книгу "100 Дуа из Корана и пречистой Сунны" Шейха Аль-Мунаджида и хотел бы создать на её основе серию коротких видео для нашего канала. Все дуа я буду брать напрямую из первоисточников (Куран.ком, Сунна.ком), но ваша книга послужит источником вдохновения для тематической структуры.
>
> Если возможно, я бы хотел получить ваше благословение на этот проект и упомянуть вашу книгу как источник вдохновения. Также готов разместить ссылку на вашу публикацию в каждом видео.
>
> БаракаЛлаху фик.

(Don't send this without re-reading once fully awake post-Hajj.)

## Change log

| Date | Change | By |
|---|---|---|
| 2026-05-17 | Initial backlog created from book scan during pre-Hajj session | Farhod / Claude session |
