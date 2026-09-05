#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
translate-candidates.py - Stage 2 of the sourcing pipeline.

Reads hadith_candidates at status='deduped', translates the ARABIC MATN into
EN / RU / UZ-Cyrillic / TJ, and writes the result back with per-field
provenance. Dry-run by default: proposes to a JSON file for human reading,
writes nothing until --commit.

WHY FROM THE ARABIC, ALWAYS
  P075 built the current Tajik column by translating text_uzbek -> text_tajik.
  That is a translation of a translation, and its errors compound: «Неки» for
  «Некӣ» (R037) and the P050 Russian-fallback class both live downstream of it.
  Guardrail G3 requires native Tajik generated from the matn. This script will
  refuse to translate a candidate that has no text_arabic rather than fall back
  to another language column.

WHAT IT DOES NOT DO
  It does not verify. Stage 3 does that, with two independent passes, and the
  design (D2) requires pass B to be a DIFFERENT model from the one used here -
  a model must not be the sole verifier of its own output.
  It does not fill text_uzbek_latin. That is derived from the canonical
  Cyrillic by scripts/lib/uzbek-translit.ts (deriveBothScripts), which is
  already tested for okina vs tutuq and apostrophe folding. Reimplementing it
  in Python would produce a second, subtly different set of okina bugs.
  It does not promote. Stage 5 does that, after the human gate.

USAGE
  python scripts/translate-candidates.py                    # dry run, all deduped
  python scripts/translate-candidates.py --row 527          # one hadith_number
  python scripts/translate-candidates.py --lang tj          # one language
  python scripts/translate-candidates.py --limit 10         # D5 batch size
  python scripts/translate-candidates.py --commit           # write to DB

  Review out/candidate-translations.json before ever passing --commit.

Requires in .env.local:
  NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

MODEL = 'claude-sonnet-5'
MAX_TOKENS = 1500
ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
ANTHROPIC_VERSION = '2023-06-01'

OUT_PATH = os.path.join('out', 'candidate-translations.json')

URL_KEYS = ('NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_URL')
SERVICE_KEYS = ('SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_KEY',
                'SERVICE_ROLE_KEY')
ANTHROPIC_KEYS = ('ANTHROPIC_API_KEY',)

# Column per language. text_uzbek_latin is deliberately absent - derived, not
# translated (D4: Cyrillic canonical).
TARGETS = {
    'en': 'text_english',
    'ru': 'text_russian',
    'uz': 'text_uzbek_cyrillic',
    'tj': 'text_tajik',
}

# ---------------------------------------------------------------- prompts

# The fabrication rules are the point of this block. A model asked only for a
# "formal and reverent" register will smooth a terse matn into something
# fuller - the same length-pressure failure as P116, where forbidding invented
# FACT, COMPARISON and SOURCE still left invented IMPORTANCE open.
COMMON_RULES = """You are translating a single hadith matn from Arabic. This is
religious text and the translation will be published.

ABSOLUTE RULES:
- Translate ONLY what the Arabic says. Add no clause, no explanation, no
  connective that is not in the source.
- Do not supply an attribution the matn does not carry. If the Arabic does not
  say who spoke, your translation does not either.
- Do not add comparisons, similes or imagery. If the matn has none, neither
  does the translation.
- Do not elevate. Do not add "greatest", "most important", "foundational" or
  any ranking the Arabic does not state. A short hadith stays short. Brevity
  is not an invitation to supply significance.
- Preserve the honorific ﷺ exactly where it appears, as the glyph.
- Keep proper names as names.
- If any part of the Arabic is unclear to you, output the marker
  [UNCERTAIN: your note] inline at that point rather than guessing. Abstaining
  is correct; a plausible invention is not.

OUTPUT: the translation only. No preamble, no quotation marks, no notes."""

