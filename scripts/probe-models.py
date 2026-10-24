#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe-models.py - measure a model as a Stage 3 pass before trusting it as one.

NOT A GATE. This writes nothing, commits nothing and decides nothing. It runs
N models over the same (Arabic, translation) pairs and prints what each one
said, so a pass-B choice is measured instead of assumed. P275 did exactly this
by hand across 128 calls; this is that, as a script.

WHY THE PROMPT IS IMPORTED AND NOT COPIED
  verify-candidates.py, on its own SYSTEM block: "Divergence in the prompt
  would make disagreement uninterpretable - we could not tell a real catch from
  a difference in instructions." That holds across models as hard as it holds
  across passes. A second copy of SYSTEM here would drift from the first, and
  every number this script prints would then be anchored to nothing. So SYSTEM,
  user_msg and _parse are imported from the gate itself. If the gate's prompt
  changes, this probe changes with it, silently and correctly.

WHY ONE PROVIDER FOR ALL OF THEM
  Abacus RouteLLM is OpenAI-compatible, so a single code path reaches Gemini,
  Qwen, Grok, GPT and Claude alike. Every model is then called identically -
  same body, same timeout, same retry, same parse. A per-vendor SDK for each
  would reintroduce exactly the differences this is trying to measure past.
  Needs ABACUS_API_KEY in .env.local.

WHY FOUR RUNS BY DEFAULT
  P272: one run cannot show noise. P275 found terra false-failing CLEAN Russian
  in 1 run of 4 - a single run had a 75% chance of calling it clean. A model
  that is right three times and wrong once is not a model that is right.

WHAT D2 ACTUALLY REQUIRES
  A model does not need to remember writing a translation in order to pass it.
  It tends to accept the constructions it tends to produce, so a translator and
  a verifier drawn from the same model fail together - correlated blind spots,
  not recognition. That is why pass B must come from a different company than
  whatever produced the text, and why this probe reports each model separately
  and never pools them into one verdict.

OUTPUT ENCODING
  The report goes to out/model-probe.txt and out/model-probe.json as UTF-8.
  Only an ASCII summary goes to stdout: `python -I` ignores PYTHONIOENCODING,
  and a console write of Cyrillic or Arabic dies on cp1252 under PowerShell.

USAGE
  # score what is already in the library row
  python scripts/probe-models.py --row 3540 --library --all-langs

  # score PROPOSED text that is not in the DB yet (verify before write)
  python scripts/probe-models.py --from-json out/proposed-3540.json

  # one language, more runs, a chosen set
  python scripts/probe-models.py --row 3540 --library --lang tj --runs 6
  python scripts/probe-models.py --row 3540 --library --models gemini-4-argon,qwen3.8-max

  --from-json takes:
    {"arabic": "...", "translations": {"ru": "...", "uz": "...", "tj": "..."}}
