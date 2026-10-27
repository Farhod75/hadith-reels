// lib/caption.ts — the caption BODY, in one place.
//
// WHY THIS FILE EXISTS (P305). The body was assembled inline inside
// app/admin/page.tsx's buildCaption(), which made the admin the only thing in
// the project able to produce a caption. P246 showed the cost: #6570's
// generated blocks were lost when draft.txt was overwritten, and rebuilding
// its captions outside the admin left two bad choices — re-generate the blocks
// (P245 re-attributed the moral in 7 of 8 generations) or write a second
// assembler and let the two drift.
//
// Drift here is not hypothetical. Everything in this file is a typographic fix
// that took a published defect to find: P180 (a matn that BEGINS with «),
// P236 (a matn carrying « INSIDE it, nested identically), and the closing
// period that belongs outside the guillemet in ru/uz/tj. Each was one defect
// across every caption, not one reel. A second copy of this logic is a
// guarantee that the next such fix lands in one copy only.
//
// Same reasoning as P121 / P168 / P237: one place answers the question and
// callers ask it, rather than each caller re-implementing the rule. The admin
// and scripts/build-caption.ts both call buildCaptionBody().
//
// This file is PURE — no DB, no filesystem, no clock — so it is safe to call
// from a script, a route or a React component.

import { buildRef, buildTranslationCredit } from './refs'

// P150: the verify line and hashtags were hardcoded English and appended to
// Cyrillic body text on every RU/UZ/TJ reel. Topic tags stay English — they
// come from the library's `tags` column and travel across languages.
//
// Exported because fitTagLine()'s caller needs `tags`, `kids` and `lang` from
// the same table that supplies `verify` here. Two tables would drift.
export const CAPTION_L10N: Record<
  string,
  { verify: string; tags: string; kids: string; lang: string }
> = {
  en: { verify: 'Verify',           tags: '#hadith #islamic #authentic', kids: '#kids',      lang: '#english' },
  ru: { verify: 'Проверить хадис',  tags: '#хадис #ислам #сунна',        kids: '#дети',      lang: '#русский' },
  uz: { verify: 'Ҳадисни текшириш', tags: '#ҳадис #ислом #суннат',       kids: '#болаларга', lang: '#ўзбекча' },
  tj: { verify: 'Ҳадисро санҷед',   tags: '#ҳадис #ислом #суннат',       kids: '#кӯдакон',   lang: '#тоҷикӣ' },
  ar: { verify: 'تحقق من الحديث',     tags: '#حديث #إسلام #سنة',            kids: '#أطفال',     lang: '#العربية' },
}

// Only the fields the body actually reads. Narrower than the admin's `Hadith`
// on purpose: a script fetching three columns should not have to invent the
// rest of that interface to call this.
export interface CaptionRow {
  text_display?: string | null
  text_english: string
  text_arabic?: string | null
  collection: string
  hadith_number?: string | number | null
  narrator: string
  translation_source?: string | null
}

// The two generated blocks the body quotes. The admin passes its `Generated`,
// which carries more; a script passes just these.
export interface CaptionBlocks {
  title: string
  moral: string
}

// Russian, Uzbek and Tajik typography put a closing period AFTER the closing
// guillemet — «…питьё». — while a question or exclamation mark stays inside:
// «Кто это?». The stored matn carries its own terminal period, the wrapper put
// it inside, and so every RU/UZ/TJ caption this project published read
// «…питьё.». One defect, every caption, not one reel.
//
// The fix belongs in the WRAPPER for the same reason P236's did: the matn is
// quoted as the source quotes it, and it is the wrapper that creates the
// boundary. Editing the stored columns would change quoted source text across
// many rows to undo something we add.
//
// en and ar are left alone — English convention differs, Arabic uses other
// quotation marks, and neither was reported. A trailing '..' is left alone so
// an ellipsis does not lose a dot.
export function wrapMatn(text: string, lang: string): string {
  // P236: a matn carrying « INSIDE it. Wrapping gives «… «kalima» …»,
  // identical guillemets nested, which Russian, Uzbek and Tajik typography all
  // read as broken. It hit Bukhari #6423 in RU and UZ and was corrected BY
  // HAND both times, in the same hour, before anyone noticed it was one defect
  // rather than two. Demote the inner pair to „…“, the second-level
  // convention in all three Cyrillic languages this channel publishes.
  const inner = text.replace(/«/g, '„').replace(/»/g, '“').trimEnd()
  if (!['ru', 'uz', 'tj'].includes(lang)) return `«${inner}»`
  if (inner.endsWith('.') && !inner.endsWith('..')) return `«${inner.slice(0, -1)}».`
  return `«${inner}»`
}

// The body never flexes. P116: length pressure on generated text is
// fabrication pressure — told to be shorter, the model complied on narrative
// and inflated importance instead. The hadith text and the Arabic matn are the
// caption's verifiability (P106, P153). Only the tag line, which the CALLER
// appends via fitTagLine(), gives when Telegram's cap is tight.
export function buildCaptionBody(opts: {
  row: CaptionRow
  blocks: CaptionBlocks
  lang: string
}): string {
  const { row, blocks, lang } = opts
  const l10n = CAPTION_L10N[lang] || CAPTION_L10N.en

  const hadithText = row.text_display || row.text_english

  // P150: localised collection with the Latin name kept in parentheses — the
  // citation has to stay verifiable, and some readers read only their own
  // language.
  const ref = buildRef(row.collection, row.hadith_number, row.narrator, lang)

  // P176: HadeethEnc's licence requires crediting them on every row carrying
  // their text. Returns '' for in-house rows, so nothing is emitted.
  const credit = buildTranslationCredit(row.translation_source, lang)

  return (
    `${blocks.title}\n\n` +
    // P180: these matns begin with « themselves (the first words are the
    // Prophet's speech), so the wrapper produced «« and a lone closing ».
    // Only wrap text that isn't already quoted.
    (hadithText.trim().startsWith('«')
      ? `${hadithText}\n\n`
      : `${wrapMatn(hadithText, lang)}\n\n`) +
    // P153: the Arabic was in the DB and in the admin card but never reached a
    // viewer, so nobody with Arabic could check the translation against the
    // source — which is the one external check this project has. Full matn,
    // never truncated.
    (row.text_arabic ? `${row.text_arabic}\n\n` : '') +
    `${blocks.moral}\n\n` +
    `📖 ${ref}\n` +
    // Ternary, not `${credit}\n` — an in-house row would otherwise emit a
    // blank line where the credit would have been.
    (credit ? `${credit}\n` : '') +
    `🔍 ${l10n.verify}: hadithverifier.com\n\n`
  )
}