LANG_RULES = {
    'en': """Target: English.
Formal, plain, reverent. Match the register of a scholarly hadith translation,
not devotional prose.""",

    'ru': """Target: Russian (Cyrillic).
Formal and reverent. Use Аллах for the divine name - never Бог. Watch case
endings: "любимо Аллаху" (dative) and "любимо Аллахом" (instrumental) are both
grammatical but mean different things; choose the one the Arabic requires.
Every character must be Cyrillic - a Latin letter inside a Cyrillic word is
invisible on screen and has shipped before.""",

    'uz': """Target: Uzbek in CYRILLIC script (this is the canonical script).
Use Аллоҳ for the divine name - never Худо. Use ҳ, қ, ғ, ў correctly per Uzbek
convention, not their Russian equivalents. Do not output Latin script; the
Latin column is derived from this one by a separate transliterator.""",

    'tj': """Target: Tajik in Cyrillic script, as NATIVE TAJIK - not a
transliteration of Uzbek or Russian.
Use the Tajik letters properly: ҷ (not ж), ӣ (long i, e.g. некӣ not неки),
ӯ (long u), ҳ, қ, ғ. Use Persian-derived Tajik vocabulary and constructions.
Use Аллоҳ for the divine name. A Tajik reader must not be able to tell this
was produced by a machine reading Arabic.""",
}

# ---------------------------------------------------------------- helpers


