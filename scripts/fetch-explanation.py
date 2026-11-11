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
import urllib.error
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
                       'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه',
                       # P391: a hamza seat is spelling, not wording (فبائع / فبايع)
                       'ئ': 'ي', 'ؤ': 'و'})


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


# The reel narrates a fragment of a long hadith (Muslim #2699 is one sentence of
# a hadith eight sentences long). When the source's text is longer than the
# library matn by more than an isnad opener, the page shows the full text too.
EXCERPT_MARGIN = 60          # Arabic letters; an opener like "عن أبي هريرة قال قال رسول الله" is ~25


def matn_word_diff(library_arabic, source_arabic):
    """Words (letters only) in which the library matn differs from the closest
    stretch of the source: (missing_from_library, extra_in_library). For the
    operator to read when same_hadith() fails on a wording variant."""
    import difflib
    def key(w):
        # a leading wa- ("and") joins clauses in a long hadith; an excerpt starts
        # without it. Compared without it; never removed from any shown text.
        w = letters(w)
        return w[1:] if w.startswith('و') and len(w) > 2 else w
    lw = [key(w) for w in (library_arabic or '').split() if letters(w)]
    sw = [key(w) for w in (source_arabic or '').split() if letters(w)]
    if not lw or not sw:
        return sw, lw
    # Anchor on the longest common run, then compare the library matn with the
    # stretch of the source it lines up with - not with the whole long hadith.
    m = difflib.SequenceMatcher(a=sw, b=lw, autojunk=False).find_longest_match(0, len(sw), 0, len(lw))
    if not m.size:
        return sw, lw
    lo = max(0, m.a - m.b)
    hi = min(len(sw), m.a + (len(lw) - m.b) + 2)
    ops = difflib.SequenceMatcher(a=sw[lo:hi], b=lw, autojunk=False).get_opcodes()
    while ops and ops[0][0] == 'delete':     # source words before the matn begins
        ops = ops[1:]
    while ops and ops[-1][0] == 'delete':    # source words after it ends
        ops = ops[:-1]
    missing, extra = [], []
    for tag, i1, i2, j1, j2 in ops:
        if tag in ('replace', 'delete'):
            missing += sw[lo + i1:lo + i2]
        if tag in ('replace', 'insert'):
            extra += lw[j1:j2]
    return missing, extra


QUOTED_MARGIN = 10          # inside the quotation marks there is no opener to allow for


# The text before the quote is only an opener when it ends by handing over to the Prophet's
# speech: "... رسول الله صلى الله عليه وسلم (قال)". A companion's own narrative before the quote
# (Bukhari #3559: "he was not obscene ... and he used to say") is part of the hadith.
_OPENER_END = re.compile('(صلياللهعليهوسلم|رسولالله|النبي)(قال|يقول|فقال)?$')


def library_is_excerpt(library_arabic, source_arabic):
    """P395: when the source quotes the Prophet's words after a plain opener, measure only the
    quote - Tirmidhi #1987's opener names two companions and was read as a longer hadith.
    Otherwise the whole text against EXCERPT_MARGIN, as before."""
    a = letters(library_arabic)
    if not a:
        return False
    src = source_arabic or ''
    q = re.search('[«"]', src)
    if q and _OPENER_END.search(letters(src[:q.start()])):
        return len(letters(src[q.end():])) - len(a) > QUOTED_MARGIN
    return len(letters(src)) - len(a) > EXCERPT_MARGIN


def strong_grade(grade_ar):
    """HadeethEnc's Arabic grade for a related event: sahih or hasan only (HARD RULE 8)."""
    g = grade_ar or ''
    return ('صحيح' in g or 'حسن' in g) and 'ضعيف' not in g


# ---- building the page document ------------------------------------------
def build_related(hadeethenc_id, payloads, raw_hashes, fetched_at, see_also=''):
    """PURE. A related event (Ҳадисга оид воқеалар) from its own HadeethEnc entry.
    payloads may lack languages HadeethEnc has not translated - they are left out;
    the page shows the Arabic and says a translation is pending. see_also is the
    map reference (a modern book and page), never quoted text."""
    if 'ar' not in payloads:
        raise ValueError('related event %s has no Arabic entry' % hadeethenc_id)
    if not strong_grade(payloads['ar'].get('grade')):
        raise ValueError('related event %s is graded %r - only sahih/hasan is shown'
                         % (hadeethenc_id, payloads['ar'].get('grade')))
    langs = {}
    for src_lang, site_lang in LANGS.items():
        p = payloads.get(src_lang)
        if not p or not (p.get('hadeeth') or '').strip():
            continue
        langs[site_lang] = {
            'url': 'https://hadeethenc.com/%s/browse/hadith/%s' % (src_lang, hadeethenc_id),
            'raw': 'raw/hadeethenc-%s-%s.json' % (hadeethenc_id, src_lang),
            'raw_sha256': raw_hashes[src_lang],
            'title': p.get('title') or '',
            'hadeeth': p.get('hadeeth') or '',
            'attribution': p.get('attribution') or '',
            'grade': p.get('grade') or '',
        }
    return {'source': 'hadeethenc', 'source_id': str(hadeethenc_id), 'publisher': PUBLISHER,
            'fetched_at': fetched_at, 'see_also': see_also, 'langs': langs}


