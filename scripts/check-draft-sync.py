#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-draft-sync.py - P282: draft.txt must match the row being rendered.

  python scripts/check-draft-sync.py --lang ru --slug sunan-abu-dawud-1488
  python scripts/check-draft-sync.py --lang uz --slug bukhari-13 --draft other.txt

WHY THIS EXISTS
`stt-validate` compares the burned subtitles against draft.txt, and its whole
authority rests on draft.txt being the text that was actually narrated. Nothing
enforced that. It has failed twice, in both directions:

  2026-10-21  draft.txt held the PREVIOUS wording of the same language. A whole
              clause differed and the comparison still reported 0.958.
  2026-10-22  draft.txt held the EN blocks during a RU render. Correct Russian
              subtitles scored 0.291 and every cue reported "source is latin".
              The subtitles were right; the comparison input was wrong.

The second one looks like a catastrophe and is harmless. The first looks fine
and is the dangerous one - which is why this compares against the DATABASE, not
against a threshold on the SRT.

WHAT IT CHECKS
  1. SCRIPT  - the S block is in the writing system the language uses. en is
               Latin, ru/uz/tj are Cyrillic, ar is Arabic. This alone catches
               the whole-wrong-language case.
  2. MATN    - the S block quotes `text_<lang>` from hadith_library. Compared on
               letters only, so punctuation and quote marks cannot mask a real
               difference, and reported as a ratio so a near miss is legible.

Exits 0 clean, 1 on a mismatch, 2 when it could not run (P093: a gate that
cannot see its data must not report pass).
"""

import argparse
import difflib
import importlib.util
import io
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

_spec = importlib.util.spec_from_file_location(
    'audit_library', os.path.join(HERE, 'audit-library.py'))
_al = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_al)

FIELD = {'en': 'text_english', 'ru': 'text_russian',
         'uz': 'text_uzbek_cyrillic', 'tj': 'text_tajik', 'ar': 'text_arabic'}

SCRIPT = {'en': 'LATIN', 'ru': 'CYRILLIC', 'uz': 'CYRILLIC',
          'tj': 'CYRILLIC', 'ar': 'ARABIC'}

# P294: no longer a pass threshold - the matn must appear contiguously.
# Kept only to describe how far off a stale draft is.


def letters_only(s):
    return ''.join(c.lower() for c in s if c.isalpha())


def dominant_script(s):
    counts = {}
    for c in s:
        if not c.isalpha():
            continue
        name = unicodedata.name(c, '')
        for key in ('LATIN', 'CYRILLIC', 'ARABIC'):
            if key in name:
                counts[key] = counts.get(key, 0) + 1
                break
    if not counts:
        return None
    return max(counts, key=counts.get)


def story_block(path):
    try:
        text = io.open(path, encoding='utf-8-sig').read()
    except (IOError, OSError) as e:
        print('FAILED: cannot read %s (%s)' % (path, e))
        sys.exit(2)
    blocks, current = {}, None
    for raw in text.splitlines():
        m = re.match(r'^\s*([SMHC])\s*:\s*(.*)$', raw)
        if m:
            current = m.group(1)
            blocks.setdefault(current, []).append(m.group(2))
        elif current:
            blocks[current].append(raw)
    if 'S' not in blocks:
        print('FAILED: %s has no S: block' % path)
        sys.exit(2)
    return ' '.join(blocks['S']).strip()


def main():
    ap = argparse.ArgumentParser(description='draft.txt vs the library row.')
    ap.add_argument('--lang', required=True, choices=sorted(FIELD))
    ap.add_argument('--slug', required=True,
                    help='collection-number, e.g. sunan-abu-dawud-1488')
    ap.add_argument('--draft', default='draft.txt')
    args = ap.parse_args()

    m = re.search(r'(\d+)$', args.slug)
    if not m:
        print('FAILED: no hadith number at the end of slug %r' % args.slug)
        return 2
    number = m.group(1)

    draft_path = args.draft
    if not os.path.isabs(draft_path):
        draft_path = os.path.join(ROOT, draft_path)
    story = story_block(draft_path)

    want_script = SCRIPT[args.lang]
    got_script = dominant_script(story)
    if got_script and got_script != want_script:
        print('MISMATCH: %s expects %s, the S block in %s is %s.'
              % (args.lang, want_script, os.path.basename(draft_path), got_script))
        print('  -> the draft holds another language. Re-sync it before TTS.')
        return 1

    env = _al.load_env(os.path.join(ROOT, '.env.local'))
    base = next((env[k] for k in _al.URL_KEYS if env.get(k)), None)
    key = next((env[k] for k in _al.SERVICE_KEYS if env.get(k)), None)
    if not base or not key:
        print('FAILED: need a Supabase URL and service-role key in .env.local')
        return 2
    rows = [r for r in _al.fetch_rows(base, key, 'hadith_library', row=number)]
    if not rows:
        print('FAILED: no hadith_library row for #%s' % number)
        return 2
    row = rows[0]

    matn = row.get(FIELD[args.lang]) or ''
    if not matn:
        print('FAILED: %s is empty on %s - nothing to compare against'
              % (FIELD[args.lang], _al.ref_of(row)))
        return 2

    a, b = letters_only(story), letters_only(matn)

    # P294: the matn must appear CONTIGUOUSLY. The ratio was accepting an
    # inserted word - «яъне» added four letters to a forty-five letter matn and
    # scored 0.94 against a 0.90 threshold. A gloss after the quote is a
    # placement problem; a word inside it is speech the Prophet (saw) did not
    # say. The ratio stays, but only to describe HOW far off a stale draft is -
    # it no longer decides.
    if b and b in a:
        print('OK  draft.txt S block quotes %s exactly (%s)'
              % (FIELD[args.lang], _al.ref_of(row)))
        return 0

    ratio = difflib.SequenceMatcher(None, a, b).ratio()

    # An insertion scores high and is NOT a near miss: every letter of the matn
    # is present, in order, with something wedged between.
    sm = difflib.SequenceMatcher(None, b, a)
    covered = sum(bl.size for bl in sm.get_matching_blocks())
    if b and covered == len(b):
        print('INSERTION: every letter of %s is present in the S block, in '
              'order, with text wedged between (similarity %.3f).'
              % (FIELD[args.lang], ratio))
        print('  draft: %s' % story[:200])
        print('  db   : %s' % matn[:200])
        print('  -> words added INSIDE the quotation are speech the Prophet')
        print('     (saw) did not say. Quote the matn exactly; commentary')
        print('     belongs in H (P294).')
        return 1

    print('MISMATCH: the S block does not quote %s (%s). similarity %.3f'
          % (FIELD[args.lang], _al.ref_of(row), ratio))
    print('  draft: %s' % story[:160])
    print('  db   : %s' % matn[:160])
    print('  -> draft.txt is stale. stt-validate would score the SUBTITLES')
    print('     against this text and report a defect that is not there,')
    print('     or miss one that is. Re-sync before TTS (P282).')
    return 1


if __name__ == '__main__':
    sys.exit(main())