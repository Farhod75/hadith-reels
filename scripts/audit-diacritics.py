#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit-diacritics.py - do our stored vowel marks match the source?

WHY THIS EXISTS (P259). Bukhari #1520 stored لَكُنَّ (kaf with DAMMA = "for you
[women]") where the source reads لَكِنَّ (kaf with KASRA = "but"). One vowel, a
different word, a different grammatical role - and the Arabic is what appears
on screen. Nothing in the pipeline compared our diacritics against anything:

  - Stage 3 (verify-candidates.py) asks whether the TRANSLATION matches the
    MATN. Both readings of #1520 produced a defensible translation.
  - verify-matn-source.py asks whether the matn appears in the collection at
    all. It normalises diacritics away before comparing, by design, so this
    class is invisible to it.
  - lint-content.py checks conventions in generated text, not stored Arabic.

So this fills the one gap: same letters, different vowels.

TWO METHOD BUGS, FOUND THE DAY THIS WAS WRITTEN. Both inflate the finding
count, and the first run reported 56 differences where there were 19.

  1. COMBINING-MARK ORDER IS NOT A DIFFERENCE. A letter carrying both shadda
     and fatha may be stored as shadda+fatha or fatha+shadda. They render
     identically. Our DB is NFC-normalised (fatha ccc=30 sorts before shadda
     ccc=33); the mirror is not. Compare NFC forms or every such letter is a
     false hit.
  2. A FAILED ALIGNMENT IS NOT A DIFFERENCE. When the stored matn could not be
     located inside the mirror entry, the first version fell back to comparing
     against the start of the entry - which is the ISNAD - and duly reported a
     difference at character 0 for half the library.

WHAT IT CLASSIFIES. Raw differences are mostly noise; the value is the split.

  EXACT        identical after NFC
  PUNCTUATION  we add or drop a comma, colon or space. Harmless.
  ORTHOGRAPHIC same consonants, different conventional spelling - لَا vs لاَ,
               hamza seat, alef maqsura for ya. Both valid.
  VOWEL        same consonantal skeleton, different vowels. THIS is the class
               #1520 belongs to, and the only one that exits non-zero.
  LETTER       the consonants themselves differ - a different wording, or the
               mirror carries another edition. Review.
  NOT FOUND    the matn is not in the mirror at all. That is
               verify-matn-source.py's question, not this one.

THE MIRROR IS NOT AN AUTHORITY (P145, and verify-matn-source.py's limit 3). It
is a third-party scrape. A VOWEL finding means OUR reading and the mirror's
reading differ - it does not say which is right. #1520 was confirmed against
sunnah.com before anything was written. Treat output as a worklist, never a
verdict, and never write a correction on this script's say-so.

THE MIRROR NUMBERS DIFFERENTLY. idInBook runs LOWER than sunnah.com and the gap
widens through the book (#1520 sits at 1468; 6446 sits at 6207). This script
therefore matches on TEXT, never on number, and a number mismatch is not
evidence of a miscitation.

USAGE
  python scripts/audit-diacritics.py --mirror "C:/QA/Hadith verification AI app/hadith-json"
  python scripts/audit-diacritics.py --mirror ... --number 1520
  python scripts/audit-diacritics.py --mirror ... --strict    # non-zero on VOWEL

OUTPUT
  A table, plus out/diacritic-audit.json.
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

MIRROR_SUBPATH = os.path.join('db', 'by_book', 'the_9_books')

COLLECTION_FILE = {
    'Sahih al-Bukhari': 'bukhari.json',
    'Sahih Muslim': 'muslim.json',
    'Jami at-Tirmidhi': 'tirmidhi.json',
    'Sunan Abu Dawud': 'abudawud.json',
    'Sunan an-Nasai': 'nasai.json',
    'Sunan Ibn Majah': 'ibnmajah.json',
    'Musnad Ahmad': 'ahmed.json',
}

URL_KEYS = ('NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_URL')
SERVICE_KEYS = ('SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_KEY')

# Arabic letters, excluding the combining marks at 064B-0652.
LETTERS = set(range(0x0621, 0x064B))
# Fold conventional spelling variants that carry no difference in reading.
FOLD = {0x0623: 0x0627, 0x0625: 0x0627, 0x0622: 0x0627, 0x0671: 0x0627,
        0x0649: 0x064A, 0x0629: 0x0647}
# Presentation characters that are not part of the text.
INVISIBLE = dict.fromkeys(
    [0x200C, 0x200D, 0x200E, 0x200F, 0x061C, 0x00AB, 0x00BB,
     0x201C, 0x201D, 0x0022], None)
PUNCT = set(' .,:;!?\u060C\u061B\u061F\u002E\u003A\u003B')
# Combining marks that trail a consonant and belong to its span.
TRAILING = set(range(0x064B, 0x0653)) | {0x0670, 0x0653, 0x0654, 0x0655}

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
    return None


def sb_get(base, key, table, params):
    url = f'{base.rstrip("/")}/rest/v1/{table}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'apikey': key, 'Authorization': f'Bearer {key}',
        'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def clean(s):
    """NFC, drop presentation characters, collapse whitespace.

    NFC first and always - see method bug 1 in the module docstring.
    """
    if not isinstance(s, str):
        return ''
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s.translate(INVISIBLE))).strip()


