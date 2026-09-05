#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-matn-source.py - is each library row's Arabic actually IN the collection
it claims to come from?

WHY THIS EXISTS (P142). Nothing verified matn against source. Stage 3 A/B
compares TRANSLATION against MATN - it asks whether the Russian says what the
Arabic says. It cannot notice that the Arabic itself is not the hadith at the
cited reference.

Two rows proved the failure mode:

  #2318 stored الصلاة عماد الدين - a weak, widely-circulated wording - under
        Muadh ibn Jabal's name, citing sunnah.com/tirmidhi:2616, which actually
        serves رأس الأمر الإسلام وعموده الصلاة. Every translation of that row
        was faithful. The Arabic was wrong.

  #3104 stored الجنة تحت أقدام الأمهات - graded munkar by al-Albani from Anas -
        under an-Nasai 3104, which actually records Mu'awiyah ibn Jahimah:
        فالزمها فإن الجنة تحت رجليها. Popular weak wording on a sound
        narration's number and grade.

WHY A LOCAL MIRROR (P145). The first version fetched sunnah.com per row.
sunnah.com returns HTTP 403 to scripted clients - not a User-Agent problem,
browser-like headers were refused identically. Their API needs a key blocked
on sunnah-com/api issue #3675, and that repo has API requests open since
March, so waiting is not a plan.

This reads a local clone of AhmedBaset/hadith-json instead - a scraped mirror
of sunnah.com, 50,884 hadiths across the nine books.

WHAT THIS CHECK IS, PRECISELY. Not a lookup by number: the mirror numbers
hadiths differently from sunnah.com's URLs (Bukhari 6446 there is 6207). The
question asked is better than a number match anyway -

    does our stored Arabic appear ANYWHERE in the collection it claims?

Both real defects answer NO: الصلاة عماد الدين is not in Tirmidhi, and
الجنة تحت أقدام الأمهات is not in an-Nasai. Both would have been flagged.

THREE LIMITS, STATED PLAINLY. This screens; it does not certify.

  1. NOT FOUND means REVIEW, never FAIL. It can mean our text is wrong. It can
     also mean the mirror is incomplete or carries a different edition's
     wording. A human decides.
  2. FOUND verifies the TEXT only - not the grade, not the narrator. #3104 had
     a correct grade and the wrong narrator; this check cannot see that.
  3. The mirror is a THIRD-PARTY SCRAPE. Nothing is marked matn_verified_at on
     its say-so. A match narrows the field; a human confirms.

KNOWN GAP: the mirror's README states Musnad Ahmad chapters 8-30 are missing
from the source data. Ahmad rows returning NOT FOUND may be that gap rather
than a defect - the output says so.

USAGE
  python scripts/verify-matn-source.py --mirror "C:/QA/Hadith verification AI app/hadith-json"
  python scripts/verify-matn-source.py --mirror ... --number 6446
  python scripts/verify-matn-source.py --mirror ... --unverified-only

OUTPUT
  A table, plus out/matn-verify-report.json.
