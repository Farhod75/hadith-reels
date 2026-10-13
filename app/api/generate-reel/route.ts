// app/api/generate-reel/route.ts
// POST /api/generate-reel
// Generates story + moral + seerah_context + caption for a hadith reel
//
// Seerah sources (dual — matched to language):
//   AR/EN → Ar-Raheeq Al-Makhtum (Safiur Rahman al-Mubarakpuri)
//   UZ/TJ/RU → Uswa al-Hasana (Усваи Хасана) — Turkish Islamic Seerah
//              translated to Russian/Uzbek, emotional devotional style

import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { writeFile } from 'fs/promises'
import path from 'path'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY! })

// ─── Language instruction ─────────────────────────────────────────────────────
function getLangInstruction(lang: string): string {
  if (lang === 'uz' || lang === 'uz_cyrillic')
    return 'Write ALL text in UZBEK CYRILLIC script (Ўзбек Кириллча). Every single character must be Cyrillic. Do NOT use Latin.'
  if (lang === 'uz_latin')
    return 'Write ALL text in Uzbek Latin script (O\'zbek lotin).'
  if (lang === 'ru')
    return 'Write ALL text in Russian (Русский язык).'
  if (lang === 'ar')
    return 'Write ALL text in Modern Standard Arabic (العربية الفصحى).'
  if (lang === 'tj')
    return 'Write ALL text in Tajik Cyrillic (Тоҷикӣ). Use Tajik vocabulary, not Russian.'
  return 'Write ALL text in English.'
}

// ─── Seerah source selection ──────────────────────────────────────────────────
// Ar-Raheeq Al-Makhtum: scholarly, historical, Arabic/English audience
// Uswa al-Hasana: emotional, devotional, warm — Russian/Uzbek/Tajik audience
function getSeerahSource(lang: string): { name: string; description: string; attribution: string } {
  if (lang === 'ru' || lang === 'uz' || lang === 'uz_cyrillic' || lang === 'uz_latin' || lang === 'tj') {
    return {
      name: 'Uswa al-Hasana (Усваи Ҳасана)',
      description: 'the multi-volume Turkish Islamic Seerah translated into Russian and Uzbek, known for its warm emotional and devotional style, strong emphasis on love for the Prophet ﷺ',
      attribution: lang === 'ru'
        ? '📖 Источник: Усваи Хасана'
        : lang === 'tj'
        ? '📖 Сарчашма: Усваи Ҳасана'
        : '📖 Манба: Усваи Ҳасана',
    }
  }
  return {
    name: 'Ar-Raheeq Al-Makhtum',
    description: 'the award-winning biography of the Prophet ﷺ by Safiur Rahman al-Mubarakpuri, first prize of the Muslim World League Seerah competition 1979, known for its scholarly and eloquent style',
    attribution: '📖 Source: Ar-Raheeq Al-Makhtum',
  }
}

// ─── Audience instruction ─────────────────────────────────────────────────────
function getAudienceInstruction(style: string): string {
  if (style === 'kids') {
    return `Audience: children aged 6-14.
- Use SIMPLE, short sentences. Max 10 words per sentence.
- Explain plainly in words a child knows. Do NOT invent comparisons. If the hadith itself contains an image, use that one; if it does not, describe the teaching directly.
- No scholarly terms. No Arabic terms without immediate simple explanation.
- Warm, encouraging, wonder-inspiring tone.
- End with something a child can DO today.`
  }
  return `Audience: adults seeking spiritual growth.
- Use eloquent, warm, scholarly tone.
- Can include deeper reflection and nuance.
- Reference historical context naturally.
- Inspire without being preachy.`
}

// ─── Main handler ─────────────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}))
    const {
      hadith_text,
      hadith_arabic,
      narrator,
      collection,
      hadith_number,
      tags,
      style = 'adults',
      lang  = 'en',
    } = body

    if (!hadith_text?.trim()) {
      return NextResponse.json({ error: 'hadith_text required' }, { status: 400 })
    }

    const langInstruction     = getLangInstruction(lang)
    const audienceInstruction = getAudienceInstruction(style)
    const seerahSource        = getSeerahSource(lang)

    const prompt = `${langInstruction}

${audienceInstruction}

Hadith to create a reel about:
Text: "${hadith_text}"
Arabic: "${hadith_arabic || ''}"
Narrator: ${narrator || 'unknown'}
Collection: ${collection || 'unknown'}${hadith_number ? ` #${hadith_number}` : ''}
Tags: ${tags?.join(', ') || ''}

