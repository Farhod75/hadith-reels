#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit-library.py - deterministic per-language checks over hadith_library.

Sibling to lint-content.py, but a different target. lint-content.py reads
draft.txt (GENERATED reel text) and catches what the generator does wrong.
This reads the LIBRARY and catches what the source rows have wrong - defects
that exist upstream of any reel and survive into every reel made from them.

Grounding cases:
  - P050  text_tajik held a Russian fallback. Undetectable at reel time,
          because the generator paraphrases; the DB sentence never appears
          verbatim in draft.txt.
  - R037  text_tajik read «Неки» where Tajik requires «Некӣ» (U+04E3).
          Caught by a human reading it, after the kids reel was produced.
  - R039  text_russian «Аллахом» where the sentence wanted «Аллаху».
  - R024  caption pulled Latin text_uzbek into a Cyrillic body (5 occurrences).
  - R027  Latin homoglyphs inside Cyrillic words, invisible on screen.

READ-ONLY. Never writes, never edits. Warn-only by default; --strict makes
HIGH findings exit non-zero so it can be used as a gate.

A clean run does NOT mean the library is correct. It means these checks
found nothing.

USAGE
  python scripts/audit-library.py                 # audit hadith_library
  python scripts/audit-library.py --table hadith_candidates
  python scripts/audit-library.py --row 527       # one hadith_number
  python scripts/audit-library.py --lang tj       # one language's checks
  python scripts/audit-library.py --strict        # exit 1 on any HIGH

