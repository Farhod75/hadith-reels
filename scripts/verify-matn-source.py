#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-matn-source.py - does each library row's Arabic actually appear at the
URL it cites?

WHY THIS EXISTS (P142). Nothing verified matn against source. Stage 3 A/B
compares TRANSLATION against MATN - it asks whether the Russian says what the
Arabic says. It cannot notice that the Arabic itself is not the hadith at the
cited URL.

hadith_library #2318 stored الصلاة عماد الدين - a weak, widely-circulated
wording - under Muadh ibn Jabal's name, citing sunnah.com/tirmidhi:2616, which
actually serves رأس الأمر الإسلام وعموده الصلاة. Every translation of that row
was faithful. The Arabic was wrong. A/B would have passed it, and did not run
on it at all: 55 of 66 rows were bulk-inserted straight into hadith_library on
2026-05-12 and never entered the candidate pipeline.

So this is the missing check, and it is deliberately DUMB: fetch the page,
normalise both sides, compare. No model, no judgement, no grading opinion. It
answers one question - is this text on that page - and leaves everything else
to a human.

BLOCKED AS OF 2026-09-02. sunnah.com returns HTTP 403 to this script. Not a
User-Agent problem - a browser-like UA, Accept and Accept-Language were tried
and refused identically, so the block is at the TLS/edge layer. Impersonating
a browser more convincingly was rejected as an approach: sunnah.com is
donation-funded and publishes an API precisely so scripts do not scrape the
site.

The fix is api.sunnah.com, which needs the key blocked on
github.com/sunnah-com/api issue #3675 - open since 2026-08-21. That issue now
blocks TWO things: new sourcing (Stage 0) and verification of the 66 rows
already in the library.

Everything except the fetch layer is finished and tested. When the key lands,
replace fetch_page() with an api.sunnah.com call; normalisation, coverage,
thresholds and reporting are unchanged.

USAGE
  python scripts/verify-matn-source.py                 # all rows
  python scripts/verify-matn-source.py --limit 5       # first 5, for a smoke test
  python scripts/verify-matn-source.py --number 6446   # one row
  python scripts/verify-matn-source.py --no-cache      # ignore cached pages

OUTPUT
  A table, plus out/matn-verify-report.json for follow-up.

NOTE ON WHAT PASSING MEANS. A PASS says the stored Arabic appears at the cited
URL. It says nothing about whether the GRADE is right, whether the narrator is
right, or whether the English translation is faithful. Those are separate
questions with separate owners.
"""
import argparse
import difflib
import html
import json
import os
import re
import sys
import time
import unicodedata
import ssl
import urllib.error
import urllib.parse
import urllib.request

try:
    import certifi
    # Python on Windows does not use the OS certificate store, so urllib has
    # no trusted roots and every https fetch fails CERTIFICATE_VERIFY_FAILED.
    # Point it at certifi's bundle. NEVER disable verification instead - this
    # script's entire value is that the page it read came from sunnah.com.
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    sys.exit('FAILED: certifi not installed. Run: pip install certifi')

URL_KEYS = ('NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_URL')
SERVICE_KEYS = ('SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_KEY',
                'SERVICE_ROLE_KEY', 'SUPABASE_KEY')

CACHE_DIR = os.path.join('out', '.cache', 'sunnah')
REPORT = os.path.join('out', 'matn-verify-report.json')

# Politeness. sunnah.com is a free service run on donations; do not hammer it.
DELAY_S = 1.5

# Thresholds. A stored matn is usually an EXCERPT of a longer hadith, so exact
# equality is the wrong test - containment of the excerpt is what matters.
PASS_RATIO = 0.90
REVIEW_RATIO = 0.60


# ---------------------------------------------------------------- env
def load_env(path='.env.local'):
    """Read KEY=value pairs. Values may be quoted - strip them, or the quote
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
    sys.exit(f'FAILED: none of {keys} found in environment or .env.local ({label})')


# ---------------------------------------------------------------- arabic
# Harakat, tanwin, shadda, sukun, superscript alef, and the Quranic marks that
# sunnah.com carries but a stored matn usually does not.
DIACRITICS = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]')

ALEF = re.compile(r'[\u0622\u0623\u0625\u0671]')      # آ أ إ ٱ  -> ا
YA = re.compile(r'\u0649')                            # ى -> ي
NON_ARABIC = re.compile(r'[^\u0621-\u063A\u0641-\u064A\s]')


def normalise_arabic(s):
    """Strip everything that varies between a printed matn and a web page:
    diacritics, tatweel, alef and ya variants, punctuation, whitespace."""
    if not s:
        return ''
    s = unicodedata.normalize('NFKC', s)
    s = DIACRITICS.sub('', s)
    s = ALEF.sub('\u0627', s)
    s = YA.sub('\u064A', s)
    s = NON_ARABIC.sub(' ', s)
    return ' '.join(s.split())


def coverage(needle_words, hay_words):
    """What fraction of the stored matn appears as ONE CONTIGUOUS RUN on the page?

    Not a similarity score. The question is containment: a stored matn is
    normally an excerpt of a longer hadith, so it should appear intact
    somewhere on the correct page.

    A sliding-window difflib comparison was tried first and rejected - it
    scored the genuinely-correct #2616 matn at 0.875, below the pass line,
    because the window offsets stepped past the right alignment by one word.
    Longest contiguous run has no alignment to get wrong.

    Measured on the real #2318 case:
        correct matn                     1.000
        correct matn, diacritics removed 1.000
        the weak wording that was stored 0.333
        an unrelated hadith              0.000
        correct matn, one word dropped   0.714  -> REVIEW, correctly
    """
    if not needle_words or not hay_words:
        return 0.0
    sm = difflib.SequenceMatcher(None, needle_words, hay_words, autojunk=False)
    m = sm.find_longest_match(0, len(needle_words), 0, len(hay_words))
    return m.size / len(needle_words)


