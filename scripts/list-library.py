#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
list-library.py - what is in hadith_library, and what has not shipped yet.

  python scripts/list-library.py              # unused rows only
  python scripts/list-library.py --all        # used and unused
  python scripts/list-library.py --tag parents

"Used" means the hadith number appears in reel-tracker.md's Active reels
table, which is the same source the duplicate-check index is built from.

Read-only. It reuses audit-library.py's load_env and fetch_rows rather than
re-implementing credential handling, so there is one place that knows how to
reach Supabase.
"""

import argparse
import importlib.util
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# audit-library.py has a hyphen, so it cannot be imported by name.
_spec = importlib.util.spec_from_file_location(
    'audit_library', os.path.join(HERE, 'audit-library.py'))
_al = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_al)


def used_numbers():
    """Hadith numbers that already have reels, from the tracker."""
    path = os.path.join(ROOT, 'reel-tracker.md')
    try:
        t = io.open(path, encoding='utf-8-sig').read()
    except (IOError, OSError):
        print('WARN: no reel-tracker.md — treating every row as unused')
        return set()
    used = set()
    for line in t.splitlines():
        if re.match(r'^\|\s*R\d{3}\s*\|', line):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cells) > 2:
                m = re.search(r'#(\d+)', cells[2])
                if m:
                    used.add(m.group(1))
    return used


def first(row, *names):
    for n in names:
        v = row.get(n)
        if v:
            return v
    return ''


def main():
    ap = argparse.ArgumentParser(description='List hadith_library rows.')
    ap.add_argument('--all', action='store_true', help='include used rows')
    ap.add_argument('--tag', help='only rows carrying this tag')
    ap.add_argument('--chars', type=int, default=220,
                    help='how much English text to print (default 220)')
    ap.add_argument('--row', help='dump ONE hadith number in every language, '
                                  'in full - the read every reel starts with')
    ap.add_argument('--min-en', type=int, default=0,
                    help='only rows whose English matn is at least this long')
    ap.add_argument('--sort', choices=['collection', 'length'],
                    default='collection', help='ordering (default collection)')
    args = ap.parse_args()

    env = _al.load_env()
    base = next((env[k] for k in _al.URL_KEYS if env.get(k)), None)
    key = next((env[k] for k in _al.SERVICE_KEYS if env.get(k)), None)
    if not base or not key:
        print('FAILED: need a Supabase URL and service-role key in .env.local')
        return 2

    rows = _al.fetch_rows(base, key, 'hadith_library')
    if not rows:
        print('FAILED: hadith_library returned no rows')
        return 2

    # --row: the full read. Printed in full and never truncated, because the
    # generation is checked AGAINST this text and a truncated matn is how a
    # model ends up reaching for the missing continuation (see an-Nasai #463,
    # where the row held only the opening clause and three separate blocks
    # tried to finish it).
    if args.row:
        hits = [r for r in rows
                if str(first(r, 'hadith_number', 'number')) == str(args.row)]
        if not hits:
            print('no row with hadith_number %s' % args.row)
            return 1
        if len(hits) > 1:
            print('⚠ %d rows share #%s — P147: the number is not unique. '
                  'Match the WORDING, not the number.\n' % (len(hits), args.row))
        for r in hits:
            print('=' * 72)
            print('%s #%s — %s · %s'
                  % (first(r, 'collection') or '?',
                     first(r, 'hadith_number', 'number'),
                     first(r, 'narrator') or 'narrator?',
                     first(r, 'grade', 'authenticity', 'grading') or 'grade?'))
            tags = r.get('tags') or []
            if tags:
                print('tags: %s' % ', '.join(str(x) for x in tags))
            print('=' * 72)
            for col in ('text_arabic', 'text_english', 'text_russian',
                        'text_uzbek_cyrillic', 'text_uzbek_latin', 'text_tajik'):
                if col not in r:
                    continue
                v = (r.get(col) or '').strip()
                print('\n--- %s ---' % col)
                print(v if v else '(EMPTY)')
            for col in ('source_url', 'grade_source', 'matn_verified_at'):
                if r.get(col):
                    print('\n%s: %s' % (col, r[col]))
            print()
        return 0

    used = used_numbers()
    out = []
    for r in rows:
        num = str(first(r, 'hadith_number', 'number'))
        is_used = num in used
        if is_used and not args.all:
            continue
        tags = r.get('tags') or []
        if args.tag and args.tag.lower() not in [str(t).lower() for t in tags]:
            continue
        if args.min_en and len((r.get('text_english') or '').strip()) < args.min_en:
            continue
        out.append((r, num, is_used, tags))

    if args.sort == 'length':
        out.sort(key=lambda x: -len((x[0].get('text_english') or '').strip()))
    else:
        out.sort(key=lambda x: (first(x[0], 'collection'),
                                int(x[1]) if x[1].isdigit() else 0))

    print('%d rows total · %d used · %d unused%s\n'
          % (len(rows), len(used), len(rows) - len(used),
             ('  ·  showing %d' % len(out)) if args.tag or args.all else ''))

    for r, num, is_used, tags in out:
        mark = '[shipped] ' if is_used else ''
        # Matn length is a SELECTION criterion, not a discovery. A four-word
        # matn cannot carry a 45s adults reel, and length pressure on the
        # generator is fabrication pressure (P116). ar = Arabic chars,
        # en = English chars. Rough guide from shipped reels: under ~120 en
        # is a short reel (~25-30s), 150-400 is the adults sweet spot.
        ar_len = len((r.get('text_arabic') or '').strip())
        en_len = len((r.get('text_english') or '').strip())
        print('%s%s #%s — %s · %s   [ar %d · en %d]'
              % (mark,
                 first(r, 'collection') or '?', num,
                 first(r, 'narrator') or 'narrator?',
                 first(r, 'grade', 'authenticity', 'grading') or 'grade?',
                 ar_len, en_len))
        if tags:
            print('   tags: %s' % ', '.join(str(t) for t in tags))
        en = re.sub(r'\s+', ' ', str(first(r, 'text_english', 'text_en'))).strip()
        if en:
            print('   %s' % (en[:args.chars] + ('…' if len(en) > args.chars else '')))
        missing = [c for c in ('text_english', 'text_russian', 'text_uzbek_cyrillic',
                               'text_tajik', 'text_arabic')
                   if c in r and not r.get(c)]
        if missing:
            print('   ⚠ empty: %s' % ', '.join(missing))
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