def skeleton(s):
    """Consonants only, spelling variants folded, marks and punctuation gone."""
    out = []
    for ch in s:
        c = FOLD.get(ord(ch), ord(ch))
        if c in LETTERS:
            out.append(chr(c))
    return ''.join(out)


def depunct(s):
    return ''.join(c for c in s if c not in PUNCT)


def classify(ours, theirs):
    """ours and theirs are already clean()ed and cover the same span."""
    if ours == theirs:
        return 'EXACT', None
    if skeleton(ours) != skeleton(theirs):
        return 'LETTER', None
    if depunct(ours) == depunct(theirs):
        return 'PUNCTUATION', None
    # Same consonants, same punctuation once removed - so the marks differ.
    a, b = depunct(ours), depunct(theirs)
    i = next((j for j in range(min(len(a), len(b))) if a[j] != b[j]), min(len(a), len(b)))
    # A spelling variant folded by skeleton() but visible here is orthographic,
    # not a vowel difference: the differing char is a LETTER on one side.
    ca = ord(a[i]) if i < len(a) else 0
    cb = ord(b[i]) if i < len(b) else 0
    if (ca in LETTERS) != (cb in LETTERS) or FOLD.get(ca) or FOLD.get(cb):
        return 'ORTHOGRAPHIC', i
    return 'VOWEL', i

def load_mirror(mirror_root, collection):
    """Return [(clean_arabic, skeleton, entry)] for one collection, once.

    The skeleton is precomputed here deliberately: computing it per library row
    meant 72 x 50,884 recomputations and a two-minute run.
    """
    fn = COLLECTION_FILE.get(collection)
    if not fn:
        return None
    path = os.path.join(mirror_root, MIRROR_SUBPATH, fn)
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as fh:
        data = json.load(fh)
    recs = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get('arabic'), str):
                c = clean(o['arabic'])
                recs.append((c, skeleton(c), o))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)
    return recs


def locate(ours, entries):
    """Find the mirror entry containing our matn, and the span it occupies.

    Matching is on the consonantal skeleton, so a vowel difference still
    locates - that is the whole point. The span is then recovered by walking
    the cleaned mirror text and counting consonants, never by str.find(), which
    fails on exactly the rows we care about (method bug 2).
    """
    sk = skeleton(ours)
    if not sk:
        return None
    for mc, msk, entry in entries:
        pos = msk.find(sk)
        if pos < 0:
            continue
        start = end = None
        seen = 0
        for idx, ch in enumerate(mc):
            c = FOLD.get(ord(ch), ord(ch))
            if c in LETTERS:
                if seen == pos and start is None:
                    start = idx
                seen += 1
                if seen == pos + len(sk):
                    end = idx + 1
                    # Trailing marks belong to the span. Ending at the last
                    # CONSONANT clips the final i'rab vowel off the mirror side
                    # while ours keeps it, which reported a VOWEL difference on
                    # 31 of 36 rows - all of them at the last character, all of
                    # them this bug rather than a finding.
                    while end < len(mc) and ord(mc[end]) in TRAILING:
                        end += 1
                    break
        if start is not None and end is not None:
            return entry, mc[start:end]
    return None

def context(s, i, width=20):
    lo = max(0, i - width)
    return ('...' if lo else '') + s[lo:i + width] + ('...' if i + width < len(s) else '')


