#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe-passb.py - THROWAWAY. Not part of the pipeline. Delete after reading.

Question: can the proposed pass-B model actually SEE defects in Tajik and
Uzbek, or does it rubber-stamp? A verifier that cannot read the language
fails in the worst possible way - it looks like a working gate from outside.
D2 requires pass B to be a different model; it does not guarantee that model
is competent in these languages. The design doc flagged this as the
"pass-B competence" caveat and it was never tested.

Method: give it Bukhari #527's Arabic matn and, per language, two versions -
the CLEAN translation now in hadith_candidates, and the SAME text with one
planted defect. A useful verifier passes clean and fails planted. A model
that passes both is blind. A model that fails both is noise. Either way we
learn it here, on one hadith, and not at candidate 200.

  python scripts/probe-passb.py
  python scripts/probe-passb.py --model gpt-5.6-luna

Requires OPENAI_API_KEY in .env.local.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

OPENAI_URL = 'https://api.openai.com/v1/chat/completions'
DEFAULT_MODEL = 'gpt-5.6-terra'

ARABIC = ('أَيُّ الْعَمَلِ أَحَبُّ إِلَى اللَّهِ قَالَ الصَّلَاةُ عَلَى وَقْتِهَا '
          'قُلْتُ ثُمَّ أَيٌّ قَالَ بِرُّ الْوَالِدَيْنِ')

# Clean = what Stage 2 actually wrote to hadith_candidates.
# Planted = one specific, named defect. Each is a real defect class from the
# reel log, not an invented one.
CASES = {
    'en': {
        'clean': 'Which deed is most beloved to Allah? He said: Prayer at its '
                 'time. I said: Then which? He said: Kindness to parents.',
        'planted': 'Which deed is most beloved to Allah? The Prophet ﷺ smiled '
                   'and said: Prayer at its time, for it is the greatest of all '
                   'deeds. I said: Then which? He said: Kindness to parents.',
        'defect': 'ADDED: "smiled" (invented action, P105 class) and "for it is '
                  'the greatest of all deeds" (invented ranking, P116 class)',
    },
    'ru': {
        'clean': 'Какое деяние более любимо Аллаху? Он сказал: Молитва в своё '
                 'время. Я сказал: Затем какое? Он сказал: Почтение к родителям.',
        'planted': 'Какое деяние более любимо Аллаху? Он сказал: Молитва в своё '
                   'время. Я сказал: Затем какое? Он сказал: Почтение к матери.',
        'defect': 'CHANGED: «родителям» (parents, dual الوالدين) -> «матери» '
                  '(mother only) - drops the father, meaning inversion',
    },
    'uz': {
        'clean': 'Қайси амал Аллоҳга энг севимли? У: "Намозни ўз вақтида ўқиш", '
                 '- деди. Мен: "Сўнгра қайси?" - дедим. У: "Ота-онага яхшилик '
                 'қилиш", - деди.',
        'planted': 'Қайси амал Худога энг севимли? У: "Намозни ўз вақтида ўқиш", '
                   '- деди. Мен: "Сўнгра қайси?" - дедим. У: "Ота-онага яхшилик '
                   'қилиш", - деди.',
        'defect': 'CHANGED: «Аллоҳ» -> «Худо» - divine name substitution, the '
                  'R025 defect class',
    },
    'tj': {
        'clean': 'Кадом амал назди Аллоҳ маҳбубтар аст? Гуфт: Намоз дар вақташ. '
                 'Гуфтам: Баъд кадом? Гуфт: Некӣ ба падару модар.',
        'planted': 'Кадом амал назди Аллоҳ маҳбубтар аст? Гуфт: Намоз дар '
                   'вақташ, ки чун сутуни осмон аст. Гуфтам: Баъд кадом? Гуфт: '
                   'Неки ба падару модар.',
        'defect': 'ADDED: «ки чун сутуни осмон аст» (like a pillar of the sky - '
                  'invented simile, P111 rule 14). ALSO «Некӣ» -> «Неки» - lost '
                  'U+04E3 diacritic, the R037 defect',
    },
}

