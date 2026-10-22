#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit-docs.py - mechanical consistency checks on the docs, so doc drift fails
a push the way a library defect does.

  python scripts/audit-docs.py            # full report
  python scripts/audit-docs.py --quiet    # failures only, for the hook

Exits 1 on DRIFT. Exits 2 when the check could not run (missing file, bad
parse) - P093: a gate that cannot see its data must not report pass.

WHY THIS EXISTS (2026-10-01)
A whole session was spent correcting docs that had quietly stopped describing
the repo: reel-creation-pipeline.md argued the nasheed picker was unsafe three
patterns after it was fixed; its cost table was a model and a clip length out
of date; animated-reel-scene-prompts.md was headed "not yet built" for a lane
that had shipped 29 reels; AGENTS.md still routed UZ/TJ to browser
SpeechSynthesis. None of it was caught by anything, because nothing looked.

The fix was a rule in CLAUDE.md saying read the repo at session start. That is
exactly the shape P119, P126 and P185 all failed in: a check with no caller.
This script is the caller. It cannot judge prose, so it does not try - it
checks only what is COUNTABLE, where wrong is wrong with no opinion involved.

DELIBERATELY NOT CHECKED: whether a paragraph is true. That needs a reader.
What this buys is that the NUMBERS can never silently disagree again, and the
numbers are what went wrong every time.
"""

import argparse
import datetime
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRACKER  = os.path.join(ROOT, 'reel-tracker.md')
PATTERNS = os.path.join(ROOT, 'fix_patterns.md')
REGISTRY = os.path.join(ROOT, 'assets', 'asset-registry.json')
RETRO    = os.path.join(ROOT, 'reel-retro.md')
HV_ROOT  = os.path.join(os.path.dirname(ROOT), 'hadith-verifier')

fails, warns = [], []
def fail(where, msg): fails.append((where, msg))
def warn(where, msg): warns.append((where, msg))


def read(path):
    try:
        return io.open(path, encoding='utf-8-sig').read()   # P186
    except (IOError, OSError) as e:
        print('FAILED: cannot read %s (%s)' % (path, e))
        sys.exit(2)


# --------------------------------------------------------------- tracker rows

def active_rows(tracker):
    """Every | R### | ... | row in the Active reels table, as a list of cells."""
    rows = []
    for line in tracker.splitlines():
        if not re.match(r'^\|\s*R\d{3}\s*\|', line):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 20:
            warn('tracker', 'row %s has %d columns, expected >=20 - not checked'
                 % (cells[0], len(cells)))
            continue
        rows.append(cells)
    return rows


# Column indices in the Active reels table, by the header's own order.
C_ID, C_DATE, C_HADITH = 0, 1, 2
C_LANG, C_STYLE = 7, 8
C_CLIPS, C_NASHEED = 13, 15


def stat(tracker, label):
    m = re.search(r'^\|\s*%s\s*\|\s*([^|]+?)\s*\|' % re.escape(label),
                  tracker, re.MULTILINE)
    return m.group(1) if m else None


def check_counts(tracker, rows):
    n = len(rows)

    declared = stat(tracker, 'Total reels posted')
    if declared is None:
        fail('tracker', 'no "Total reels posted" row in Production stats')
    elif declared.strip() != str(n):
        fail('tracker', 'Production stats says %s reels; Active reels has %d rows'
             % (declared, n))

    # The highest ID must equal the count, or an ID was skipped or reused.
    ids = sorted(int(r[C_ID][1:]) for r in rows)
    if ids and ids[-1] != n:
        fail('tracker', 'highest reel ID is R%03d but there are %d rows - an ID '
             'was skipped or reused' % (ids[-1], n))
    dupes = set(i for i in ids if ids.count(i) > 1)
    if dupes:
        fail('tracker', 'duplicate reel IDs: %s'
             % ', '.join('R%03d' % i for i in sorted(dupes)))

    for label, style in (('Adults reels', 'adults'), ('Kids reels', 'kids')):
        declared = stat(tracker, label)
        actual = sum(1 for r in rows if r[C_STYLE].strip().lower() == style)
        if declared is None:
            warn('tracker', 'no "%s" row in Production stats' % label)
        elif declared.strip() != str(actual):
            fail('tracker', '%s says %s; the Style column has %d'
                 % (label, declared, actual))

    declared = stat(tracker, 'Hadiths used (unique)')
    actual = len(set(r[C_HADITH] for r in rows))
    if declared is not None and declared.strip() != str(actual):
        fail('tracker', 'Hadiths used (unique) says %s; the Hadith column has %d '
             'distinct values' % (declared, actual))