Requires SUPABASE URL + service-role key in .env.local (same as
promote-candidates.py).
"""

import argparse
import difflib
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------- config

URL_KEYS = ('NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_URL')
SERVICE_KEYS = ('SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_KEY',
                'SERVICE_ROLE_KEY', 'SUPABASE_KEY')

# Letters that exist in Tajik Cyrillic and not in Russian Cyrillic.
TJ_LETTERS = 'ӣӯҳқғҷӢӮҲҚҒҶ'

# P050: a Tajik column that is really the Russian one. Genuine translations
# share loanwords and Cyrillic, so they score well below this; a copy scores
# at or near 1.0. Measured against the live library: the four zero-diacritic
# rows (Muslim 82, Tirmidhi 2396, Abu Dawud 1479, Bayhaqi 2318) are all
# genuine Tajik and score far under it.
TJ_RU_SIMILARITY_HIGH = 0.85

# Below this many characters, absence of Tajik-specific letters is not
# evidence of anything - short sentences legitimately use only shared
# Cyrillic. Set from the live library, where every row above 52 chars
# carries at least one Tajik letter.
TJ_DIACRITIC_MIN_LEN = 60

# G4: the okina in oʻ / gʻ is U+02BB MODIFIER LETTER TURNED COMMA.
OKINA = '\u02bb'
OKINA_WRONG = {
    '\u0027': "ASCII apostrophe '",
    '\u2018': 'left single quote \u2018',
    '\u2019': 'right single quote \u2019',
    '\u0060': 'grave accent `',
    '\u00b4': 'acute accent \u00b4',
    '\u02bc': 'modifier apostrophe \u02bc',
}

# Latin characters that render identically to a Cyrillic letter.
HOMOGLYPHS = {
    'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х', 'y': 'у',
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К', 'M': 'М',
    'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х', 'Y': 'У',
}

CYRILLIC_FIELDS = {
    'text_russian': 'ru',
    'text_uzbek_cyrillic': 'uz',
    'text_tajik': 'tj',
}

ALL_TEXT_FIELDS = [
    'text_arabic', 'text_english', 'text_russian',
    'text_uzbek', 'text_uzbek_cyrillic', 'text_uzbek_latin', 'text_tajik',
]

VALID_GRADES = ('sahih', 'hasan')

LEVELS = ('HIGH', 'WARN', 'INFO')

# ---------------------------------------------------------------- helpers


class Finding:
    def __init__(self, level, check, ref, field, note, detail=''):
        self.level = level
        self.check = check
        self.ref = ref
        self.field = field
        self.note = note
        self.detail = detail


def load_env(path='.env.local'):
    """Minimal .env reader - no dependency on python-dotenv."""
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def pick(env, names):
    for n in names:
        if env.get(n):
            return env[n], n
        if os.environ.get(n):
            return os.environ[n], n
    return None, None


def fetch_rows(base_url, key, table, row=None):
    """PostgREST select. Read-only."""
    params = {'select': '*'}
    if row:
        params['hadith_number'] = f'eq.{row}'
    url = f'{base_url.rstrip("/")}/rest/v1/{table}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def ref_of(row):
    return f'{row.get("collection", "?")} #{row.get("hadith_number", "?")}'


def norm(s):
    """Casefold, strip diacritics and punctuation, collapse whitespace."""
    s = unicodedata.normalize('NFKD', (s or '').casefold())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def is_cyrillic(ch):
    return '\u0400' <= ch <= '\u04ff'


# ---------------------------------------------------------------- checks


def check_tj_russian_fallback(row):
    """P050: text_tajik is a copy of text_russian, not a translation."""
    tj, ru = row.get('text_tajik'), row.get('text_russian')
    if not tj or not ru:
        return []
    score = difflib.SequenceMatcher(None, norm(tj), norm(ru)).ratio()
    if score >= TJ_RU_SIMILARITY_HIGH:
        return [Finding(
            'HIGH', 'tj-russian-fallback', ref_of(row), 'text_tajik',
            f'text_tajik is {score:.0%} identical to text_russian - this is '
            f'the P050 Russian fallback, not a Tajik translation',
            f'tj: {tj[:70]}\n          ru: {ru[:70]}')]
    return []


def check_tj_diacritics(row):
    """Tajik-specific letters absent from a passage long enough that their
    absence is implausible. INFO, not HIGH: short sentences legitimately
    use only shared Cyrillic."""
    tj = row.get('text_tajik')
    if not tj:
        return []
    if any(c in TJ_LETTERS for c in tj):
        return []
    if len(tj) < TJ_DIACRITIC_MIN_LEN:
        return []
    return [Finding(
        'INFO', 'tj-no-diacritics', ref_of(row), 'text_tajik',
        f'{len(tj)} characters with none of {TJ_LETTERS[:6]} - verify this '
        f'is Tajik and not Russian-with-Tajik-word-order',
        tj[:90])]


def check_uz_okina(row):
    """G4: oʻ / gʻ must use U+02BB, not an apostrophe or quote mark."""
    out = []
    for field in ('text_uzbek', 'text_uzbek_latin'):
        val = row.get(field)
        if not val:
            continue
        for wrong, name in OKINA_WRONG.items():
            for m in re.finditer(f'[oOgG]{re.escape(wrong)}', val):
                out.append(Finding(
                    'WARN', 'uz-okina', ref_of(row), field,
                    f'{name} used where the okina U+02BB ({OKINA}) belongs',
                    f'...{val[max(0, m.start() - 25):m.end() + 25]}...'))
                break
    return out


def check_uz_script_mixing(row):
    """The Cyrillic column holding Latin, or the Latin column holding
    Cyrillic. Source of the caption defect hit 5 times (R024, R036...)."""
    out = []
    cyr = row.get('text_uzbek_cyrillic')
    lat = row.get('text_uzbek_latin')
    if cyr:
        runs = re.findall(r'[A-Za-z]{3,}', cyr)
        if runs:
            out.append(Finding(
                'WARN', 'uz-script-mixed', ref_of(row), 'text_uzbek_cyrillic',
                f'Latin run(s) in the Cyrillic column: {", ".join(runs[:4])}',
                cyr[:90]))
    if lat:
        runs = re.findall(r'[\u0400-\u04ff]{3,}', lat)
        if runs:
            out.append(Finding(
                'WARN', 'uz-script-mixed', ref_of(row), 'text_uzbek_latin',
                f'Cyrillic run(s) in the Latin column: {", ".join(runs[:4])}',
                lat[:90]))
    return out


def check_homoglyphs(row):
    """R027: a Latin character hiding inside a Cyrillic word. Renders
    identically on screen and is invisible to human review by construction."""
    out = []
    for field, _lang in CYRILLIC_FIELDS.items():
        val = row.get(field)
        if not val:
            continue
        for word in re.findall(r'\S+', val):
            has_cyr = any(is_cyrillic(c) for c in word)
            if not has_cyr:
                continue
            bad = [c for c in word if c in HOMOGLYPHS]
            if bad:
                fixed = ''.join(HOMOGLYPHS.get(c, c) for c in word)
                out.append(Finding(
                    'HIGH', 'homoglyph', ref_of(row), field,
                    f'Latin {", ".join(repr(c) for c in bad)} inside a '
                    f'Cyrillic word - «{word}» should be «{fixed}»',
                    ''))
    return out


def check_missing_translations(row):
    """Which languages this row cannot serve."""
    missing = [f for f in ('text_english', 'text_russian', 'text_tajik')
               if not (row.get(f) or '').strip()]
    if not (row.get('text_uzbek_cyrillic') or row.get('text_uzbek') or '').strip():
        missing.append('text_uzbek_cyrillic')
    if not missing:
        return []
    return [Finding(
        'INFO', 'missing-translation', ref_of(row), ', '.join(missing),
        f'{len(missing)} language field(s) empty - this row cannot produce '
        f'a full 4-language set', '')]


def check_grade(row):
    g = (row.get('grade') or '').strip().lower()
    if g in VALID_GRADES:
        return []
    return [Finding(
        'HIGH', 'grade', ref_of(row), 'grade',
        f'grade is {g!r} - only {"/".join(VALID_GRADES)} may be published', '')]


def check_source(row):
    url = (row.get('source_url') or '').strip()
    if not url:
        # hadith_candidates stores deep-links as source_urls (jsonb, plural)
        urls = row.get('source_urls') or {}
        if isinstance(urls, dict):
            for k in ('dorar', 'sunnah', 'hadeethenc'):
                if urls.get(k):
                    url = str(urls[k]).strip()
                    break
    if not url:
        return [Finding('WARN', 'source', ref_of(row), 'source_url',
                        'no source URL - the project requires deep-links', '')]
    if re.match(r'^https?://[^/]+/?$', url):
        return [Finding('WARN', 'source', ref_of(row), 'source_url',
                        'homepage, not a deep-link to this hadith', url)]
    return []


CHECKS = [
    ('tj', check_tj_russian_fallback),
    ('tj', check_tj_diacritics),
    ('uz', check_uz_okina),
    ('uz', check_uz_script_mixing),
    (None, check_homoglyphs),
    (None, check_missing_translations),
    (None, check_grade),
    (None, check_source),
]

# ---------------------------------------------------------------- report


def report(findings, n_rows, table, strict):
    width = 74
    print('=' * width)
    print(f' library audit - {table}  ({n_rows} rows)')
    print('=' * width)

    if not findings:
        print('  no findings.')
    else:
        order = {l: i for i, l in enumerate(LEVELS)}
        findings.sort(key=lambda f: (order[f.level], f.check, f.ref))
        for f in findings:
            print(f'  [{f.level}] {f.check}  -  {f.ref}  ({f.field})')
            print(f'    -> {f.note}')
            if f.detail:
                for line in f.detail.splitlines():
                    print(f'       {line}')
            print()

    counts = {l: sum(1 for f in findings if f.level == l) for l in LEVELS}
    print('-' * width)
    print(f'  {counts["HIGH"]} high   {counts["WARN"]} warn   '
          f'{counts["INFO"]} info')
    if strict:
        print('  strict: HIGH findings exit non-zero.')
    else:
        print('  read-only, warn-only: nothing was changed. A clean run means')
        print('  these checks passed, NOT that the library is correct.')
    print('-' * width)

    return 1 if (strict and counts['HIGH']) else 0


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(
        description='Deterministic per-language checks over hadith_library.')
    ap.add_argument('--table', default='hadith_library',
                    choices=['hadith_library', 'hadith_candidates'])
    ap.add_argument('--row', help='audit one hadith_number only')
    ap.add_argument('--lang', choices=['ru', 'uz', 'tj'],
                    help='run only this language\'s checks')
    ap.add_argument('--strict', action='store_true',
                    help='exit 1 if any HIGH finding')
    args = ap.parse_args()

    env = load_env()
    base_url, url_name = pick(env, URL_KEYS)
    key, key_name = pick(env, SERVICE_KEYS)

    if not base_url or not key:
        print('FAILED: need a Supabase URL and service-role key in .env.local')
        print(f'  looked for URL in: {", ".join(URL_KEYS)}')
        print(f'  looked for key in: {", ".join(SERVICE_KEYS)}')
        return 2

    try:
        rows = fetch_rows(base_url, key, args.table, args.row)
    except urllib.error.HTTPError as e:
        print(f'FAILED: {e.code} {e.reason} reading {args.table}')
        print(f'  (using {url_name} + {key_name})')
        return 2
    except Exception as e:  # noqa: BLE001
        print(f'FAILED: {e}')
        return 2

    if not rows:
        print(f'no rows in {args.table}'
              + (f' for hadith_number={args.row}' if args.row else ''))
        return 0

    findings = []
    for row in rows:
        for lang, fn in CHECKS:
            if args.lang and lang and lang != args.lang:
                continue
            findings.extend(fn(row))

    return report(findings, len(rows), args.table, args.strict)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