LANG_NAME = {'en': 'English', 'ru': 'Russian', 'uz': 'Uzbek (Cyrillic)',
             'tj': 'Tajik (Cyrillic)'}

SYSTEM = """You verify translations of hadith against the Arabic source.

Report ONLY what the Arabic does or does not support. Check for:
- ADDED content: any clause, action, ranking, comparison or attribution that
  is not in the Arabic
- OMITTED content: anything in the Arabic missing from the translation
- CHANGED meaning: a word rendered as something the Arabic does not say
- ORTHOGRAPHY: wrong divine name, missing language-specific diacritics

Answer with JSON only, no markdown fence:
{"verdict":"pass"|"fail","issues":[{"type":"added"|"omitted"|"changed"|"orthography","quote":"...","why":"..."}],"confidence":"high"|"medium"|"low"}

If the translation is faithful, return verdict "pass" with an empty issues
array. Do not invent issues to appear thorough."""


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


def ask(key, model, lang, translation):
    user = (f'Arabic source:\n{ARABIC}\n\n'
            f'{LANG_NAME[lang]} translation to verify:\n{translation}')
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'system', 'content': SYSTEM},
                     {'role': 'user', 'content': user}],
    }, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(OPENAI_URL, data=body, headers={
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read().decode('utf-8'))
    txt = data['choices'][0]['message']['content'].strip()
    txt = txt.replace('```json', '').replace('```', '').strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {'verdict': '?', 'raw': txt[:300]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default=DEFAULT_MODEL)
    args = ap.parse_args()

    key = load_env().get('OPENAI_API_KEY') or os.environ.get('OPENAI_API_KEY')
    if not key:
        print('FAILED: no OPENAI_API_KEY in .env.local')
        return 2

    print('=' * 74)
    print(f' pass-B competence probe - {args.model}')
    print(' clean SHOULD pass. planted SHOULD fail. anything else = blind.')
    print('=' * 74)

    score = {}
    for lang, case in CASES.items():
        print(f'\n{LANG_NAME[lang]}')
        row = {}
        for kind in ('clean', 'planted'):
            try:
                res = ask(key, args.model, lang, case[kind])
            except urllib.error.HTTPError as e:
                print(f'  {kind:8} HTTP {e.code}: {e.read().decode()[:200]}')
                row[kind] = 'error'
                continue
            except Exception as e:  # noqa: BLE001
                print(f'  {kind:8} {e}')
                row[kind] = 'error'
                continue

            v = res.get('verdict', '?')
            row[kind] = v
            want = 'pass' if kind == 'clean' else 'fail'
            mark = 'OK ' if v == want else '>>>'
            print(f'  {mark} {kind:8} verdict={v:5} (want {want})'
                  f'  confidence={res.get("confidence", "-")}')
            for iss in (res.get('issues') or [])[:3]:
                print(f'        - {iss.get("type")}: {iss.get("why", "")[:90]}')
            if 'raw' in res:
                print(f'        raw: {res["raw"][:120]}')
        if kind == 'planted':
            print(f'  planted defect was: {case["defect"]}')
        score[lang] = row

    print('\n' + '-' * 74)
    good = [l for l, r in score.items()
            if r.get('clean') == 'pass' and r.get('planted') == 'fail']
    blind = [l for l, r in score.items()
             if r.get('clean') == 'pass' and r.get('planted') == 'pass']
    noisy = [l for l, r in score.items() if r.get('clean') == 'fail']
    print(f'  usable  : {", ".join(good) or "none"}')
    print(f'  BLIND   : {", ".join(blind) or "none"}   (passed a planted defect)')
    print(f'  NOISY   : {", ".join(noisy) or "none"}   (failed clean text)')
    print('  A language that is BLIND must not be gated by this model.')
    print('  One run is one sample - these models are non-deterministic.')
    print('-' * 74)
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
