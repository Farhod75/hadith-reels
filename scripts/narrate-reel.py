#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
narrate-reel.py - narrate one language's S and M blocks from its draft file.

    python scripts/narrate-reel.py --lang en --slug bukhari-5185
    python scripts/narrate-reel.py --lang en --slug bukhari-5185 --dry-run

The pipeline documents narration as two buttons in the admin studio. The route
behind them is an ordinary POST, so this drives it directly: no clicking, and
no chance of the studio's Regenerate button replacing four reviewed blocks
(P079).

It narrates FROM THE DRAFT FILE, which is the same file lint-content.py and
check-draft-sync.py read, and the /api/tts route writes a .txt sidecar of the
exact text it voiced. That is what makes the three agree afterwards; narrating
from anything else is how audio and draft drift apart (P297).

S becomes the story section and M the moral. H and C are never narrated - H is
caption prose and C is the title.

Existing audio for the same slug and language is OVERWRITTEN, and the script
asserts the bytes actually changed, so a silent no-op cannot pass for a
re-narration. This step spends money; nothing before it does.
"""
import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.environ.get('HR_DEV_ORIGIN', 'http://localhost:3002') + '/api/tts'


def die(msg):
    print('ABORT: %s' % msg)
    sys.exit(2)


ap = argparse.ArgumentParser()
ap.add_argument('--lang', required=True, choices=('en', 'ru', 'uz', 'tj'))
ap.add_argument('--slug', required=True, help='collection-number, e.g. bukhari-5185')
ap.add_argument('--style', default='adults', choices=('adults', 'kids'))
ap.add_argument('--mascot', choices=('boy', 'girl'))
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()

if a.style == 'kids' and not a.mascot:
    die('--mascot is required on the kids lane')

draft = os.path.join(ROOT, 'out', 'draft-%s-%s.txt' % (a.slug, a.lang))
if not os.path.exists(draft):
    die('no draft at %s - write it at approval time, not before the render'
        % os.path.relpath(draft, ROOT))
with io.open(draft, encoding='utf-8-sig', newline='') as fh:
    raw = fh.read()
blocks = {}
for line in raw.replace('\r\n', '\n').split('\n'):
    if len(line) > 2 and line[1] == ':' and line[0] in 'SMHC':
        blocks[line[0]] = line[2:].strip()
for k in ('S', 'M'):
    if not blocks.get(k):
        die('%s has no %s block' % (os.path.relpath(draft, ROOT), k))

# P337: S opens with the narrator, from hadith_library, in the fixed form for
# this language - not omitted, not added, never generated. Checked BEFORE the
# dry-run exit and before any TTS call. Adults lane only: the kids story block
# has its own shape and has not been decided.
if a.style == 'adults':
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        '_nl', os.path.join(ROOT, 'scripts', 'lib', 'narrator_leadin.py'))
    _nl = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_nl)
    try:
        _narrator = _nl.db_narrator(a.slug)
    except Exception as exc:
        die('cannot read the narrator for %s from hadith_library (%s) - P337 '
            'needs it before narrating' % (a.slug, exc))
    _problems = _nl.check_story(blocks['S'], _narrator, a.lang, _nl.load_narrators())
    if _problems:
        for _p in _problems:
            print('  P337: ' + _p)
        die('the S block does not open with the narrator from hadith_library '
            '(%s). Nothing was sent and nothing was spent.' % _narrator)
    print('narrator: %s - S opens with the P337 lead-in' % _narrator)

work = os.path.join(ROOT, 'out', 'work', a.style, a.slug, a.lang)


def side(section, ext):
    return os.path.join(work, '%s-%s-%s-%s.%s'
                        % (a.style, a.lang, a.slug, section, ext))


def stat(p):
    return (os.path.getsize(p), int(os.path.getmtime(p))) \
        if os.path.exists(p) else None


jobs = [('story', blocks['S']), ('moral', blocks['M'])]
print('draft : %s' % os.path.relpath(draft, ROOT))
for section, text in jobs:
    print('%-6s: %d chars  %s' % (section, len(text), text[:68]))
if a.dry_run:
    print('\nDRY RUN - nothing was sent and nothing was spent.')
    sys.exit(0)

before = {s: stat(side(s, 'mp3')) for s, _ in jobs}
rows = []
bad = 0
for section, text in jobs:
    payload = {'text': text, 'lang': a.lang, 'style': a.style,
               'slug': a.slug, 'section': section}
    if a.mascot:
        payload['mascot'] = a.mascot
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=300)
        audio = resp.read()
        code = resp.getcode()
    except urllib.error.HTTPError as exc:
        rows.append((section, 'HTTP %d' % exc.code, 0, 0, False, False))
        bad += 1
        continue
    except urllib.error.URLError as exc:
        die('cannot reach %s - is the dev server running? (%s)' % (API, exc.reason))

    mp3 = stat(side(section, 'mp3'))
    txt = side(section, 'txt')
    voiced = None
    if os.path.exists(txt):
        with io.open(txt, encoding='utf-8-sig') as fh:
            voiced = fh.read()
    changed = before[section] is None or (mp3 is not None and mp3 != before[section])
    matches = voiced is not None and voiced.strip() == text.strip()
    ok = (code == 200 and len(audio) > 2000 and mp3 and mp3[0] > 2000
          and changed and matches)
    if not ok:
        bad += 1
    rows.append((section, 'HTTP %d' % code, len(audio),
                 mp3[0] if mp3 else 0, changed, matches))

print()
print('%-6s %-9s %9s %9s %8s %9s'
      % ('sect', 'status', 'stream', 'on disk', 'changed', 'sidecar'))
for section, status, n, size, changed, matches in rows:
    print('%-6s %-9s %9d %9d %8s %9s'
          % (section, status, n, size, 'yes' if changed else 'NO',
             'ok' if matches else 'MISMATCH'))
print('FAILED %d of %d' % (bad, len(jobs)) if bad
      else 'both narrations written and match the draft')
sys.exit(1 if bad else 0)
