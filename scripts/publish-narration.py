#!/usr/bin/env python3
"""publish-narration.py - put each set's narrated story.mp3 where the public site can play it.

The library page's "Listen" button had two bad choices on the deployed site: call
ElevenLabs on every anonymous click (P353 closed that - it was paid for by the
operator per click), or the browser's robotic voice (Russian for Uzbek). Every
published set already HAS the right audio: S-block narration, narrator + matn, in
the voice chosen for that language. This copies it to Supabase Storage and keeps an
index the page reads (P362).

    python scripts/publish-narration.py              # dry run: what would be uploaded
    python scripts/publish-narration.py --commit     # upload + rewrite the index

What counts as usable, per library row and language:
  - out/work/**, out/published/** or out/library-narration/** (P370) has
    adults-<lang>-<slug>-story.mp3 AND its .txt
    (the exact text that was narrated, P246);
  - recorded on/after --since (default 2026-10-04: eleven_v4 and the current voice
    matrix - older takes used retired voices);
  - the .txt contains the row's stored translation for that language (--min-cover,
    default 0.9 of its characters), so Listen never plays a story about a hadith in
    place of the hadith.
The newest usable take wins. Re-run at every set close; unchanged files are skipped.

Storage layout (bucket "narration", public read):
  <library_id>/<lang>-<sha8>.mp3   - content-addressed, so a replaced take is a new URL
  index.json                       - {"version":1,"items":{id:{lang:{path,sha256,ref,recorded}}}}
"""
import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

BUCKET = 'narration'
COLS = {'en': 'text_english', 'ru': 'text_russian', 'uz': 'text_uzbek_cyrillic', 'tj': 'text_tajik'}
STORY = re.compile(r'^adults-(en|ru|uz|tj)-(.+)-(\d+[a-z]?)-story\.mp3$')


def load_env(path='.env.local'):
    env = {}
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def norm(s):
    return re.sub(r'[^\w]+', ' ', (s or '').lower()).strip()


def coll_key(name):
    """'Sahih al-Bukhari' and the slug 'bukhari' -> 'bukhari'; 'Jami at-Tirmidhi' and
    'at-tirmidhi' -> 'tirmidhi'."""
    c = norm(name.replace('-', ' '))
    for w in ('sahih', 'sunan', 'jami', 'al', 'at', 'an', 'as', 'musnad', 'imam'):
        c = re.sub(r'\b%s\b' % w, ' ', c)
    return c.replace(' ', '')


def coverage(matn, spoken):
    """Share of the stored translation's characters found, in order, in what was spoken."""
    a, b = norm(matn), norm(spoken)
    if not a:
        return 0.0
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(x.size for x in sm.get_matching_blocks()) / len(a)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def find_takes(rows, roots, since_ts, min_cover):
    """-> {(library_id, lang): take}, newest usable take per row and language."""
    lib = {(coll_key(r['collection']), str(r['hadith_number']).strip()): r for r in rows}
    best = {}
    for top in roots:
        for d, _, files in os.walk(top):
            for f in files:
                m = STORY.match(f)
                if not m:
                    continue
                lang, coll, num = m.groups()
                mp3 = os.path.join(d, f)
                txt = mp3[:-4] + '.txt'
                row = lib.get((coll_key(coll), num))
                if not row or not os.path.exists(txt):
                    continue
                t = os.path.getmtime(mp3)
                if t < since_ts:
                    continue
                with open(txt, encoding='utf-8') as fh:
                    spoken = fh.read()
                cov = coverage(row.get(COLS[lang]) or '', spoken)
                if cov < min_cover:
                    continue
                key = (row['id'], lang)
                if key in best and best[key]['mtime'] >= t:
                    continue
                best[key] = {'id': row['id'], 'lang': lang, 'mp3': mp3, 'mtime': t,
                             'ref': '%s #%s' % (row['collection'], row['hadith_number']),
                             'recorded': dt.datetime.fromtimestamp(t).strftime('%Y-%m-%d'),
                             'cover': round(cov, 3)}
    return best


