#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make-drafts.py - one set file -> the four draft.txt files AND the caption blocks.

Replaces the per-set out/drafts_<n>.py and the hand-written out/caption-<n>.json (automation,
OPEN_ITEMS item 2, 2026-11-03). The words that are ours - title, moral, H block - are written
ONCE per language in out/set-<n>.json; everything else comes from the database:

    {"number": "2749", "slug": "muslim-2749", "library_id": "a783064f-...",
     "langs": {"en": {"title": "If You Did Not Sin",
                      "moral": "This is not permission to sin. ...",
                      "h": "Narrated by Abu Hurairah and recorded in Sahih Muslim, no. 2749, ..."},
               "ru": {...}, "uz": {...}, "tj": {...}}}

S block = the narrator lead-in (scripts/lib/narrator_leadin.py, P337, from the row's narrator)
          + the matn read LIVE from hadith_library, quoted: "..." in EN, «...» in RU/UZ/TJ.
          Quotation marks inside the matn are dropped (P342: nested quotes break stt-validate's
          span pairing) - words identical.
P414: a hadith with a dialogue (a man asks, the Prophet answers) cannot be one quotation after
"the Prophet said:" - that puts the man's words in the Prophet's mouth. A language block may carry
  "dialogue": [["q", "<the Prophet's words>"], ["t", "A man said:"], ["q", "<the man's words>"], ...]
q = quoted, t = the narration between the quotes. The pieces must be the stored matn, letter for
letter, in order (refused otherwise), so nothing is added or dropped; only the quotation marks move.
M = moral, H = h, C = title. Written to out/draft-<slug>-<lang>.txt (CRLF, as the admin writes
them), and out/caption-<n>.json for build-caption.ts gets the same title and moral.
Then each draft goes through lint-content.py and narrate-reel.py --dry-run.

Dry run by default (prints the drafts); --write writes. Refuses to overwrite an existing draft
unless --force - a draft may already carry the operator's corrections.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'lib'))
LANGS = ('en', 'ru', 'uz', 'tj')
COLS = {'en': 'text_english', 'ru': 'text_russian', 'uz': 'text_uzbek_cyrillic', 'tj': 'text_tajik'}
N = '\r\n'


def strip_inner_quotes(s):
    return re.sub(u'[«»"“”„]', '', s).strip()


def quote_matn(matn, lang):
    m = strip_inner_quotes(matn)
    if lang == 'en':
        return '"' + m + '"'
    body = m[:-1] if m.endswith('.') else m
    return u'«' + body + u'».'


def letters(s):
    """Letters and digits only, lower-cased - what check-draft-sync.py compares."""
    return ''.join(ch for ch in s.lower() if ch.isalnum())


def quote_dialogue(parts, matn, lang, caption=False):
    """P414: quote only the spoken parts of a dialogue matn. caption=True (P415): the caption
    convention - guillemets in every language, the period inside them in EN (lib/caption.ts)."""
    if not parts or any(len(p) != 2 or p[0] not in ('q', 't') for p in parts):
        raise ValueError('%s: dialogue must be [["q"|"t", text], ...]' % lang)
    if not any(k == 'q' for k, _ in parts):
        raise ValueError('%s: dialogue has no quoted part' % lang)
    if letters(''.join(t for _, t in parts)) != letters(matn):
        raise ValueError('%s: the dialogue pieces are not the stored matn letter for letter (P414) - '
                         'only the quotation marks may move' % lang)
    out = ''
    for kind, text in parts:
        t = strip_inner_quotes(text)
        if kind == 'q':
            if lang == 'en' and caption:
                piece = u'\u00ab' + t + u'\u00bb'
            elif lang == 'en':
                piece = '"' + t + '"'
            else:
                end = t.endswith('.')
                piece = u'\u00ab' + (t[:-1] if end else t) + u'\u00bb' + ('.' if end else '')
        else:
            piece = t
        if out and not piece[:1] in ',.;:!?':
            out += ' '
        out += piece
    return out


def build_draft(leadin, matn, block, lang):
    """The four lines of draft.txt for one language."""
    for k in ('title', 'moral', 'h'):
        if not (block.get(k) or '').strip():
            raise ValueError('%s: "%s" is empty in the set file' % (lang, k))
    s_body = quote_dialogue(block['dialogue'], matn, lang) if block.get('dialogue') else quote_matn(matn, lang)
    return ['S: ' + leadin + ' ' + s_body,
            'M: ' + block['moral'].strip(),
            'H: ' + block['h'].strip(),
            'C: ' + block['title'].strip()]


def caption_blocks(setfile, row=None):
    """P415: a dialogue set also carries matn_quoted, the matn quoted per speaker, which
    build-caption.ts uses instead of wrapping the whole matn in one pair of guillemets."""
    langs = {}
    for l, b in setfile['langs'].items():
        langs[l] = {'title': b['title'].strip(), 'moral': b['moral'].strip()}
        if b.get('dialogue') and row is not None:
            langs[l]['matn_quoted'] = quote_dialogue(b['dialogue'], row[COLS[l]], l, caption=True)
    return {'hadith_number': setfile['number'], 'id': setfile['library_id'], 'style': 'adults',
            'langs': langs}


def _row(library_id):
    env = {}
    for line in io.open(os.path.join(REPO, '.env.local'), encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    url = (env.get('NEXT_PUBLIC_SUPABASE_URL') or env.get('SUPABASE_URL')).rstrip('/')
    key = env['SUPABASE_SERVICE_ROLE_KEY']
    q = urllib.parse.urlencode({'id': 'eq.' + library_id,
                                'select': 'hadith_number,narrator,book,' + ','.join(COLS.values())})
    rows = json.loads(urllib.request.urlopen(urllib.request.Request(
        url + '/rest/v1/hadith_library?' + q, headers={'apikey': key, 'Authorization': 'Bearer ' + key}),
        timeout=30).read().decode())
    if len(rows) != 1:
        raise SystemExit('FAILED: library id %s returned %d rows' % (library_id, len(rows)))
    return rows[0]


def main(argv=None):
    ap = argparse.ArgumentParser(description='Set file -> draft.txt x4 + caption blocks (dry run unless --write).')
    ap.add_argument('--set', required=True, help='out/set-<n>.json')
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--force', action='store_true', help='overwrite existing drafts')
    args = ap.parse_args(argv)
    # P392 class: the drafts carry ﷺ and Cyrillic; the cp1252 console must not crash the run
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    import narrator_leadin as nl
    s = json.load(io.open(args.set, encoding='utf-8-sig'))
    row = _row(s['library_id'])
    if str(row['hadith_number']) != str(s['number']):
        raise SystemExit('FAILED: library row is #%s, the set file says #%s' % (row['hadith_number'], s['number']))
    table = nl.load_narrators()
    drafts = {}
    for lang in LANGS:
        if lang not in s['langs']:
            continue
        lead = nl.leadin(row['narrator'], lang, table)
        drafts[lang] = build_draft(lead, row[COLS[lang]], s['langs'][lang], lang)
        print('=== %s' % lang)
        print('\n'.join(drafts[lang]))
    if not args.write:
        print('\nDRY RUN - nothing written. Add --write.')
        return 0
    paths = {l: os.path.join(REPO, 'out', 'draft-%s-%s.txt' % (s['slug'], l)) for l in drafts}
    exist = [p for p in paths.values() if os.path.exists(p)]
    if exist and not args.force:
        print('REFUSED - already exist (may carry corrections); --force to overwrite: ' + ', '.join(exist))
        return 1
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    for lang, lines in drafts.items():
        io.open(paths[lang], 'w', encoding='utf-8', newline='').write(N.join(lines) + N)
        assert io.open(paths[lang], encoding='utf-8', newline='').read() == N.join(lines) + N
    cap = os.path.join(REPO, 'out', 'caption-%s.json' % s['number'])
    io.open(cap, 'w', encoding='utf-8').write(json.dumps(caption_blocks(s, row), ensure_ascii=False, indent=2) + '\n')
    print('\nwrote %d drafts + %s' % (len(drafts), os.path.relpath(cap, REPO)))
    for lang in drafts:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'lint-content.py'), paths[lang], '--lang', lang,
                            '--matn', row[COLS[lang]]], capture_output=True, text=True, env=env,
                           encoding='utf-8', errors='replace')
        summary = [l.strip() for l in r.stdout.splitlines() if re.search(r'\d+ fail', l)]
        r2 = subprocess.run([sys.executable, os.path.join(HERE, 'narrate-reel.py'), '--lang', lang, '--slug',
                             s['slug'], '--dry-run'], capture_output=True, text=True, env=env,
                            encoding='utf-8', errors='replace')
        print('  %s  lint: %s | narrate dry-run exit %d' % (lang, summary[-1] if summary else '?', r2.returncode))
    return 0


if __name__ == '__main__':
    sys.exit(main())
