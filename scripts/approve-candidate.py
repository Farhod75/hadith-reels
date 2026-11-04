#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
approve-candidate.py - record the operator's Stage 4 decision on ONE candidate, by id.

Replaces the per-set out/approve_<n>.py scripts (automation, OPEN_ITEMS item 2, 2026-11-03).
Stage 4 is the human gate (sourcing-pipeline-design.md, G1): this script does not decide - it
writes what the operator decided, with his words, and only onto the row he decided about.

    python scripts/approve-candidate.py --id 2c978c61-... --number 2749 \\
        --note "если аб проверки и преводы прошли проверку, да"            # dry run
    ... --commit                                                          # writes

Writes status (approved / rejected), reviewed_by, reviewed_at, review_action and review_reason
(the operator's words). Refuses unless the row exists, its hadith_number is the one named, and -
for an approval - its status is 'verified' (both A/B passes, Stage 3). A row already approved,
rejected or promoted is never touched. Next step after an approval:
    python scripts/promote-candidates.py --show --tags <a,b,c>
"""
import argparse
import datetime as dt
import io
import json
import os
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TERMINAL = ('approved', 'rejected', 'promoted')


def decide(row, number, action):
    """None when the write may go ahead, else the reason it may not."""
    if row is None:
        return 'no candidate with that id'
    if str(row.get('hadith_number')) != str(number):
        return 'the row is #%s, not #%s - nothing written' % (row.get('hadith_number'), number)
    st = row.get('status')
    if st in TERMINAL:
        return 'the row is already %s' % st
    if action == 'approve' and st != 'verified':
        return "status is %r - only a 'verified' row (A/B passed, Stage 3) can be approved" % st
    return None


def patch_for(action, note, reviewer, now=None):
    return {'status': 'approved' if action == 'approve' else 'rejected',
            'reviewed_by': reviewer,
            'reviewed_at': (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec='seconds'),
            'review_action': action,
            'review_reason': note}


def _env():
    env = {}
    for line in io.open(os.path.join(REPO, '.env.local'), encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    url = (env.get('NEXT_PUBLIC_SUPABASE_URL') or env.get('SUPABASE_URL') or '').rstrip('/')
    return url, env['SUPABASE_SERVICE_ROLE_KEY']


def main(argv=None):
    ap = argparse.ArgumentParser(description='Record the operator\'s Stage 4 decision on one candidate.')
    ap.add_argument('--id', required=True, help='candidate_id')
    ap.add_argument('--number', required=True, help='the hadith number the operator approved - a guard')
    ap.add_argument('--action', choices=('approve', 'reject'), default='approve')
    ap.add_argument('--note', required=True, help="the operator's words, verbatim, and when")
    ap.add_argument('--reviewer', default='farhod')
    ap.add_argument('--commit', action='store_true')
    args = ap.parse_args(argv)

    url, key = _env()
    H = {'apikey': key, 'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
         'Prefer': 'return=representation'}
    flt = urllib.parse.urlencode({'candidate_id': 'eq.' + args.id})
    rows = json.loads(urllib.request.urlopen(urllib.request.Request(
        url + '/rest/v1/hadith_candidates?' + flt + '&select=candidate_id,collection,hadith_number,status,verify_agreement',
        headers=H), timeout=30).read().decode())
    row = rows[0] if len(rows) == 1 else None
    why = decide(row, args.number, args.action)
    print('candidate %s: %s' % (args.id, json.dumps(row, ensure_ascii=False)))
    if why:
        print('REFUSED: ' + why)
        return 1
    patch = patch_for(args.action, args.note, args.reviewer)
    print('would write: ' + json.dumps(patch, ensure_ascii=False))
    if not args.commit:
        print('DRY RUN - add --commit.')
        return 0
    out = json.loads(urllib.request.urlopen(urllib.request.Request(
        url + '/rest/v1/hadith_candidates?' + flt, data=json.dumps(patch).encode('utf-8'), method='PATCH',
        headers=H), timeout=30).read().decode())
    if len(out) != 1 or out[0].get('status') != patch['status']:
        print('FAILED: PATCH touched %d rows' % len(out))
        return 1
    print('WRITTEN: status=%s' % out[0]['status'])
    if args.action == 'approve':
        print('next: python scripts/promote-candidates.py --show --tags <a,b,c>')
    return 0


if __name__ == '__main__':
    sys.exit(main())