def check_duplicate_index(tracker, rows):
    """Every hadith that has shipped must appear in the duplicate-check index -
    that index is what the next session reads BEFORE producing, so a hadith
    missing from it is how the same reel gets made twice."""
    try:
        idx = tracker.split('## Duplicate-check index')[1].split('\n---')[0]
    except IndexError:
        fail('tracker', 'no "Duplicate-check index" section')
        return
    for h in sorted(set(r[C_HADITH] for r in rows)):
        num = re.search(r'#(\d+)', h)
        if not num:
            continue
        if not re.search(r'#%s\b' % num.group(1), idx):
            fail('tracker', '%s has shipped reels but is not in the '
                 'duplicate-check index' % h)


def check_nasheed_table(tracker, rows):
    """The usage table must agree with the Active reels table three ways: the
    declared count, the listed reel IDs, and what the reels actually say.

    Forgetting any one of them is the real-world failure. The rotation is
    planned off this table, so a missing reel ID plans a repeat - and the two
    defects this check found on its first run were exactly that, one of them
    four months old (R007 on ramadan-bg) and one from the set shipped the day
    before (R094 on light-of-my-heart-bg)."""
    try:
        sec = tracker.split('### Nasheed usage')[1].split('###')[0]
    except IndexError:
        fail('tracker', 'no "### Nasheed usage" section')
        return

    actual = {}
    for r in rows:
        bed = r[C_NASHEED].strip()
        if bed.endswith('.mp3'):
            actual.setdefault(bed, []).append(r[C_ID].strip())

    seen = set()
    for line in sec.splitlines():
        m = re.match(r'^\|\s*([A-Za-z0-9._-]+\.mp3)\s*\|\s*(\d+)\s*\|'
                     r'\s*([^|]*)\|\s*(.*?)\s*\|?\s*$', line.strip())
        if not m:
            continue
        bed, declared, last, idcell = m.group(1), int(m.group(2)), m.group(3).strip(), m.group(4)
        seen.add(bed)
        used = actual.get(bed, [])

        # A retired bed carries 0 uses and a prose note; its note names the
        # reels it was PULLED from, which are not uses. Nothing to reconcile.
        if declared == 0 and not used:
            continue

        listed = re.findall(r'R\d{3}', idcell)
        if len(listed) != declared:
            fail('tracker', '%s declares %d uses but lists %d reel IDs'
                 % (bed, declared, len(listed)))
        if len(used) != len(listed):
            missing = [x for x in used if x not in listed]
            extra   = [x for x in listed if x not in used]
            detail  = []
            if missing: detail.append('missing ' + ', '.join(missing))
            if extra:   detail.append('lists ' + ', '.join(extra) + ' which do not use it')
            fail('tracker', '%s is used by %d reels but its row lists %d - %s'
                 % (bed, len(used), len(listed), '; '.join(detail)))
        elif used and last and last != used[-1]:
            fail('tracker', '%s says last used %s; the newest reel using it is %s'
                 % (bed, last, used[-1]))

    for bed in sorted(set(actual) - seen):
        fail('tracker', '%s is used by %s but has no row in the Nasheed usage '
             'table' % (bed, ', '.join(actual[bed])))


