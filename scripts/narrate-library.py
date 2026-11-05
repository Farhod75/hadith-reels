#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
narrate-library.py - narrate the library hadiths that have no reel yet, so Listen
works for them on the public site.

    python scripts/narrate-library.py                       # dry run: what, how many characters
    python scripts/narrate-library.py --narrate --max-chars 40000
    python scripts/publish-narration.py --commit            # then publish, as at a set close

P370. Listen on hadithreels.com plays stored narration only (P353 closed the paid
per-click route; P362 published the reels' own story.mp3). Rows without a reel had
no Listen at all on the deployed site. This narrates, per row and language, exactly
the S block a reel of that row would narrate - the P337 narrator lead-in and the
quoted matn, built by the same functions make-drafts.py uses - through the dev
server's /api/tts, so the voice matrix and cleanForTTS are the reels' own. A later
reel of the same row narrates its own take; nothing here is reused for a reel.

Takes are moved to out/library-narration/<slug>/<lang>/ (publish-narration.py
reads that root) so out/work/ keeps meaning "sets in production".

What is NOT narrated, and why - every skip is printed:
  - a (row, language) already in the public index.json (it has Listen);
  - a row whose grade is not sahih/hasan, or whose text for that language is empty;
  - a row whose collection + number is not unique in the library (publish-narration
    matches takes by that key, so a duplicate could attach audio to the wrong row);
  - a row whose narrator has no lead-in in lib/refs.ts NARRATORS;
  - an S block over 1000 characters (/api/tts refuses it, P354);
  - anything listed in scripts/narration-exclusions.json - a known defect in the
    row's text must be fixed before it is read aloud (operator reviews that list);
  - a row with an out/work/adults/<slug>/ folder - a reel is in production and will
    narrate it.
Spending guard: --narrate needs --max-chars and stops before the job that would
cross it. Dry run by default.
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'lib'))
LANGS = ('en', 'ru', 'uz', 'tj')
COLS = {'en': 'text_english', 'ru': 'text_russian', 'uz': 'text_uzbek_cyrillic', 'tj': 'text_tajik'}
TTS_LIMIT = 1000
OUT_ROOT = os.path.join('out', 'library-narration')
API = os.environ.get('HR_DEV_ORIGIN', 'http://localhost:3002') + '/api/tts'


def _norm(s):
    return re.sub(r'[^\w]+', ' ', (s or '').lower()).strip()


def coll_key(name):
    """Same key publish-narration.py matches takes by."""
    c = _norm((name or '').replace('-', ' '))
    for w in ('sahih', 'sunan', 'jami', 'al', 'at', 'an', 'as', 'musnad', 'imam'):
        c = re.sub(r'\b%s\b' % w, ' ', c)
    return c.replace(' ', '')


def slug_for(row):
    return '%s-%s' % (coll_key(row['collection']), str(row['hadith_number']).strip())


def strip_inner_quotes(s):
    return re.sub(u'[«»"“”„]', '', s).strip()


def quote_matn(matn, lang):
    """Identical to make-drafts.py quote_matn (the reel's S block)."""
    m = strip_inner_quotes(matn)
    if lang == 'en':
        return '"' + m + '"'
    body = m[:-1] if m.endswith('.') else m
    return u'«' + body + u'».'


def load_exclusions(path=os.path.join(HERE, 'narration-exclusions.json')):
    if not os.path.exists(path):
        return {}
    data = json.load(io.open(path, encoding='utf-8'))
    out = {}
    for e in data.get('exclude', []):
        for lang in e.get('langs') or list(LANGS):
            out[(e['id'], lang)] = e.get('reason', '')
    return out


def plan(rows, index_items, leadin_fn, exclusions, in_production):
    """-> (jobs, skips). A job: {id, ref, slug, lang, text}. Pure: no I/O."""
    keys = {}
    for r in rows:
        k = (coll_key(r['collection']), str(r['hadith_number']).strip())
        keys[k] = keys.get(k, 0) + 1
    jobs, skips = [], []
    for r in sorted(rows, key=lambda x: (x['collection'], int(re.sub(r'\D', '', str(x['hadith_number'])) or 0))):
        ref = '%s #%s' % (r['collection'], r['hadith_number'])
        k = (coll_key(r['collection']), str(r['hadith_number']).strip())
        slug = slug_for(r)
        for lang in LANGS:
            why = None
            if lang in (index_items.get(r['id']) or {}):
                why = 'has Listen'
            elif (r.get('grade') or '').lower() not in ('sahih', 'hasan'):
                why = 'grade %s' % r.get('grade')
            elif not (r.get(COLS[lang]) or '').strip():
                why = 'no %s text' % lang
            elif keys[k] > 1:
                why = 'number not unique in the library (%d rows)' % keys[k]
            elif (r['id'], lang) in exclusions:
                why = 'excluded: ' + exclusions[(r['id'], lang)]
            elif slug in in_production:
                why = 'reel in production (out/work/adults/%s)' % slug
            if why:
                skips.append((ref, lang, why))
                continue
            try:
                lead = leadin_fn(r['narrator'], lang)
            except KeyError:
                skips.append((ref, lang, 'no lead-in for narrator %r' % r.get('narrator')))
                continue
            text = lead + ' ' + quote_matn(r[COLS[lang]], lang)
            if len(text) > TTS_LIMIT:
                skips.append((ref, lang, '%d chars > %d (P354)' % (len(text), TTS_LIMIT)))
                continue
            jobs.append({'id': r['id'], 'ref': ref, 'slug': slug, 'lang': lang, 'text': text})
    return jobs, skips


