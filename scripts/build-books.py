#!/usr/bin/env python3
"""build-books.py - book translations (Markdown) -> reader sections for /books.

Reads <src>/<lang>/<prefix>_V<NN>_<LANG>_Cyrillic.md (the al-bidaya-wan-nihaya-translation
repo layout) and writes, per language and volume:

  content/books/<book>/<lang>/v<NN>/manifest.json   title, sections, table of contents
  content/books/<book>/<lang>/v<NN>/s<NNN>.json      one reading section: html + footnotes
  content/books/<book>/<lang>/assets/<file>          images the text refers to (served by
                                                     /books/asset, which applies the same
                                                     access rule as the text)

Nothing is rewritten: the translation text is converted, not edited. What changes:
  - HTML comments (translator working notes) are dropped;
  - "## [PDF 409; ...]" page markers become small page labels, not headings;
  - footnotes are collected per volume and printed under the section that cites them.

Usage:
  python scripts/build-books.py --src <path>/translation --book al-bidaya \
      --langs uz tj [--write]
Dry run unless --write.
"""
import argparse, hashlib, html, json, os, re, shutil, sys

try:
    import markdown
except ImportError:
    sys.exit('pip install markdown')

MIN_CHARS = 12000      # a section shorter than this is merged with the next one
MAX_CHARS = 45000      # a longer one is cut at a page marker
PDF_MARK = re.compile(r'^##\s*\[(PDF[^\]]*)\]\s*$')
HEADING = re.compile(r'^(#{1,3})\s+(.+?)\s*$')
FN_DEF = re.compile(r'^\[\^([^\]]+)\]:\s?(.*)$')
FN_REF = re.compile(r'\[\^([^\]]+)\]')
COMMENT = re.compile(r'<!--.*?-->', re.S)
IMG_ASSET = re.compile(r'\]\((assets/[^)\s]+)\)')

MD = markdown.Markdown(extensions=['tables', 'sane_lists'])


def md_html(text):
    MD.reset()
    return MD.convert(text)


def inline_html(text):
    h = md_html(text).strip()
    return re.sub(r'^<p>(.*)</p>$', r'\1', h, flags=re.S)


def read_volume(path):
    raw = open(path, encoding='utf-8').read()
    raw = COMMENT.sub('', raw)
    lines = raw.split('\n')
    # The translators' service preamble (status, audit log) sits between the H1
    # and the first '## ' line in every volume. It is not part of the book: keep
    # the H1, drop the rest of the preamble.
    first = next((i for i, ln in enumerate(lines) if ln.startswith('## ')), None)
    if first is not None:
        lines = [ln for ln in lines[:first] if ln.startswith('# ')] + lines[first:]
    # footnote definitions (may continue on indented lines)
    notes, body, cur = {}, [], None
    for ln in lines:
        m = FN_DEF.match(ln)
        if m:
            cur = m.group(1); notes[cur] = m.group(2); continue
        if cur and ln.startswith('    '):
            notes[cur] += ' ' + ln.strip(); continue
        cur = None
        body.append(ln)
    return body, notes


def blocks_of(lines):
    """Split the body into units that start at a heading or a page marker."""
    units, cur = [], {'kind': 'text', 'lines': []}
    for ln in lines:
        if PDF_MARK.match(ln) or (HEADING.match(ln) and not PDF_MARK.match(ln)):
            if cur['lines'] or cur['kind'] != 'text':
                units.append(cur)
            cur = {'kind': 'mark' if PDF_MARK.match(ln) else 'head', 'lines': [ln]}
        else:
            cur['lines'].append(ln)
    units.append(cur)
    return units


def size(u):
    return sum(len(x) for x in u['lines'])


def sections_of(units):
    """Group units into sections: start a new one at a heading once MIN_CHARS is reached,
    or at a page marker once MAX_CHARS is reached."""
    secs, cur, n = [], [], 0
    for u in units:
        start = (u['kind'] == 'head' and n >= MIN_CHARS) or (u['kind'] == 'mark' and n >= MAX_CHARS)
        if start and cur:
            secs.append(cur); cur, n = [], 0
        cur.append(u); n += size(u)
    if cur:
        if secs and n < MIN_CHARS // 3:
            secs[-1].extend(cur)
        else:
            secs.append(cur)
    return secs