def check_registry(rows):
    """Assets named in the tracker must exist in the registry the renderer
    gates on. A name here that the registry does not know is a reel that
    cannot be reproduced."""
    try:
        reg = json.load(io.open(REGISTRY, encoding='utf-8-sig'))
    except Exception as e:
        print('FAILED: cannot read the asset registry (%s)' % e)
        sys.exit(2)

    audio  = set(reg.get('audio', {}))
    scenes = set(reg.get('scenes', {}))

    for r in rows:
        rid = r[C_ID].strip()
        bed = r[C_NASHEED].strip()
        if bed.endswith('.mp3') and bed not in audio:
            warn('registry', '%s uses %s, absent from the registry\'s audio'
                 % (rid, bed))
        for clip in [c.strip() for c in r[C_CLIPS].split(',')]:
            if not clip.endswith('.mp4'):
                continue
            if re.match(r'^(kids-|adults-)?.*clip\d+\.mp4$', clip):
                continue              # per-reel mascot clips, never registered
            if clip not in scenes:
                warn('registry', '%s uses scene %s, absent from the registry'
                     % (rid, clip))


def check_pattern_refs():
    """No doc may cite a pattern number above the frontier. Below it and
    missing is almost always an HV pattern - one sequence, two files - so that
    is INFO, not a failure. Above the frontier cannot be anything but invented
    (QA_STANDARDS 10.2)."""
    pat = read(PATTERNS)
    have = set(int(n) for n in re.findall(r'^##\s*PATTERN\s+(\d+)', pat, re.M))
    if not have:
        print('FAILED: no "## PATTERN n" headings in fix_patterns.md')
        sys.exit(2)
    frontier = max(have)

    for name in sorted(os.listdir(ROOT)):
        if not name.endswith('.md') or name == 'fix_patterns.md':
            continue
        text = read(os.path.join(ROOT, name))
        for n in sorted(set(int(x) for x in re.findall(r'\bP(\d{3})\b', text))):
            if n > frontier:
                fail(name, 'cites P%03d, above the frontier P%03d in '
                     'fix_patterns.md - that pattern does not exist' % (n, frontier))
    return frontier


def check_sibling_frontier(frontier):
    """P246's shape, found 2026-10-15: HV's CLAUDE.md cached the shared
    P-frontier as "P186 as of 2026-10-01" and still said so when HR had reached
    P246 - sixty patterns, two weeks.

    The daily doc-drift task was meant to catch exactly this, but that step
    lived in the TASK'S PROMPT as something for the agent to read and compare,
    not here as a check with a return value. Nothing that exits non-zero was
    looking, and the agent's prose went to a session with no notification
    configured, so two weeks of daily reports reached nobody.

    The signature of a stale cache is specific: a P-number ABOVE HV's own top
    pattern but BELOW HR's frontier. HV legitimately cites its own numbers and
    its frozen duplicate's, and those all sit at or under its top. A number in
    the gap can only be a frontier somebody wrote down, and a written-down
    frontier rots by construction. Above HR's frontier is the invented-pattern
    case that check_pattern_refs() already catches for THIS repo's docs but
    never covered the sibling.
    """
    hv_claude = os.path.join(HV_ROOT, 'CLAUDE.md')
    hv_pat = os.path.join(HV_ROOT, 'fix_patterns.md')
    if not (os.path.exists(hv_claude) and os.path.exists(hv_pat)):
        warn('sibling', 'hadith-verifier is not beside this repo - frontier '
                        'cross-check skipped')
        return
    hv_have = set(int(n) for n in
                  re.findall(r'^##\s*PATTERN\s+(\d+)', read(hv_pat), re.M))
    if not hv_have:
        warn('sibling', 'no "## PATTERN n" headings in hadith-verifier/'
                        'fix_patterns.md - frontier cross-check skipped')
        return
    hv_top = max(hv_have)
    where = 'hadith-verifier/CLAUDE.md'
    for n in sorted(set(int(x) for x in
                        re.findall(r'\bP(\d{3})\b', read(hv_claude)))):
        if n > frontier:
            fail(where, 'cites P%03d, above HR\'s frontier P%03d - that pattern '
                        'does not exist' % (n, frontier))
        elif hv_top < n < frontier:
            fail(where, 'cites P%03d, above HV\'s own top pattern P%03d and below '
                        "HR's frontier P%03d. That is a CACHED FRONTIER and it is "
                        'already stale. Point at HR\'s fix_patterns.md tail instead '
                        'of writing a number down.' % (n, hv_top, frontier))


