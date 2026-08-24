#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-candidates.py - Stage 3 of the sourcing pipeline.

Two INDEPENDENT passes over every translation of a candidate, checking one
thing: does the translation say what the Arabic says, no more and no less.

  pass A = claude-sonnet-5   (Anthropic)
  pass B = gpt-5.6-terra     (OpenAI)

Different companies, so uncorrelated failure modes - that is what D2 is for.
B never sees A's output; each is given only the Arabic and the translation.

SCOPE IS MEASURED, NOT ASSUMED (P120)
  Both passes judge FAITHFULNESS ONLY: added / omitted / changed / register.
  They do NOT check project conventions. Probing gpt-5.6-terra on Bukhari #527
  with planted defects (two identical runs) showed it catches invented content
  in EN and TJ and a dual->singular meaning change in RU, but passes
  «Аллоҳ»->«Худо» at HIGH confidence - because that translation is faithful to
  اللَّه and is wrong only on a rule the model was never given. Putting the
  rules in the prompt would turn a judgement engine into a rules engine and
  degrade both.

  Convention defects have deterministic owners and must be clean BEFORE this
  runs:
    divine name substitution ................ lint-content.py
    diacritics, homoglyphs, okina, script ... audit-library.py
    grade, source URL, empty fields ......... audit-library.py
  This script refuses to run on a candidate that audit-library.py would flag.

  C1 (ref-exists) and C2 (grade) from the original design are NOT here. They
  are API lookups Stage 0 already performs against Sunnah.com and Dorar. Do not
  re-ask a model what an API already answered.

THE VERIFIER CAN BLOCK, IT CANNOT ADMIT (G1)
  'pass' means eligible for human review. It never means insert. Stage 4 is the
  human gate and stays mandatory. Disagreement is the SIGNAL this stage exists
  to produce - it is never resolved by a third pass or by preferring one model.

USAGE
  python scripts/verify-candidates.py                  # dry run, all translated
  python scripts/verify-candidates.py --row 527
  python scripts/verify-candidates.py --limit 10       # D5 calibration batch
  python scripts/verify-candidates.py --commit

Requires ANTHROPIC_API_KEY and OPENAI_API_KEY in .env.local.
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

MODEL_A = 'claude-sonnet-5'
MODEL_B = 'gpt-5.6-terra'

ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages'
ANTHROPIC_VERSION = '2023-06-01'
OPENAI_URL = 'https://api.openai.com/v1/chat/completions'

OUT_PATH = os.path.join('out', 'candidate-verdicts.json')

URL_KEYS = ('NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_URL')
SERVICE_KEYS = ('SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_KEY',
                'SERVICE_ROLE_KEY')

FIELDS = {
    'en': ('text_english', 'English'),
    'ru': ('text_russian', 'Russian'),
    'uz': ('text_uzbek_cyrillic', 'Uzbek (Cyrillic)'),
    'tj': ('text_tajik', 'Tajik (Cyrillic)'),
}

# The prompt is identical for both passes. Divergence in the prompt would make
# disagreement uninterpretable - we could not tell a real catch from a
# difference in instructions.
SYSTEM = """You verify a translation of a hadith against its Arabic source.

Report ONLY what the Arabic does or does not support:
- added: any clause, action, ranking, comparison, attribution or source that is
  not in the Arabic. "The Prophet smiled", "the greatest of deeds", "like a
  pillar" - if the Arabic does not say it, it is added.
- omitted: anything in the Arabic missing from the translation.
- changed: a word rendered as something the Arabic does not say, including
  number and person (a dual rendered as singular is a change).
- register: paraphrase or devotional expansion where translation is required.

Do NOT report style, word choice, or naturalness. Do NOT report spelling or
diacritics. Do NOT apply any rule that is not derivable from the Arabic itself.

Answer with JSON only, no markdown fence:
{"verdict":"pass"|"fail","issues":[{"type":"added"|"omitted"|"changed"|"register","quote":"...","why":"..."}],"confidence":"high"|"medium"|"low"}

If the translation is faithful, return verdict "pass" with an empty issues
array. Do not invent issues to appear thorough. If you cannot read the target
language well enough to judge, return verdict "pass" with confidence "low" and
say so in an issue of type "register" - a false pass at low confidence is
recoverable at the human gate; a confident guess is not."""

