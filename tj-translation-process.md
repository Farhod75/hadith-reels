# HR Tajik Translation Process

Reusable pattern for AI-translating hadith corpus content from one language to another, with human review gate.

**First applied:** May 15, 2026 — Uzbek Cyrillic → Tajik Cyrillic for 70 hadiths.

---

## When to use this pattern

Use when:
- Target language has NO existing column/data in `hadith_library`
- Source language column EXISTS and has clean data
- You read both source and target languages well enough to spot-check
- 50-100 rows of content (manual translation too slow, full automation too risky)

Do NOT use for:
- Adding more than ~200 rows at once (cost + review fatigue)
- Languages you don't read (no review possible)
- Initial seed of corpus (use authoritative sources instead)

---

## Architecture

```
Supabase                    Local                       Supabase
hadith_library              out/                        hadith_library
─────────────              ───────                      ──────────────
text_uzbek (60 rows) ──→  Claude API (Sonnet 4.5)
                          per-row translation
                                  │
                                  ▼
                          tajik-translations.json
                                  │
                                  ▼  human review + edit
                          tajik-translations.json (verified)
                                  │
                                  ▼
                                                   ──→ text_tajik UPDATE
```

Two scripts, one JSON checkpoint. Translation never writes directly to DB without human approval.

---

## Prerequisites

**Schema:** target language column must exist in `hadith_library`. If not, ALTER first:
```sql
ALTER TABLE hadith_library ADD COLUMN text_tajik TEXT;
-- or text_<lang> for other languages
```

**Env vars in `.env.local`:**
- `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ANTHROPIC_API_KEY`

**npm packages:**
- `@supabase/supabase-js`
- `@anthropic-ai/sdk`
- `tsx` (devDep)
- `dotenv` (devDep)

---

## Step 1 — Generate translations (no DB writes)

```powershell
cd "C:\QA\Hadith verification AI app\hadith-reels"
npx tsx scripts/translate-tajik.ts
```

**Behavior:**
- Reads all rows from `hadith_library`
- For each row, sends `text_uzbek` to Claude Sonnet 4.5 with strict Tajik system prompt
- Saves results to `out/tajik-translations.json`
- Console prints each translation with 80-char preview (full text in JSON)
- ~30 min for 70 rows; ~$0.10-0.30 in Anthropic API costs at Sonnet pricing

**System prompt design (key rules):**
- Preserve religious phrases exactly (Аллоҳ, Расулуллоҳ, ﷺ)
- Use Tajik-specific letters: ҷ (not ж), ӣ (long i), ӯ (long u), ҳ, қ, ғ
- Use Persian-derived Tajik vocabulary, not just transliterated Uzbek
- Match formal religious register
- Output ONLY the translation, no preamble or quotes
- Keep proper nouns unchanged (Абу Ҳурайра, Мадина)

**Output JSON schema:**
```json
{
  "id": "uuid",
  "hadith_number": "1956",
  "collection": "Jami at-Tirmidhi",
  "text_english_preview": "Your smile for your brother is char",  // truncated to 60 chars
  "text_uzbek": "<full Uzbek text>",
  "text_tajik_proposed": "<full Tajik proposal>",
  "status": "success" | "error",
  "error": "<message if error>"
}
```

---

## Step 2 — Human review

Open `out/tajik-translations.json` in VS Code. Skim through.

**What to look for:**
- Religious terms preserved (Аллоҳ, Расулуллоҳ)
- Tajik grammar feels native (not transliterated source)
- No truncation, no English bleeding through, no hallucinations
- Proper use of Tajik-specific letters (ҷ, ӣ, ӯ)
- Quotation marks, punctuation reasonable

**What to do if you find issues:**
- Edit `text_tajik_proposed` field directly in the JSON
- Save the file
- The apply script will use whatever the JSON says

**What NOT to do:**
- Don't change `id`, `text_uzbek`, or `status` fields
- Don't add new entries
- Don't reorder

**Time required:** ~30-60 min for 70 hadiths if you read the target language.

---

## Step 3 — Dry-run apply

```powershell
npx tsx scripts/apply-tajik-translations.ts
```

**This is a DRY RUN — no DB writes.** Prints:
- Count of entries ready to write
- Count of entries that would be skipped (status≠success or empty translation)
- Preview of first 3 writes

If preview looks correct, proceed to Step 4. If anything looks wrong, fix the JSON and re-dry-run.

---

## Step 4 — Real apply

```powershell
npx tsx scripts/apply-tajik-translations.ts --apply
```

**This writes to Supabase.** Per-row UPDATE on `hadith_library` matched by `id`. Console shows each write as it happens. Final summary box with success/fail counts.

---

## Step 5 — Verify in Supabase

```sql
SELECT hadith_number, LEFT(text_tajik, 60) AS tj_preview
FROM hadith_library 
WHERE text_tajik IS NOT NULL 
LIMIT 10;
```

Should show 10 hadiths with Tajik Cyrillic previews. Spot-check a few in the Supabase UI Table editor for completeness.

---

## Adapting this pattern for other language pairs

For UZ → AR, EN → RU, EN → AR, etc., copy `scripts/translate-tajik.ts` to a new file (e.g. `translate-arabic.ts`) and modify:

1. **System prompt** — language-specific guidance (Arabic diacritics, Russian declensions, etc.)
2. **Source field** — change `h.text_uzbek` to whatever source you're translating from
3. **Target field** — change `text_tajik_proposed` to e.g. `text_arabic_proposed`
4. **Output filename** — change `tajik-translations.json` to e.g. `arabic-translations.json`
5. **Apply script** — copy `apply-tajik-translations.ts`, change column name from `text_tajik` to target column

---

## Cost ballpark

Per 70 hadiths, Sonnet 4.5:
- Input: ~100 tokens per hadith (system prompt + UZ text)
- Output: ~150 tokens per hadith (TJ translation)
- Total: ~17.5K input + ~10K output tokens
- Cost: ~$0.10-0.30 depending on Sonnet pricing tier

Negligible for non-profit Islamic content work. For 1000+ hadiths the math still holds at a few dollars.

---

## Quality observations from May 2026 run

**What Claude Sonnet 4.5 got right:**
- Persian-derived Tajik constructions: "то ҳангоме ки" (not literal Uzbek)
- Proper Tajik vocabulary: "панҷ" (not Uzbek "беш"), "бунёд ёфтааст" (not "қурилган")
- Religious phrases preserved verbatim
- Grammar matched formal Tajik register

**Minor issues observed (1 manual edit needed in 70):**
- Hadith #13: "то он ҳангоме ки" had redundant "он", changed to "то ҳангоме ки"
- A few entries reflected typos/spacing bugs from source UZ data — fixed in source, will re-translate post-Hajj
- Some entries used slightly bookish Persian register; native Tajik speaker might soften — acceptable for v1

**Conclusion:** Sonnet 4.5 is sufficient for v1 production use of religious content translation between closely-related languages. For language pairs with greater distance (UZ → AR, EN → AR), human review density should be higher.

---

## Post-Hajj enhancement ideas

- Re-translate UZ → TJ after fixing UZ source data quality issues (one source of truth)
- Add `text_translator` column to track provenance: "claude-sonnet-4-5 / 2026-05-15" vs "manual / native-speaker"
- Cross-LLM A/B validation: same translation from Claude + ChatGPT + Kimi, flag disagreements
- Backfill all 5 languages where missing (especially AR translations for non-AR content)

