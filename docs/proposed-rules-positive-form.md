# PROPOSED — generator rules 7–21 in positive form

**STATUS: NOT APPLIED. Do not paste this into `generate-reel/route.ts` yet.**

Hold until **Bukhari #6570 has been generated and read** under rule 25 alone.
Rule 25 is explicitly NOT YET VERIFIED and #6570 is its test. Applying this
rewrite first destroys that test: one generation, two changes, no signal — a
clean result would not say which change worked, and a dirty one would not say
which failed. Rules 23 and 24 looked exactly this sound when they went in on
2026-10-12 and lost within a day, which is the reason to find out what KIND of
fix holds rather than stack another plausible one.

Second reason to go slowly: P101. That was a generator-prompt edit that actively
instructed fabrication, and it took two Russian generations with invented speech
attributed to the Prophet ﷺ before anyone caught it. Fifteen rules rewritten at
once in this prompt is the same shape of change.

## Why rewrite at all

Two findings point the same way.

- **R026** — negations reinforce what they forbid. The prompt is 25 rules and
  most of 7–21 lead with NEVER.
- **P233** — rule 22 and rule 25, the two rules written as a positive TEST the
  generation runs against itself, are the two with a clean record. Rules that
  enumerate forbidden wordings (23, 24) were walked around by the next wording.

So the change is not cosmetic de-negation. It is: **give each rule a positive
action the model can execute, and keep the prohibition as the named failure** —
the house style rules 23, 24 and 25 already use (DO first, failing form second,
evidence last). No constraint is dropped. Every piece of evidence is kept.

## What this is NOT

It does not touch rules 1–6, 22, 23, 24 or 25. It does not remove a single
prohibition — each one survives as the second clause of its rule. If a reviewer
finds a constraint in the current prompt that is not in the text below, that is a
defect in this draft, not an intended simplification.

---

## Proposed text for rules 7–21

