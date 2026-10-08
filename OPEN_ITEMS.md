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

## Blocks content — do not ship past these

**Jami at-Tirmidhi #1899, `text_tajik`**
The parents hadith. 85 characters with none of ӣүҳқғҷ — it reads as Russian with
Tajik word order, not Tajik. `audit-library.py` has flagged it as INFO on every
run since it was noticed, including 2026-10-08. Do NOT produce that set until
the column is rewritten and the audit comes back clean.

**Sahih al-Bukhari #6871 must never be selected**
It is #2654's twin wording. The duplicate-check index keys on `hadith_number`,
so nothing stops it being picked and nothing would flag the near-duplicate after
it shipped. P147 class. Check wording, not just the number.

---

## Recorded, not built

**P200 — post-Whisper capitalisation and yo pass.** Fires on EVERY en/ru reel.
Whisper transcribes sound, so divine-pronoun capitalisation and Russian yo are
destroyed every time and restored by hand at the review pause. Four of five RU
findings on the #2759 set were this class. `-NoReview` skips the human and the
validator only warns, so a render can ship lowercase divine pronouns with a
clean-looking run. The source text is already on disk as draft.txt. Highest
value of anything in this section.

**P196 — the linter only ever sees text a human already cleaned.**

**P197 — `b2628` is misnamed.** It is a Sahih Muslim hadith carrying a Bukhari
prefix, and Bukhari #2628 is a real and different hadith on gifts. Needs the
files, the registry and the R102—R105 tracker rows renamed to `m2628`. Second
half: `audit-assets.py` has no opinion on whether a clip name matches its
hadith, and the tracker holds both columns, so the reconciliation is a few lines.

**P126 — classifier blind spots.** Partly covered.

**Verify: further P147 duplicate-number collisions.**
An earlier session recorded that Jami at-Tirmidhi #2616 and Sahih al-Bukhari
#1469 each appear TWICE in `hadith_library` under one number. The tracker's
duplicate-check index documents only the #6018 collision, so this is unconfirmed
— it may have been noted in conversation and never written down, or it may
have been resolved. Sweep `hadith_library` for repeated `hadith_number` values
before the next sourcing run and either fix the index or delete this item.

---

## Pipeline / design

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

---

## Assets

**Kids-lane nasheed beds.** The eight Aswati tracks registered 2026-10-05 are
ADULTS ONLY. The kids rotation is unchanged and still thin. Separate search.

**Aswati per-track licence certificates.** Eight of them, from Aswati Studio
— Account — Your licenses, into `out/backgrounds/licenses/`. Section 1 of
their licence calls these the proof; only the terms snapshot is saved so far.
Note `out/` is gitignored, so that folder is not backed up by the repo — a
copy exists on D:\licenses.

**No reel has used an Aswati bed yet.** The next set will be the first. The
reply to Al-Mutawari committed to sending him that link when it ships.

---

## Tools

**Kling 3.0 evaluation.** OPEN on `self_upskilling.md`. Run at a set boundary,
same prompt through both models, as FLUX 2 was evaluated. Watchlist next due
2026-10-11.

---

## External / blocked

**Facebook Page** — avatar, bio, cross-post toggle still unset.

**Agent #15 (comment triage), step 1: the Meta app.** BLOCKED behind the
Facebook account appeal. The account was disabled after being created and
registered as a developer the same day.

---

## Recently closed

- 2026-10-05 — R110—R113 shipped, Sahih Muslim #2759, four languages, four
  platforms each.
- 2026-10-05 — P199 generator rules 21—22 and the `quote-addition` lint check.
- 2026-10-05 — P201 per-reel nasheed sidecar.
- 2026-10-05 — eight Aswati beds registered; adults-eligible beds 9 -> 17.
- 2026-10-04 — P198 FLUX 2 adopted as the stills default.
