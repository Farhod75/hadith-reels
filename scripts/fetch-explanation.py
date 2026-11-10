#!/usr/bin/env python3
# scripts/fetch-explanation.py
# ============================================================
# P387: the hadith explanation page's content - a scholar's explanation,
# carried VERBATIM, never written by us.
#
# hadithreels.com/hadith/<collection>/<number> shows the hadith, then what a
# named source says about it: the explanation, the lessons, word meanings,
# and the occasion (sabab al-wurud) only when a source records one. This
# script fetches one HadeethEnc entry in ar / en / ru / uz / tg, checks it is
# the SAME hadith as the library row (Arabic letters, diacritics ignored),
# and writes:
#
#   content/explanations/<slug>.json           what the page renders
#   content/explanations/raw/hadeethenc-<id>-<lang>.json   the exact bytes
#   content/explanations/index.json            slugs (the card's link)
#   lib/explanations-registry.ts               static imports for the page
#
# Every text field in <slug>.json is copied from the raw payload unchanged -
# HadeethEnc's API terms: no modification, addition or deletion, and credit
# the publisher. test_fetch_explanation.py re-reads the raw files and fails
# on any difference, so a hand edit of the page text cannot pass the hook.
#
# Usage (dry run unless --commit):
#   python scripts/fetch-explanation.py --hadeethenc 4555 \
#       --library-id 8eeb6788-dcca-4494-8a38-c43f5ce00de1 [--commit]
#
# Stdlib only.
# ============================================================
import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONTENT = os.path.join(ROOT, 'content', 'explanations')
RAW = os.path.join(CONTENT, 'raw')
REGISTRY_TS = os.path.join(ROOT, 'lib', 'explanations-registry.ts')

API_BASE = 'https://hadeethenc.com/api/v1'
UA = 'hadith-reels/1.0 (+https://hadithverifier.com)'   # HadeethEnc 403s urllib's default UA (source_hadeethenc.py)

# HadeethEnc language code -> the site's language code. Tajik is `tg` there.
LANGS = {'ar': 'ar', 'en': 'en', 'ru': 'ru', 'uz': 'uz', 'tg': 'tj'}

PUBLISHER = 'HadeethEnc.com'
LICENCE = ('HadeethEnc API terms: no modification, addition or deletion of the '
           'content; credit the publisher and source (HadeethEnc.com).')


def load_collections():
    with open(os.path.join(CONTENT, 'collections.json'), encoding='utf-8') as fh:
        return json.load(fh)


def slug_for(collection, number, collections):
    """'Sahih Muslim', '2564' -> 'muslim-2564'. An unmapped collection is an
    error, not a guessed slug: the URL is public and must not change later."""
    if collection not in collections:
        raise ValueError('collection %r has no slug in content/explanations/collections.json'
                         % collection)
    num = str(number).strip()
    if not re.fullmatch(r'[0-9]+[a-z]?', num):
        raise ValueError('hadith number %r is not a plain number' % number)
    return '%s-%s' % (collections[collection], num)


# ---- same-hadith check ---------------------------------------------------
_MARKS = re.compile('[ؐ-ًؚ-ٰٟۖ-ۭـ]')
_ALEF = str.maketrans({'آ': 'ا', 'أ': 'ا', 'إ': 'ا',
                       'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه'})


def letters(s):
    """Arabic letters only: no diacritics, tatweel, punctuation or spaces;
    alef forms, alef maqsura and ta marbuta folded. For COMPARING, never shown."""
    s = unicodedata.normalize('NFC', s or '')
    s = _MARKS.sub('', s).translate(_ALEF)
    return ''.join(ch for ch in s if 'ء' <= ch <= 'ي')


def same_hadith(library_arabic, source_arabic):
    """The library matn must appear inside the source's text (which carries the
    isnad opener). An empty side never matches."""
    a, b = letters(library_arabic), letters(source_arabic)
    return bool(a) and bool(b) and a in b


# ---- building the page document ------------------------------------------
def build_doc(row, payloads, raw_hashes, hadeethenc_id, fetched_at, collections):
    """PURE. row: the library row. payloads: {hadeethenc_lang: parsed json}.
    Text fields are copied as-is; nothing is trimmed, joined or reworded."""
    ar = payloads['ar']
    langs = {}
    for src_lang, site_lang in LANGS.items():
        p = payloads.get(src_lang)
        if not p or not (p.get('explanation') or '').strip():
            continue                     # absent language: no section, never a fallback
        langs[site_lang] = {
            'url': 'https://hadeethenc.com/%s/browse/hadith/%s' % (src_lang, hadeethenc_id),
            'raw': 'raw/hadeethenc-%s-%s.json' % (hadeethenc_id, src_lang),
            'raw_sha256': raw_hashes[src_lang],
            'title': p.get('title') or '',
            'explanation': p.get('explanation') or '',
            'lessons': list(p.get('hints') or []),
            'word_meanings': list(p.get('words_meanings') or []),
            'attribution': p.get('attribution') or '',
            'grade': p.get('grade') or '',
        }
    return {
        'schema': 1,
        'slug': slug_for(row['collection'], row['hadith_number'], collections),
        'library_id': row['id'],
        'collection': row['collection'],
        'hadith_number': str(row['hadith_number']),
        # Sabab al-wurud: only ever filled from a cited source, by hand review.
        # null means no source we hold records one - the page shows nothing.
        'occasion': None,
        'commentaries': [{
            'source': 'hadeethenc',
            'source_id': str(hadeethenc_id),
            'publisher': PUBLISHER,
            'licence': LICENCE,
            'fetched_at': fetched_at,
            'references_ar': ar.get('reference') or '',
            'langs': langs,
        }],
    }