def _env():
    env = {}
    for line in io.open(os.path.join(REPO, '.env.local'), encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _get(url, key=None):
    h = {'apikey': key, 'Authorization': 'Bearer ' + key} if key else {}
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60).read()


def narrate(job):
    """One take through the dev server; returns the moved mp3 path."""
    payload = {'text': job['text'], 'lang': job['lang'], 'style': 'adults',
               'slug': job['slug'], 'section': 'story'}
    req = urllib.request.Request(API, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req, timeout=300).read()
    src = os.path.join(REPO, 'out', 'work', 'adults', job['slug'], job['lang'])
    dst = os.path.join(REPO, OUT_ROOT, job['slug'], job['lang'])
    os.makedirs(dst, exist_ok=True)
    moved = None
    for ext in ('mp3', 'txt'):
        name = 'adults-%s-%s-story.%s' % (job['lang'], job['slug'], ext)
        s = os.path.join(src, name)
        if not os.path.exists(s):
            raise RuntimeError('the route did not write %s' % os.path.relpath(s, REPO))
        shutil.move(s, os.path.join(dst, name))
        if ext == 'mp3':
            moved = os.path.join(dst, name)
    # leave no empty set folder behind in out/work (it would read as a set in production)
    for d in (src, os.path.dirname(src)):
        try:
            os.rmdir(d)
        except OSError:
            pass
    return moved


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--narrate', action='store_true', help='call /api/tts (paid)')
    ap.add_argument('--max-chars', type=int, default=0, help='spend cap for --narrate')
    ap.add_argument('--langs', nargs='*', choices=LANGS, default=list(LANGS))
    ap.add_argument('--limit', type=int, default=0, help='at most this many takes')
    a = ap.parse_args(argv)

    import narrator_leadin as nl
    table = nl.load_narrators()
    env = _env()
    base = (env.get('NEXT_PUBLIC_SUPABASE_URL') or env.get('SUPABASE_URL')).rstrip('/')
    key = env['SUPABASE_SERVICE_ROLE_KEY']
    rows = json.loads(_get(base + '/rest/v1/hadith_library?select=id,collection,hadith_number,grade,'
                           'narrator,' + ','.join(COLS.values()) + '&limit=5000', key).decode('utf-8'))
    try:
        index = json.loads(_get(base + '/storage/v1/object/public/narration/index.json').decode('utf-8'))
    except urllib.error.HTTPError:
        index = {}
    work = os.path.join(REPO, 'out', 'work', 'adults')
    in_prod = set(os.listdir(work)) if os.path.isdir(work) else set()
    jobs, skips = plan(rows, index.get('items', {}), lambda n, l: nl.leadin(n, l, table),
                       load_exclusions(), in_prod)
    jobs = [j for j in jobs if j['lang'] in a.langs]
    if a.limit:
        jobs = jobs[:a.limit]

    total = sum(len(j['text']) for j in jobs)
    by_lang = {l: sum(len(j['text']) for j in jobs if j['lang'] == l) for l in LANGS}
    print('library rows %d | takes to narrate %d | characters %d (%s)'
          % (len(rows), len(jobs), total, ', '.join('%s %d' % kv for kv in by_lang.items())))
    reasons = {}
    for _, _, why in skips:
        k = why.split(':')[0] if why.startswith('excluded') else re.sub(r'\d+', 'N', why)
        reasons[k] = reasons.get(k, 0) + 1
    print('skipped %d: %s' % (len(skips), '; '.join('%s x%d' % kv for kv in sorted(reasons.items()))))
    for ref, lang, why in skips:
        if not why.startswith('has Listen'):
            print('  skip  %-30s %s  %s' % (ref, lang, why))
    plan_path = os.path.join(REPO, 'out', 'library-narration-plan.json')
    io.open(plan_path, 'w', encoding='utf-8').write(json.dumps(
        {'jobs': jobs, 'skips': skips, 'characters': total}, ensure_ascii=False, indent=1))
    print('plan: %s' % os.path.relpath(plan_path, REPO))
    if not a.narrate:
        print('DRY RUN - nothing narrated. --narrate --max-chars N to spend.')
        return 0
    if a.max_chars <= 0:
        print('REFUSED: --narrate needs --max-chars (spending cap).')
        return 1
    spent, done, failed = 0, 0, 0
    for j in jobs:
        if spent + len(j['text']) > a.max_chars:
            print('STOP at the cap: %d chars spent, next take is %d' % (spent, len(j['text'])))
            break
        try:
            narrate(j)
            spent += len(j['text'])
            done += 1
            print('  OK    %-30s %s  %d chars' % (j['ref'], j['lang'], len(j['text'])))
        except Exception as e:  # noqa: BLE001
            failed += 1
            print('  FAIL  %-30s %s  %s' % (j['ref'], j['lang'], e))
            if failed >= 3:
                print('STOP: three failures')
                break
    print('narrated %d, failed %d, characters %d. Next: python scripts/publish-narration.py --commit'
          % (done, failed, spent))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