def build_doc(row, payloads, raw_hashes, hadeethenc_id, fetched_at, collections, related=()):
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
            'hadeeth': p.get('hadeeth') or '',
            'explanation': p.get('explanation') or '',
            'lessons': list(p.get('hints') or []),
            'word_meanings': list(p.get('words_meanings') or []),
            'attribution': p.get('attribution') or '',
            'grade': p.get('grade') or '',
        }
    return {
        'schema': 2,
        'slug': slug_for(row['collection'], row['hadith_number'], collections),
        'library_id': row['id'],
        'collection': row['collection'],
        'hadith_number': str(row['hadith_number']),
        'library_is_excerpt': library_is_excerpt(row.get('text_arabic'), ar.get('hadeeth')),
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
        'related_events': list(related),
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
def fetch_raw(hadeethenc_id, lang, missing_ok=False):
    """Raw bytes, or None when missing_ok and HadeethEnc has no such language (404)."""
    q = urllib.parse.urlencode({'language': lang, 'id': str(hadeethenc_id)})
    req = urllib.request.Request('%s/hadeeths/one/?%s' % (API_BASE, q),
                                 headers={'Accept': 'application/json', 'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if missing_ok and e.code == 404:
            return None
        raise


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
    ap.add_argument('--related', action='append', default=[], metavar='ID',
                    help='HadeethEnc id of a related event (repeatable); sahih/hasan only')
    ap.add_argument('--see-also', action='append', default=[], metavar='ID=TEXT',
                    help='map reference for a related event, e.g. 65557="Лучший пример, т. 1, с. 282"')
    ap.add_argument('--accept-variant', metavar='NOTE',
                    help='the library matn differs from the source by a wording variant of at most 2 '
                         'words; NOTE (why) is stored in the file and the page is built anyway')
    ap.add_argument('--commit', action='store_true', help='write the files (default: dry run)')
    sys.stdout.reconfigure(encoding='utf-8')     # P395: before argparse - --help prints Cyrillic
    a = ap.parse_args(argv)

    row = library_row(a.library_id)
    if row.get('grade') not in ('sahih', 'hasan'):
        sys.exit('STOP: library grade is %r' % row.get('grade'))
    collections = load_collections()
    slug = slug_for(row['collection'], row['hadith_number'], collections)

    raws, payloads, hashes = {}, {}, {}
    for lang in LANGS:
        b = fetch_raw(a.hadeethenc, lang, missing_ok=True)   # newer entries lack some languages
        if b is None:
            continue
        raws[lang], payloads[lang] = b, json.loads(b.decode('utf-8'))
        hashes[lang] = hashlib.sha256(b).hexdigest()
    if 'ar' not in payloads:
        sys.exit('STOP: HadeethEnc %s has no Arabic entry' % a.hadeethenc)

    src_ar = payloads['ar'].get('hadeeth') or ''
    variant = None
    if not same_hadith(row.get('text_arabic'), src_ar):
        missing, extra = matn_word_diff(row.get('text_arabic'), src_ar)
        print('  matn differs - missing from library: %s | extra in library: %s'
              % (' '.join(missing) or '-', ' '.join(extra) or '-'))
        if a.accept_variant and len(missing) + len(extra) <= 2:
            variant = {'note': a.accept_variant, 'missing_from_library': missing,
                       'extra_in_library': extra}
    if not same_hadith(row.get('text_arabic'), src_ar) and not variant:
        sys.exit('STOP: HadeethEnc %s is not the library matn of %s #%s - not written.\n'
                 '  library: %s\n  source : %s' % (a.hadeethenc, row['collection'],
                                                   row['hadith_number'], row.get('text_arabic'), src_ar))

    today = datetime.date.today().isoformat()
    see = dict(x.split('=', 1) for x in a.see_also)
    related = []
    for rid in a.related:
        rp, rh = {}, {}
        for lang in LANGS:
            b = fetch_raw(rid, lang, missing_ok=True)
            if b is None:
                continue
            raws['%s:%s' % (rid, lang)] = b
            rp[lang], rh[lang] = json.loads(b.decode('utf-8')), hashlib.sha256(b).hexdigest()
        try:
            related.append(build_related(rid, rp, rh, today, see.get(rid, '')))
        except ValueError as e:
            sys.exit('STOP: %s - not written.' % e)
        print('  related %s: %s (%s)' % (rid, rp['ar'].get('title'), ', '.join(sorted(related[-1]['langs']))))
    doc = build_doc(row, payloads, hashes, a.hadeethenc, today, collections, related)
    if variant:
        doc['matn_variant'] = variant         # recorded, never silent (OPEN_ITEMS: Arabic reader)
    if doc['library_is_excerpt']:
        print('  the library matn is an EXCERPT - the page shows the full text from the source')
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

    for key, b in raws.items():
        hid, lang = key.split(':') if ':' in key else (a.hadeethenc, key)
        write_bytes(os.path.join(RAW, 'hadeethenc-%s-%s.json' % (hid, lang)), b)
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