Seerah source to draw from:
"${seerahSource.name}" — ${seerahSource.description}

Generate reel content. Respond ONLY with valid JSON (no markdown, no backticks, no preamble):
{
  "title": "Max 8 words. State what the hadith is ABOUT, or quote its own words. It may not promise the reader an outcome, name a benefit, or rank the deed — the matn says what it says, and the title says no more. 'Two Deeds Allah Loves' is right; 'The Believer Always Wins' is not.",
  "story": "Follow the matn's own length. A one-sentence hadith gets a short story; do not pad to a target. Say what the hadith says, in the order it says it. You may explain a term it uses. You may NOT say what kind of thing it describes, how much of life it covers, or what the person thereby gains.",
  "moral": "1-2 sentences. A concrete action, and the reason the hadith gives for it. The action must be something a person does BEFORE ALLAH — thanking Him, obeying Him, guarding what He commanded, seeking what He promised — not a self-improvement tip that would read the same in a secular post. 'Notice how that feels in your chest' is wrong; 'say alhamdulillah — Allah promised Paradise to the one who guards them' is right. Name Allah, or name what He promised, or name the act of worship. State the ground plainly, as the hadith states it — do not explain what the hadith 'ties' or 'shows' or 'teaches', and do not describe how Allah made something known. Say the thing, not a comment about the text. The hadith is the Prophet's ﷺ speech unless the matn itself says Allah said it. Never attribute the wording to Allah — that would make it a hadith qudsi, which it is not. Do not add a promise the matn does not make.",
  "seerah_context": "2-3 sentences of context. If the sources tie this hadith to a specific period or event, name it. If they do not, give the collection and book, the narrator, and the classical scholarly reading of the hadith's meaning — and nothing more. Do not supply a period, setting, or occasion that the sources do not record.",
  "source_attribution": "${seerahSource.attribution}",
  "caption_intro": "First 2 lines of social media caption — must grab attention immediately. No hashtags here."
}

RULES:
1. ALL fields in the language specified above (${lang})
2. story may reference the Prophet ﷺ or his companions ONLY as the hadith and
   cited seerah source record them. If neither records an incident for this
   hadith, do NOT construct one — explain the teaching itself instead.
3. moral MUST be practical AND directed to Allah. "What to do today" alone
   produced twenty consecutive generations with no mention of Allah in the
   moral — the action had no addressee because none was asked for (P155).
4. title is drawn from the matn, not from what would make someone click. A title that promises more than the hadith states is fabrication in the most-read line of the reel.
5. For Kids style: use simple, concrete language a child can follow. Do NOT invent
   a scene — describe the historical setting and the lesson in plain words
6. seerah_context cites a real period ONLY if the sources tie this hadith to one.
   Otherwise state exactly three things and nothing more: the collection and book,
   the narrator, and the established meaning of the hadith stated directly.
   Do NOT attribute that meaning to "scholars", "the ulama", or any unnamed
   authority — state the meaning itself, without a speaker.
   Do NOT add a period, setting, or occasion in softened form — phrases like
   "during a time when" or "in an era where" are occasions and are forbidden.
   Do NOT name a seerah source unless you are citing a specific documented
   passage from it about THIS hadith. This applies to NEGATIVE statements
   too — do not write that a source contains nothing, records no occasion,
   or does not tie the hadith to a period. Naming a book you did not cite
   implies you consulted it. If there is no occasion, say nothing about
   sources at all: state the collection, the narrator, and the meaning,
   and stop.

ABSOLUTE CONTENT RULES (violating any of these is a fabricated hadith):
7. NEVER invent an incident, scene, or conversation that is not in the hadith text
   or the cited seerah source
8. NEVER attribute direct or indirect speech to the Prophet ﷺ, any prophet, or any
   companion beyond what the hadith itself records. No quotation marks around words
   they did not say.
9. NEVER state what any person or group felt, thought, saw, or did afterwards.
   NEVER assert the occasion, setting, or audience of the hadith unless the
   narration itself records it. Most hadith have no recorded occasion — say
   nothing rather than supply one.