def registry_ts(slugs):
    lines = ['// GENERATED by scripts/fetch-explanation.py - do not edit by hand (P387).',
             '// Static imports so the hadith page bundles every explanation it can show.',
             "import type { Explanation } from './explanations'"]
    names = []
    for s in sorted(slugs):
        name = 'x_' + re.sub(r'[^a-z0-9]', '_', s)
        names.append((s, name))
        lines.append("import %s from '@/content/explanations/%s.json'" % (name, s))
    lines.append('')
    lines.append('export const EXPLANATIONS: Record<string, Explanation> = {')
    for s, name in names:
        lines.append("  '%s': %s as Explanation," % (s, name))
    lines.append('}')
    return '\n'.join(lines) + '\n'


def existing_slugs():
    if not os.path.isdir(CONTENT):
        return []
    return sorted(f[:-5] for f in os.listdir(CONTENT)
                  if f.endswith('.json') and f not in ('index.json', 'collections.json'))


# ---- network -------------------------------------------------------------
def fetch_raw(hadeethenc_id, lang):
    q = urllib.parse.urlencode({'language': lang, 'id': str(hadeethenc_id)})
    req = urllib.request.Request('%s/hadeeths/one/?%s' % (API_BASE, q),
                                 headers={'Accept': 'application/json', 'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def load_env(path):
    env = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def library_row(library_id):
    env = load_env(os.path.join(ROOT, '.env.local'))
    base, key = env.get('NEXT_PUBLIC_SUPABASE_URL'), env.get('SUPABASE_SERVICE_ROLE_KEY')
    if not base or not key:
        sys.exit('STOP: .env.local has no Supabase URL / service key')
    q = urllib.parse.urlencode({'id': 'eq.' + library_id,
                                'select': 'id,collection,hadith_number,grade,text_arabic,source_url'})
    req = urllib.request.Request(base.rstrip('/') + '/rest/v1/hadith_library?' + q,
                                 headers={'apikey': key, 'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(req, timeout=30) as r:
        rows = json.loads(r.read().decode('utf-8'))
    if len(rows) != 1:
        sys.exit('STOP: library id %s matched %d rows' % (library_id, len(rows)))
    return rows[0]


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as fh:
        fh.write(data)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--hadeethenc', required=True, help='HadeethEnc hadeeth id')
    ap.add_argument('--library-id', required=True, help='hadith_library.id')
    ap.add_argument('--commit', action='store_true', help='write the files (default: dry run)')
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')

    row = library_row(a.library_id)
    if row.get('grade') not in ('sahih', 'hasan'):
        sys.exit('STOP: library grade is %r' % row.get('grade'))
    collections = load_collections()
    slug = slug_for(row['collection'], row['hadith_number'], collections)

    raws, payloads, hashes = {}, {}, {}
    for lang in LANGS:
        b = fetch_raw(a.hadeethenc, lang)
        raws[lang], payloads[lang] = b, json.loads(b.decode('utf-8'))
        hashes[lang] = hashlib.sha256(b).hexdigest()

    src_ar = payloads['ar'].get('hadeeth') or ''
    if not same_hadith(row.get('text_arabic'), src_ar):
        sys.exit('STOP: HadeethEnc %s is not the library matn of %s #%s - not written.\n'
                 '  library: %s\n  source : %s' % (a.hadeethenc, row['collection'],
                                                   row['hadith_number'], row.get('text_arabic'), src_ar))

    today = datetime.date.today().isoformat()
    doc = build_doc(row, payloads, hashes, a.hadeethenc, today, collections)
    have = sorted(doc['commentaries'][0]['langs'])
    print('%s  <- HadeethEnc %s  (%s)' % (slug, a.hadeethenc, ', '.join(have)))
    for lg in ('uz', 'ru', 'en', 'tj', 'ar'):
        x = doc['commentaries'][0]['langs'].get(lg)
        print('  %-2s  explanation %4d chars, %d lessons, %d word meanings'
              % (lg, len(x['explanation']), len(x['lessons']), len(x['word_meanings']))
              if x else '  %-2s  MISSING - that language shows no explanation' % lg)
    if not a.commit:
        print('dry run - nothing written (add --commit)')
        return 0

    for lang, b in raws.items():
        write_bytes(os.path.join(RAW, 'hadeethenc-%s-%s.json' % (a.hadeethenc, lang)), b)
    write_bytes(os.path.join(CONTENT, slug + '.json'),
                (json.dumps(doc, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    slugs = sorted(set(existing_slugs()) | {slug})
    write_bytes(os.path.join(CONTENT, 'index.json'),
                (json.dumps(slugs, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    write_bytes(REGISTRY_TS, registry_ts(slugs).encode('utf-8'))
    print('written: content/explanations/%s.json, raw x%d, index.json, lib/explanations-registry.ts'
          % (slug, len(raws)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
