#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-candidates.py - Stage 3 of the sourcing pipeline.

Two INDEPENDENT passes over every translation of a candidate, checking one
thing: does the translation say what the Arabic says, no more and no less.

  pass A = claude-sonnet-5   (Anthropic)
  pass B = gpt-6.1-sol       (OpenAI)

Different companies, so uncorrelated failure modes - that is what D2 is for.
B never sees A's output; each is given only the Arabic and the translation.

SCOPE IS MEASURED, NOT ASSUMED (P120)
  Both passes judge FAITHFULNESS ONLY: added / omitted / changed / register.
  They do NOT check project conventions. Probing on Bukhari #527 with planted
  defects showed every candidate model catches invented content in EN and TJ
  and a dual->singular meaning change in RU, but passes «Аллоҳ»->«Худо» at
  HIGH confidence - because that translation is faithful to اللَّه and is wrong
  only on a rule the model was never given. Putting the rules in the prompt
  would turn a judgement engine into a rules engine and degrade both.

  2026-10-18, P275: re-probed with FOUR runs per model across four candidates.
  The «Худо» result above held for all of them and is not a defect in any of
  them - it is this scope boundary working. What separated them was noise and
  true-positive reach: terra false-failed CLEAN Russian in 1 run of 4 and never
  once named the lost U+04E3 in the Tajik case; gpt-6.1-sol and gpt-6-astra
  false-failed nothing in 4 runs and named it 4/4. gpt-6-luna false-failed
  clean Russian in 4 of 4 and is disqualified. B moved terra -> gpt-6.1-sol on
  that basis. One run cannot show any of this (P272); run four.

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
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# P264: where translate-candidates.py writes its proposals.
PROPOSED_PATH = os.path.join('out', 'candidate-translations.json')

MODEL_A = 'claude-sonnet-5'
MODEL_B = 'gpt-6.1-sol'

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


# P223: a momentary provider failure used to discard a whole row. `incomplete`
# is per-language and rolls up, so ONE transient 429 on one language threw away
# that row's other seven calls - both passes, already paid for - and the row
# came back unchecked. 5 scattered 429s cost 3 of 5 rows on the first funded
# run. Retry what can succeed on another attempt; never retry what cannot.
RETRY_ATTEMPTS = 4
RETRY_WAITS = (2, 5, 12)

# The balance being empty is not a burst. Retrying spends wall-clock and
# changes nothing, and it is the one 429 that needs a human, not a backoff.
PERMANENT_429 = ('insufficient_quota', 'credit_balance_exhausted')


def _transient(exc):
    """True when another attempt could plausibly succeed."""
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 429:
            body = getattr(exc, 'body_text', '') or ''
            return not any(p in body for p in PERMANENT_429)
        return exc.code in (500, 502, 503, 504, 529)
    return isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError,
                            http.client.IncompleteRead, http.client.BadStatusLine))


def _post(req, timeout, label=''):
    """POST with bounded retry. Raises with the response BODY, not just the
    status line - 'HTTP Error 429: Too Many Requests' cost a session the
    distinction between an empty balance and a burst, which are the same code
    and opposite problems."""
    for attempt in range(RETRY_ATTEMPTS):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    exc.body_text = exc.read().decode('utf-8', 'replace')
                except Exception:  # noqa: BLE001
                    exc.body_text = ''
            last = attempt == RETRY_ATTEMPTS - 1
            if last or not _transient(exc):
                if isinstance(exc, urllib.error.HTTPError):
                    detail = (getattr(exc, 'body_text', '') or '')[:220]
                    raise RuntimeError(
                        f'HTTP {exc.code}: {" ".join(detail.split())}') from exc
                raise
            wait = RETRY_WAITS[min(attempt, len(RETRY_WAITS) - 1)]
            if isinstance(exc, urllib.error.HTTPError) and exc.headers:
                ra = exc.headers.get('retry-after')
                if ra:
                    try:
                        wait = max(wait, min(int(float(ra)), 30))
                    except ValueError:
                        pass
            print(f'         {label}transient ({type(exc).__name__}), '
                  f'retry {attempt + 1}/{RETRY_ATTEMPTS - 1} in {wait}s')
            time.sleep(wait)