def plan(best, index):
    """-> (uploads, new_index). An upload is needed when the take's bytes are not
    what the index already points at."""
    items = json.loads(json.dumps(index.get('items', {})))
    uploads = []
    for (rid, lang), take in sorted(best.items(), key=lambda kv: (kv[1]['ref'], kv[0][1])):
        digest = sha256_file(take['mp3'])
        cur = items.get(rid, {}).get(lang)
        if cur and cur.get('sha256') == digest:
            continue
        path = '%s/%s-%s.mp3' % (rid, lang, digest[:8])
        uploads.append((take, path))
        items.setdefault(rid, {})[lang] = {'path': path, 'sha256': digest,
                                           'ref': take['ref'], 'recorded': take['recorded']}
    return uploads, {'version': 1, 'items': items}


# ---------------------------------------------------------------- storage


def _req(method, url, key, data=None, ctype=None, extra=None):
    h = {'apikey': key, 'Authorization': 'Bearer ' + key}
    if ctype:
        h['Content-Type'] = ctype
    h.update(extra or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()


def read_index(base, key):
    try:
        _, body = _req('GET', '%s/storage/v1/object/%s/index.json' % (base, BUCKET), key)
        return json.loads(body.decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return {'version': 1, 'items': {}}
        raise


def ensure_bucket(base, key):
    try:
        _req('GET', '%s/storage/v1/bucket/%s' % (base, BUCKET), key)
    except urllib.error.HTTPError as e:
        if e.code not in (400, 404):
            raise
        _req('POST', '%s/storage/v1/bucket' % base, key,
             json.dumps({'id': BUCKET, 'name': BUCKET, 'public': True}).encode(), 'application/json')


def upload(base, key, path, data, ctype):
    _req('POST', '%s/storage/v1/object/%s/%s' % (base, BUCKET, path), key, data, ctype,
         {'x-upsert': 'true', 'cache-control': 'max-age=31536000'})


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--commit', action='store_true', help='upload and rewrite index.json')
    ap.add_argument('--since', default='2026-10-04', help='oldest recording to use (YYYY-MM-DD)')
    ap.add_argument('--min-cover', type=float, default=0.9)
    args = ap.parse_args()

    env = load_env()
    base = (env.get('NEXT_PUBLIC_SUPABASE_URL') or env.get('SUPABASE_URL') or '').rstrip('/')
    key = env.get('SUPABASE_SERVICE_ROLE_KEY')
    if not base or not key:
        print('FAILED: Supabase URL / service key missing in .env.local')
        return 2

    _, body = _req('GET', '%s/rest/v1/hadith_library?select=id,collection,hadith_number,%s&limit=5000'
                   % (base, ','.join(COLS.values())), key)
    rows = json.loads(body.decode('utf-8'))
    since = dt.datetime.strptime(args.since, '%Y-%m-%d').timestamp()
    # P370: out/library-narration/ holds narrate-library.py's takes for rows with no reel.
    best = find_takes(rows, [os.path.join('out', 'work'), os.path.join('out', 'published'),
                             os.path.join('out', 'library-narration')],
                      since, args.min_cover)
    index = read_index(base, key)
    uploads, new_index = plan(best, index)

    have = sum(len(v) for v in new_index['items'].values())
    print('library rows %d | usable takes %d | already published %d | to upload %d'
          % (len(rows), len(best), have - len(uploads), len(uploads)))
    for take, path in uploads:
        print('  %-30s %s  %s  cover %.0f%%  -> %s'
              % (take['ref'], take['lang'], take['recorded'], take['cover'] * 100, path))
    if not args.commit:
        print('DRY RUN - nothing uploaded. --commit to publish.')
        return 0

    ensure_bucket(base, key)
    failed = 0
    for take, path in uploads:
        try:
            with open(take['mp3'], 'rb') as fh:
                upload(base, key, path, fh.read(), 'audio/mpeg')
        except Exception as e:  # noqa: BLE001
            failed += 1
            print('  UPLOAD FAILED %s %s: %s' % (take['ref'], take['lang'], e))
            new_index['items'][take['id']].pop(take['lang'], None)
    new_index['updated'] = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    upload(base, key, 'index.json', json.dumps(new_index, ensure_ascii=False).encode('utf-8'),
           'application/json')
    print('uploaded %d, failed %d; index.json rewritten (%d clips)'
          % (len(uploads) - failed, failed, sum(len(v) for v in new_index['items'].values())))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
