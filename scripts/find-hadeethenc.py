#!/usr/bin/env python3
# scripts/find-hadeethenc.py
# ============================================================
# P387 backfill helper: which HadeethEnc entry is this library hadith?
# Read-only. For each hadith it asks HadeethEnc's own site search with the
# library's Arabic matn and keeps only results whose Arabic CONTAINS the
# library matn (fetch-explanation.same_hadith) - or differs from it by at most
# two words, reported as a variant for a human to read. Nothing is written
# except the report.
#
#   python scripts/find-hadeethenc.py --published        # every hadith in reel-tracker.md
#   python scripts/find-hadeethenc.py --hadith "Sahih Muslim #2699"
#
# Report: out/hadeethenc-map.tsv
#   collection  number  library_id  status  hadeethenc_id  note
#   status: match | variant | none | ambiguous | no_library_row
#
# The search endpoint is the one hadeethenc.com/ar/hybrid-search posts to.
# One request per hadith, 1.5 s apart. Stdlib only.
# ============================================================
import argparse
import importlib.util
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
_spec = importlib.util.spec_from_file_location('fetch_explanation', os.path.join(HERE, 'fetch-explanation.py'))
fe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fe)

SEARCH = 'https://hadeethenc.com/ar/hybrid-search/query'
TRACKER_ROW = re.compile(r'^\|\s*R\d+\s*\|[^|]*\|\s*([^|#]+?)\s*#\s*(\d+[a-z]?)\s*\|')


def published_hadiths(tracker_text):
    """[(collection, number)] in first-published order, each once."""
    seen, out = set(), []
    for line in tracker_text.splitlines():
        m = TRACKER_ROW.match(line)
        if m:
            key = (m.group(1).strip(), m.group(2))
            if key not in seen:
                seen.add(key)
                out.append(key)
    return out


def search_query(arabic, words=14):
    """The first words of the matn, letters only - enough for the lexical side."""
    ws = [fe.letters(w) for w in (arabic or '').split() if fe.letters(w)]
    return ' '.join(ws[:words])


def tail_query(arabic, words=12):
    """P401: the last words of the matn. A matn that opens with a narrative ("a man came to the
    Messenger of Allah and said...") shares its opening with dozens of entries; Bukhari #5971's
    first query returned twelve of them and not its own. The end is where a hadith is itself."""
    ws = [fe.letters(w) for w in (arabic or '').split() if fe.letters(w)]
    return ' '.join(ws[-words:])


def classify(library_arabic, results):
    """PURE. results: [{'id', 'matn'}]. -> (status, id, note)."""
    exact = [r for r in results if fe.same_hadith(library_arabic, r.get('matn', ''))]
    if len(exact) == 1:
        return 'match', exact[0]['id'], ''
    if len(exact) > 1:
        return 'ambiguous', ','.join(r['id'] for r in exact), 'several entries contain the matn'
    near = []
    for r in results:
        missing, extra = fe.matn_word_diff(library_arabic, r.get('matn', ''))
        if len(missing) + len(extra) <= 2:
            near.append((r, missing, extra))
    if len(near) == 1:
        r, missing, extra = near[0]
        return 'variant', r['id'], 'missing: %s | extra: %s' % (' '.join(missing) or '-', ' '.join(extra) or '-')
    if near:
        return 'ambiguous', ','.join(r['id'] for r, _, _ in near), 'several near matches'
    return 'none', '', ''


def search(query):
    body = json.dumps({'query': query, 'mode': 'hybrid', 'target': 'remote'}).encode('utf-8')
    req = urllib.request.Request(SEARCH, data=body, method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'Accept': 'application/json', 'User-Agent': fe.UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8')).get('results', [])


def library_by_ref(collection, number):
    env = fe.load_env(os.path.join(ROOT, '.env.local'))
    base, key = env['NEXT_PUBLIC_SUPABASE_URL'], env['SUPABASE_SERVICE_ROLE_KEY']
    # P147: hadith_number is not unique across collections - always both.
    q = urllib.parse.urlencode({'collection': 'eq.' + collection, 'hadith_number': 'eq.' + number,
                                'select': 'id,text_arabic,grade'})
    req = urllib.request.Request(base.rstrip('/') + '/rest/v1/hadith_library?' + q,
                                 headers={'apikey': key, 'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--published', action='store_true', help='every hadith in reel-tracker.md')
    g.add_argument('--hadith', action='append', help='"Sahih Muslim #2699" (repeatable)')
    ap.add_argument('--out', help='report path (default: out/hadeethenc-map.tsv with --published; '
                    'none with --hadith, so a one-off lookup never overwrites the full map)')
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8')

    if a.published:
        with open(os.path.join(ROOT, 'reel-tracker.md'), encoding='utf-8') as fh:
            todo = published_hadiths(fh.read())
    else:
        todo = []
        for h in a.hadith:
            coll, num = h.rsplit('#', 1)
            todo.append((coll.strip(), num.strip()))

    lines = ['collection\tnumber\tlibrary_id\tstatus\thadeethenc_id\tnote']
    for i, (coll, num) in enumerate(todo):
        rows = library_by_ref(coll, num)
        if len(rows) != 1:
            lines.append('%s\t%s\t\tno_library_row\t\t%d rows' % (coll, num, len(rows)))
            print('%-22s #%-6s %d library rows' % (coll, num, len(rows)))
            continue
        row = rows[0]
        if i:
            time.sleep(1.5)
        try:
            results = search(search_query(row['text_arabic']))
        except Exception as e:                       # report, never stop the batch
            lines.append('%s\t%s\t%s\terror\t\t%s' % (coll, num, row['id'], e))
            print('%-22s #%-6s search error: %s' % (coll, num, e))
            continue
        status, hid, note = classify(row['text_arabic'], results)
        if status == 'none':                     # P401: try the end of the matn too
            time.sleep(1.5)
            try:
                more = search(tail_query(row['text_arabic']))
            except Exception:
                more = []
            seen = {r.get('id') for r in results}
            status, hid, note = classify(row['text_arabic'], results + [r for r in more if r.get('id') not in seen])
        lines.append('\t'.join([coll, num, row['id'], status, hid, note]))
        print('%-22s #%-6s %-10s %-8s %s' % (coll, num, status, hid, note))

    out = a.out or (os.path.join(ROOT, 'out', 'hadeethenc-map.tsv') if a.published else None)
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(lines) + '\n')
        print('report: %s' % os.path.relpath(out, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