"""
import argparse
import difflib
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

URL_KEYS = ('NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_URL')
SERVICE_KEYS = ('SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_KEY',
                'SERVICE_ROLE_KEY', 'SUPABASE_KEY')

REPORT = os.path.join('out', 'matn-verify-report.json')

# Library collection name -> mirror filename under db/by_book/the_9_books/.
# Collections absent here are reported out-of-scope rather than guessed at.
COLLECTION_FILES = {
    'Sahih al-Bukhari': 'bukhari.json',
    'Sahih Muslim':     'muslim.json',
    'Jami at-Tirmidhi': 'tirmidhi.json',
    'Sunan Abu Dawud':  'abudawud.json',
    'Sunan an-Nasai':   'nasai.json',
    'Sunan Ibn Majah':  'ibnmajah.json',
    'Musnad Ahmad':     'ahmed.json',
}

# Collections the mirror covers only partially. A MISSING here is weak
# evidence and the report says so.
PARTIAL_COVERAGE = {
    'Musnad Ahmad': 'mirror README: chapters 8-30 missing from source data',
}

FOUND_RATIO = 0.90
PARTIAL_RATIO = 0.60
# P146: a high gapped score with no contiguous run is coincidence, not a match.
MIN_CONTIGUOUS = 0.30


# ---------------------------------------------------------------- env
def load_env(path='.env.local'):
    """KEY=value pairs. Values may be quoted - strip them, or the quote
    character travels into the header and produces a 401 that looks like a
    bad key."""
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


def pick(env, keys, label):
    for k in keys:
        v = os.environ.get(k) or env.get(k)
        if v:
            return v
    sys.exit(f'FAILED: none of {keys} in environment or .env.local ({label})')


# ---------------------------------------------------------------- arabic
DIACRITICS = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]')
ALEF = re.compile(r'[\u0622\u0623\u0625\u0671]')
YA = re.compile(r'\u0649')
NON_ARABIC = re.compile(r'[^\u0621-\u063A\u0641-\u064A\s]')


def normalise_arabic(s):
    """Strip what varies between one printing of a matn and another:
    diacritics, tatweel, alef and ya variants, punctuation, whitespace.

    Not optional. Searching the mirror for غنى النفس returns nothing until
    both sides are normalised, because it stores الْغِنَى غِنَى النَّفْسِ.
    That was tried by hand first and returned zero hits.
    """
    if not s:
        return ''
    s = unicodedata.normalize('NFKC', s)
    s = DIACRITICS.sub('', s)
    s = ALEF.sub('\u0627', s)
    s = YA.sub('\u064A', s)
    s = NON_ARABIC.sub(' ', s)
    return ' '.join(s.split())


def coverage(needle_words, hay_words):
    """What fraction of the stored matn appears as ONE CONTIGUOUS RUN?

    Containment, not similarity. A stored matn is normally an excerpt of a
    longer hadith, so it should appear intact somewhere in the entry.

    A sliding-window difflib comparison was tried first and rejected - it
    scored the genuinely-correct #2616 matn at 0.875, below the pass line,
    because window offsets stepped past the right alignment by one word.
    Longest contiguous run has no alignment to get wrong.

    Calibrated on the real #2318 case:
        correct matn                     1.000
        correct matn, diacritics removed 1.000
        the weak wording that was stored 0.333
        an unrelated hadith              0.000
        correct matn, one word dropped   0.714  -> PARTIAL, correctly
    """
    if not needle_words or not hay_words:
        return 0.0
    sm = difflib.SequenceMatcher(None, needle_words, hay_words, autojunk=False)
    m = sm.find_longest_match(0, len(needle_words), 0, len(hay_words))
    return m.size / len(needle_words)


def gapped_recall(needle_words, hay_words):
    """What fraction of the stored matn's words appear IN ORDER, gaps allowed?

    Added after the first full run. Contiguous-run coverage under-scores a
    legitimate EXCERPT: Muslim #2999 stores the believer's-affair hadith with
    two phrases dropped (وليس ذاك لأحد إلا للمؤمن, and فكان خيرا له after each
    condition). Every word is genuine and in order, but the omissions break the
    run, so it scored 0.47 and was reported MISSING. It is published across
    eight reels and is perfectly sound.

    A check that flags sound rows teaches the reader to skim it - the P138
    lesson. So both measures are computed and the verdict takes the higher.

    Measured:
                                contiguous   gapped
        #2999 elided, genuine        0.467    1.000
        #2318 wrong wording          0.333    0.333
        #2616 correct excerpt        1.000    1.000
        common particles only        0.000    0.000

    The particle control matters: Arabic function words (من، في، الله، و) are
    everywhere, so a short matn could in principle score high by accident. It
    scores zero, because get_matching_blocks requires ORDER, not just presence.
    """
    if not needle_words or not hay_words:
        return 0.0
    sm = difflib.SequenceMatcher(None, needle_words, hay_words, autojunk=False)
    return sum(b.size for b in sm.get_matching_blocks()) / len(needle_words)


# ---------------------------------------------------------------- mirror
_cache = {}


def load_collection(mirror, filename):
    """Load a collection and pre-normalise every hadith ONCE. The whole file
    is scanned per row; normalising inside the comparison loop would turn
    seconds into minutes."""
    if filename in _cache:
        return _cache[filename]
    path = os.path.join(mirror, 'db', 'by_book', 'the_9_books', filename)
    if not os.path.exists(path):
        _cache[filename] = None
        return None
    with open(path, encoding='utf-8') as fh:
        data = json.load(fh)
    entries = [{'idInBook': h.get('idInBook'),
                'words': normalise_arabic(h.get('arabic', '')).split()}
               for h in data.get('hadiths', [])]
    _cache[filename] = entries
    return entries


def best_match(needle_words, entries):
    """Best entry, ranked on (contiguous, gapped) in that order.

    P146. Ranking on gapped alone selected the WRONG ENTRY, not merely a noisy
    score. Tirmidhi #3373 (من لم يسأل الله يغضب عليه) was matched to mirror
    entry 1104 - a hadith about marriage without a guardian - while the correct
    entry 3457 sat right there. Two effects compounded:

      1. Gapped recall rises with HAYSTACK LENGTH. A long entry gives more
         chances for six common words (من، لا، الله، عليه) to appear in order
         by coincidence. The particle control that cleared this measure was run
         against a SHORT entry, so it could not surface that.
      2. Ties went to file order. `if g > best_g` keeps the first of equal
         scores, and 1104 precedes 3457.

    Contiguous is the discriminating measure - a real run of consecutive words
    is hard to hit by accident:

                                  contiguous   gapped
        #3373 vs correct 3457          0.667    0.833
        #3373 vs spurious 1104         0.333    0.833   <- tie on gapped
        #2999 vs correct entry         0.467    1.000

    So rank on contiguous, break ties on gapped, and let gapped classify the
    verdict afterwards. #2999 still reads FOUND-as-excerpt; #3373 and #4811 now
    point at the right entries.
    """
    best_key, best_g, best_c, best_id = (-1.0, -1.0), 0.0, 0.0, None
    for e in entries:
        c = coverage(needle_words, e['words'])
        # Cheap skip: gapped can never be below contiguous, but an entry that
        # cannot beat the current contiguous score cannot win on this key.
        if (c, 1.0) < best_key:
            continue
        g = gapped_recall(needle_words, e['words'])
        if (c, g) > best_key:
            best_key, best_g, best_c, best_id = (c, g), g, c, e['idInBook']
            if best_c >= 0.999:
                break
    return best_g, best_c, best_id


# ---------------------------------------------------------------- supabase
def fetch_rows(base_url, key, number=None, unverified_only=False):
    q = (f'{base_url}/rest/v1/hadith_library'
         '?select=id,hadith_number,collection,narrator,grade,text_arabic,'
         'source_url,matn_verified_at'
         '&order=collection.asc,hadith_number.asc')
    if number:
        q += f'&hadith_number=eq.{urllib.parse.quote(str(number))}'
    if unverified_only:
        q += '&matn_verified_at=is.null'
    req = urllib.request.Request(q, headers={
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(
        description='Screen library rows against a local hadith-json mirror.')
    ap.add_argument('--mirror', required=True,
                    help='path to a clone of AhmedBaset/hadith-json')
    ap.add_argument('--number', help='check one hadith_number')
    ap.add_argument('--unverified-only', action='store_true',
                    help='only rows where matn_verified_at is null')
    args = ap.parse_args()

    if not os.path.isdir(os.path.join(args.mirror, 'db', 'by_book')):
        sys.exit(f'FAILED: no db/by_book under {args.mirror}. '
                 'Clone https://github.com/AhmedBaset/hadith-json first.')

    env = load_env()
    base = pick(env, URL_KEYS, 'Supabase URL').rstrip('/')
    key = pick(env, SERVICE_KEYS, 'Supabase service key')

    rows = fetch_rows(base, key, args.number, args.unverified_only)
    if not rows:
        sys.exit('FAILED: no rows returned.')

    width = 78
    print()
    print('=' * width)
    print(f' matn -> collection screening   ({len(rows)} rows)')
    print(' local mirror, third-party scrape. SCREENS, does not certify.')
    print('=' * width)

    counts = {'FOUND': 0, 'PARTIAL': 0, 'MISSING': 0, 'SKIP': 0}
    report = []

    for r in rows:
        num = r.get('hadith_number')
        coll = r.get('collection') or ''
        stored = r.get('text_arabic')
        label = f'{coll} #{num}'
        mid = None
        ratio = 0.0
        contig = 0.0

        fname = COLLECTION_FILES.get(coll)
        if not fname:
            verdict, note = 'SKIP', 'collection not in mirror'
        elif not stored:
            verdict, note = 'SKIP', 'no text_arabic'
        else:
            entries = load_collection(args.mirror, fname)
            if entries is None:
                verdict, note = 'SKIP', f'{fname} not found in mirror'
            else:
                needle = normalise_arabic(stored).split()
                ratio, contig, mid = best_match(needle, entries)
                if ratio >= FOUND_RATIO and contig >= MIN_CONTIGUOUS:
                    verdict = 'FOUND'
                    note = f'mirror id {mid}'
                    if contig < PARTIAL_RATIO:
                        note += f' (excerpt: contiguous {contig:.2f})'
                elif ratio >= FOUND_RATIO:
                    # High gapped, almost no contiguous run: the coincidence
                    # shape from P146. Never FOUND on that evidence alone.
                    verdict = 'PARTIAL'
                    note = (f'gapped {ratio:.2f} but contiguous only '
                            f'{contig:.2f}, mirror id {mid} - read both')
                elif ratio >= PARTIAL_RATIO:
                    verdict = 'PARTIAL'
                    note = f'partial, mirror id {mid} - read both'
                else:
                    verdict = 'MISSING'
                    note = 'stored matn not in this collection'
                    if coll in PARTIAL_COVERAGE:
                        note += f' (NB: {PARTIAL_COVERAGE[coll]})'

        counts[verdict] += 1
        report.append({
            'hadith_number': num, 'collection': coll,
            'narrator': r.get('narrator'), 'grade': r.get('grade'),
            'verdict': verdict, 'ratio': round(ratio, 3),
            'contiguous': round(contig, 3),
            'mirror_id': mid, 'note': note,
            'already_verified': bool(r.get('matn_verified_at')),
        })

        mark = {'FOUND': 'ok  ', 'PARTIAL': 'HMM ',
                'MISSING': 'MISS', 'SKIP': '--  '}[verdict]
        print(f'  {mark} {label:<30} {ratio:.2f}  {note}')

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print()
    print('-' * width)
    print(f'  {counts["FOUND"]} found   {counts["PARTIAL"]} partial   '
          f'{counts["MISSING"]} missing   {counts["SKIP"]} skipped')
    print(f'  report: {REPORT}')
    print()
    print('  FOUND = the stored Arabic is somewhere in that collection. It says')
    print('  NOTHING about the grade or the narrator, and the mirror is a')
    print('  third-party scrape - confirm against sunnah.com before setting')
    print('  matn_verified_at. MISSING = read it yourself; it may be our text,')
    print('  or a gap in the mirror.')
    print('-' * width)

    return 0


if __name__ == '__main__':
    sys.exit(main())
