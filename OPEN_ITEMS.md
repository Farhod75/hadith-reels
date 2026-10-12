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

Set after set, agreed 2026-10-09. Each fills a theme gap the tracker records
as uncovered.

1. **Sahih Muslim #1631** — the three ongoing deeds. IN PROGRESS. Fills
   Death / Afterlife (zero coverage) and is the hadith this channel exists
   under: ongoing charity and beneficial knowledge. Library row verified clean
   across all six columns before generation.
2. **Jami at-Tirmidhi #3895** — best to his family. Fills the family /
   marriage gap. Works in the kids lane if that lane is due.
3. **Sahih al-Bukhari #5027** — learn the Quran and teach it. Fills
   Quran / Tilawah (zero coverage). STARTED 2026-10-11; library row read and
   clean in all six fields.
   **Scene-set question resolved 2026-10-11.** This entry and the registry
   disagreed: here, `ad3641-rahle` "risks reading as a repeat"; on
   `m1631-circle`, the manuscript was left out "so ad3641-rahle stays clear
   for #5027". R026's note settles it — that clip was pushed through three
   FLUX rounds deliberately AWAY from a mushaf layout, into a student's
   working-notes register (irregular lines, marginal annotations, ink blots).
   So the mushaf image is genuinely unused and belongs to this hadith, but
   reusing `ad3641-rahle` inside this set would put two manuscript-on-a-stand
   compositions in one reel. **Decision: #5027 gets ONE new mushaf scene and
   does not reuse ad3641-rahle.** The other new scenes should carry what this
   matn uniquely has and the library does not — transmission, learn AND teach,
   one becoming many — not a second study image. Era note: before Uthman's
   codex the Quran was written on palm stalks, thin flat stones and parchment,
   which is attested for the Hijaz and visually unused here; Uthman narrates
   this hadith, so the codex itself is also era-apt. Avoid a named lamp in any
   prompt (b2654 generated a temple shrine, b6446 a shrine niche) and describe
   positively rather than by negation (R026, R026-class negation failure).

Not this round: #1469 and #2616 each have the two-row collision, so picking
either means first deciding which clause. #1903 sits close to #2654's subject
(false speech) — not a twin, but look at it deliberately rather than by
surprise.

---
## Blocks content — do not ship past these

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
2. **Sahih al-Bukhari #425** — Itban ibn Malik, Kitab as-Salah, Bab
   al-Masajid fi'l-Buyut. Allah has forbidden the Fire to whoever says
   “La ilaha illallah” seeking thereby the Face of Allah. Number confirmed;
   the Muslim number was NOT confirmed, so cite Bukhari alone until it is.
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

Not yet in the library — all four numbers were checked against it and none
exist as rows. Library rows still to be written for the three cleared.

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