# ---------------------------------------------------------------- fetch
def cache_path(url):
    safe = re.sub(r'[^A-Za-z0-9]+', '_', url).strip('_')
    return os.path.join(CACHE_DIR, safe + '.html')


def fetch_page(url, use_cache=True):
    cp = cache_path(url)
    if use_cache and os.path.exists(cp):
        with open(cp, encoding='utf-8') as fh:
            return fh.read(), True
    req = urllib.request.Request(url, headers={
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/126.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as resp:
        body = resp.read().decode('utf-8', errors='replace')
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cp, 'w', encoding='utf-8') as fh:
        fh.write(body)
    return body, False


def page_arabic(body):
    """Everything Arabic on the page, as one normalised word list.

    Deliberately crude - no attempt to isolate the matn from the isnad or the
    chapter heading. A false PASS would need the stored text to appear
    somewhere on the correct page, which is the thing being checked anyway.
    """
    text = re.sub(r'<script.*?</script>', ' ', body, flags=re.S | re.I)
    text = re.sub(r'<style.*?</style>', ' ', text, flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return normalise_arabic(text)


# ---------------------------------------------------------------- supabase
def fetch_rows(base_url, key, number=None, limit=None):
    q = (f'{base_url}/rest/v1/hadith_library'
         '?select=id,hadith_number,collection,narrator,grade,text_arabic,source_url'
         '&order=collection.asc,hadith_number.asc')
    if number:
        q += f'&hadith_number=eq.{urllib.parse.quote(str(number))}'
    if limit:
        q += f'&limit={int(limit)}'
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
        description='Verify each row\'s Arabic matn appears at its cited URL.')
    ap.add_argument('--number', help='check one hadith_number')
    ap.add_argument('--limit', type=int, help='check the first N rows')
    ap.add_argument('--no-cache', action='store_true',
                    help='re-fetch pages instead of using out/.cache/sunnah')
    args = ap.parse_args()

    env = load_env()
    base = pick(env, URL_KEYS, 'Supabase URL').rstrip('/')
    key = pick(env, SERVICE_KEYS, 'Supabase service key')

    rows = fetch_rows(base, key, args.number, args.limit)
    if not rows:
        sys.exit('FAILED: no rows returned.')

    width = 74
    print()
    print('=' * width)
    print(f' matn -> source verification   ({len(rows)} rows)')
    print('=' * width)

    results, counts = [], {'PASS': 0, 'REVIEW': 0, 'FAIL': 0, 'ERROR': 0}
    fetched = 0

    for r in rows:
        num = r.get('hadith_number')
        coll = r.get('collection') or ''
        url = r.get('source_url')
        stored = r.get('text_arabic')
        label = f'{coll} #{num}'

        if not url:
            verdict, ratio, note = 'ERROR', 0.0, 'no source_url'
        elif not stored:
            verdict, ratio, note = 'ERROR', 0.0, 'no text_arabic'
        else:
            try:
                body, cached = fetch_page(url, use_cache=not args.no_cache)
                if not cached:
                    fetched += 1
                    time.sleep(DELAY_S)
                hay = page_arabic(body).split()
                needle = normalise_arabic(stored).split()
                ratio = coverage(needle, hay)
                if ratio >= PASS_RATIO:
                    verdict, note = 'PASS', ''
                elif ratio >= REVIEW_RATIO:
                    verdict, note = 'REVIEW', 'partial match - read both'
                else:
                    verdict, note = 'FAIL', 'stored matn is not on that page'
            except urllib.error.HTTPError as e:
                verdict, ratio, note = 'ERROR', 0.0, f'HTTP {e.code}'
            except Exception as e:                       # noqa: BLE001
                verdict, ratio, note = 'ERROR', 0.0, str(e)[:60]

        counts[verdict] += 1
        results.append({
            'hadith_number': num, 'collection': coll,
            'narrator': r.get('narrator'), 'grade': r.get('grade'),
            'source_url': url, 'verdict': verdict,
            'ratio': round(ratio, 3), 'note': note,
        })

        mark = {'PASS': 'ok  ', 'REVIEW': 'HMM ',
                'FAIL': 'FAIL', 'ERROR': 'ERR '}[verdict]
        line = f'  {mark} {label:<34} {ratio:.2f}'
        if note:
            line += f'  {note}'
        print(line)

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print()
    print('-' * width)
    print(f'  {counts["PASS"]} pass   {counts["REVIEW"]} review   '
          f'{counts["FAIL"]} fail   {counts["ERROR"]} error')
    print(f'  {fetched} page(s) fetched, rest from cache')
    print(f'  report: {REPORT}')
    print()
    print('  A PASS means the stored Arabic is on the cited page. It says')
    print('  NOTHING about the grade, the narrator, or the translation.')
    print('-' * width)

    return 1 if counts['FAIL'] or counts['ERROR'] else 0


if __name__ == '__main__':
    sys.exit(main())
