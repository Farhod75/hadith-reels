// scripts/lib/caption-explain.test.ts - P387: the caption's link to the hadith page.
// Run: npx tsx scripts/lib/caption-explain.test.ts  (the pre-push hook runs it)
import assert from 'node:assert/strict'
import { explainLine, buildCaptionBody } from '../../lib/caption'

// a hadith with a page: the line, in the caption's language, with the page's language
assert.equal(explainLine('Sahih Muslim', '2564', 'uz'),
  '📚 Тўлиқ ҳадис ва шарҳи: hadithreels.com/hadith/muslim/2564?lang=uz\n')
assert.match(explainLine('Sahih Muslim', 2564, 'tj'), /hadithreels\.com\/hadith\/muslim\/2564\?lang=tj\n$/)

// no page, no line - the caption never points at an empty page
assert.equal(explainLine('Sahih Muslim', '999999', 'ru'), '')
assert.equal(explainLine('Riyad as-Salihin', '1', 'ru'), '')
// AR has no site language
assert.equal(explainLine('Sahih Muslim', '2564', 'ar'), '')

// in the body: after the reference, before the verify line
const body = buildCaptionBody({
  row: { text_english: 'x', collection: 'Sahih Muslim', hadith_number: '2564', narrator: 'Abu Hurairah' },
  blocks: { title: 'T', moral: 'M' },
  lang: 'ru',
})
const iRef = body.indexOf('📖'), iLink = body.indexOf('📚'), iVerify = body.indexOf('🔍')
assert.ok(iRef < iLink && iLink < iVerify, body)

console.log('caption-explain: 6 checks passed')
