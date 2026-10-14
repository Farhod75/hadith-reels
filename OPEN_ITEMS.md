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

**#6570 DROPPED BACK TO `translated` — re-run Stage 3 before producing it.**
The Tajik kalima spacing fix on 2026-10-14 went through sign → apply, and
`--apply` sets `status='translated'` for any row not at a terminal status.
That is correct behaviour, not a bug: the text changed, so the Stage 3
verdict no longer describes the text it passed. The change was orthographic
(«Лоилоҳа» → «Ло илоҳа», same words) and no verifier would score it
differently — but the system cannot know that, and #6570 is 2–3 weeks out, so
there is time to re-verify rather than reason around it. `verify_agreement`
still reads `pass` from the previous run; that verdict is now STALE.

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
translated rows, and **pass B returned HTTP 429 on all 20 calls: “You have no
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
  pass B has no credits. TJ «холис аз таҳти дили худ» and EN “from his own
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
