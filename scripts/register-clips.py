#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
register-clips.py - add a reel set's scene clips to assets/asset-registry.json, and mark them
verified when the set closes.

Replaces the per-set out/w<nn>_reg<n>.py scripts and the hand edit at set close (automation,
OPEN_ITEMS item 2, 2026-11-03). Nothing may be rendered until a clip is registered (P121); the
render gate (audit-assets.py --check) enforces that, this script only writes the entries.

Two modes, both DRY RUN unless --commit:

  --spec out/clips-<n>.json   register new clips (verified:false until the operator reviews
                              the renders). The spec:
      {"common": "Sahih Muslim #2749, Abu Hurairah, sahih - ... MODE B ...",
       "clips": [
         {"file": "m2749-people.mp4", "sidecar": "m2749-people",
          "note": "FLUX 2 still (people-2) -> Kling 3.0 Pro i2v 10s. Depicts: ..."},
         {"file": "m2749-footprints.mp4", "sidecar": "m2749-footprints", "lanes": [],
          "note": "RAW take, not for use (P141)"}
       ]}
      lanes defaults to ["adults"]; each note is followed by the common text.

  --verify <prefix>           at set close, set verified:true on every scene whose key starts
                              with the prefix (e.g. m2749-), after the operator's lg.

Refuses (and writes nothing) when: a key is already registered, a clip file is missing from
out/backgrounds/new/, or the registry would not round-trip byte for byte (indent, ensure_ascii,
line endings and the trailing newline are detected, never assumed). Runs audit-assets.py --audit
after a commit.
"""
import argparse
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REG = os.path.join(REPO, 'assets', 'asset-registry.json')
NEW_DIR = os.path.join(REPO, 'out', 'backgrounds', 'new')


def detect_format(raw):
    """(ensure_ascii, trailing, eol) that reproduce raw exactly, or None."""
    data = json.loads(raw)
    nl = '\r\n' if raw.count('\r\n') > (raw.count('\n') - raw.count('\r\n')) else '\n'
    for ea in (False, True):
        t = json.dumps(data, indent=2, ensure_ascii=ea).replace('\n', nl)
        for tail in ('', nl):
            if t + tail == raw:
                return ea, tail, nl
    return None


def dump(data, fmt):
    ea, tail, nl = fmt
    return json.dumps(data, indent=2, ensure_ascii=ea).replace('\n', nl) + tail


def plan_register(data, spec, new_dir=NEW_DIR):
    """(entries to add, problems). Pure apart from the file-existence check."""
    scenes = data.get('scenes', {})
    common = spec.get('common', '').strip()
    add, problems = {}, []
    for c in spec.get('clips', []):
        f = c.get('file', '')
        if not f.endswith('.mp4'):
            problems.append('%r is not an .mp4' % f); continue
        if f in scenes or f in add:
            problems.append('%s is already registered' % f); continue
        if not os.path.exists(os.path.join(new_dir, f)):
            problems.append('%s is not in out/backgrounds/new/' % f); continue
        note = (c.get('note', '').strip() + ' ' + common).strip()
        entry = {'classification': 'scene', 'lanes': list(c.get('lanes', ['adults'])), 'verified': False, 'notes': note}
        if c.get('sidecar'):
            entry['prompt_sidecar'] = 'assets/scene-prompts/%s.json' % c['sidecar']
        add[f] = entry
    return add, problems


def plan_verify(data, prefix):
    return sorted(k for k, v in data.get('scenes', {}).items() if k.startswith(prefix) and not v.get('verified'))


def main(argv=None):
    ap = argparse.ArgumentParser(description='Register a set\'s clips, or mark them verified (dry run unless --commit).')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--spec', help='out/clips-<n>.json')
    g.add_argument('--verify', metavar='PREFIX', help='mark scenes starting with PREFIX verified (set close)')
    ap.add_argument('--commit', action='store_true')
    ap.add_argument('--date', default=None, help='value for the registry "updated" field (YYYY-MM-DD)')
    args = ap.parse_args(argv)

    raw = io.open(REG, 'r', encoding='utf-8', newline='').read()
    fmt = detect_format(raw)
    if fmt is None:
        print('FAILED: the registry does not round-trip - nothing written'); return 1
    data = json.loads(raw)

    if args.spec:
        spec = json.load(io.open(args.spec, encoding='utf-8-sig'))
        add, problems = plan_register(data, spec)
        for p in problems:
            print('  REFUSED: ' + p)
        if problems:
            print('FAILED: nothing written'); return 1
        for k, e in add.items():
            side = e.get('prompt_sidecar')
            side_ok = side and os.path.exists(os.path.join(REPO, side))
            print('  + %-28s lanes=%-10s sidecar=%s' % (k, e['lanes'], side + ('' if side_ok else '  (MISSING)') if side else '-'))
        data['scenes'].update(add)
        what = '%d clip(s) registered' % len(add)
    else:
        keys = plan_verify(data, args.verify)
        if not keys:
            print('nothing to verify under %r' % args.verify); return 0
        for k in keys:
            print('  verified: ' + k)
            data['scenes'][k]['verified'] = True
        what = '%d clip(s) verified' % len(keys)

    if args.date and isinstance(data.get('updated'), str):
        data['updated'] = args.date
    if not args.commit:
        print('DRY RUN - %s would be written. Add --commit.' % what); return 0
    out = dump(data, fmt)
    io.open(REG, 'w', encoding='utf-8', newline='').write(out)
    if io.open(REG, 'r', encoding='utf-8', newline='').read() != out:
        print('FAILED: read-back mismatch'); return 1
    print('WRITTEN - ' + what)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'audit-assets.py'), '--audit'], cwd=REPO,
                       capture_output=True, text=True, encoding='utf-8', errors='replace',
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    tail = [l for l in r.stdout.splitlines() if 'unregistered' in l or 'unverified' in l]
    print('audit-assets exit %d  %s' % (r.returncode, ' | '.join(l.strip() for l in tail)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