```
ABSOLUTE CONTENT RULES (violating any of these is a fabricated hadith):
7. The story contains only what the hadith text or the cited seerah source
   records. Every incident, scene and exchange in it must be traceable to one of
   those two. A detail you cannot point at in either is invented, however
   plausible it sounds.
8. Quotation marks enclose only words the narration itself records. Attribute
   speech to the Prophet ﷺ, to any prophet, or to any companion exactly as far
   as the hadith gives it: where the matn ends, the quotation ends.
9. Report what the narration records, and stop there. Inner states - what a
   person felt, thought, saw, or did afterwards - and the occasion, setting or
   audience belong in the reel only where the narration supplies them. Most
   hadith record no occasion, and silence is the correct output rather than a
   supplied one.
10. Let a short hadith stay short. Where it needs context, draw that from
    documented history of the period. A shorter story is a correct story;
    narrative added to fill the space is not.
11. Name a narrator plainly - "narrated by Ibn Umar" - and let the name stand
    alone. Standard honorifics that follow a name in the target language (RA,
    رضي الله عنه, розияллоҳу анҳу) belong. Epithets, descriptions, family
    relationships and standing among the companions do not: "the great
    companion", "son of the second caliph", "one of the closest companions".
12. Use isnad verbs by their roles: the Prophet ﷺ SAID the hadith, the companion
    NARRATED or TRANSMITTED it. In Russian that is «сказал» for the Prophet ﷺ,
    not «передал» or «рассказал»; every language carries the same distinction
    and it holds in all of them.
13. Write the divine name in its fixed form:
    EN "Allah" · RU "Аллах" · UZ "Аллоҳ" · TJ "Аллоҳ" · AR "الله".
    Where the hadith itself says Rabb, render it Lord / Господь / Парвардигор /
    Раббим - that is a different word in the source and is kept as such. Any
    other substitute ("God", "Бог", "Худо") replaces the name the source uses.
    Directing an action TO Allah means addressing the action to Him - "for the
    sake of Allah", "Allah sees this". State a warrant - what Allah commanded,
    entrusted or categorised - only where the matn states one. On Tirmidhi #3895
    all FOUR languages satisfied this rule while inventing a warrant the matn
    does not contain: "Allah has entrusted their care to you", "бу Аллоҳнинг
    амри", "Который возложил на человека ответственность", "аз роҳҳои ба даст
    овардани ризои Аллоҳ". Sound teaching, absent from the hadith (P212).
14. Explain what a term MEANS; take what it is LIKE only from the hadith. A
    comparison the matn does not make is an invention even when it illuminates -
    "like standing near a warm light", "like being close to the sun", "like a
    door being opened" were all produced that way.
15. Carry the hadith's meaning at its own level. Where it states a station of
    closeness, honour or elevation, render it as that station; a softened or
    inverted rendering reports something the matn did not say.
16. State the subject at the rank the matn gives it. If the hadith says a thing
    IS worship, that is what it is - not the greatest worship, the highest
    worship, the foundation of all worship, or the most valuable of deeds. If it
    states a virtue, state that virtue without measuring it against virtues the
    matn does not mention. A short hadith stays short: brevity is not an
    invitation to supply significance the text does not claim.
    Keep its TENSE and MOOD too. If the matn says Allah FORBADE the Fire to him,
    that is a completed act - writing that He PROMISED to moves it from done to
    pending, and the listener is owed the matn's own certainty. Three of four
    languages did this on Bukhari #6423 (RU, UZ, TJ: ваъда / ваъда қилган /
    ваъдаи), while the moral field description above had said "do not add a
    promise the matn does not make" the whole time - in prose, not in this list.
    P226 again.
17. The MORAL applies the hadith in your own words, addressed to the listener;
    the STORY block carries the attribution. A clause of the form "the Prophet ﷺ
    said that X" in the moral re-quotes instead of applying, and it reads as
    compliant with rule 8 precisely because X is a faithful paraphrase of the
    matn - it is not compliant. Evidence: across two sets and eight generations,
    nearly every moral block re-attributed.
18. Keep everything between "the Prophet ﷺ said" and the end of that saying
    inside the matn. Scope words the matn does not contain - "in worldly
    matters", "v etom mire", "in this life" - are additions to his speech even
    when the qualification is correct scholarship. They belong in
    seerah_context.
19. Render a hadith with a reason clause as ONE continuous utterance, because it
    is one saying. Splitting it into a quote plus a separate act of explaining -
    "and he explained that", "Va izoh dod", "On obyasnil" - frames a second
    speech event that nothing records.
20. The hadith's own instruction is the only instruction the reel gives. Naming
    a dhikr, a du'a formula or a phrase to repeat that the matn does not contain
    adds an instruction to it: no "say alhamdulillah" unless the matn says it.
21. Open every STORY block by naming the speaker - "The Prophet ﷺ said",
    "Пророк ﷺ сказал", "Пайғамбар ﷺ айтдилар", "Паёмбар ﷺ фармуданд" - and let
    the saying follow. A block that states the matn as bare text is not a
    shorter correct version of an attributed one; it is an unattributed claim,
    and an unattributed claim is the one thing this channel cannot publish.
    Evidence: the Uzbek generation for Sahih Muslim #2759 came back with no
    attribution anywhere in the block, from the same prompt that produced a
    correct attribution in English, Russian and Tajik.
```

---

## Review checklist before applying

1. **#6570 has been generated and read** under rule 25 alone, and the result is
   recorded. This is the gate; nothing below matters until it is met.
2. Diff this against the live rules 7–21 and confirm **every prohibition still
   present**. The rewrite is a change of register, not of content.
3. Rules 1–6 and 22–25 unchanged.
4. Apply as ONE commit, with its own pattern number, marked NOT YET VERIFIED.
   Its test is the set AFTER #6570 — not #6570 itself, which is rule 25's.
5. Expect it to be judged the same way rules 23 and 24 were: by reading four
   languages of the next set side by side (P235, Workflow I step 3a).

## The honest uncertainty

R026 is a sound principle and the rule-22/rule-25 evidence is suggestive, but it
is two data points. It is equally possible that what makes a rule hold is being a
TEST rather than being POSITIVE, in which case rewriting 7–21 in positive voice
changes little and the real work is converting them to checks the generation runs
against itself — a much larger change than this one. #6570 is the first evidence
that bears on it either way.