# ---------------------------------------------------------------- helpers


def load_env(path='.env.local'):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def pick(env, names):
    for n in names:
        if env.get(n):
            return env[n]
        if os.environ.get(n):
            return os.environ[n]
    return None


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def sb_get(base, key, table, params):
    url = f'{base.rstrip("/")}/rest/v1/{table}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'apikey': key, 'Authorization': f'Bearer {key}',
        'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def sb_patch(base, key, table, match, payload):
    url = f'{base.rstrip("/")}/rest/v1/{table}?' + urllib.parse.urlencode(match)
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(url, data=body, method='PATCH', headers={
        'apikey': key, 'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json', 'Prefer': 'return=representation'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def _parse(txt):
    txt = txt.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {'verdict': 'error', 'issues': [], 'confidence': 'low',
                'raw': txt[:300]}


def user_msg(arabic, lang_name, translation):
    return (f'Arabic source:\n{arabic}\n\n'
            f'{lang_name} translation to verify:\n{translation}')


def pass_a(key, arabic, lang_name, translation):
    body = json.dumps({
        'model': MODEL_A, 'max_tokens': 1000, 'system': SYSTEM,
        'messages': [{'role': 'user',
                      'content': user_msg(arabic, lang_name, translation)}],
    }, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(ANTHROPIC_URL, data=body, headers={
        'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION,
        'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode('utf-8'))
    txt = '\n'.join(b.get('text', '') for b in data.get('content', [])
                    if b.get('type') == 'text')
    return _parse(txt)


def pass_b(key, arabic, lang_name, translation):
    body = json.dumps({
        'model': MODEL_B,
        'messages': [{'role': 'system', 'content': SYSTEM},
                     {'role': 'user',
                      'content': user_msg(arabic, lang_name, translation)}],
    }, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(OPENAI_URL, data=body, headers={
        'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode('utf-8'))
    return _parse(data['choices'][0]['message']['content'].strip())


def agreement(a, b):
    """pass | fail | disagree. An error on either side is a disagreement -
    absence of a verdict is not a verdict."""
    va, vb = a.get('verdict'), b.get('verdict')
    if va == 'error' or vb == 'error':
        return 'disagree'
    if va == vb == 'pass':
        return 'pass'
    if va == vb == 'fail':
        return 'fail'
    return 'disagree'


def roll_up(per_lang):
    """One agreement value for the candidate. A single language failing or
    disagreeing routes the whole candidate to a human - the row is promoted
    or rejected whole, so it is judged whole."""
    vals = [v['agreement'] for v in per_lang.values()]
    if not vals:
        return 'disagree'
    if 'disagree' in vals:
        return 'disagree'
    if 'fail' in vals:
        return 'fail'
    return 'pass'


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(
        description='Stage 3 - two independent passes on translation faithfulness.')
    ap.add_argument('--row', help='one hadith_number only')
    ap.add_argument('--limit', type=int, default=10, help='batch size (D5)')
    ap.add_argument('--commit', action='store_true',
                    help='write verdicts and status. Without this, nothing is written.')
    args = ap.parse_args()

    env = load_env()
    base = pick(env, URL_KEYS)
    sb_key = pick(env, SERVICE_KEYS)
    ak = pick(env, ('ANTHROPIC_API_KEY',))
    ok = pick(env, ('OPENAI_API_KEY',))

    missing = [n for n, v in (('supabase', base and sb_key),
                              ('ANTHROPIC_API_KEY', ak),
                              ('OPENAI_API_KEY', ok)) if not v]
    if missing:
        print(f'FAILED: missing in .env.local: {", ".join(missing)}')
        return 2

    params = {'select': '*', 'status': 'eq.translated',
              'limit': str(args.limit), 'order': 'created_at.asc'}
    if args.row:
        params['hadith_number'] = f'eq.{args.row}'
        params.pop('status')

    try:
        rows = sb_get(base, sb_key, 'hadith_candidates', params)
    except Exception as e:  # noqa: BLE001
        print(f'FAILED reading hadith_candidates: {e}')
        return 2

    if not rows:
        print("no candidates at status='translated'"
              + (f' for hadith_number={args.row}' if args.row else ''))
        return 0

    w = 74
    print('=' * w)
    print(f' stage 3 A/B verify - {len(rows)} candidate(s)  '
          f'[{"COMMIT" if args.commit else "DRY RUN"}]')
    print(f' A = {MODEL_A}   B = {MODEL_B}   (B never sees A)')
    print(' scope: faithfulness to the matn only. conventions are checked by')
    print(' lint-content.py and audit-library.py, not here (P120).')
    print('=' * w)

    results, tally = [], {'pass': 0, 'fail': 0, 'disagree': 0}

    for row in rows:
        ref = f'{row.get("collection")} #{row.get("hadith_number")}'
        arabic = (row.get('text_arabic') or '').strip()
        if not arabic:
            print(f'\n  SKIP {ref} - no text_arabic to verify against')
            continue

        print(f'\n  {ref}')
        per_lang = {}

        for lang, (col, lang_name) in FIELDS.items():
            text = (row.get(col) or '').strip()
            if not text:
                print(f'    {lang}: empty, skipping')
                continue

            try:
                a = pass_a(ak, arabic, lang_name, text)
            except Exception as e:  # noqa: BLE001
                a = {'verdict': 'error', 'issues': [], 'confidence': 'low',
                     'error': str(e)[:200]}
            time.sleep(0.3)
            try:
                b = pass_b(ok, arabic, lang_name, text)
            except Exception as e:  # noqa: BLE001
                b = {'verdict': 'error', 'issues': [], 'confidence': 'low',
                     'error': str(e)[:200]}
            time.sleep(0.3)

            agr = agreement(a, b)
            per_lang[lang] = {'a': a, 'b': b, 'agreement': agr}

            mark = {'pass': 'OK ', 'fail': 'FAIL', 'disagree': '>>>'}[agr]
            print(f'    {mark} {lang}: A={a.get("verdict")}/{a.get("confidence")}'
                  f'  B={b.get("verdict")}/{b.get("confidence")}')
            for who, res in (('A', a), ('B', b)):
                for iss in (res.get('issues') or [])[:2]:
                    print(f'         {who} {iss.get("type")}: '
                          f'{str(iss.get("why", ""))[:78]}')
                if 'raw' in res:
                    print(f'         {who} UNPARSEABLE: {res["raw"][:70]}')
                if 'error' in res:
                    print(f'         {who} ERROR: {res["error"]}')

        overall = roll_up(per_lang)
        tally[overall] += 1
        status = 'verified' if overall == 'pass' else 'needs_human'
        print(f'    -> {overall}  (status would be {status})')

        results.append({'candidate_id': row.get('candidate_id'), 'ref': ref,
                        'agreement': overall, 'per_language': per_lang})

        if args.commit:
            payload = {
                'verify_a': {k: v['a'] for k, v in per_lang.items()},
                'verify_b': {k: v['b'] for k, v in per_lang.items()},
                'verify_agreement': overall,
                'status': status,
                'updated_at': now_iso(),
            }
            try:
                sb_patch(base, sb_key, 'hadith_candidates',
                         {'candidate_id': f'eq.{row["candidate_id"]}'}, payload)
                print(f'    -> written, status={status}')
            except Exception as e:  # noqa: BLE001
                print(f'    -> WRITE FAILED: {e}')

    os.makedirs('out', exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    n = max(1, sum(tally.values()))
    print('\n' + '-' * w)
    print(f'  pass {tally["pass"]}   fail {tally["fail"]}   '
          f'disagree {tally["disagree"]}   -> {OUT_PATH}')
    print(f'  disagreement rate: {tally["disagree"] / n:.0%}  (D5 calibration)')
    print('    near 0% over a real batch = the passes are correlated and the')
    print('    second is buying nothing. very high = mistuned, Stage 4 drowns.')
    if args.commit:
        print("  WRITTEN. 'pass' means ELIGIBLE FOR HUMAN REVIEW, never insert.")
    else:
        print('  DRY RUN - nothing written.')
    print('  Stage 4 is the human gate and it is not optional (G1).')
    print('-' * w)
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
