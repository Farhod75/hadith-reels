"""P438: the grade docs-set writes into the tracker - from the library row, never assumed.

docs-set.py wrote "Sahih" for every set; Tirmidhi #3479 (al-Albani: hasan) had to be fixed by hand.
Order: the docs config's "grade" (operator override), else hadith_library.grade for the set's
library_id (from the docs config or out/set-<number>.json). Only sahih/hasan are published (P-rule),
so anything else stops the docs instead of being written.
"""
import io
import json
import os
import urllib.parse
import urllib.request

PUBLISHED = ('sahih', 'hasan')


def grade_label(raw):
    g = (raw or '').strip().lower()
    if g not in PUBLISHED:
        raise SystemExit('grade %r: only sahih/hasan are published - check the library row' % (raw,))
    return g.capitalize()


def library_id(cfg, repo):
    if cfg.get('library_id'):
        return cfg['library_id']
    p = os.path.join(repo, 'out', 'set-%s.json' % cfg['number'])
    if os.path.exists(p):
        lid = json.load(io.open(p, encoding='utf-8')).get('library_id')
        if lid:
            return lid
    raise SystemExit('no library_id: add it to the docs config or out/set-%s.json' % cfg['number'])


def _env(repo):
    env = {}
    for line in io.open(os.path.join(repo, '.env.local'), encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def fetch_grade(lid, repo):
    env = _env(repo)
    base = (env.get('NEXT_PUBLIC_SUPABASE_URL') or env.get('SUPABASE_URL')).rstrip('/')
    key = env['SUPABASE_SERVICE_ROLE_KEY']
    url = base + '/rest/v1/hadith_library?select=grade&id=eq.' + urllib.parse.quote(lid)
    req = urllib.request.Request(url, headers={'apikey': key, 'Authorization': 'Bearer ' + key})
    rows = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if len(rows) != 1:
        raise SystemExit('library row %s: %d rows' % (lid, len(rows)))
    return rows[0].get('grade')


def set_grade(cfg, repo, fetch=fetch_grade):
    if cfg.get('grade'):
        return grade_label(cfg['grade'])
    return grade_label(fetch(library_id(cfg, repo), repo))