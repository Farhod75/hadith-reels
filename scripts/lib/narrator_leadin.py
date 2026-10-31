"""scripts/lib/narrator_leadin.py - P337: the narrated story block opens with
the narrator, taken from hadith_library, in a fixed form.

WHY. On the tirmidhi-1161 set only the UZ reel named Umm Salamah. The operator's
rule: do not omit and do not add. The same matn reaches us through different
companions, and each is a different record - the project has already met Abu
Bakra (Nufay' ibn al-Harith) beside Abu Bakr as-Siddiq, one letter apart, two
people (fix_patterns.md P-entry on Abu Bakra). So the narrator is said in every
language, and it is never generated: the name comes from hadith_library.narrator
and its localised form from lib/refs.ts NARRATORS - the table the caption
reference line already uses, so the voice and the caption cannot disagree.

    leadin(narrator, lang, table) -> the exact opening of S
    check_story(story, narrator, lang, table) -> [] or the problems
    db_narrator(slug) -> hadith_library.narrator for collection + number

narrate-reel.py calls these and refuses to spend on a story block that does not
open with the lead-in. A narrator missing from the table is refused too, rather
than falling back to Latin the way the caption line does.
"""
import io
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REFS = os.path.join(ROOT, 'lib', 'refs.ts')

ENTRY = re.compile(
    r"""^\s*(['"])(?P<name>.+?)\1\s*:\s*\{\s*ru:\s*'(?P<ru>[^']*)',\s*"""
    r"""uz:\s*'(?P<uz>[^']*)',\s*tj:\s*'(?P<tj>[^']*)'"""
    r"""(?:,\s*h:\s*'(?P<h>m|f|pair)')?\s*\},?\s*$""", re.M)

HON_EN = {'m': 'him', 'f': 'her', 'pair': 'them'}
HON_RU = {'m': 'им', 'f': 'ею', 'pair': 'ими'}
HON_UZ_TJ = {'m': 'анҳу', 'f': 'анҳо', 'pair': 'анҳумо'}


def load_narrators(path=REFS):
    """Parse the NARRATORS object out of lib/refs.ts. Refuses a partial parse:
    every quoted entry line in the block must be understood, so a format
    change cannot silently drop a narrator."""
    with io.open(path, encoding='utf-8') as fh:
        text = fh.read().replace('\r\n', '\n')
    start = text.index('export const NARRATORS')
    end = text.index('\n}', start)
    block = text[start:end]
    out = {}
    for m in ENTRY.finditer(block):
        out[m.group('name')] = {'ru': m.group('ru'), 'uz': m.group('uz'),
                                'tj': m.group('tj'), 'h': m.group('h') or 'm'}
    quoted = [l for l in block.split('\n')[1:] if re.match(r"""^\s*['"]""", l)]
    if len(quoted) != len(out):
        raise ValueError('lib/refs.ts NARRATORS: %d entry lines, %d parsed - '
                         'the line format changed' % (len(quoted), len(out)))
    return out


def leadin(narrator, lang, table):
    e = table[narrator]
    h = e['h']
    if lang == 'en':
        return ('%s (may Allah be pleased with %s) narrated that the Prophet '
                '\ufdfa said:' % (narrator, HON_EN[h]))
    if lang == 'ru':
        verb = 'передала' if h == 'f' else 'передал'
        return ('%s, да будет доволен %s Аллах, %s, что Пророк \ufdfa сказал:'
                % (e['ru'], HON_RU[h], verb))
    if lang == 'uz':
        return ('%s розияллоҳу %sдан ривоят қилинади: Пайғамбар соллаллоҳу '
                'алайҳи ва саллам айтдилар:' % (e['uz'], HON_UZ_TJ[h]))
    if lang == 'tj':
        return ('Аз %s розияллоҳу %s ривоят аст, ки Пайғамбар соллаллоҳу '
                'алайҳи ва саллам фармуданд:' % (e['tj'], HON_UZ_TJ[h]))
    raise ValueError('no lead-in for lang %r' % lang)


def _norm(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s or '')).strip()


def check_story(story, narrator, lang, table):
    if not narrator:
        return ['hadith_library has no narrator for this row - fill it before '
                'narrating']
    if narrator not in table:
        return ['narrator %r is not in lib/refs.ts NARRATORS - add it with all '
                'three forms (and h: if not m) before narrating' % narrator]
    want = leadin(narrator, lang, table)
    if not _norm(story).startswith(_norm(want)):
        return ['S must open with exactly: %s' % want]
    return []


def db_narrator(slug):
    """hadith_library.narrator for a slug like tirmidhi-1161. Filters on the
    collection as well as the number (P147: the number alone is not a key)."""
    import importlib.util
    import json
    import urllib.parse
    import urllib.request

    def _load(name, rel):
        spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    coll_slug, number = slug.rsplit('-', 1)
    pc = _load('_pc', os.path.join('scripts', 'promote-candidates.py'))
    al = _load('_al', os.path.join('scripts', 'audit-library.py'))
    collection = pc.library_collection(coll_slug)
    env = al.load_env(os.path.join(ROOT, '.env.local'))
    base, _ = al.pick(env, al.URL_KEYS)
    key, _ = al.pick(env, al.SERVICE_KEYS)
    q = urllib.parse.urlencode({'select': 'narrator', 'collection': 'eq.' + collection,
                                'hadith_number': 'eq.' + number})
    req = urllib.request.Request('%s/rest/v1/hadith_library?%s' % (base.rstrip('/'), q),
                                 headers={'apikey': key, 'Authorization': 'Bearer ' + key})
    rows = json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8'))
    if len(rows) != 1:
        raise ValueError('%d rows for %s #%s' % (len(rows), collection, number))
    return rows[0]['narrator']