def pass_a(key, arabic, lang_name, translation):
    body = json.dumps({
        # P152: 1000 predates thinking models and predates matn lengths like
        # an-Nasai #463, which quadrupled when its continuation was restored.
        # A returned JSON truncated mid-string four times in one session and
        # each truncation surfaced as UNPARSEABLE -> error -> disagree.
        'model': MODEL_A, 'max_tokens': 3000, 'system': SYSTEM,
        'messages': [{'role': 'user',
                      'content': user_msg(arabic, lang_name, translation)}],
    }, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(ANTHROPIC_URL, data=body, headers={
        'x-api-key': key, 'anthropic-version': ANTHROPIC_VERSION,
        'Content-Type': 'application/json'})
    data = _post(req, 120)
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
    data = _post(req, 120)
    return _parse(data['choices'][0]['message']['content'].strip())


def agreement(a, b):
    """pass | fail | disagree | incomplete.

    P152: an error USED to be a disagreement, on the reasoning that absence of
    a verdict is not a verdict and a human should look. Conservative, and wrong
    in practice. Four transport failures in one session — two SSL resets from
    B, two truncated responses from A — each routed a row to the human gate
    with nothing to adjudicate, and each counted toward the disagreement rate
    the script prints for D5 calibration. A gate that reports contested when
    nothing was checked is noise, and noise is what teaches an operator to skim
    the report (P138).

    `incomplete` says the true thing: this was not checked. It is not a verdict
    and does not pretend to be one.
    """
    va, vb = a.get('verdict'), b.get('verdict')
    if va == 'error' or vb == 'error':
        return 'incomplete'
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
        return 'incomplete'
    # P152: a real verdict outranks a missing one — a fail or a disagreement in
    # any language still routes the row to a human, whether or not another
    # language failed to be checked. Only when nothing worse happened does an
    # unchecked language decide the outcome, and then it says so.
    if 'disagree' in vals:
        return 'disagree'
    if 'fail' in vals:
        return 'fail'
    if 'incomplete' in vals:
        return 'incomplete'
    return 'pass'


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(
        description='Stage 3 - two independent passes on translation faithfulness.')
    ap.add_argument('--row', help='one hadith_number only')
    ap.add_argument('--limit', type=int, default=10, help='batch size (D5)')
    ap.add_argument('--commit', action='store_true',
                    help='write verdicts and status. Without this, nothing is written.')
    ap.add_argument('--library', action='store_true',
                    help='verify rows in hadith_library instead of candidates '
                    '(P151: for rows re-translated after a matn correction)')
    ap.add_argument('--from-json', dest='from_json', metavar='PATH',
                    nargs='?', const=PROPOSED_PATH,
                    help='P264: score the PROPOSED translations in this file '
                    'against the matn WITHOUT writing them to the row first. '
                    f'Defaults to {PROPOSED_PATH}. Refuses --commit.')
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

        # P151: a matn correction re-translates a row that is already in
    # hadith_library and will never re-enter the candidate flow.
    table = 'hadith_library' if args.library else 'hadith_candidates'
    if args.from_json:
        # P264: this script read only from the DATABASE, so the only way to
        # Stage-3 a library re-translation was to write it to the live row
        # first. A shipped row had to pass through an unverified state to be
        # checked, and a bad verdict left it worse than before with no stored
        # previous value to restore. #6009 is the row that proved the cost.
        # This scores the PROPOSED text and touches nothing.
        if args.commit:
            print('  --from-json scores proposed text; there is no row to '
                  'write to. Drop --commit.')
            return 2
        try:
            with open(args.from_json, encoding='utf-8') as fh:
                proposals = json.load(fh)
        except FileNotFoundError:
            print(f'  not found: {args.from_json}'
                  ' - run a translate dry run first')
            return 1
        rows = []
        for p in proposals:
            coll, _, num = (p.get('ref') or '').rpartition('#')
            if args.row and num.strip() != str(args.row):
                continue
            row = {'collection': coll.strip(), 'hadith_number': num.strip(),
                   'text_arabic': p.get('text_arabic')}
            row.update(p.get('proposed') or {})
            rows.append(row)
        if not rows:
            print(f'  nothing to score in {args.from_json}'
                  + (f' for hadith_number={args.row}' if args.row else ''))
            return 0
    elif args.library:
        params = {'select': '*', 'limit': str(args.limit),
                  'order': 'hadith_number.asc'}
        if args.row:
            params['hadith_number'] = f'eq.{args.row}'
        else:
            params['matn_verified_at'] = 'is.null'
    else:
        params = {'select': '*', 'status': 'eq.translated',
                  'limit': str(args.limit), 'order': 'created_at.asc'}
        if args.row:
            params['hadith_number'] = f'eq.{args.row}'
            params.pop('status')
    if not args.from_json:
        try:
            rows = sb_get(base, sb_key, table, params)
        except Exception as e:  # noqa: BLE001
            print(f'FAILED reading {table}: {e}')
            return 2

    if not rows:
        print("no candidates at status='translated'"
              + (f' for hadith_number={args.row}' if args.row else ''))
        return 0

    w = 74
    print('=' * w)
    print(f' stage 3 A/B verify - {len(rows)} candidate(s)  '
          f'[{"COMMIT" if args.commit else "DRY RUN"}]'
          + (f'  <- {args.from_json} (nothing written)' if args.from_json else ''))
    print(f' A = {MODEL_A}   B = {MODEL_B}   (B never sees A)')
    print(' scope: faithfulness to the matn only. conventions are checked by')
    print(' lint-content.py and audit-library.py, not here (P120).')
    print('=' * w)

    results, tally = [], {'pass': 0, 'fail': 0, 'disagree': 0, 'incomplete': 0}

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

            # P222: agreement() has returned FOUR values since P152 taught it
            # 'incomplete' - its own docstring says so. This renderer knew
            # three and raised KeyError on the first row of the first real
            # run, AFTER both paid passes had completed, so that spend was
            # thrown away. P152 updated the roll-up and the status map and
            # missed the one dict that prints the value. .get() keeps a
            # display string from ever ending a paid run again.
            mark = {'pass': 'OK ', 'fail': 'FAIL', 'disagree': '>>>',
                    'incomplete': 'n/a'}.get(agr, f'?{agr[:2]}')
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
        # P152: an incomplete row was not checked — it does not need a human,
        # it needs re-running. Marking it needs_human sends someone to
        # adjudicate a verdict that was never produced.
        status = ('verified' if overall == 'pass'
                  else 'incomplete' if overall == 'incomplete'
                  else 'needs_human')
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
            if args.library:
                # P151: REPORT ONLY on library rows. Deliberate, not an
                # omission. matn_verified_at has meant "a human read this
                # against a source" for every row carrying it; letting a model
                # pass set it would silently change what the column means and
                # make the hand-read rows indistinguishable from machine-passed
                # ones. hadith_library also has no verify_a / verify_b /
                # verify_agreement / status / updated_at columns - a write here
                # would 400 on all five. The human sets the timestamp, which is
                # what this script's own footer says: the human gate is Stage 4.
                print(f'    -> agreement={overall}, NOT written '
                      f'(library rows are report-only; set matn_verified_at '
                      f'by hand after reading)')
            else:
                try:
                    sb_patch(base, sb_key, table,
                             {'candidate_id': f'eq.{row["candidate_id"]}'}, payload)
                    print(f'    -> written, status={status}')
                except Exception as e:  # noqa: BLE001
                    print(f'    -> WRITE FAILED: {e}')

    os.makedirs('out', exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    # P152: the calibration rate measures the two passes against EACH OTHER, so
    # rows nobody checked cannot be in the denominator. Counting transport
    # failures as disagreements made the rate meaningless in exactly the
    # sessions where it mattered.
    adjudicated = tally['pass'] + tally['fail'] + tally['disagree']
    n = max(1, adjudicated)
    print('\n' + '-' * w)
    print(f'  pass {tally["pass"]}   fail {tally["fail"]}   '
          f'disagree {tally["disagree"]}   incomplete {tally["incomplete"]}'
          f'   -> {OUT_PATH}')
    print(f'  disagreement rate: {tally["disagree"] / n:.0%} '
          f'of {adjudicated} adjudicated  (D5 calibration)')
    if tally['incomplete']:
        print(f'  {tally["incomplete"]} row(s) NOT CHECKED - an API call failed. '
              're-run them; do not send them to Stage 4.')
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
