# Open items

**What this file is for.** `fix_patterns.md` records WHY something happened and
carries a Status line at the bottom of each pattern. That is 200+ Status lines
scattered through one long file, and it is not a list of what is outstanding.
Everything else lived in chat, and chat ends. Items have slipped twice that way.

**The rule:** an item leaves this file only when it is DONE, or deliberately
dropped with the reason written here. Not when it stops being interesting.

Read at session start, step 3. Added 2026-10-08.

**Completeness.** This file was first assembled on 2026-10-08 from one
session's view, and four items from earlier sessions were missing on the first
pass — found only because the operator asked whether everything had been
carried over. Assume it is still incomplete. Add to it rather than trusting it.


---

## Production queue
**A/B SWEEP OF THE SHIPPED LIBRARY, 2026-10-17 — 16 ROWS NEED ADJUDICATION.**
First Stage 3 run over `hadith_library`: 34 rows, 35 verdicts, **19 pass / 4
fail / 12 disagree, 46% not clean.** Conventions audited clean first. Dry runs
only, nothing written. Full reasons: `out/ab-library-sweep-2026-10-17.txt`.
Background and the three classes of finding: P257.

**FAIL — both models agree, these are real and they have shipped:**

| row | reels | finding |
|---|---|---|
| Bukhari #527 | R034-R041 (8) | TJ: أحب "most beloved" rendered «беҳтарин» (best); قُلْتُ dropped |
| Bukhari #6009 | R006-R009 (4) | all four langs: يأكل الثرى (eating earth) as licking mud; فشكر الله له (Allah thanked him) as accepted/pleased |
| Bukhari #8 | R018-R021 (4) | **FIXED 2026-10-17.** `text_arabic` restored to the full matn (31 -> 184 chars), verified against sunnah.com/bukhari:8 and the local mirror. Re-translated, Latin re-derived, Stage 3 8/8 pass. Awaiting Stage 4 sign-off. The 16 published captions still carry the old short Arabic. |
| Bukhari #6857 | R098-R101 (4) | أكل الربا loses its verb; قذف المحصنات loosened; singular قال rendered plural |

**DISAGREE — A and B split, human decides, never a third pass (P177):**
#1, #1417, #82, #574, #4248, #2628, #2963, #2759, #5027, #13, #1773, #1520.

**#8 DONE 2026-10-17.** Full matn restored and verified against two independent
sources that agree: sunnah.com/bukhari:8 (the row's own cited `source_url`) and
the local hadith-json mirror at idInBook=8. Re-translated from the corrected
Arabic. Three translator interpolations were removed before apply, each flagged
by a model and each absent from the Arabic: a bracketed noun in RU, an
intensifier on iqam as-salah in UZ, and 'true' deity plus 'month of' in TJ.
Stage 3 re-run: 8/8 pass, zero disagreement. `matn_verified_at` left null -
Stage 4 is the human gate.

**OPEN: the 16 published captions were NOT corrected.** R018-R021 shipped
2026-08-11 to four platforms in four languages and still carry the 31-char
Arabic and the reversed Hajj/fasting order. Decision not taken: edit them or
leave them. The short Arabic is a true partial quote, not a fabrication.

**Then re-check extent on the rest.** #8 was found by accident — the models
flagged "added content" and the truth was a short Arabic. Muslim #223, #2699 and
#2963 are the same shape and already recorded. Nothing in the pipeline checks
that a stored matn is the WHOLE hadith.

**#1520 DONE 2026-10-17 - and it was NOT truncation.** Two defects: a wrong
diacritic (`lakunna` for `lakinna`, one vowel, a different word) and a cut matn
missing Aisha's question. They concealed each other, and all four translations
papered over the gap with a '(for women)' gloss that vanished on its own once
the matn was restored. Stage 3: 8/8 pass. See P259. OPEN: the Tajik uses «На»
for 'no' where «Не» is standard - needs a Tajik speaker, Stage 3 cannot see it.
#1520 can come OFF the DISAGREE list above.

**NEXT THREE, ranked by P259's gloss detector + ratio:** #1521 (gloss 'after
Hajj free from all sins', ratio 2.33), #1773 (the mabrur gloss again, already in
DISAGREE), #1894 (18-char Arabic, the shortest in the library). #574 carries a
gloss in all four languages but is probably benign - al-bardayn really does mean
Fajr and Asr.