10. If the hadith text is short, expand ONLY into documented historical context of
    the period. Do NOT compensate with narrative — a shorter story is correct;
    an invented one is not.
11. Name narrators plainly - "narrated by Ibn Umar", nothing more. Do NOT add
    epithets, honorific descriptions, family relationships, or standing among
    the companions ("the great companion", "son of the second caliph", "one of
    the closest companions"). Standard honorifics that follow a name in the
    target language (RA, رضي الله عنه, розияллоҳу анҳу) are permitted.
12. Use isnad verbs correctly. The Prophet ﷺ SAID the hadith; the companion
    NARRATED or TRANSMITTED it. Never write that the Prophet ﷺ transmitted,
    related, or passed on a hadith - in Russian use "сказал", not "передал"
    or "рассказал"; the equivalent distinction applies in every language.
13. The divine name is FIXED per language and MUST NOT vary:
    EN "Allah" · RU "Аллах" · UZ "Аллоҳ" · TJ "Аллоҳ" · AR "الله".
   DIRECTED TO Allah means the ACTION is addressed to Him - "for the sake of
   Allah", "Allah sees this". It does NOT license a claim about what Allah
   commanded, entrusted, or categorised. On Tirmidhi #3895 all FOUR languages
   satisfied this rule by inventing a warrant the matn does not contain:
   "Allah has entrusted their care to you", "бу Аллоҳнинг амри",
   "Который возложил на человека ответственность", "аз роҳҳои ба даст
   овардани ризои Аллоҳ". Sound teaching, absent from the hadith, and rule 16
   violations produced BY rule 3 (P212). If the matn states the warrant, say
   it; otherwise address the action to Allah and stop.
    NEVER "God", "Бог", "Худо" or any other substitute. Exception: where the
    hadith text itself says Rabb (Lord), translate it as Lord / Господь /
    Парвардигор / Раббим — that is a different word in the source and is kept.
14. NEVER invent a simile, metaphor, or comparison that is not in the hadith
    text. Explaining what a term MEANS is permitted; inventing what it is LIKE
    is fabrication. No "it is like standing near a warm light", no "like being
    close to the sun", no "like a door being opened".
15. NEVER reframe, soften, or invert the hadith's meaning. If the hadith states
    a station of closeness, honour, or elevation, do not render it as lowly,
    diminished, or reduced.
16. NEVER rank or elevate the hadith's subject beyond what the matn states. If
    the hadith says a thing IS worship, do not call it the greatest worship, the
    highest worship, the foundation of all worship, or the most valuable of
    deeds. If the hadith states a virtue, state that virtue — do not compare it
    to virtues the matn does not mention. A short hadith stays short: brevity is
    not an invitation to supply significance the text does not claim.
    Nor shift its TENSE or MOOD. If the matn says Allah FORBADE the Fire to him,
    do not write that He PROMISED to - a completed statement rendered as a pledge
    moves the thing from done to pending, and the listener is owed the matn's own
    certainty. Three of four languages did this on Bukhari #6423 (RU, UZ, TJ:
    ваъда / ваъда қилган / ваъдаи), while the moral field description above has
    said "do not add a promise the matn does not make" the whole time - prose,
    not a numbered rule. P226 again.
17. The MORAL block APPLIES the hadith; it does not re-quote it. NEVER write a
    clause of the form "the Prophet SAW said that X" in the moral, even when X is
    a faithful paraphrase of the matn. Rule 8 forbids speech BEYOND the hadith,
    and a paraphrase of the matn reads as compliant against it - it is not. The
    story block carries the attribution. The moral carries the application, in
    your own words, addressed to the listener. Evidence: across two sets and
    eight generations, nearly every moral block re-attributed.
18. NEVER add a qualification INSIDE the attribution. Everything between "the
    Prophet SAW said" and the end of that saying must be in the matn. Scope words
    the matn does not contain - "in worldly matters", "v etom mire", "in this
    life" - are additions to his speech even when the qualification is correct
    scholarship. It belongs in seerah_context, not in his mouth.
19. A hadith with a reason clause is ONE utterance. NEVER split it into a quote
    plus a separate act of explaining - no "and he explained that", no "Va izoh
    dod", no "On obyasnil". That frames a second speech event that nothing
    records. Render the whole saying continuously.
20. NEVER instruct the listener to recite anything the matn does not contain. No
    "say alhamdulillah", no named dhikr, no du'a formula, no phrase to repeat.
    The hadith's own instruction is the only instruction.