def load_env(path='.env.local'):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def pick(env, names):
    for n in names:
        if env.get(n):
            return env[n]
        if os.environ.get(n):
            return os.environ[n]
    return None


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def sb_get(base, key, table, params):
    url = f'{base.rstrip("/")}/rest/v1/{table}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'apikey': key, 'Authorization': f'Bearer {key}',
        'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def sb_patch(base, key, table, match, payload):
    url = f'{base.rstrip("/")}/rest/v1/{table}?' + urllib.parse.urlencode(match)
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body, method='PATCH', headers={
        'apikey': key, 'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json', 'Prefer': 'return=representation'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def translate(api_key, arabic, lang):
    """One call, one language. Never chained off another translation."""
    system = COMMON_RULES + '\n\n' + LANG_RULES[lang]
    body = json.dumps({
        'model': MODEL,
        'max_tokens': MAX_TOKENS,
        'system': system,
        'messages': [{'role': 'user', 'content': arabic}],
    }, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(ANTHROPIC_URL, data=body, headers={
        'x-api-key': api_key,
        'anthropic-version': ANTHROPIC_VERSION,
        'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode('utf-8'))
    parts = [b.get('text', '') for b in data.get('content', [])
             if b.get('type') == 'text']
    return '\n'.join(parts).strip()


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(
        description='Stage 2 - translate candidate matn into EN/RU/UZ/TJ.')
    ap.add_argument('--row', help='one hadith_number only')
    ap.add_argument('--lang', choices=sorted(TARGETS), action='append',
                    help='limit to these languages (repeatable)')
    ap.add_argument('--limit', type=int, default=10,
                    help='batch size (D5: small, human-digestible)')
    ap.add_argument('--overwrite', action='store_true',
                    help='retranslate fields that already have text')
    ap.add_argument('--commit', action='store_true',
                    help='write to the DB. Without this, nothing is written.')
    ap.add_argument('--library', action='store_true',
                    help='translate rows in hadith_library instead of candidates '
                    '(P151: for rows whose matn was corrected after promotion)')
    args = ap.parse_args()

    langs = args.lang or list(TARGETS)

    env = load_env()
    base = pick(env, URL_KEYS)
    key = pick(env, SERVICE_KEYS)
    api_key = pick(env, ANTHROPIC_KEYS)
    if not base or not key:
        print('FAILED: need Supabase URL + service-role key in .env.local')
        return 2
    if not api_key:
        print('FAILED: need ANTHROPIC_API_KEY in .env.local')
        return 2

        # P151: a corrected matn needs re-translating, but the row is already in
    # hadith_library and will never appear in hadith_candidates again. Six matn
    # corrections on 2026-09-04 left three library rows with null translations
    # and no supported way to refill them.
    table = 'hadith_library' if args.library else 'hadith_candidates'
    if args.library:
        # No status column in the library. Default to rows whose translations
        # are missing, which is exactly the post-correction case.
        params = {'select': '*', 'limit': str(args.limit),
                  'order': 'hadith_number.asc'}
        if args.row:
            params['hadith_number'] = f'eq.{args.row}'
        else:
            params['text_russian'] = 'is.null'
    else:
        params = {'select': '*', 'status': 'eq.deduped',
                  'limit': str(args.limit), 'order': 'created_at.asc'}
        if args.row:
            params['hadith_number'] = f'eq.{args.row}'
            params.pop('status')
    try:
        rows = sb_get(base, key, table, params)
    except Exception as e:  # noqa: BLE001
        print(f'FAILED reading {table}: {e}')
        return 2

    if not rows:
        print("no candidates at status='deduped'"
              + (f' for hadith_number={args.row}' if args.row else ''))
        return 0

    width = 74
    print('=' * width)
    print(f' stage 2 translate - {len(rows)} candidate(s)  '
          f'[{"COMMIT" if args.commit else "DRY RUN"}]')
    print(f' model: {MODEL}   from: text_arabic (never another translation)')
    print('=' * width)

    results = []
    for row in rows:
        ref = f'{row.get("collection")} #{row.get("hadith_number")}'
        arabic = (row.get('text_arabic') or '').strip()

        if not arabic:
            print(f'  SKIP {ref} - no text_arabic. G3 forbids falling back to '
                  f'another language column.')
            continue

        print(f'\n  {ref}')
        proposed, meta = {}, dict(row.get('translation_meta') or {})

        for lang in langs:
            col = TARGETS[lang]
            if (row.get(col) or '').strip() and not args.overwrite:
                print(f'    {lang}: already present, skipping (--overwrite to redo)')
                continue
            try:
                text = translate(api_key, arabic, lang)
            except urllib.error.HTTPError as e:
                print(f'    {lang}: HTTP {e.code} - {e.read().decode("utf-8")[:200]}')
                continue
            except Exception as e:  # noqa: BLE001
                print(f'    {lang}: {e}')
                continue

            proposed[col] = text
            meta[col] = {'provenance': 'machine', 'model': MODEL,
                         'source_field': 'text_arabic', 'at': now_iso()}
            flag = '  [UNCERTAIN]' if '[UNCERTAIN' in text else ''
            print(f'    {lang}: {text[:64]}{"..." if len(text) > 64 else ""}{flag}')
            time.sleep(0.4)

        if not proposed:
            continue

        results.append({'candidate_id': row.get('candidate_id') or row.get('id'), 'ref': ref,
                        'text_arabic': arabic, 'proposed': proposed,
                        'translation_meta': meta})

        if args.commit:
            payload = dict(proposed)
            payload['translation_meta'] = meta
            if args.library:
                # P151: a re-translation is UNVERIFIED until Stage 3 passes.
                # Clearing matn_verified_at prevents a corrected row carrying a
                # verification stamp for translations nobody has checked - the
                # exact mistake made on #2616 on 2026-09-04.
                payload.pop('translation_meta', None)   # not a library column
                payload['matn_verified_at'] = None
                match = {'id': f'eq.{row["id"]}'}
                done = 'written, matn_verified_at cleared - run Stage 3'
            else:
                payload['status'] = 'translated'
                payload['updated_at'] = now_iso()
                match = {'candidate_id': f'eq.{row["candidate_id"]}'}
                done = 'written, status=translated'
            try:
                sb_patch(base, key, table, match, payload)
                print(f'    -> {done}')
            except Exception as e:  # noqa: BLE001
                print(f'    -> WRITE FAILED: {e}')

    os.makedirs('out', exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print('\n' + '-' * width)
    print(f'  {len(results)} candidate(s) translated -> {OUT_PATH}')
    if args.commit:
        if args.library:
            print('  WRITTEN to hadith_library. matn_verified_at CLEARED -')
            print('  these translations are unverified until Stage 3 passes.')
        else:
            print('  WRITTEN. status=translated. Uzbek Latin is still empty -')
            print('  derive it with uzbek-translit.ts, then Stage 3 verifies.')
    else:
        print('  DRY RUN - nothing written. Read the JSON, then --commit.')
    print('  A translation is machine output. The human gate is Stage 4.')
    print('-' * width)
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
