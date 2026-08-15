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

    unregistered, missing, unverified, retired_present = [], [], [], []

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
            # retired entries live in a subfolder; check there too
            path = os.path.join(folder, key)
            if not os.path.exists(path):
                if base in on_disk:
                    path = os.path.join(folder, base)
                else:
                    missing.append((section, key))
                    continue
            if not val.get('verified', False):
                unverified.append((section, base, val.get('notes', '')))
            if not val.get('lanes') and base in on_disk:
                retired_present.append((section, base))

    if unregistered:
        print()
        print(f'  UNREGISTERED  ({len(unregistered)}) - on disk, not in the')
        print('  registry. The render gate will BLOCK these.')
        for section, path in unregistered:
            print(f'    [{section}] {path}')

    if retired_present:
        print()
        print(f'  RETIRED BUT REACHABLE  ({len(retired_present)}) - approved')
        print('  for no lane, yet sitting where the picker can find them.')
        for section, base in retired_present:
            print(f'    [{section}] {base}')

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

    total = len(unregistered) + len(missing) + len(unverified) + \
        len(retired_present)
    print()
    print('-' * width)
    if total == 0:
        print('  registry and disk agree; every entry is human-verified.')
    else:
        print(f'  {len(unregistered)} unregistered   '
              f'{len(retired_present)} retired-but-reachable')
        print(f'  {len(missing)} missing        '
              f'{len(unverified)} unverified')
    print('  audit reports only. --check is the gate that blocks.')
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
    args = ap.parse_args()

    if not args.check and not args.audit:
        ap.error('give --audit or --check FILE --lane LANE')
    if args.check and not args.lane:
        ap.error('--check requires --lane')

    reg = load_registry(args.registry)

    if args.check:
        return cmd_check(reg, args.check, args.lane)
    return cmd_audit(reg)


if __name__ == '__main__':
    sys.exit(main())