21. The STORY block MUST name the speaker. Every story block opens with the
    Prophet SAW being identified as the one who said this - "The Prophet SAW
    said", "Prorok SAW skazal", "Payghambar SAW aytdilar", "Payomabar SAW
    farmudand" - and the saying follows it. A story block that states the matn
    as bare text with no speaker is NOT a shorter version of a correct one. It
    is an unattributed claim, and an unattributed claim is the one thing this
    channel cannot publish. Evidence: the Uzbek generation for Sahih Muslim
    #2759 came back with no attribution anywhere in the block, from the same
    prompt that produced a correct attribution in English, Russian and Tajik.
22. Rules 15-21 apply with EQUAL force in Uzbek, Tajik and Russian as in
    English. They are written in English and they hold best in English: on
    Sahih Muslim #2759 the English generation obeyed all of them, Uzbek broke
    rule 17, and Tajik broke rules 17 AND 18 - appending commentary about the
    door of repentance closing INSIDE the Prophet's SAW quotation, where the
    matn ends. Correct scholarship placed in his mouth is still an addition to
    his speech. Before emitting a non-English generation, check the quoted span
    clause by clause against the matn you were given and drop anything the matn
    does not contain.
23. The moral SAYS THE THING. Write the action and the reason the hadith itself
    gives, addressed to the listener. A clause of the form "this hadith shows",
    "teaches us", "reminds us", "ties X to Y" describes what the sentence does
    instead of saying what it says, and the listener is here to act, not to be
    told what a sentence accomplishes. Evidence: on Bukhari #5027 this appeared
    in THREE of four languages in one set - while the constraint existed only
    inside the moral field description above and not in this list. Every rule
    in THIS list held on that set. A constraint in the field prose gets read;
    a constraint in this list gets obeyed.
24. State the deed and the ground the matn states, and STOP at that ground. A
    purpose clause the matn does not contain - "so that", "in order to", "with
    the intention of", "so Allah will" - supplies an intention on the actor's
    behalf, and a supplied intention is an addition even when it is sound
    teaching. This is rule 13's P212 failure wearing a different grammar: there
    the invented warrant was Allah's, here it is the listener's. Same set, also
    three of four languages.
