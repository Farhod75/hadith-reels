#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-matn-number.py - is each row's Arabic at the NUMBER the row cites?

THE MISSING HALF (P306). `verify-matn-source.py` asks, in its own words,
"does our stored Arabic appear ANYWHERE in the collection it claims?" - and it
deliberately does not match on the number, because the local mirror's ids are
not sunnah.com's reference numbers (P145). That trade was sound and it opened
exactly one hole, which #3559 then fell into:

  The row cited Sahih al-Bukhari 3559 and stored
  «إِنَّ مِنْ أَحَبِّكُمْ إِلَيَّ أَحْسَنَكُمْ أَخْلَاقًا». That matn is authentic Bukhari from
  the row's own narrator, Abdullah ibn Amr - at reference 3759, 3760.
  Reference 3559 carries «إِنَّ مِنْ خِيَارِكُمْ أَحْسَنَكُمْ أَخْلَاقًا».

  Right collection, right narrator, real text, wrong number. The existing
  check answers FOUND, correctly, and the row ships. Two reels published on it.

So this asks the other question, and only that one:

    is our stored Arabic present ON THE PAGE AT THE CITED NUMBER?

WHY NOT sunnah.com ITSELF. It returns no response to scripted clients; P145
recorded that and it still holds (probed again 2026-10-29). en.tohed.com serves
the same corpus keyed by the same reference numbering, answers scripts, and was
checked against sunnah.com by hand on bukhari 3559 and 3759 - the two pages
this defect turns on - before being adopted here. That substitution is the main
assumption in this script and the report states it on every row.

VERDICTS. MATCH - the matn is on the cited page. MERGED - it is on the page
one number away, which means a merged reference like "Sahih al-Bukhari 5185,
5186" or a source that paginates Arabic and English differently (P312); not a
defect. MISMATCH - it is on neither. SKIP - nothing to check against.

WHAT A DISAGREEMENT MEANS. REVIEW, never FAIL. The fetched page can carry a
different edition's vocalisation, our row can hold a legitimately trimmed
clause, or the substitution above can be wrong for some collection. A human
decides. Nothing here writes to the database.

MATCHING. Both sides are normalised to bare Arabic letters: harakat, tatweel
and tashkeel removed, alef variants folded to ا, alef maqsura to ي, ta marbuta
to ه, everything else dropped. Then our matn must appear as a CONTIGUOUS
substring of the page. Contiguity is the point - a gapped similarity score is
what let a composite entry look like a match before (P146).

USAGE
  python scripts/verify-matn-number.py                 # every row
  python scripts/verify-matn-number.py --number 3559   # one row
  python scripts/verify-matn-number.py --no-cache      # refetch
OUTPUT
  a table, plus out/matn-number-report.json
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'out', 'source-cache')
REPORT = os.path.join(ROOT, 'out', 'matn-number-report.json')
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
DELAY = 1.5

# Library collection name -> en.tohed.com path segment. Each slug was
# probed against a real row's number on 2026-10-29, not guessed: the
# hyphenated forms are the live ones and the obvious unhyphenated
# spellings all 404. A collection absent
# here is reported out-of-scope rather than guessed at.
TOHED = {
    'Sahih al-Bukhari': 'bukhari',
    'Sahih Muslim': 'muslim',
    'Jami at-Tirmidhi': 'tirmidhi',
    'Sunan Abu Dawud': 'abu-dawud',
    'Sunan an-Nasai': 'nasai',
    'Sunan Ibn Majah': 'ibn-majah',
    'Musnad Ahmad': 'musnad-ahmad',
}

HARAKAT = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ]')
NOT_ARABIC = re.compile(r'[^ء-ي]')
TAG = re.compile(r'<[^>]+>')


def norm(s):
    s = HARAKAT.sub('', s or '')
    s = (s.replace('أ', 'ا').replace('إ', 'ا')
          .replace('آ', 'ا').replace('ٱ', 'ا')
          .replace('ى', 'ي').replace('ة', 'ه'))
    return NOT_ARABIC.sub('', s)


def strip_html(html):
    html = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', html)
    return re.sub(r'\s+', ' ', TAG.sub(' ', html))


def fetch(url, use_cache=True):
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1(url.encode('utf-8')).hexdigest()[:16]
    path = os.path.join(CACHE, key + '.html')
    if use_cache and os.path.exists(path):
        with io.open(path, encoding='utf-8') as fh:
            return fh.read(), True
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en,ar;q=0.8'})
    body = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
    with io.open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(body)
    return body, False