def main():
    ap = argparse.ArgumentParser(
        description='Do our stored vowel marks match the source? (P259)')
    ap.add_argument('--mirror', required=True,
                    help='clone of AhmedBaset/hadith-json')
    ap.add_argument('--number', help='check one hadith_number')
    ap.add_argument('--strict', action='store_true',
                    help='exit non-zero if any VOWEL difference is found')
    args = ap.parse_args()

    if not os.path.isdir(args.mirror):
        print(f'mirror not found: {args.mirror}')
        return 2

    env = load_env()
    base = pick(env, URL_KEYS)
    key = pick(env, SERVICE_KEYS)
    if not base or not key:
        print('missing supabase env in .env.local')
        return 2

    params = {'select': '*', 'limit': '500'}
    if args.number:
        params['hadith_number'] = f'eq.{args.number}'
    rows = sb_get(base, key, 'hadith_library', params)

    buckets = {k: [] for k in
               ('EXACT', 'PUNCTUATION', 'ORTHOGRAPHIC', 'VOWEL', 'LETTER',
                'NOT_FOUND', 'NO_MIRROR')}
    cache = {}
    findings = []

    for row in rows:
        coll = row.get('collection')
        num = row.get('hadith_number')
        ours = clean(row.get('text_arabic') or '')
        if not ours:
            continue
        if coll not in cache:
            cache[coll] = load_mirror(args.mirror, coll)
        entries = cache[coll]
        if entries is None:
            buckets['NO_MIRROR'].append((num, coll))
            continue
        found = locate(ours, entries)
        if not found:
            buckets['NOT_FOUND'].append((num, coll, len(ours)))
            continue
        entry, theirs = found
        verdict, i = classify(ours, theirs)
        buckets[verdict].append((num, coll))
        if verdict in ('VOWEL', 'LETTER', 'ORTHOGRAPHIC'):
            findings.append({
                'hadith_number': num, 'collection': coll,
                'mirror_idInBook': entry.get('idInBook'),
                'verdict': verdict, 'index': i,
                'ours': ours, 'mirror': theirs,
            })

    width = 74
    print('=' * width)
    print(f' diacritic audit vs local mirror - {len(rows)} row(s)')
    print(' the mirror is a third-party scrape. a finding is a worklist entry,')
    print(' never a verdict, and never a reason to write a correction (P145).')
    print('=' * width)
    for k in ('EXACT', 'PUNCTUATION', 'ORTHOGRAPHIC', 'VOWEL', 'LETTER',
              'NOT_FOUND', 'NO_MIRROR'):
        print('  %-12s %d' % (k, len(buckets[k])))

    vowels = [f for f in findings if f['verdict'] == 'VOWEL']
    letters = [f for f in findings if f['verdict'] == 'LETTER']

    for title, group in (('VOWEL - same consonants, different reading', vowels),
                         ('LETTER - the consonants differ', letters)):
        if not group:
            continue
        print('')
        print('-' * width)
        print(f'  {title}')
        print('-' * width)
        for f in group:
            print('')
            print('  #%s  %s  (mirror idInBook=%s)'
                  % (f['hadith_number'], f['collection'], f['mirror_idInBook']))
            i = f['index']
            if i is None:
                print('    ours  : %s' % f['ours'][:90])
                print('    mirror: %s' % f['mirror'][:90])
            else:
                a, b = depunct(f['ours']), depunct(f['mirror'])
                print('    ours  : %s' % context(a, i))
                print('    mirror: %s' % context(b, i))
                print('    at %d: ours U+%04X vs mirror U+%04X'
                      % (i, ord(a[i]) if i < len(a) else 0,
                         ord(b[i]) if i < len(b) else 0))

    if buckets['NOT_FOUND']:
        print('')
        print('-' * width)
        print('  NOT FOUND in the mirror - that is verify-matn-source.py\'s')
        print('  question (P142), not this one. Listed so the count reconciles.')
        print('-' * width)
        for num, coll, n in buckets['NOT_FOUND']:
            print('    #%-8s %-20s %d chars' % (num, coll, n))

    os.makedirs('out', exist_ok=True)
    with open(os.path.join('out', 'diacritic-audit.json'), 'w',
              encoding='utf-8') as fh:
        json.dump({'summary': {k: len(v) for k, v in buckets.items()},
                   'findings': findings}, fh, ensure_ascii=False, indent=2)

    print('')
    print('  -> out/diacritic-audit.json')
    if args.strict and vowels:
        print('  STRICT: %d VOWEL difference(s).' % len(vowels))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
