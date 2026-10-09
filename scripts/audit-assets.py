#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit-assets.py - enforce what the asset registry records.

Every reusable asset carries a classification (what it contains) and an approval
(which lane may use it). This script does not judge assets. It enforces a
judgement a human already wrote down in assets/asset-registry.json.

Two modes:

  --check <file> --lane kids|adults
      Gate for the render scripts. Exit 0 if the asset is registered and
      approved for that lane; exit 1 otherwise. Intended to BLOCK.

  --audit
      Sweep the asset folders and report: files on disk that are not in the
      registry, registry entries whose files are missing, and entries not yet
      verified by a human. Reports only; never blocks.

WHY THIS EXISTS
  Generation-time review cannot catch a defect that entered the library before
  generation. Every background bed was instrumental for months, approved once in
  May and reused across 26 reels; a text auditor would have passed all 26. And
  twice on 2026-08-15 the random picker crossed lanes - a kids hamd onto an
  adults reel, an adults ambience bed onto a kids reel. Both are lookups, not
  judgements, which is exactly what a machine should be doing.

USAGE
  python scripts/audit-assets.py --audit
  python scripts/audit-assets.py --check vocal-hamd-kids-01.mp3 --lane adults
"""

import argparse
import re
import io
import json
import os
import sys

REGISTRY = os.path.join('assets', 'asset-registry.json')

# section -> (folder on disk, file extensions)
SECTIONS = {
    'audio':   (os.path.join('out', 'backgrounds'), ('.mp3',)),
    'mascots': (os.path.join('assets', 'mascot'), ('.png', '.jpg')),
    'scenes':  (os.path.join('out', 'backgrounds', 'new', 'normalized'),
                ('.mp4',)),
}


def load_registry(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except FileNotFoundError:
        print(f'FAILED: registry not found: {path}')
        print('  Run from the repo root.')
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f'FAILED: registry is not valid JSON: {e}')
        sys.exit(2)


def find_entry(reg, name):
    """Look up by bare filename across all sections."""
    base = os.path.basename(name)
    for section, entries in reg.items():
        if section.startswith('_') or section == 'updated':
            continue
        if not isinstance(entries, dict):
            continue
        for key, val in entries.items():
            if os.path.basename(key) == base:
                return section, key, val
    return None, None, None


def cmd_check(reg, name, lane):
    section, key, entry = find_entry(reg, name)
    base = os.path.basename(name)

    if entry is None:
        print(f'BLOCKED: {base} is not in the asset registry.')
        print(f'  Nothing may be used in a reel until a human has classified')
        print(f'  it. Add it to {REGISTRY} with a classification, the lanes it')
        print(f'  is approved for, and why.')
        return 1

    lanes = entry.get('lanes', [])
    if not lanes:
        print(f'BLOCKED: {base} is RETIRED (approved for no lane).')
        print(f'  classification: {entry.get("classification")}')
        print(f'  {entry.get("notes", "")}')
        return 1

    if lane not in lanes:
        print(f'BLOCKED: {base} is not approved for the {lane} lane.')
        print(f'  classification: {entry.get("classification")}')
        print(f'  approved for:   {", ".join(lanes)}')
        print(f'  {entry.get("notes", "")}')
        return 1

    if not entry.get('verified', False):
        print(f'OK (unverified): {base} - approved for {lane}, but no human '
              f'has confirmed the classification yet.')
        print(f'  {entry.get("notes", "")}')
        return 0

    print(f'OK: {base} - {entry.get("classification")}, approved for {lane}.')
    return 0


def cmd_audit(reg):
    width = 66
    print()
    print('=' * width)
    print(f' asset audit   (registry updated: {reg.get("updated", "unknown")})')
    print('=' * width)

    unregistered, missing, unverified = [], [], []

    for section, (folder, exts) in SECTIONS.items():
        entries = reg.get(section, {})

        on_disk = set()
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(exts):
                    on_disk.add(f)
        else:
            print(f'  note: folder not found, skipping: {folder}')

        registered = {os.path.basename(k): (k, v) for k, v in entries.items()}

        for f in sorted(on_disk - set(registered)):
            unregistered.append((section, os.path.join(folder, f)))

        for base, (key, val) in sorted(registered.items()):
            # fall back to the bare filename: registry keys sometimes carry a
            # path prefix that no longer matches where the file sits
            path = os.path.join(folder, key)
            if not os.path.exists(path):
                if base in on_disk:
                    path = os.path.join(folder, base)
                else:
                    missing.append((section, key))
                    continue
            if not val.get('verified', False):
                unverified.append((section, base, val.get('notes', '')))
                        # P141: an asset with lanes:[] whose file is still on disk is the
            # EXPECTED state, not a finding. The gate blocks it by lane at
            # render time (line 90), so its presence in the folder is harmless
            # and its registry entry is the only record of WHY it was retired.
            # Reporting it every run produced a permanent 4-line non-finding —
            # the shape P138 fixed in the Fabric gate: a warning that fires when
            # nothing is wrong teaches the reader to skip the whole report.
            #
            # The comment above ("retired entries live in a subfolder") describes
            # a convention that was never implemented — os.listdir on line 126 is
            # not recursive and nothing checks a _retired/ path. Same shape as
            # P127's dead TEST_PATTERNS. Removed rather than built: moving the
            # files would make them report as MISSING, which is a real alarm
            # state, and would strand the retirement notes.

    if unregistered:
        print()
        print(f'  UNREGISTERED  ({len(unregistered)}) - on disk, not in the')
        print('  registry. The render gate will BLOCK these.')
        for section, path in unregistered:
            print(f'    [{section}] {path}')

    if missing:
        print()
        print(f'  MISSING  ({len(missing)}) - in the registry, not on disk.')
        for section, key in missing:
            print(f'    [{section}] {key}')

    if unverified:
        print()
        print(f'  UNVERIFIED  ({len(unverified)}) - registered and usable, but')
        print('  no human has confirmed the classification.')
        for section, base, note in unverified:
            print(f'    [{section}] {base}')
            if note:
                print(f'        {note[:100]}')

    total = len(unregistered) + len(missing) + len(unverified)
    print()
    print('-' * width)
    if total == 0:
        print('  registry and disk agree; every entry is human-verified.')
    else:
        print(f'  {len(unregistered)} unregistered   '
              f'{len(missing)} missing')
        print(f'  {len(unverified)} unverified')
    print('  audit reports only. --check is the gate that blocks.')
    print('-' * width)
    print()
    return 0
def cmd_list(reg, lane, classification=None):
    """
    P168: print the filenames approved for a lane, one per line, nothing else.
    The render scripts filtered the pool by FILENAME (`ambient-*`, `*-kids-*`)
    while retirement lives in the registry, so a retired asset was still DRAWN
    and then blocked at the gate — killing the render instead of being skipped.
    This is the registry answering "what may I use?" rather than each caller
    re-implementing the rule.

    stdout is machine-readable on purpose: callers split on newlines. NOTHING
    is written to stderr — PowerShell turns native stderr into an ErrorRecord,
    and with $ErrorActionPreference='Stop' in the render scripts that is a
    terminating error. A count line on stderr broke the caller twice.
    """
    section_for = {'audio': 'audio', 'mascots': 'mascots', 'scenes': 'scenes'}
    out = []
    for section, entries in reg.items():
        if section.startswith('_') or section == 'updated':
            continue
        if classification and section != section_for.get(classification, classification):
            continue
        if not isinstance(entries, dict):
            continue
        for name, meta in entries.items():
            if not isinstance(meta, dict):
                continue
            if lane in (meta.get('lanes') or []):
                out.append(name)
    for name in sorted(out):
        print(name)

    return 0

# Collection -> the letter a scene clip's name must start with. The
# convention was never written down until P197, and it was inferred BACKWARDS
# from a misnamed set before that: b2628 carries a Bukhari prefix on a Sahih
# Muslim hadith, and Bukhari #2628 is a real and different hadith about gifts.
# Four shipped reels reference it.
COLLECTION_LETTER = {
    'sahih al-bukhari': 'b',
    'sahih muslim': 'm',
    'sunan abu dawud': 'ad',
    'jami at-tirmidhi': 't',
    'sunan ibn majah': 'ij',
    'musnad ahmad': 'ah',
}

CLIP_NAME = re.compile(r'^([a-z]+)(\d+)-')


def cmd_names(tracker):
    """Reconcile every scene clip name against the hadith it was used for.

    audit-assets --audit enforces that a clip is REGISTERED and approved for
    the lane, which is what P117 built it for. It has no opinion about whether
    the NAME matches the narration. The tracker holds the hadith and the clip
    names side by side on every row, so the reconciliation is mechanical - and
    it is the check that would have caught b2628 at the time instead of six
    sets later.
    """
    try:
        text = io.open(tracker, encoding='utf-8-sig').read()
    except OSError as e:
        print('FAILED: cannot read %s (%s)' % (tracker, e))
        return 2

    rows = [l for l in text.split('\n') if l.startswith('|')]
    header = None
    for l in rows:
        cells = [c.strip() for c in l.split('|')]
        if 'Reel ID' in cells and 'Bg Clips Used' in cells:
            header = cells
            break
    if not header:
        print('FAILED: no Active reels header in %s' % tracker)
        return 2
    i_id = header.index('Reel ID')
    i_hadith = header.index('Hadith')
    i_clips = header.index('Bg Clips Used')

    findings = {}
    reuse = {}
    checked = 0
    for l in rows:
        cells = [c.strip() for c in l.split('|')]
        if len(cells) <= max(i_id, i_hadith, i_clips):
            continue
        rid = cells[i_id]
        if not re.match(r'^R\d+$', rid):
            continue
        m = re.match(r'^(.*?)\s*#\s*(\d+)', cells[i_hadith])
        if not m:
            continue
        want_letter = COLLECTION_LETTER.get(m.group(1).strip().lower())
        want_num = m.group(2)
        if not want_letter:
            continue
        for clip in [c.strip() for c in cells[i_clips].split(',') if c.strip()]:
            cm = CLIP_NAME.match(clip)
            if not cm:
                continue  # kaaba.mp4, makka-tower.mp4 and friends are generic
            checked += 1
            got_letter, got_num = cm.group(1), cm.group(2)
            if got_letter == want_letter and got_num == want_num:
                continue
            key = (clip, '%s #%s' % (m.group(1).strip(), want_num))
            # Reuse is intended: a scene set may carry a later reel for a
            # different hadith, and the tracker's own rule is only 'not
            # within three sets'. The discriminator is the NUMBER. Same
            # number with the wrong collection letter is a misnaming - the
            # set was built for this hadith and labelled with another
            # collection. A different number is the set being reused.
            if got_num == want_num:
                findings.setdefault(key, []).append(rid)
            else:
                reuse.setdefault(key, []).append(rid)

    width = 66
    print()
    print('=' * width)
    print(' clip-name audit - %d clip references across the tracker' % checked)
    print('=' * width)
    if not findings:
        print('  no misnamed clips: every clip built for a hadith carries that')
        print('  hadith\'s collection letter.')
    for (clip, hadith), reels in sorted(findings.items()):
        cm = CLIP_NAME.match(clip)
        implied = [k for k, v in COLLECTION_LETTER.items() if v == cm.group(1)]
        print()
        print('  [MISMATCH] %s' % clip)
        print('    used for : %s' % hadith)
        print('    name says: %s #%s' % (
              implied[0].title() if implied else 'unknown prefix %r' % cm.group(1),
              cm.group(2)))
        print('    reels    : %s' % ', '.join(sorted(set(reels))))
    if reuse:
        print()
        print('  %d clip(s) reused on a different hadith - expected, not a' % len(reuse))
        print('  defect; the set rule is only not-within-three-sets:')
        for (clip, hadith), reels in sorted(reuse.items()):
            print('    %-26s on %-24s (%s)'
                  % (clip, hadith, ', '.join(sorted(set(reels)))))
    print()
    print('-' * width)
    print('  %d misnamed clip(s), %d reused' % (len(findings), len(reuse)))
    print('  Reports only. A name that points at a different narration is')
    print('  wrong in the registry permanently, across every reel using it.')
    print('-' * width)
    print()
    return 0


def main():
    ap = argparse.ArgumentParser(
        description='Enforce the asset registry.')
    ap.add_argument('--registry', default=REGISTRY)
    ap.add_argument('--check', metavar='FILE',
                    help='assert one asset is approved for a lane')
    ap.add_argument('--lane', choices=['kids', 'adults'],
                    help='required with --check')
    ap.add_argument('--audit', action='store_true',
                    help='sweep the asset folders and report')
    ap.add_argument('--list', action='store_true',
                    help='print filenames approved for --lane, one per line')
    ap.add_argument('--section', choices=['audio', 'mascots', 'scenes'],
                    help='restrict --list to one section')
    ap.add_argument('--names', action='store_true',
                    help='reconcile scene clip names against the tracker')
    ap.add_argument('--tracker', default='reel-tracker.md',
                    help='tracker to read for --names')
    args = ap.parse_args()

    if args.names:
        return cmd_names(args.tracker)

    if not args.check and not args.audit and not args.list:
        ap.error('give --audit, --names, --list --lane LANE, or --check FILE --lane LANE')
    if args.check and not args.lane:
        ap.error('--check requires --lane')
    if args.list and not args.lane:
        ap.error('--list requires --lane')

    reg = load_registry(args.registry)

    if args.check:
        return cmd_check(reg, args.check, args.lane)
    if args.list:
        return cmd_list(reg, args.lane, args.section)
    return cmd_audit(reg)


if __name__ == '__main__':
    sys.exit(main())