def render_section(units, notes, asset_base, toc, sidx, used_assets):
    out, fn_order, hcount = [], [], 0
    para = []

    def flush():
        if para:
            text = '\n'.join(para)
            text = IMG_ASSET.sub(lambda m: '](' + asset_base + os.path.basename(m.group(1)) + ')', text)
            for m in IMG_ASSET.finditer('\n'.join(para)):
                used_assets.add(os.path.basename(m.group(1)))

            def ref(m):
                k = m.group(1)
                if k not in notes:
                    return m.group(0)
                if k not in fn_order:
                    fn_order.append(k)
                i = fn_order.index(k) + 1
                return f'<sup class="fn"><a href="#fn-{sidx}-{i}" id="fr-{sidx}-{i}">{i}</a></sup>'
            text = FN_REF.sub(ref, text)
            out.append(md_html(text))
            para.clear()

    for u in units:
        first = u['lines'][0]
        m = PDF_MARK.match(first)
        if u['kind'] == 'mark' and m:
            flush()
            out.append(f'<div class="pdf-mark">{html.escape(m.group(1))}</div>')
            para.extend(u['lines'][1:])
        elif u['kind'] == 'head':
            flush()
            hm = HEADING.match(first)
            level = len(hm.group(1))
            hcount += 1
            hid = f'h{sidx}-{hcount}'
            title_html = inline_html(hm.group(2))
            out.append(f'<h{level + 1} id="{hid}">{title_html}</h{level + 1}>')
            toc.append({'level': level, 'title': re.sub('<[^>]+>', '', title_html), 'section': sidx, 'id': hid})
            para.extend(u['lines'][1:])
        else:
            para.extend(u['lines'])
    flush()
    fns = []
    for i, k in enumerate(fn_order, 1):
        fns.append({'n': i, 'html': inline_html(notes[k])})
    return '\n'.join(out), fns


def volume_title(lines):
    for ln in lines:
        m = HEADING.match(ln)
        if m and len(m.group(1)) == 1 and not PDF_MARK.match(ln):
            return re.sub(r'[*_`]', '', m.group(2)).strip()
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='translation/ folder with uz/ tj/ ...')
    ap.add_argument('--book', required=True)
    ap.add_argument('--langs', nargs='+', default=['uz', 'tj'])
    ap.add_argument('--out', default='content/books')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()

    catalog = []
    for lang in a.langs:
        d = os.path.join(a.src, lang)
        files = sorted(f for f in os.listdir(d) if re.search(r'_V(\d+)_.*\.md$', f))
        vols = []
        used_assets = set()
        for f in files:
            vno = int(re.search(r'_V(\d+)_', f).group(1))
            body, notes = read_volume(os.path.join(d, f))
            title = volume_title(body) or f'V{vno:02d}'
            secs = sections_of(blocks_of(body))
            toc, rendered = [], []
            base = f'/books/asset/{a.book}/{lang}/'
            for i, s in enumerate(secs, 1):
                h, fns = render_section(s, notes, base, toc, i, used_assets)
                stitle = next((t['title'] for t in toc if t['section'] == i), None)
                rendered.append({'n': i, 'title': stitle, 'html': h, 'footnotes': fns})
            # a section with no heading of its own takes the last heading before it
            last = title
            for r in rendered:
                if r['title']:
                    last = r['title']
                else:
                    r['title'] = last
            chars = sum(len(r['html']) for r in rendered)
            src_sha = hashlib.sha256(open(os.path.join(d, f), 'rb').read()).hexdigest()
            manifest = {'book': a.book, 'lang': lang, 'volume': vno, 'title': title, 'source_file': f,
                        'source_sha256': src_sha, 'sections': [{'n': r['n'], 'title': r['title']} for r in rendered],
                        'toc': toc, 'footnotes': len(notes)}
            vols.append({'volume': vno, 'title': title, 'sections': len(rendered)})
            print(f'{lang} V{vno:02d}  {len(rendered):3d} sections  {len(toc):4d} headings  {len(notes):3d} notes  '
                  f'{chars // 1024:5d} KB  "{title}"')
            if a.write:
                vd = os.path.join(a.out, a.book, lang, f'v{vno:02d}')
                if os.path.isdir(vd):
                    shutil.rmtree(vd)
                os.makedirs(vd)
                json.dump(manifest, open(os.path.join(vd, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False)
                for r in rendered:
                    json.dump(r, open(os.path.join(vd, f's{r["n"]:03d}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        if a.write:
            ad = os.path.join(a.out, a.book, lang, 'assets')
            os.makedirs(ad, exist_ok=True)
            for name in sorted(used_assets):
                shutil.copyfile(os.path.join(d, 'assets', name), os.path.join(ad, name))
        catalog.append({'lang': lang, 'volumes': vols})
    if a.write:
        json.dump({'book': a.book, 'languages': catalog},
                  open(os.path.join(a.out, a.book, 'catalog.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('written to', os.path.join(a.out, a.book))
    else:
        print('dry run - add --write')


if __name__ == '__main__':
    main()