**#1773 DONE 2026-10-17 - matn was CLEAN, translations were not.** Second false
positive from the gloss detector (after #1521): the parentheticals clarified a
complete matn. The translations inserted 'sins' and 'next umrah', and the
English had dropped إلى العمرة entirely. Re-translated; Uzbek and Tajik given
by the operator verbatim. Stage 3 8/8 - COMES OFF THE DISAGREE LIST. P263.

**RE-READ THE REMAINING DISAGREEMENTS BEFORE ADJUDICATING.** #1773 aggregated
to `disagree` while both models objected to the SAME insertion in DIFFERENT
columns - nothing was in dispute. A split across LANGUAGES is not a conflict
of judgement on a CLAIM, and P177 does not apply to it. Also: «следующей» in
Russian was the same addition as «навбатӣ» in Tajik and both models passed the
Russian, so check sibling columns by hand whenever one is flagged.

**OPEN - مبرور is rendered four ways:** EN 'the accepted Hajj', RU «мабрур»
transliterated, UZ «мақбул», TJ «мақбул». Russian is the odd one out.

**#1894 DONE 2026-10-17.** Stored 18 chars where the matn runs 370 - the
largest restoration so far. Tajik «бехудагӣ» for يرفث failed by both models
unanimously and was corrected; Uzbek «оғиз ҳидини» carried a case error no
model can see. Stage 3 8/8 pass, audit-library clean. A hand-edit of Claude's
typed ү (U+04AF) for ӯ (U+04EF) and was caught only by reading it back, so
`check_out_of_alphabet` now guards that class library-wide (WARN). P262.

**#5185 DONE 2026-10-17.** Stored 32 chars - the opening imperative only, rib
simile cut off - and it was STAMPED verified on 2026-09-05. Third stamped row
found holding defective content. Restored to 225 chars, re-translated, Stage 3
8/8 pass. Uzbek «васият қилинглар» corrected to «нисбатан яхши муомалада
бўлинглар» (the dative aimed the counsel at women rather than about them).
OPEN: Tajik «мешиканиаш» looks like a malformed contraction - needs a Tajik
speaker. P261.

**CONVENTION SET 2026-10-17:** `text_arabic` holds ONE COMPLETE admonition from
the cited narration, never a clipped one. Where a narration carries two, store
the one the row is about in full and let the citation locate it. Applies to the
excerpt rows below - #2999 (contiguous 0.47), #1151 (0.58), #5971 (0.56) - each
of which needs the same judgement: complete admonition, or clipped?

**DIACRITIC AUDIT, 2026-10-17 - 3 ROWS NEED A TIER-1 SOURCE.**
`scripts/audit-diacritics.py --mirror "C:/QA/Hadith verification AI app/hadith-json"`
Over 72 rows: EXACT 32, PUNCTUATION 5, ORTHOGRAPHIC 19, VOWEL 3, LETTER 0, NOT
FOUND 13. Only VOWEL matters - same consonants, different reading, the #1520
class. The mirror is a scrape, so these say OUR reading and ITS reading differ,
not which is right:

| row | ours | mirror | what changes |
|---|---|---|---|
| #463 | antuqisa | antaqasa | passive vs active voice |
| #223 | at-tahur | at-tuhur | both attested readings |
| #82 | tarku (nom) | tarka (acc) | which noun is the predicate |

Not wired into the pre-push gate until these three are settled - `--strict`
would block every push. P260.

**verify-matn-source.py --mirror, FIRST EVER RUN, 2026-10-17.** 66 found, 3
partial, 3 missing of 72.

- MISSING, all Musnad Ahmad: #6576, #6626, #7936. The mirror README states
  Ahmad chapters 8-30 are absent from its source data, so these are most likely
  a mirror gap. #7936 is independently known bad (P244).
- PARTIAL: #1899 (0.80), #2616 (0.86), #5185 (0.67).
- EXCERPT, stored matn scattered rather than contiguous: #2999 (0.47), #1151
  (0.58), #5971 (0.56). #2999 already sits in PARTIAL EXTENT below - confirmed
  by a second method.
- #5185 is now flagged by THREE independent methods: en/ar ratio 0.53 with a
  17-char English, 0.67 partial here, and the A/B sweep. Worth doing early.

**A cheap signal exists: character count.** #8 FAILED only because its
translations enumerated what its Arabic did not. Rows with SHORTER Arabic
PASSED, because their translations are equally short - consistent and
incomplete, invisible to a faithfulness check by the same construction that
hides a split matn (P257). Shortest `text_arabic` among the 36 used rows, as a
work queue: #1894 (18 chars), #1005 (24), #1479 (28), #1 (34), #1417 (41), #574
(43), #1520 (43). #1894 is the top suspect. Note that #1, #1417, #574 and #1520
already sit in the DISAGREE list above - short Arabic may be the real cause
there rather than a translation defect.

**P258 BLAST RADIUS - NOT YET ENUMERATED.** `--apply` silently wrote nothing for
every `--library` row for as long as the flag existed (fixed 2026-10-17, P258).
Any library row re-translated through the sign/apply route in that window kept
its old text while the script reported success. Some of the 12 DISAGREE rows
above may be that rather than translation defects. Needs: list the library rows
whose matn was corrected after promotion and compare their translations against
the current Arabic.

**Do NOT re-run disagreements hoping for a cleaner roll.** The models are
non-deterministic (#1903 RU moved pass/pass -> A=pass/B=fail on unchanged text).
Disagreement is the output.


**LIBRARY ROWS THAT CANNOT BE PRODUCED AS THEY STAND — found 2026-10-15** while
picking a hadith for the day's reel. Five rows in one morning, out of 38 unused.

**`Musnad Ahmad #7936` — DO NOT PRODUCE.** Wrong on four counts, verified against
two independent Dorar entries:

| field | library | Dorar |
|---|---|---|
| narrator | Abu Hurairah | سخبرة الأزدي (Sakhbarah al-Azdi) |
| grade | **hasan** | al-Mundhiri: لا يتطرق إليه احتمال التحسين — cannot be raised to hasan |
| matn | ends at وظلم فعفا | continues: ثم سكت → they ask → أولئك لهم الأمن وهم مهتدون |
| wording | فعفا | فغفر |

The grade is the serious one. All four translations also invent a main clause —
“Blessed is he” / «Блажен тот» / «Бахтлидир» / «Хушбахт аст» — because the stored
Arabic is a مَن conditional with its apodosis cut off. There is no طوبى in it. See
P244: the fabrication is what made the truncation invisible.

**PARTIAL EXTENT — need a Workflow L re-pull before production:**

- `Sahih Muslim #223` — carries only الطهور شطر الإيمان. The hadith continues
  through praise filling the scale, prayer as light, charity as proof, patience
  as brightness, the Qur'an as evidence for or against you. Yesterday's ZAD
  cross-check flagged #13 and #19 for partial extent and MISSED this one,
  because ZAD's own entry was equally abbreviated.
- `Sahih Muslim #2699` — only the seeking-knowledge clause.

**ONE HADITH STORED AS TWO ROWS UNDER ONE NUMBER:**

- `Jami at-Tirmidhi #2616` — one row “head of the matter is Islam… pillar is
  prayer… summit is jihad” graded *hasan*, another “charity extinguishes sin as
  water extinguishes fire” graded *sahih*. Both are clauses of the same hadith,
  with DIFFERENT grades. `verify-matn-source.py`'s own docstring cites this
  reference.
- `Sahih al-Bukhari #1469` — “no gift better than patience” (ar 61) and
  “whoever tries to be patient” (ar 36), both Abu Said al-Khudri, both sahih.

Duplicate numbers break the tracker's duplicate-check index, which keys on
hadith number. The library deserves an extent-and-attribution audit rather than
catching these one at a time; `verify-matn-source.py` already covers the
attribution half but needs a `--mirror`.

**Library rows corrected 2026-10-15** (all read back after the UPDATE —
“Success. No rows returned” says nothing about rows touched):

- `#6570.text_english` — “O Abu Hurayrah” → “O Abu Hurairah”, matching its own
  narrator field and the 49 uses across the repo. NOTE: the EN reel was rendered
  BEFORE this, so its caption still reads Hurayrah while its narration and burned
  subtitles read Hurairah. Rebuild the EN caption before #6570 publishes.
- `#13.text_russian` — added «истинно» so all four languages carry the
  completeness qualifier (EN “truly”, UZ ғақиқий, TJ ҳақиқӣ already had it).
- `#13.text_uzbek_cyrillic` and `text_uzbek_latin` — «ўз учун» → «ўзи учун»,
  operator-caught at review.


**ZAD Semester-2 Hadith — cross-checked against the library 2026-10-14.**
Source: `ZAD_Semester2_Hadith_UZ_Cyrillic_Corrected.pdf` (project docs). Text
extracts cleanly; the four scanned CourseBook PDFs do not, which is what parked
this before. 21 hadiths. The book cites COLLECTION ONLY — «Бухорий ривояти»,
«Бухорий ва Муслим ривояти» — never a number, and carries no Arabic. It is a
POINTER, not a source: anything produced from it goes through Workflow L so
Dorar supplies the number and the matn.

ALREADY OURS (4 of 21):

| ZAD | Opening | Narrator | Library row | Status |
|---|---|---|---|---|
| 13 | Аллоҳ гаплашади / ярим хурмо | Adiy ibn Hatim | Bukhari #1417 | shipped (kids, R014–R017) |
| 15 | Покланиш иймоннинг ярмидир | Abu Malik al-Ash'ari | Muslim #223 | in library, UNUSED |
| 19 | Мўминдан машаққатни кетказса | Abu Hurairah | Muslim #2699 | in library, UNUSED |
| 21 | Инсон вафот этганда | Abu Hurairah | Muslim #1631 | shipped (R114–R117) |

THREE CAVEATS, and they matter more than the counts:

1. **#13 and #19 are PARTIAL matches.** Our Bukhari #1417 carries only “protect
   yourself from the Fire, even with half a date”; ZAD has the fuller hadith
   opening with Allah speaking to each person without an interpreter. Our Muslim
   #2699 carries only the seeking-knowledge clause; ZAD has the whole hadith —
   relieving distress, easing a debtor, concealing a fault. If either is
   produced, RE-PULL the matn at full extent first.
2. **ZAD #18 is NOT Bukhari #5984**, though both concern kinship ties. Ours is
   Jubayr ibn Mut'im, “one who severs ties will not enter Paradise”; ZAD’s is
   Anas, “whoever wants his provision expanded, let him join them.” Different
   narrator, inverse framing. The false match P235’s side-by-side read exists
   to catch.
3. **Every number above came from matching narrator + wording against our own
   library**, not from the book. None of them is a citation the book made.

NOT IN THE LIBRARY — 17 sourcing candidates, in book order:

1 wilayah qudsi (Abu Hurairah, Bukhari) · 2 moderation in worship (Anas, B+M) ·
3 the moths and the fire (Jabir, Muslim) · 4 holding embers (Anas, Tirmidhi) ·
5 “I will do no more than this” (Jabir, Muslim) · 6 five prayers expiate (Abu
Hurairah, Muslim) · 7 «Эй ёшлар жамоаси» (Ibn Mas'ud, B+M) · 8 “this world is
sweet and green” (Abu Sa'id, Muslim) · 9 «ғариб ёки йўловчидек» (Ibn Umar,
Bukhari) · 10 Paradise ringed with hardship (Anas, B+M) · 11 “he has succeeded
who became Muslim” (Abdullah ibn Amr, Muslim) · 12 “whom Allah wishes good”
(Mu'awiya, B+M) · 14 every tasbih is charity (Abu Dharr, Muslim) · 16 the 360
joints (Abu Hurairah, B+M) · 17 “leave what makes you doubt” (Hasan ibn Ali,
Tirmidhi) · 18 kinship and provision (Anas, B+M) · 20 “be indifferent to the
world” (Sahl ibn Sa'd, Ahmad + Ibn Majah)

Themes worth noting against the tracker’s gap list: #17 (doubt/wara‘) and #20
(zuhd) are both uncovered, and #2 and #10 bear on the Akhlaq gap. None is a
duplicate of anything shipped.

**TRACKER ROW NUMBERS — THE #6570 TABLE BELOW IS NOW WRONG.** It reserves
R134–R137, written when #6570 was the next thing to publish. It is not:
**Bukhari #1903 EN published 2026-10-16 and took R134** (in the tracker now).
The tracker appends on post, so #6570's four rows renumber to **R138–R141** when
it posts ~2026-10-27 — assuming #1903's RU/UZ/TJ take R135–R137 first, which they
will if the set finishes before then. #1903's own set will not be contiguous
either if #6570 lands mid-set. Fix the numbers in that table before pasting it.

**#6570 PRODUCED 2026-10-14, all four languages — HELD until ~2026-10-27.**
Publishing waits on the 2-3 week Tawheed-arc spacing from #6423 (posted
2026-10-13). Nothing outstanding on the reels themselves; every frame checked.

The tracker is deliberately NOT updated yet. Its own rule is "After posting a
reel - append a new row", so R134-R137, the clip-library rows and the
production stats (→ 137 reels, 35 hadiths) all go in on publish day. Everything
needed to write them:

| Row | Lang | Duration | Size | Nasheed | Scenes |
|---|---|---|---|---|---|
| R134 | EN | 44.8s | 10.1 MB | aswati-Peaceful-Contemplation | lamp, ink, plain, kalima, garden |
| R135 | RU | 47.1s | 10.5 MB | aswati-Steady-Motivation | lamp, ink, plain, kalima, garden |
| R136 | UZ | 53.2s | 13.5 MB | aswati-Heartfelt-Gratitude | lamp, ink, plain, **b6423-plain**, kalima, garden |
| R137 | TJ | 43.7s | 9.9 MB | vocal-nasheed-05 | lamp, ink, plain, kalima, garden |

Subtitles EN/RU only (P078). Scene order is NOT the order the clips were
generated in: the kalima was moved from third to fourth after the first EN
render put the green sheet on screen one beat BEFORE the words - see P238's
neighbour note and the EN frame check. UZ carries a sixth clip for P240.

**Before publishing, three things:**

1. **Rebuild the EN caption** from the blocks. `text_english` was normalized
   after the EN reel was rendered (P241), so the caption as built still reads
   `Hurayrah` while the narration and burned subtitles read `Hurairah`.
2. ~~**`matn_verified_at`** is null on both #6423 and #6570.~~ **SET by the
   operator 2026-10-15** (2026-10-16 00:54 UTC) on both rows, read back after
   the UPDATE rather than trusting "Success. No rows returned". The UPDATE
   carried `AND matn_verified_at IS NULL` so it could not overwrite an existing
   date. P151 holds: the field means a HUMAN read the row against the source, so
   setting it is an assertion only the operator can make — #6570 was re-verified
   2026-10-14 and #6423 was in the batch of four verified 2026-10-12.
3. **Nasheed spacing — RESOLVED 2026-10-15.** Posted order per language runs
   #6423 → #13 → #6570. All four now pass the tracker's rule (not the same
   nasheed on 2 consecutive reels in the same language):

   - **RU: no action.** #6570 RU's `aswati-Steady-Motivation` clashed with
     #6423 RU (R127), but #13 RU (R131) sits between them on
     `vocal-nasheed-05`. Not consecutive. NOT re-rendered.
   - **EN: re-rendered** 2026-10-15 17:54 with
     `-Nasheed aswati-Peaceful-Contemplation.mp3`. Was `vocal-nasheed-06`, the
     same bed as #13 EN (R130). 44.8s / 10.1 MB unchanged; only the bed differs.
   - **UZ: re-rendered** 2026-10-15 18:23 with
     `-Nasheed aswati-Heartfelt-Gratitude.mp3`. Was
     `aswati-Focused-Determination`, the same bed as #13 UZ (R132).
     53.2s / 13.5 MB unchanged.
   - **TJ: no action.** `vocal-nasheed-05`; TJ's previous bed was
     `aswati-Steady-Motivation` (R133).

   Beds read back from the four P201 `*-render.json` sidecars, not from the
   session log — the chat had RU and TJ transposed for several turns, and the
   sidecars are what caught it. `-Nasheed` was passed explicitly so the picker
   could not re-roll.
4. **The narrated TEXT for these four reels is not on disk (P246).**
   `draft.txt` was overwritten by #13's generation the next day. EN and RU can
   be reconstructed from their `*-narration.srt`; UZ and TJ ship without
   subtitles (P078) and have NO text record — the reviewed wording survives
   only as audio. Not in the repo, the session transcript, or chat history.

   On publish day, for UZ and TJ, either:
   - **transcribe** the caption's story line from the reel audio — keeps the
     wording that was actually reviewed and corrected, ~15 min; or
   - **regenerate** in admin and re-review all four blocks — fresh text means
     fresh defects, and P245 re-attributed the moral in 7 of 8 generations.

   Transcribing is cheaper and safer. Reels rendered from 2026-10-15 onward
   archive their own text (`{style}-{lang}-{slug}-{section}.txt`, written by the
   TTS route beside each mp3), so this applies to #6570 alone.
**Rule 25's verdict is in — see P239.** It lost 3-of-4. The fifteen-rule
rewrite in `docs/proposed-rules-positive-form.md` stays on hold; what goes in
next is one rule naming the MOVE (affirmation rendered as contrast), tested
alone on the next set.


**#6570 re-verified 2026-10-14 — back to `verified`, no action outstanding.**
The Tajik kalima spacing fix dropped the row to `translated` (correct: the text
changed, so the Stage 3 verdict no longer described it). Re-run on the corrected
text: EN, RU, UZ, TJ all pass BOTH passes, 0 disagreements. UZ pass A came back
medium confidence, the only soft reading in the set. The fix was orthographic and
no verdict moved — which was the expectation, and is now measured rather than
assumed. Ready for production: green kalima frame, 2–3 weeks after #6423.

**Operator decision 2026-10-13 — the Tawheed series gets a colour arc.**
#6423's kalima scene is warm parchment under raking dawn light. For **#6570,
the second reel, the kalima frame is GREEN** — operator's call, made while
reviewing #6423's scenes. Green carries the garden association, which suits
#6570 (intercession) better than it would #6423 (the Fire forbidden). The
composite itself is now scripted: `scripts/composite-matn.py`, so only the
FLUX page prompt changes — ask for a green-toned ground rather than recolouring
the ink.

**EMPTY as of 2026-10-13. All three items shipped; the entries below replaced
what had been sitting here marked IN PROGRESS.**

| Hadith | Reels | Shipped | Theme filled |
|---|---|---|---|
| Sahih Muslim #1631 | R114–R117 | 2026-10-09 | Death / Afterlife |
| Jami at-Tirmidhi #3895 | R118–R121 | 2026-10-10 | Family / Marriage |
| Sahih al-Bukhari #5027 | R122–R125 | 2026-10-12 | Quran / Tilawah |
| Sahih al-Bukhari #6423 | R126–R129 | 2026-10-13 | Tawheed / Sincerity |

**Next pick is undecided.** What the tracker's gap list actually leaves
(2026-10-13):

- **Akhlaq / anger — ZERO reels.** The only remaining theme at zero. The
  obvious matn is «لا تغضب» (Bukhari #6116); it is not in the library yet, so it
  needs Workflow L first.
- **Zakat proper — partial.** #1417 is from Kitab az-Zakat but framed as
  sadaqah, so zakat as an obligation is still uncovered.
- **Arabic lane — ZERO reels.** A language gap, not a theme gap: no new hadith
  needed, only an AR leg on a set already made.
- **Tawheed — 8 reels (R010–R013 intentions; R126–R129 Bukhari #6423, shipped 2026-10-13).** FIRST of the arc is done; #6570 is next, 2–3 weeks out, with the GREEN kalima frame, then #3435. The four candidates verified 2026-10-12
  land here: Bukhari #6423, #6570, #6446 and Muslim #2999. They are
  `status='verified'` in hadith_candidates, which is ELIGIBLE, not promoted —
  Stage 4 and promotion to hadith_library come before any of them can be
  produced, and the operator asked for 2–3 weeks between them.

Still deferred, unchanged: #1469 and #2616 each carry the two-row collision, so
picking either means first deciding which clause. #1903 sits close to #2654's
subject (false speech) — look at it deliberately rather than by surprise.

---
## Blocks content — do not ship past these
**#1903 العمل به — the RU matn is LOOSER than the EN, found 2026-10-16 while
producing the RU leg. NOT a blocker; decide from a source at the set boundary.**

The matn is من لم يدع قول الزور والعمل به. `qawl az-zur` is speech ONLY. The
second clause is `al-'amal` (action) bound by `bihi`, a resumptive pronoun
pointing back at qawl az-zur — so the hadith names false speech AND ACTING UPON
IT, one thing plus its execution, not two independent sins.

| column | stored text | pronoun |
|---|---|---|
| `text_english` | "false speech and acting upon it" | preserved |
| `text_russian` | «лживые слова и поступки» | LOST |

Read plainly the Russian is two coordinated adjectival nouns — false words and
[false] deeds — a broader claim than the Arabic makes. Same hadith, same library,
two extents. P220's class: translation fidelity has no automated reader, and no
gate could see this. UZ and TJ not yet checked on the same clause; check them
when those legs are produced.

**Why it was NOT fixed on the spot:** it is imprecise rather than false, so it
fails nothing the way the RU moral's «нужно Аллаху» did; the precision IS
carried, in the H block («поступки по ней»), which is where P111 rule 18 says
scholarship belongs while the matn stays as the source quotes it; and the honest
fix is a sourcing task (Dorar + Fath al-Bari on العمل به, whether it means acting
on the falsehood specifically or on sin generally), not a wording choice. Stage 3
re-verification is blocked on the OpenAI billing regardless. #3435's clause was
rewritten by three successive sessions, twice in OPPOSITE directions, each time
decided late at night without a source — that is the trap this note exists to
avoid.

If it is reopened, it is reopened from a source, and all four languages move
together or none do.


**#3435 على ما كان من العمل — DECIDED 2026-10-12. Wording stands; the row
stays `needs_human` on this clause, permanently, and that is the correct
resting state, not an unfinished task.** All four languages now render it
without resolving it (EN “with the deeds he had done”, RU «с теми деяниями,
что у него были», UZ «қилган амали билан», TJ «бо он амале ки дошт»). Three
reasons to leave it there:
  1. The EN is almost verbatim the published USC-MSA rendering on Sunnah.com,
     and pass A fails it. A model rejecting the published translation of
     Bukhari is a limit of the model, not a defect in the text.
  2. The two passes reject the wording for MUTUALLY EXCLUSIVE reasons (A:
     “regardless of”; B: “according to”) — see P225. No wording satisfies
     both, because the ambiguity is in the Arabic, not in our Russian.
  3. P224: the commentators preserve على rather than resolve it. Matching them
     is the faithful choice even though it cannot score a clean pass.
Do NOT 'fix' this clause again. Three sessions have now rewritten it — twice
in opposite directions — and each rewrite was an interpretive choice wearing
a correctness costume. If it is reopened, it is reopened from a source.

**P220's central claim was contested by Stage 3 — SOURCED 2026-10-12, see
P224. P220 was wrong and is amended.** Neither wording is the matn: the
published English (Sunnah.com / USC-MSA) reads “with the deeds which he had
done even if those deeds were few”, and al-Sabt's sharh glosses the clause by
restating it almost verbatim, adding only that he may be punished first and
enter Paradise after — which rules out “regardless” as unconditional. على is
economical and the commentators keep it so. «амалига қараб» resolves it one
way and «қатъи назар» the other; a faithful rendering resolves it neither way.
DECISION NEEDED: one neutral wording per language (“upon / with whatever deeds
he had”), applied via sign → apply and re-verified. EN and RU carry the same
resolved reading and change with it.

**«ҳақ» on #3435 — RESOLVED 2026-10-13, AND IT WAS THE TAJIK, NOT THE UZBEK.**
The Uzbek was already clean («Аллоҳдан бошқа илоҳ йўқлигига», matching
`2002-hadis.pdf` #39). The interpolation was sitting in the TAJIK — «ҳеҷ
маъбуде ба ҳақ нест ҷуз Аллоҳ» — the language nobody had checked, and it
would have shipped. Dropped via sign → apply; see P234 for what else that
apply did. Original note, kept for the reasoning:
 Both
Stage 3 passes flagged “true god” as a word not in لا إله إلا الله. The
project's own published Uzbek source settles the convention: `2002-hadis.pdf`
#39 renders the kalima «Ла илоҳа иллаллоҳ» (Аллоҳдан бошқа илоҳ йўқ) — no
«ҳақ». Classical grammar does supply بحق as the elided predicate, so the gloss
is orthodox rather than invented, but it is an interpolation and the house
reference omits it. Same book, #1052, renders sincere testimony as
«сидқидилдан» — the idiomatic one-word “sincerely”, which is also the cleanest
answer to the نفسه / “heart” question on #6570 UZ.

**The نفسه / "heart" worry on #6570 does not apply — checked 2026-10-13.** All
four stored renderings already say SELF, not heart: EN "sincerely from his own
self", RU «искренне, от самого себя», UZ «ихлос билан, ўз ичидан», TJ «холис аз
ҷониби худи ӯ» — which is what pass A asked for. «сидқидилдан» would move the
Uzbek TOWARD a heart word (сидқи + дил). Leave all four. What drifted to "heart"
on 2026-10-13 was the GENERATED Tajik moral for #6423, not a stored matn — a
generation problem, addressed by rule 25 (P233).

**ORIGINAL ITEM, superseded above:** P220 recorded «қилган амалига қараб» (“according to his deeds”)
on Bukhari #3435 as a ruling inversion, and this session corrected it to
«қандай бўлишидан қатъи назар» (“regardless of his deeds”). Pass B now says the
opposite in two languages: على ما كان من العمل means “according to / with
regard to what he had of deeds”, NOT “irrespective of”. Pass A does not flag it.
The Arabic على carries both readings and the classical commentary splits: one
line reads “whatever his deeds, even if deficient”, the other “he enters at the
rank his deeds earned”. So P220 asserted one reading as settled fact when it is
not, and graded the translator for it. RESOLVE FROM A SOURCE — Fath al-Bari on
#3435, Dorar, and the published Bukhari translations — then amend P220 to match
what the sources say. Do not resolve it by preferring a model (G1). The row
stays `needs_human` until then.

**Stage 3 COMMITTED 2026-10-12: 4 verified / 1 needs_human, 0 incomplete,
disagreement rate 20% of 5.** Bukhari #6423, #6570, #6446 and Muslim #2999
are at `status='verified'` — ELIGIBLE for Stage 4, never inserted by it (G1).
Bukhari #3435 is at `needs_human` on the deeds clause, by decision, above.
Still at `deduped`, deliberately: Muslim #28 (UNCERTAIN marker), Bukhari #99
and #6938 (variants of #6570 and the Itban group).

**Stage 3 has no `--apply` — the P177 split is still live there.**
`verify-candidates.py --commit` RE-RUNS both models and writes that fresh
roll; the verdicts a human just read in the dry run are never the verdicts
stored. Stage 2 got `--apply` for exactly this (P177, then P219's sign-off).
It matters less here — machine output stored as machine output, and the
statuses happened to reproduce across both runs tonight — but these models
are demonstrably non-deterministic: across four runs on the same text, A and
B swapped sides on #3435 RU, UZ and TJ. So `verify_a`/`verify_b` in the DB
are one roll, not the reviewed one. Fix is the same shape as P177: write the
verdicts file, then apply it.

**Translation fidelity has no automated reader (P220, 2026-10-12).** The
in-house translator put «қилган амалига қараб» — “according to his deeds” —
on Bukhari #3435, whose matn says the opposite: “whatever his deeds may have
been.” Three further fidelity defects in the same batch of three hadiths. All
four were caught by reading and by nothing else: the ruling error sat in Uzbek
Cyrillic, which P078 excludes from subtitles, and every existing gate reads
generated reel text rather than DB text — Workflow H step 9 says so outright.
Workflow I step 4 asks the operator to check against the Arabic; the operator
has said they do not read Arabic fully. Stage 3 A/B verify (Workflow K) EXISTS
and is documented — the claim that it was unbuilt was wrong (P221). It crashed
on its own `incomplete` value until today (P222). With that fixed it ran all 5
translated rows, and **pass B returned HTTP 429 on all 20 calls [**NO LONGER TRUE — SEE THE CORRECTION BELOW THIS BLOCK**]: “You have no
credits remaining” on the OpenAI account.** Every row came back `incomplete`,
which the stage correctly refuses to pass to Stage 4. Stage 3 is one billing
top-up away from being the control this needs; until then a human second reader
per batch is the only one.

**Pass A flagged Bukhari #6570 RU and UZ (2026-10-12).** نفسه is “his own
self”, not “heart”.
- RU: RESOLVED. «от своего сердца» was this session's consistency edit over
  already-faithful text; reverted to the translator's «искренне, от самого
  себя» on the operator's call, through sign → apply (not an SQL patch), and
  verified in the DB. Provenance on that field is back to `machine`.
- UZ: OPEN. «ўз қалбининг самимиятидан» is the translator's own, and the
  established EN rendering of this hadith is “sincerely from his heart”, so A
  may be stricter here than the convention. No second opinion exists while
  pass B has no credits [**STALE — B RUNS; see 2026-10-16 correction**]. TJ «холис аз таҳти дили худ» and EN “from his own
  heart” carry the same question. Decide the convention once, for all four
  languages, rather than per row.

**The Tawheed run carries four viewer-confusion traps, all rowed in the
tracker’s duplicate-check index (2026-10-12).** Same handling as #6871/#2654
below — the index keys on the hadith NUMBER, so none of these flag
automatically:
- **#99 and #6570 are the same hadith**, twice in Bukhari. Pick one number and
  keep it; the other exists and a viewer will find it.
- **#3435 (Bukhari) and #28 (Muslim) are the same hadith.** Muttafaq alayh; the
  source slide says “Bukhari and Muslim” while our caption cites one.
- **#425 / #5401 / #6938** are three further entries around the Itban event we
  cite as #6423; #425 and #5401 are not even narrated by Itban.
- **The three hadiths sound like one** to a viewer. Hence 2–3 weeks apart.

**Sahih al-Bukhari #6871 must never follow #2654 without a deliberate call.**
Different number, same subject (al-kaba'ir). The duplicate index keys on the
number so nothing flags the pair, and NO automated check covers it — a
similarity check was written and removed on 2026-10-09 because the pair scores
0.16 against a library-wide maximum of 0.29 (P205). The mechanism is now a row
in the tracker's duplicate-check index. This item stays open only as a pointer
to that row.

---

## Recorded, not built

**P196 — the linter only ever sees text a human already cleaned.**

**P126 — classifier blind spots.** Partly covered.

---

## Pipeline / design

**Re-measure the rest of the pronunciation watch-list against v4.** The ﷺ
entry is CLOSED (2026-10-09): checked on v4, all languages handle it, and
`cleanForTTS` expands it before TTS anyway so the model never sees it — the
doc had been describing a per-language distinction the code does not make.
The REST of the watch-list in `reel-creation-pipeline.md` is still scoped to
whichever model measured it, and P193 says those entries expire when the
model changes. They have not been re-run since 2026-10-04.

**Generator rules in positive form — DRAFTED 2026-10-14, HELD ON PURPOSE.**
Full proposed text for rules 7-21: `docs/proposed-rules-positive-form.md`. It is
NOT applied and must not be until **#6570 has been generated and read**. Rule 25
went in on 2026-10-13 marked NOT YET VERIFIED and #6570 is its test; applying a
fifteen-rule rewrite first collapses the two changes into one generation and
leaves no signal either way. Rules 23 and 24 looked equally sound on 2026-10-12
and lost within a day, which is exactly why what KIND of fix holds is the thing
worth measuring. P101 is the second reason for care: a generator-prompt edit that
instructed fabrication, caught only after two Russian generations had put
invented speech in the Prophet's ﷺ mouth.

The draft keeps every prohibition - each survives as the second clause of its
rule, in the DO-first house style rules 23/24/25 already use. Original note and
its reasoning below:
**Generator rules in positive form.** The prompt is now 22 rules and most of
them are NEVER. R026 is that negations reinforce what they forbid, and
Anthropic's own prompting guidance says to state what the model should DO. Both
are recorded in `self_upskilling.md` under "Practice, not tools" and neither has
been applied to the generator. P199 is evidence the prose rules are the weak
layer: rule 18 existed and was broken anyway, in the two languages furthest from
the prompt's own.

**`hr-ppd-spec.md` — designed, never built.** The per-platform posting spec was
worked out in conversation and never written to the repo. The file does not
exist. Either write it or drop this item deliberately.

---

## Platforms

**Check the Instagram comment Inbox.** Business Suite showed an empty comment
queue against a post with 251 comments. Comments made before the Page was
connected never backfill, so the open question is whether comments made SINCE
the connection appear. If they do not, the Page-link hypothesis is dead and the
Graph API is the only route to comment triage — which is what Agent #15 is for,
and it is blocked behind the Facebook appeal.

## Agent fleet

**15 agents scoped. Three have a loadable SKILL.md as of 2026-10-09** —
`reel-producing` (with a four-case eval corpus), `stt-validating` and
`tts-validating`. All three existed for weeks in `agents/`, which is not a path
anything loads from; moved to `.claude/skills/` (P206). `asset-auditing` is the
one built as scripts, and it works — it is what blocked the m2759 render until
the clips were classified.

**`reel-producing` evals RUN for the first time on 2026-10-09** (record:
`.claude/skills/reel-producing/evals/RUN-2026-10-09.md`). Passes v1 on paper —
3 of 4 cases with every required finding, zero `must_not_flag` hits — but the
pass is PROVISIONAL: case 001 was answered after its defects had been read in
the README's coverage table, so discounting it gives 2 of 3, below the bar.
Re-run 001 cold to settle it.

Still open for `reel-producing`:

  - Scripts: step 7 DONE (`scripts/pick-nasheed.py`, 2026-10-09). The step 4
    block parser was DECLINED on 2026-10-10, deliberately. Merging
    lint-content's parser (keeps line numbers, for reporting) with
    stt-validate's (returns narrated S+M, for comparison) refactors two
    working scripts to serve a programmatic v2 agent that does not exist.
    Built `scripts/check-parser-agreement.py` instead, which answers the
    question the merge was really for: do the two read a draft the same
    way? They do — verified on the shipped draft and on five adversarial
    inputs (duplicate label, a label-shaped line inside C, tight and loose
    label spacing, a preamble before any label, blank-line separation).
    Both already open with utf-8-sig, so the BOM trap is covered in both.
    Revisit the merge only if v2 is actually being built.
  - Step 2b pass B EXERCISED FOR THE FIRST TIME on 2026-10-09, R114 (Muslim
    #1631 EN): a different model, given the matn and the blocks and nothing
    else, as P120 requires. It earned the gate immediately — it caught a
    defect pass A had INTRODUCED, a corrected moral that dropped
    يدعو له entirely while fixing rule 3. Still ad-hoc, not scripted,
    and run once; the skill's A/B split is demonstrated, not routine.
  - Case 004 may be missing a required `attribution_boundary_open`: it has the
    same construction as 001, which requires it.
  - The adults lane still has no E2E checklist, which the skill names as a
    precondition for driving that lane.

**The roadmap has been found incomplete three times**, each time missing the
agent for whatever had just happened: it had no agent that PRODUCES a reel until
#13 was added on 2026-08-31, having been written with an orchestrator that would
have had nothing to dispatch; #14 came after a competitor question; #15 after a
viewer objection arrived in the Instagram comments. CLAUDE.md step 8 says to
assume a fourth gap exists. That is a standing instruction, not a resolved item.

**The unbuilt agent marked Tier 1** — highest daily return of anything unbuilt
— is the one that takes a hadith number, language, style and mascot, writes the
four blocks, checks them against the recurring-defect table, pulls the matn from
the correct DB column, writes draft.txt, runs lint-content.py, picks a least-used
nasheed, assembles the render command and then STOPS. Every one of those steps
was done by hand across four languages on 2026-10-05, and the two defects that
mattered most that day — a missing attribution and commentary inside a
quotation — were caught by reading, which is the step this agent explicitly does
not replace.

**Nothing here is scheduled.** The fleet is a roadmap with dates from the
original post-Hajj plan, all of them passed. Decide whether to build the Tier 1
agent or to mark the roadmap as aspirational and stop counting against it.

---

## Queue — Tawheed run (verified 2026-10-12)

Four hadiths from a ZAD Academy Aqidah semester-2 chapter, checked against
Dorar and sunnah.com before anything was written to the library. The theme
sits at ⚠️ with only R010–R013, so these would take it to ✅.

**SPACING, per the operator: 2–3 weeks between them, NOT back to back.**
Four shahada hadiths in a row read as one long repeat; the channel's strength
is variety across themes. Interleave other themes between them.

**CLEARED — three of the four:**

1. **Sahih al-Bukhari #3435 / Sahih Muslim #28** — Ubadah ibn as-Samit.
   Whoever testifies to tawhid, to Muhammad ﷺ as His slave and messenger, to
   Isa as His slave and His word cast to Maryam, and to Paradise and the Fire
   as true — Allah admits him to Paradise according to his deeds. Grade
   SAHIH in both. Dorar carries both wordings with mutual takhrij.
2. **Sahih al-Bukhari #6423 — SHIPPED 2026-10-13 as R126–R129.** — Itban ibn Malik. “No servant will come on the
   Day of Resurrection saying La ilaha illallah, seeking thereby the Face of
   Allah, but Allah will have forbidden the Fire to him.” 177 chars, the short
   direct form. CORRECTED 2026-10-12 from #425, which this file previously
   carried: Dorar shows #425 is narrated by Mahmud ibn ar-Rabi' al-Ansari and
   is the LONG narrative about Itban's eyesight and the Prophet ﷺ praying in
   his house. The error came from a commentary footnote citing #425 for a
   phrase inside that story. #6938 is a third, longer Itban variant.
3. **Sahih al-Bukhari #6570 AND #99** — Abu Hurairah. The most fortunate of
   people with the Prophet's ﷺ intercession is the one who said
   “La ilaha illallah” sincerely from his heart. It appears TWICE in Bukhari:
   #6570 in Kitab ar-Riqaq and #99 in Kitab al-Ilm. Either cites correctly;
   #6570 is the usual reference for intercession. Flag for the duplicate-number
   index, which already tracks three collisions.

**REJECTED — do not publish:**

4. **Jami at-Tirmidhi #3585** — “the best supplication is that of the Day of
   Arafah, and the best thing I and the prophets before me said is
   La ilaha illallah wahdahu la sharika lah…”, narrated from the grandfather
   of Amr ibn Shu'ayb (Abdullah ibn Amr). The ZAD slide grades it hasan after
   al-Albani. The chain is CONTESTED and the weight is against it:
   at-Tirmidhi himself called it gharib from this route and named Hammad ibn
   Abi Hamid as not strong; Ibn Hajar, adh-Dhahabi, Ibn al-Mulaqqin and
   al-Manawi weakened it. Al-Albani gave hasan li-ghayrihi and al-Mundhiri
   sahih al-isnad, which is why it circulates widely.
   **This channel exists to flag weak hadith spreading on social media.**
   Publishing one that Ibn Hajar and adh-Dhahabi weakened, on the strength of
   a single hasan li-ghayrihi, would undercut the premise it is built on. The
   fact that it is popular is the reason to leave it alone, not to run it.

Not yet in the library — all numbers were checked against it and none exist as
rows. **Sourced 2026-10-12 via Workflow L** (`upload-candidates.py --queries`,
Dorar only, no API key): 3 queries → 6 rows in `out/candidates-dorar.json`,
39 daif/empty dropped, 0 duplicates. Keep **bukhari #3435, #6423, #6570**;
the other three rows are Muslim/longer variants of the same three hadiths.
Still to do: `--commit` to hadith_candidates, then Workflow I for the four
translations, which are ours and not the source's (P178).

---

## Assets
**THE ASWATI BEDS SIT TOO QUIET IN THE MIX — operator, by ear, 2026-10-16.**
Only the `aswati-*` tracks; the `vocal-nasheed-*` beds and `light-of-my-heart-bg`
are fine at the same setting. The adults mix is fixed at narration 1.4 / nasheed
0.12 (P171), one level for every bed, so a quieter master lands under-audible
while a louder one is right. Raise the Aswati ones a little.

Not applied yet, deliberately: #1903 EN shipped on `light-of-my-heart-bg`, and
changing the gain mid-set would mix the four languages of one reel differently.
#1903's RU/UZ/TJ are being kept off Aswati beds so the question does not touch
this set at all.

Two ways to do it, and the second is better:
  - Normalise the eight files in place — simplest, but it edits licensed
    masters and records nothing about why.
  - Add a per-bed gain to the registry and have `render-reel.ps1` multiply 0.12
    by it. The registry is already the place a human records what a bed IS
    (P168), the reason gets written down beside the value, and the originals are
    untouched. It also gives the unplaced `aswati-Victory-March` somewhere to
    record its tone, which the Aswati note below says it needs.

Measure before setting numbers: integrated LUFS per bed, not a guessed multiplier.

**Kids-lane nasheed beds.** The eight Aswati tracks registered 2026-10-05 are
ADULTS ONLY. The kids rotation is unchanged and still thin. Separate search.

**Aswati per-track licence certificates.** Eight of them, from Aswati Studio
— Account — Your licenses, into `out/backgrounds/licenses/`. Section 1 of
their licence calls these the proof; only the terms snapshot is saved so far.
Note `out/` is gitignored, so that folder is not backed up by the repo — a
copy exists on D:\licenses.

**Aswati beds are live — and the showcase reply is CLOSED (2026-10-12).**
Twelve reels across R114—R125 (2026-10-09 to 10-11) on seven of the eight
beds. Only Victory-March is still unplaced: it is the sole 0-use bed, so the
picker recommended it on all four legs of #5027 and it was overruled on tone
every time — a quiet hadith will never take a triumphal march, so it will keep
surfacing until something places it or the registry records its tone.
The link went to Al-Mutawari for the aswati.co/showcase wall:
youtube.com/@SahihHadithReels, credited as SahihHadithReels. That closes the
commitment made in the 2026-10-10 reply. YouTube is the only platform carrying
the “Nasheed: Aswati Studio” credit line — Telegram, Instagram and TikTok
captions have none, which is fine: their licence section 4 requires no
attribution at all.

**The contemplative beds are spent.** Of 17 adults-eligible, the four calm
ones went to #1631 and the remaining unused are Focused-Determination,
Victory-March and Steady-Motivation — all driving. Four tone overrides were
needed across these two sets and every one was a guess from the FILENAME,
which is what P168 exists to warn against for lane eligibility. Either
source calm beds or listen to the three and record what they actually are.

---

## Ideas, scoped but not scheduled
**Use LATER SEGMENTS of a nasheed as separate beds — operator idea, 2026-10-16.**
Every reel starts the bed at 0:00, so only the first 20-70s of each file is ever
heard. Measured durations, all 17 adults-eligible beds (ffprobe, same session):

| Bed | Length | Segments @45s |
|---|---|---|
| aswati-Victory-March | 220.0s | 4 |
| aswati-Heartfelt-Gratitude | 206.9s | 4 |
| path-to-jannah-bg | 156.9s | 3 |
| light-of-my-heart-bg | 150.0s | 3 |
| vocal-nasheed-07 | 148.3s | 3 |
| aswati-Rising-Hope | 93.4s | 2 |
| aswati-Steady-Motivation | 89.9s | 1 |
| aswati-Focused-Determination | 88.4s | 1 |
| aswati-Peaceful-Contemplation | 56.0s | 1 |
| vocal-nasheed-03 | 50.9s | 1 |
| aswati-Gentle-Reflection | 49.6s | 1 |
| vocal-nasheed-02 | 47.6s | 1 |
| aswati-Morning-Serenity | 46.3s | 1 |
| vocal-nasheed-01 | 43.5s | 0 |
| vocal-nasheed-06 | 37.9s | 0 |
| vocal-nasheed-05 | 19.1s | 0 |
| vocal-nasheed-04 | 16.3s | 0 |

25.4 minutes of audio in total. The idea is worth doing but it is **1.5x, not 3x**:
17 beds -> 26 segments at 45s, and 8 of the 26 come from two files. The range is
16s to 220s, not the 20-60s it feels like.

**FOUND WHILE MEASURING, AND MORE URGENT: four beds are SHORTER than the reels
they carry.** `-stream_loop -1` is on the nasheed input, so they repeat.
`vocal-nasheed-04` is 16.3s and carried R096, a 69.2s reel — 4.2 plays of the
same vocal phrase. `vocal-nasheed-05` (19.1s) carried R131; `-06` (37.9s) and
`-01` (43.5s) loop on anything average-length. Nothing measures this and no gate
mentions it. Decide whether those four are retired, reserved for short reels, or
accepted; right now they are drawn like any other bed.

**What segmenting needs — it is not just `-ss`:**
  1. **Offsets are listened to, not computed.** A 45s cut into a vocal nasheed can
     start mid-word. Each offset is a human judgement, so it belongs in the
     registry next to `verified`: `"segments": [0, 48, 96, 144]`, with a note on
     what was checked.
  2. **A segment must be as identifiable as a bed.** `.last-used.json`, the
     tracker's Nasheed column and the P201 sidecar all key on filename. Without
     an identity like `aswati-Victory-March.mp3@96`, the no-repeat rule cannot
     tell two segments apart and the asset-reuse counts become wrong.
  3. **`-ss` together with `-stream_loop -1` must be TESTED.** Whether the loop
     restarts at 0 or at the offset is unknown, and guessing about a flag's
     interaction is how P214 happened.
  4. **Do it with P249's fix.** Both rewrite the picker's state; doing them
     separately means touching the same code twice and re-testing it twice.
**BETTER VARIANT, operator's: SPLIT THE FILES instead of seeking into them.**
`light-of-my-heart-bg-s1.mp3`, `-s2`, `-s3` as three separate beds. This removes
every objection above: **no code change at all** — no `-ss`, no `-stream_loop`
interaction to test — and identity comes free, because a segment IS a filename,
so `.last-used.json`, the tracker's Nasheed column, the P201 sidecar and the
asset-reuse audit all keep working untouched. The picker sees distinct beds and
its avoid logic applies with no change. Each segment gets its own registry entry:
its own `verified` (a human listened to THAT segment, which is the honest claim),
its own measured `gain`, its own note.

If it is ever built, four decisions:
  1. **No segment shorter than 70s.** The longest adults reel to date is 69.2s, so
     a 70s floor means `-stream_loop` never repeats and the looping defect above
     dies with it. Divide evenly rather than cutting fixed chunks: Victory-March
     3x73s, Heartfelt-Gratitude 2x103s, path-to-jannah 2x78s,
     light-of-my-heart 2x75s, vocal-nasheed-07 2x74s. Five beds -> eleven
     segments, 17 adults beds -> 23.
  2. **Retire the parent** (`lanes: []`) once split, or the same audio is drawable
     twice: the parent's first 75s IS segment 1. `audit-assets.py --check`
     already blocks an empty-lane bed, so the mechanism exists.
  3. **Name them `-s1/-s2/-s3`**, not `-beg/-mid/-end`: "mid" is meaningless at
     two segments and breaks at four. P197 is why naming conventions get decided
     once rather than per file.
  4. **Split points are chosen by ear.** A cut can land mid-word.

**LICENCE GATE, and it is the reason this is parked rather than scheduled.** Four
of the five long beds are Aswati, and splitting is editing a licensed master.
Their licence section 1 calls the per-track certificates the proof of licence and
only the terms snapshot is saved so far — read the terms on derivative edits
before cutting those four. `path-to-jannah-bg` and `vocal-nasheed-07` are Pixabay
and permissive, so a two-bed / four-segment pilot is available with no licence
question at all.

**Operator's call 2026-10-16: PARKED.** An idea, not a requirement — if the
licence forbids it or it turns into a lot of change, the beds stay as they are.
Reconsider only if bed variety becomes an actual complaint.



**HV: verify a hadith from a video or reel link.** Proposed 2026-10-09. The
reverse of the text/screenshot verifier: a lot of reels recite the hadith aloud,
and checking one today means copying it out by hand.

Build it in two phases, and the first one is mostly not speech at all:

  - **Phase 1 — caption path.** Paste a link, pull the post's CAPTION, run the
    EXISTING text verifier. No transcription, no new verdict logic. Most reels
    carry the hadith or at least the citation in the caption, so this covers
    the majority of real cases with the component that already works.
  - **Phase 2 — ASR, only if phase 1 shows demand.** For genuinely
    caption-less recitation. ARABIC FIRST: the matn is fixed and the register
    constrained, so a near-match is actual evidence. Output must read
    “possible match — confirm” and never a verdict, and the transcript must be
    shown so the human sees what it heard.

**Why not ASR-first.** Transcription is lossy and the matching that follows is
built on its output, so errors compound into the one thing HV must never emit:
a confident wrong verdict on a sound narration. The evidence is in this repo —
Whisper needed hand correction on FOUR consecutive RU sets of our own clean,
single-voice, no-background TTS audio, and UZ and TJ are where it is weakest.
A stranger's phone video with a nasheed bed is a much harder input than
anything we have fed it. The fuzzy-match step afterwards is the same problem
that defeated check_twin_wording on clean text (P205), with worse signal.

**Build it with agent #15, not beside it.** Both answer “someone posted a
hadith, is it sound” — #15 from comments, this from posts. One shared path:
candidate text -> library match -> human confirms. Two separate ones means two
places for a verdict to be wrong.

---

## Tools
**CORRECTION 2026-10-16 — STAGE 3 PASS B WORKS. The no-credits note above is
stale, and nothing but this line says so.** `verify-candidates.py` was run twice
tonight against Bukhari #1903 and `gpt-5.6-terra` answered every call, at high
confidence, both times. Whatever exhausted the OpenAI account has been topped up.
Stage 3 is available now, not "one billing top-up away".

**`--library` EXISTS AND HAD NEVER BEEN USED.** `verify-candidates.py --library`
(L315) verifies rows in `hadith_library` rather than candidates. That matters
more than it sounds: **the library predates the sourcing pipeline, so most of its
rows have never been A/B verified at all.** 35 of 70 rows have been used in
reels; #1903 was one of them, shipped in four languages tonight, and its first
ever A/B run was after EN and RU had already published.

What that first run found on #1903, both models agreeing, 0% disagreement:
  - `text_uzbek_cyrillic` — «амал» is generic action, losing the referential
    به that ties the deed to the falsehood. An OMISSION.
  - `text_tajik` — «амали бад», "a general bad deed", a word that is in no
    part of والعمل به. An ADDITION, and worse.
  Both corrected, `text_uzbek_latin` regenerated via derive-uzbek-latin (P097),
  re-verified pass/pass on both models.

**RU IS A LIVE DISAGREEMENT ON THE SAME CLAUSE — DO NOT RE-ROLL IT.** On the
first run both models passed `text_russian` at high confidence; on the second,
against UNCHANGED text, B failed it at high confidence for the same reason it
failed UZ. That is the non-determinism recorded for #3435. The design is explicit:
disagreement is the output Stage 3 exists to produce and is never resolved by a
third pass or by preferring one model, and P177 is the trap of re-running until
the answer is nice. RU stands as `disagree` / needs_human, and it has SHIPPED.

**UZ's four published captions quote the pre-correction matn.** The row was fixed
about an hour after the UZ reel went out, so TG/IG/YT/TikTok still read «амалдан»
while the library and the audio read «унга амал қилишдан». Same shape as #6570's
Hurayrah. The burned audio cannot change; the captions can be edited in place.

**NEXT STEP, and it is a real one: run `--library` over the rest.** 34 other used
rows have never been through Stage 3. #1903 failed two of four languages on its
first exposure. Do it in D5-sized batches and read the disagreement rate.

**The ASSISTANT's hand-written translations have no G3 guard.** Found 2026-10-16
on #1903 RU. `translate-candidates.py` translates every language from
`text_arabic` and REFUSES to fall back to another translation (G3, L479), and
prints `from: text_arabic (never another translation)` on each run. The generator
writes S/M/H/C per language from that language's own column. So the pipeline
never pivots through English. But when the assistant rewrites a defective block
by hand in chat — which happened for RU's M and H — it worked from the ENGLISH
text, and «стол» (EN's "table" for the meal) came across as an idiom that does
not carry in Russian. The operator caught it. Same shape as `-Scenes` having a
registry gate since P121 while the random-pick path still has none: the
disciplined route is guarded and the ad-hoc one is not. There is no script to
put a guard in, so the remedy is a rule: a hand-written block starts from the
Arabic matn and that language's own stored text, never from another language's
rendering.

**Cyrillic captions put the period INSIDE the closing guillemet.** «…питьё.»
where Russian puts it after the quotation mark: «…питьё». It comes from the stored
matn carrying its own trailing period plus `buildCaption`'s wrapper, so it
affects EVERY RU/UZ/TJ caption shipped, not one reel. Cosmetic, and the fix is a
choice between stripping the terminal period in the wrapper (one place, affects
all languages) or dropping it from the stored matn columns (many rows, and the
matn is quoted source text). Not urgent; decide once rather than per reel.

**P249 — the nasheed picker, now written up.** `.last-used.json` keeps one bed per
LANE and is written at pick time, so an aborted render burns the slot and a
re-render of a published reel silently changes its bed while the sidecar and the
tracker column are rewritten to match. No per-reel or per-language rule exists in
the picker at all — that is the #6570/#13 clash mechanism, still live. Workaround:
pass `-Nasheed` explicitly for every language of a set. Fix: write the state after
the render returns 0, key it by slug+lang, and read the set's `*-render.json`
sidecars. Demonstrated three times in one evening on #1903 EN.

**P250 — the FLUX still prompt is recorded nowhere, now written up.**
`generate-image.ps1` writes no sidecar, and `animated-reel-scene-prompts.md` is a
methodology doc rather than a log. #1903's four still prompts are LOST — not in
the sidecars, not in that doc, not in the transcript. Every earlier set got away
with it because the registry note was composed in the same session that generated
the stills. Fix: `generate-image.ps1` writes `<name>-still.json` with prompt,
negative prompt, model, variants returned and which was chosen.

**NO PREFLIGHT — every precondition is checked at render time.** On 2026-10-16
#1903 EN failed twice for reasons knowable in under a second: the four clips were
unregistered (registry gate, after Whisper had already run) and the narration did
not match `draft.txt` (stt lint, at the SRT pause, after ffmpeg had concatenated).
A `-Check` mode on `render-reel.ps1` that validates registry membership,
narration-against-draft and scene resolution BEFORE any slow or paid work would
have caught both at the start. This is the highest-value unbuilt thing in the
render path.

**~~`reel-creation-pipeline.md` adults checklist has no registration step.~~ RESOLVED 2026-10-16 — a registration warning was added inside Step 13 (no renumbering), and Step 13's stale `normalized`-only claim was corrected for P217. See P253 for the wider problem.** Original note:
Step 12 watch, Step 13 stage, Step 14 render — asset-registry registration appears
in none of the sixteen, though the gate has blocked renders since P121/P237. The
publishing procedure was the same kind of gap and was written down 2026-10-16;
this one is still open. Adding a numbered step renumbers 13–16, so the likely fix
is a note inside Step 13 rather than a new step.


**Random scene selection has no registry gate.** `render-reel.ps1` without
`-Scenes` globs `out\backgrounds\new\normalized\*.mp4` and draws three at
random, with no call to audit-assets. `-Scenes` has had that gate since P121,
and the nasheed picker got one in P168; this path never did, so an
unregistered or retired clip in that folder can reach a reel. Found while
fixing P217, deliberately not widened into it. Low urgency - every recent set
renders with explicit `-Scenes` - but it is the same class as P121 and P168.

**Kling 3.0 evaluation.** CLOSED 2026-10-11 — evaluated and ADOPTED. One still,
one prompt, both models, 10s each, at the #5027 set boundary. 3.0 casts
physically coherent directional light where 2.6 gives a flat warm patch; it also
reads motion instructions more aggressively, so camera moves want conservative
phrasing. Default switched in `generate-scene.ps1`. Both models preserved real
Arabic composited onto the still through 10s — see the Practice note in
`self_upskilling.md`. Blockers cleared on the way: P214 (audio-off guard scoped
to `v2\.6`) and P215 (no clip's prompt was ever stored).

---

## External / blocked

**Facebook Page** — avatar, bio, cross-post toggle still unset.

**Agent #15 (comment triage), step 1: the Meta app.** BLOCKED behind the
Facebook account appeal. The account was disabled after being created and
registered as a developer the same day.

---

## Recently closed

- 2026-10-10 — P213 closed. `lint-content.py` now flags an abbreviated
  companion honorific in a NARRATED block (S or M). A check, not an
  expansion: (RA) is gender-neutral written and gendered spoken, so
  cleanForTTS cannot resolve it and the draft must. Verified on the real
  R118 defect, on the spelled-out form, on an abbreviation confined to H
  and C, and on the Russian «(р.а.)».

- 2026-10-10 — P210 and P211 fixed; R118—R121 shipped, Tirmidhi #3895,
  four languages, four platforms each.

- 2026-10-09 — Tirmidhi #1899 reviewed and cleared. The Tajik was never
  wrong; the diacritic check is a heuristic and that sentence legitimately has
  none of ӣүҳқғҷ. The actual defect was EN and RU rendering الوالد as
  “parent” against FATHER in the Arabic, Uzbek and Tajik — now aligned.

- 2026-10-09 — P197 closed. `audit-assets.py --names` built, and all three
  misnamed sets renamed: b2628->m2628, b4248->ij4248, b4251->ij4251. 17 files,
  11 registry keys, 18 tracker lines; three prose lines left alone on purpose.

- 2026-10-09 — duplicate-number check added to audit-library.py; it found
  Tirmidhi #2616 and Bukhari #1469 doubled on first run, confirming what an
  earlier session had recorded and OPEN_ITEMS carried as unverified. Both are
  now rows in the tracker's duplicate-check index.

- 2026-10-09 — P200 fixed: `scripts/restore-srt-casing.py`, wired into
  render-reel.ps1 ahead of the validator.
- 2026-10-05 — R110—R113 shipped, Sahih Muslim #2759, four languages, four
  platforms each.
- 2026-10-05 — P199 generator rules 21—22 and the `quote-addition` lint check.
- 2026-10-05 — P201 per-reel nasheed sidecar.
- 2026-10-05 — eight Aswati beds registered; adults-eligible beds 9 -> 17.
- 2026-10-04 — P198 FLUX 2 adopted as the stills default.
