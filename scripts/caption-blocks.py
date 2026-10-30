#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
caption-blocks.py - build out/caption-<number>.json from the draft files.

    python scripts/caption-blocks.py --slug bukhari-5185

`build-caption.ts` wants a spec with a `langs` object carrying a title and a
moral per language. Those are the C and M blocks, and taking them from the
draft files rather than retyping them is what keeps the caption, the narration
and the database saying the same thing - the caption is the one surface a
reader can check against the source, so it is the last place that should drift.

Only languages whose draft file exists are included, so this can run after the
first leg and again when the set is complete. Existing entries are preserved
when the file is rebuilt, which matters because the legs are produced days
apart.

Deliberately does NOT invent a style: it reads the row to confirm the hadith
number resolves to exactly one library row (P147) before writing anything.
"""
import argparse
import importlib.util
import io
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ('en', 'ru', 'uz', 'tj')

ap = argparse.ArgumentParser()
ap.add_argument('--slug', required=True, help='collection-number, e.g. bukhari-5185')
ap.add_argument('--style', default='adults', choices=('adults', 'kids'))
a = ap.parse_args()

number = a.slug.rsplit('-', 1)[-1]
if not number.isdigit():
    sys.exit('ABORT: --slug must end in the hadith number, got %r' % a.slug)

spec = importlib.util.spec_from_file_location(
    'audit_library', os.path.join(ROOT, 'scripts', 'audit-library.py'))
al = importlib.util.module_from_spec(spec)
spec.loader.exec_module(al)
env = al.load_env(os.path.join(ROOT, '.env.local'))
base, _ = al.pick(env, ('NEXT_PUBLIC_SUPABASE_URL',))
key, _ = al.pick(env, ('SUPABASE_SERVICE_ROLE_KEY',
                       'NEXT_PUBLIC_SUPABASE_ANON_KEY'))
req = urllib.request.Request(
    '%s/rest/v1/hadith_library?hadith_number=eq.%s&select=id,collection'
    % (base.rstrip('/'), number),
    headers={'apikey': key, 'Authorization': 'Bearer ' + key})
rows = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
if len(rows) != 1:
    sys.exit('ABORT: %d library rows for hadith_number %s (P147) - '
             'build-caption cannot resolve it either' % (len(rows), number))

out = os.path.join(ROOT, 'out', 'caption-%s.json' % number)
spec_doc = {'hadith_number': number, 'style': a.style, 'langs': {}}
if os.path.exists(out):
    with io.open(out, encoding='utf-8-sig') as fh:
        spec_doc = json.load(fh)
    spec_doc.setdefault('langs', {})
spec_doc['hadith_number'] = number
spec_doc['style'] = a.style

found, missing = [], []
for lang in LANGS:
    p = os.path.join(ROOT, 'out', 'draft-%s-%s.txt' % (a.slug, lang))
    if not os.path.exists(p):
        missing.append(lang)
        continue
    with io.open(p, encoding='utf-8-sig', newline='') as fh:
        raw = fh.read()
    blocks = {}
    for line in raw.replace('\r\n', '\n').split('\n'):
        if len(line) > 2 and line[1] == ':' and line[0] in 'SMHC':
            blocks[line[0]] = line[2:].strip()
    for k in ('M', 'C'):
        if not blocks.get(k):
            sys.exit('ABORT: %s has no %s block'
                     % (os.path.relpath(p, ROOT), k))
    spec_doc['langs'][lang] = {'title': blocks['C'], 'moral': blocks['M']}
    found.append(lang)

if not found:
    sys.exit('ABORT: no draft files for %s' % a.slug)

text = json.dumps(spec_doc, ensure_ascii=False, indent=2) + '\n'
with io.open(out, 'w', encoding='utf-8', newline='') as fh:
    fh.write(text)
with io.open(out, encoding='utf-8-sig') as fh:
    back = json.load(fh)

checks = [
    ('hadith_number is a string', isinstance(back['hadith_number'], str)),
    ('one library row', len(rows) == 1),
    ('every found language present',
     all(l in back['langs'] for l in found)),
    ('no empty title or moral',
     all(back['langs'][l]['title'] and back['langs'][l]['moral']
         for l in back['langs'])),
    ('titles are short',
     all(len(back['langs'][l]['title'].split()) <= 8 for l in back['langs'])),
]
print('%s  ->  %s' % (a.slug, os.path.relpath(out, ROOT)))
print('   languages written : %s' % ', '.join(found))
if missing:
    print('   not yet drafted   : %s' % ', '.join(missing))
bad = 0
for name, ok in checks:
    print('   %-30s %s' % (name, 'ok' if ok else 'FAIL'))
    if not ok:
        bad += 1
print('FAILED %d check(s)' % bad if bad else 'spec written')
sys.exit(1 if bad else 0)