def check_retro(rows):
    """Step 17: the newest tracker row must be covered by a reel-retro.md entry.

    The retro was agreed as a step, and a step with no caller is the exact shape
    P119, P126 and P185 each failed in. This is the caller. It checks COVERAGE
    only - that an entry exists for the newest set - never whether the entry
    says anything useful, which needs a reader.
    """
    text = read(RETRO)
    covered = set()
    for m in re.finditer(r'^##\s+R(\d{3})(?:\s*-\s*R(\d{3}))?\b', text, re.MULTILINE):
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        if hi < lo:
            lo, hi = hi, lo
        covered.update(range(lo, hi + 1))
    if not covered:
        fail('retro', 'reel-retro.md has no ## R### entries - cannot confirm '
                      'coverage of any set')
        return
    ids = [int(r[C_ID][1:]) for r in rows if re.match(r'^R\d{3}$', r[C_ID])]
    if not ids:
        return
    newest = max(ids)
    if newest not in covered:
        fail('retro', 'newest tracker row R%03d has no reel-retro.md entry - '
                      'Step 17, write the retro before the tracker rows'
                      % newest)


def cadence_line(rows):
    """P248: the newest reel row, computed from the table this script already parses.

    The daily doc-drift task worked this out by READING A SLICE of
    reel-tracker.md, under a prompt instruction to tail the file because it is
    large. The Active reels table is near the TOP; a tail lands in the Change
    log. On 2026-10-16 the task reported the newest row as 2026-10-11
    (R122-R125) when R133 was dated 2026-10-15 - while the same email said
    '133 reels', a number only this table can produce. Two contradictory facts
    in one report, and the wrong one was the cadence signal.

    P247 moved the sibling check - HV's cached P-frontier - out of that prompt
    and into this script for exactly this reason, and left this one behind. The
    fix was scoped to the symptom rather than the set, which is P237's and
    P242's shape a third time.
    """
    dated = [r for r in rows if re.match(r'^\d{4}-\d{2}-\d{2}$', r[C_DATE])]
    if not dated:
        warn('tracker', 'no parseable dates in the Active reels table - '
                        'cadence not reported')
        return ''
    newest = max(d[C_DATE] for d in dated)
    ids = [d[C_ID] for d in dated if d[C_DATE] == newest]
    span = ids[0] if len(ids) == 1 else '%s-%s' % (ids[0], ids[-1])
    try:
        y, m, d = (int(x) for x in newest.split('-'))
        age = (datetime.date.today() - datetime.date(y, m, d)).days
    except ValueError:
        return ', newest reel row %s (%s)' % (newest, span)
    return ', newest reel row %s (%s), %d day%s old' % (
        newest, span, age, '' if age == 1 else 's')


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description='Mechanical doc consistency checks.')
    ap.add_argument('--quiet', action='store_true', help='failures only')
    args = ap.parse_args()

    tracker = read(TRACKER)
    rows = active_rows(tracker)
    if not rows:
        print('FAILED: no R### rows found in reel-tracker.md - cannot audit')
        sys.exit(2)

    check_counts(tracker, rows)
    check_duplicate_index(tracker, rows)
    check_nasheed_table(tracker, rows)
    check_registry(rows)
    check_retro(rows)
    frontier = check_pattern_refs()
    check_sibling_frontier(frontier)

    if not args.quiet:
        print('doc audit: %d reels, pattern frontier P%03d%s'
              % (len(rows), frontier, cadence_line(rows)))

    if warns and not args.quiet:
        print('\nWARN  (%d)' % len(warns))
        print('-' * 48)
        for where, msg in warns:
            print('  [%s] %s' % (where, msg))

    if fails:
        print('\nDRIFT  (%d)' % len(fails))
        print('-' * 48)
        for where, msg in fails:
            print('  [%s] %s' % (where, msg))
        print('\nFAILED - the docs and the repo disagree.')
        return 1

    print('\nOK - every counted fact in the docs matches the repo.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