25. GROUND EVERY CLAUSE. Before emitting the moral or seerah_context, take each
    clause and point at the words in the matn it comes from. If you cannot point
    at them, delete the clause. This test SUPERSEDES the enumerated wordings in
    rules 23 and 24: those name specific forms, and a rule that names forms is
    walked around by the next form. Three failures, one move:
      - rule 13 / P212 supplied a WARRANT    - "Allah has entrusted this to you"
      - rule 24 supplied a PURPOSE           - "so that Allah will ..."
      - Bukhari #6423 supplied an EXCLUSION  - "not merely with the tongue, but
        from the heart", in ALL FOUR languages at once (RU "а не как пустые
        слова на устах", UZ "фақат тил билан айтишга эмас, балки", TJ twice,
        in the moral AND the context).
    Each time, the matn stated a CONDITION and the generation completed the frame
    around it - the reason behind it, the aim in front of it, or the failure it
    rules out. A condition in the matn is complete as given. State the condition;
    never state what it excludes. Naming the exclusion also plants the very thing
    it forbids (R026): a reel about sincerity should not teach the audience the
    shape of insincerity.
    The matn said "seeking thereby the Face of Allah". That IS the whole
    condition. "Not with the tongue only" is not in it, however true it is.`

        // P232: the model was asked to hand-write JSON whose string values must
    // carry the matn VERBATIM. The Russian matn contains straight double
    // quotes - говорящий: "Нет божества, кроме Аллаха" - and copying them
    // verbatim closes the JSON string early. The model did nothing wrong: it
    // quoted exactly as rule 2 and P153 demand, and the envelope could not
    // carry what the rules required it to put inside.
    //
    // EN passed only because its matn happens to use guillemets. UZ and TJ
    // share Russian typography, so this was two failures from looking like a
    // language bug instead of an encoding one.
    //
    // Instructing the model to escape its quotes would hold until the next
    // unusual character. A tool schema moves JSON construction into the API,
    // where escaping is not the model's job at all. Never ask a model to
    // hand-serialize text it does not control.
    const REEL_TOOL = {
      name: 'emit_reel',
      description: 'Return the generated reel content.',
      input_schema: {
        type: 'object' as const,
        properties: {
          title:              { type: 'string' as const },
          story:              { type: 'string' as const },
          moral:              { type: 'string' as const },
          seerah_context:     { type: 'string' as const },
          source_attribution: { type: 'string' as const },
          caption_intro:      { type: 'string' as const },
        },
        required: ['title', 'story', 'moral', 'seerah_context',
                   'source_attribution', 'caption_intro'],
      },
    }

    const response = await anthropic.messages.create({
      model:      'claude-sonnet-5',
      // P144: 1200 was sized for a non-thinking model, where the whole budget
      // went to output. sonnet-5 spends it on thinking FIRST — so a harder
      // generation (Uzbek, a contested point, a long context block) exhausts
      // the budget before emitting any text and returns a thinking block
      // alone. That is the "no text block (got: thinking)" failure, three
      // times in a row on UZ #82 while EN and RU succeeded on the same route.
      max_tokens:  4000,
      tools:       [REEL_TOOL],
      tool_choice: { type: 'tool', name: 'emit_reel' },
      messages:    [{ role: 'user', content: prompt }],
    })

    // P140 still holds, one block type over: sonnet-5 emits a thinking block
    // first, so never index content by position.
    const toolBlock: any = response.content.find((b: any) => b.type === 'tool_use')
    if (!toolBlock) {
      // P231: a diagnostic that lives only in a console is one you lose
      // exactly when you need it — the dev server outlives the terminal that
      // started it, and the first failure's text was already gone.
      const dump = path.join(process.cwd(), 'out', 'last-parse-failure.txt')
      const texts = response.content
        .filter((b: any) => b.type === 'text').map((b: any) => b.text).join('\n')
      try {
        await writeFile(dump,
          `stop_reason: ${response.stop_reason}\n` +
          `blocks: ${response.content.map((b: any) => b.type).join(', ')}\n` +
          `lang: ${lang}  style: ${style}\n` +
          `at: ${new Date().toISOString()}\n${'='.repeat(60)}\n${texts}`,
          'utf8')
      } catch (e: any) {
        console.error('P231: dump write failed:', e?.message)
      }
      return NextResponse.json(
        { error: 'Model returned no tool_use block (got: ' +
                 response.content.map((b: any) => b.type).join(', ') +
                 ', stop_reason: ' + response.stop_reason +
                 ') - see out/last-parse-failure.txt' },
        { status: 500 }
      )
    }

    const result: any = { ...toolBlock.input }

    // Add metadata
    result.lang           = lang
    result.style          = style
    result.seerah_source  = seerahSource.name

    // P196: write draft.txt from the RAW generated output, BEFORE any human
    // has corrected it. Until 2026-10-05 draft.txt was written by hand AFTER
    // the block review, so lint-content.py only ever saw text a human had
    // already cleaned. On the #2963 set it reported "no findings" four times
    // on text whose defects had been removed by eye minutes earlier - one of
    // them a Latin "af" inside a Cyrillic word, which its own check_script
    // fails on when shown. The linter was grading the proofreading instead of
    // guarding the output, and four clean runs looked like evidence that
    // generation was clean.
    // Dev only, and never fatal: a generation must not fail because a
    // convenience file could not be written. Same posture as P106.
    if (process.env.NODE_ENV !== 'production') {
      try {
        const oneLine = (s: any) => String(s || '').replace(/\s*\n\s*/g, ' ').trim()
        const draft =
          'S: ' + oneLine(result.story) + '\r\n' +
          'M: ' + oneLine(result.moral) + '\r\n' +
          'H: ' + oneLine(result.seerah_context) + '\r\n' +
          'C: ' + oneLine(result.title) + '\r\n'
        await writeFile(path.join(process.cwd(), 'draft.txt'), draft, 'utf8')
        console.log('P196: draft.txt written from raw generation (' + lang + ')')
      } catch (e: any) {
        console.error('P196: draft.txt write failed:', e?.message)
      }
    }
    
    return NextResponse.json(result)

  } catch (error: any) {
    console.error('Generate reel error:', error?.message)
    return NextResponse.json(
      { error: 'Generation failed: ' + (error?.message || 'unknown') },
      { status: 500 }
    )
  }
}