"""

import argparse
import collections
import importlib.util
import io
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_URL = 'https://routellm.abacus.ai/v1/chat/completions'

# The incumbent is in the default set on purpose. A probe that measures only
# the challengers produces numbers with nothing to compare them against.
DEFAULT_MODELS = (
    'gemini-4-argon',     # Google
    'qwen3.8-max',        # Alibaba
    'grok-4.7',           # xAI
    'gpt-6.1-sol',        # OpenAI - the incumbent pass B, as the control
)

OUT_TXT = os.path.join('out', 'model-probe.txt')
OUT_JSON = os.path.join('out', 'model-probe.json')


def load_gate():
    """Import verify-candidates.py by path - the filename is not importable."""
    path = os.path.join(HERE, 'verify-candidates.py')
    spec = importlib.util.spec_from_file_location('_gate', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def call_model(gate, key, model, arabic, lang_name, translation):
    """One verification call. Same shape for every model."""
    body = json.dumps({
        'model': model,
        # The smoke test that preceded this script returned a two-character
        # fragment from gemini-3.1-pro at max_tokens=120: a reasoning model
        # spends the budget thinking and has nothing left to answer with. 3000
        # matches pass_a for the same reason (P152).
        'max_tokens': 3000,
        'messages': [
            {'role': 'system', 'content': gate.SYSTEM},
            {'role': 'user',
             'content': gate.user_msg(arabic, lang_name, translation)},
        ],
    }, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(BASE_URL, data=body, method='POST', headers={
        'Authorization': 'Bearer %s' % key,
        'Content-Type': 'application/json'})
    data = gate._post(req, 180, label='%s ' % model)
    msg = data['choices'][0]['message']
    return gate._parse((msg.get('content') or '').strip())


def rows_from_db(gate, env, number, library):
    base = gate.pick(env, gate.URL_KEYS)
    sb_key = gate.pick(env, gate.SERVICE_KEYS)
    if not base or not sb_key:
        raise SystemExit('FAILED: supabase url/key missing from .env.local')
    table = 'hadith_library' if library else 'hadith_candidates'
    rows = gate.sb_get(base, sb_key, table,
                       {'select': '*', 'hadith_number': 'eq.%s' % number})
    # P147: hadith_number is NOT unique. Refuse rather than probe the wrong one.
    if len(rows) != 1:
        raise SystemExit(
            'FAILED: hadith_number=%s matched %d rows in %s (P147). Probe by '
            'a row that is unique, or use --from-json.' % (number, len(rows), table))
    return rows[0]


def main():
    ap = argparse.ArgumentParser(
        description='Measure candidate models as a Stage 3 pass. Writes nothing.')
    ap.add_argument('--row', help='hadith_number to read')
    ap.add_argument('--library', action='store_true',
                    help='read hadith_library instead of hadith_candidates')
    ap.add_argument('--from-json', dest='from_json', metavar='PATH',
                    help='score PROPOSED text from a file instead of the DB')
    ap.add_argument('--lang', choices=sorted(('en', 'ru', 'uz', 'tj')),
                    help='one language only')
    ap.add_argument('--all-langs', action='store_true',
                    help='every language present')
    ap.add_argument('--runs', type=int, default=4,
                    help='runs per model per language (default 4; P272 - one '
                         'run cannot show noise)')
    ap.add_argument('--models', default=','.join(DEFAULT_MODELS),
                    help='comma-separated model ids')
    args = ap.parse_args()

    if not args.row and not args.from_json:
        raise SystemExit('FAILED: give --row or --from-json')
    if args.row and args.from_json:
        raise SystemExit('FAILED: --row and --from-json are exclusive')

    gate = load_gate()
    env = gate.load_env()
    key = gate.pick(env, ('ABACUS_API_KEY',))
    if not key:
        raise SystemExit('FAILED: ABACUS_API_KEY missing from .env.local')

    models = [m.strip() for m in args.models.split(',') if m.strip()]

    # ---- assemble the work
    if args.from_json:
        with io.open(args.from_json, encoding='utf-8') as fh:
            doc = json.load(fh)
        arabic = doc.get('arabic') or ''
        supplied = doc.get('translations') or {}
        label = 'proposed:%s' % os.path.basename(args.from_json)
        texts = {k: v for k, v in supplied.items() if k in gate.FIELDS and v}
    else:
        row = rows_from_db(gate, env, args.row, args.library)
        arabic = row.get('text_arabic') or ''
        label = '%s #%s' % (row.get('collection') or '?', row.get('hadith_number'))
        texts = {}
        for lang, (field, _name) in gate.FIELDS.items():
            if row.get(field):
                texts[lang] = row[field]

    if not arabic:
        raise SystemExit('FAILED: no Arabic to verify against')
    if args.lang:
        texts = {k: v for k, v in texts.items() if k == args.lang}
    elif not args.all_langs:
        raise SystemExit('FAILED: give --lang or --all-langs')
    if not texts:
        raise SystemExit('FAILED: no translations to score')

    total = len(models) * len(texts) * args.runs
    print('probe: %s' % label)
    print('models: %s' % ', '.join(models))
    print('langs: %s   runs: %d   calls: %d'
          % (', '.join(sorted(texts)), args.runs, total))
    print('')

    # ---- run
    results = []
    for lang in sorted(texts):
        lang_name = gate.FIELDS[lang][1]
        for model in models:
            verdicts = []
            for r in range(args.runs):
                try:
                    v = call_model(gate, key, model, arabic, lang_name, texts[lang])
                except Exception as exc:          # noqa: BLE001
                    v = {'verdict': 'error', 'issues': [], 'confidence': 'low',
                         'error': str(exc)[:200]}
                verdicts.append(v)
                time.sleep(0.3)
            counts = collections.Counter(v.get('verdict', '?') for v in verdicts)
            results.append({'lang': lang, 'model': model,
                            'counts': dict(counts), 'verdicts': verdicts})
            # ASCII only - see OUTPUT ENCODING above.
            print('  %-4s %-24s %s'
                  % (lang, model,
                     '  '.join('%s=%d' % kv for kv in sorted(counts.items()))))

    # ---- report
    os.makedirs('out', exist_ok=True)
    with io.open(OUT_JSON, 'w', encoding='utf-8', newline='') as fh:
        json.dump({'label': label, 'arabic': arabic, 'runs': args.runs,
                   'texts': texts, 'results': results},
                  fh, ensure_ascii=False, indent=2)

    with io.open(OUT_TXT, 'w', encoding='utf-8', newline='') as fh:
        def w(s=''):
            fh.write(s + '\n')
        w('probe: %s' % label)
        w('runs per model per language: %d' % args.runs)
        w('=' * 78)
        w('ARABIC')
        w(arabic)
        for lang in sorted(texts):
            w('')
            w('=' * 78)
            w('%s  (%s)' % (gate.FIELDS[lang][1], lang))
            w(texts[lang])
            w('-' * 78)
            for res in [r for r in results if r['lang'] == lang]:
                w('')
                w('  %s   %s' % (res['model'],
                                 '  '.join('%s=%d' % kv
                                           for kv in sorted(res['counts'].items()))))
                for i, v in enumerate(res['verdicts'], 1):
                    if v.get('error'):
                        w('    run %d  ERROR %s' % (i, v['error']))
                        continue
                    w('    run %d  %s (%s)' % (i, v.get('verdict'),
                                               v.get('confidence')))
                    for iss in v.get('issues', []) or []:
                        w('           [%s] %s' % (iss.get('type'), iss.get('why')))
                        q = iss.get('quote')
                        if q:
                            w('                  quote: %s' % q)

    print('')
    print('wrote %s' % OUT_TXT)
    print('wrote %s' % OUT_JSON)
    print('')
    print('This probe decides nothing (G1). Read the report; the human gate stands.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