def target_url(row):
    """Which page actually answers 'what is at this number?'"""
    src = (row.get('source_url') or '').strip()
    host = urllib.parse.urlparse(src).netloc.lower()
    coll = (row.get('collection') or '').strip()
    num = str(row.get('hadith_number') or '').strip()

    if 'sunnah.com' in host:
        seg = TOHED.get(coll)
        if not seg:
            return None, 'collection %r has no tohed mapping' % coll
        if not num.isdigit():
            return None, 'hadith_number %r is not numeric' % num
        return 'https://en.tohed.com/hadith/%s/%s' % (seg, num), 'tohed-for-sunnah'
    if 'hadeethenc.com' in host:
        return src, 'cited page'
    if 'dorar.net' in host and '/search' in src:
        return None, 'source_url is a Dorar SEARCH QUERY, not a hadith page'
    return src, 'cited page'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--number')
    ap.add_argument('--no-cache', action='store_true')
    a = ap.parse_args()

    spec = importlib.util.spec_from_file_location(
        'audit_library', os.path.join(ROOT, 'scripts', 'audit-library.py'))
    al = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(al)
    env = al.load_env(os.path.join(ROOT, '.env.local'))
    base, _ = al.pick(env, ('NEXT_PUBLIC_SUPABASE_URL',))
    key, _ = al.pick(env, ('SUPABASE_SERVICE_ROLE_KEY',
                           'NEXT_PUBLIC_SUPABASE_ANON_KEY'))
    if not base or not key:
        sys.exit('FAILED: supabase url or key missing from .env.local')

    q = ('%s/rest/v1/hadith_library?select=id,hadith_number,collection,'
         'narrator,grade,source_url,text_arabic,matn_screened_at,'
         'matn_verified_at&order=collection,hadith_number' % base.rstrip('/'))
    if a.number:
        q += '&hadith_number=eq.%s' % urllib.parse.quote(a.number)
    req = urllib.request.Request(q, headers={
        'apikey': key, 'Authorization': 'Bearer ' + key})
    rows = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
    if not rows:
        sys.exit('FAILED: no rows returned')

    out = []
    for i, row in enumerate(rows, 1):
        rec = {'id': row['id'], 'number': row.get('hadith_number'),
               'collection': row.get('collection'),
               'narrator': row.get('narrator'),
               'source_url': row.get('source_url'),
               'screened': bool(row.get('matn_screened_at')),
               'verified': bool(row.get('matn_verified_at'))}
        url, how = target_url(row)
        rec['checked_url'] = url
        rec['via'] = how
        ours = norm(row.get('text_arabic'))
        rec['matn_chars'] = len(ours)

        if not url:
            rec['verdict'] = 'SKIP'
            rec['note'] = how
        elif not ours:
            rec['verdict'] = 'SKIP'
            rec['note'] = 'row has no text_arabic'
        else:
            try:
                body, cached = fetch(url, use_cache=not a.no_cache)
                page = norm(strip_html(body))
                rec['page_chars'] = len(page)
                rec['cached'] = cached
                if len(page) < 40:
                    rec['verdict'] = 'REVIEW'
                    rec['note'] = 'page served almost no Arabic'
                elif ours in page:
                    rec['verdict'] = 'MATCH'
                else:
                    # P312: a merged reference ("Sahih al-Bukhari 5185, 5186")
                    # is one entry under two numbers, and a source can serve
                    # its Arabic on the second page while the English sits on
                    # the first. Look next door before calling it a mismatch -
                    # that is a pagination fact about the source, not a defect
                    # in the row. A genuinely wrong number is not next door:
                    # #3559's matn sits 200 references away.
                    merged = None
                    if how == 'tohed-for-sunnah' and str(
                            row.get('hadith_number') or '').isdigit():
                        n = int(str(row['hadith_number']))
                        seg = TOHED.get(row.get('collection') or '')
                        for d in (1, -1):
                            try:
                                nb, nb_cached = fetch(
                                    'https://en.tohed.com/hadith/%s/%d'
                                    % (seg, n + d),
                                    use_cache=not a.no_cache)
                            except Exception:  # noqa: BLE001
                                continue
                            if not nb_cached:
                                time.sleep(DELAY)
                            if ours in norm(strip_html(nb)):
                                merged = n + d
                                break
                    if merged is not None:
                        rec['verdict'] = 'MERGED'
                        rec['merged_with'] = merged
                        rec['note'] = ('served at #%d - a merged reference, '
                                       'not a wrong citation (P312)' % merged)
                    else:
                        rec['verdict'] = 'MISMATCH'
                        rec['note'] = ('stored matn is not a contiguous run on '
                                       'the page at this number or either '
                                       'neighbour')
                if not cached:
                    time.sleep(DELAY)
            except urllib.error.HTTPError as exc:
                rec['verdict'] = 'ERROR'
                rec['note'] = 'HTTP %s' % exc.code
                time.sleep(DELAY)
            except Exception as exc:  # noqa: BLE001
                rec['verdict'] = 'ERROR'
                rec['note'] = type(exc).__name__
                time.sleep(DELAY)
        out.append(rec)
        print('[%2d/%d] %-18s #%-7s %-9s %s'
              % (i, len(rows), rec['collection'], rec['number'],
                 rec['verdict'], rec.get('note', '')))

    with io.open(REPORT, 'w', encoding='utf-8', newline='') as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1) + '\n')

    counts = {}
    for r in out:
        counts[r['verdict']] = counts.get(r['verdict'], 0) + 1
    print()
    print('-' * 64)
    for k in ('MATCH', 'MERGED', 'MISMATCH', 'REVIEW', 'ERROR', 'SKIP'):
        if counts.get(k):
            print('  %-9s %d' % (k, counts[k]))
    bad = [r for r in out if r['verdict'] == 'MISMATCH']
    if bad:
        print()
        print('  rows whose stored Arabic is NOT at the number they cite:')
        for r in bad:
            print('    %-18s #%-7s %s  screened=%s verified=%s'
                  % (r['collection'], r['number'], r['narrator'],
                     r['screened'], r['verified']))
    print()
    print('  sunnah.com rows were checked against en.tohed.com, which serves')
    print('  the same reference numbering; sunnah.com refuses scripts (P145).')
    print('  MISMATCH means REVIEW, not FAIL. Nothing was written.')
    print('-' * 64)
    print('report: %s' % os.path.relpath(REPORT, ROOT))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
