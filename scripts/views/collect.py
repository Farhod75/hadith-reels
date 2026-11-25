"""scripts/views/collect.py - P436: views per reel across Telegram, YouTube, TikTok,
Instagram and Facebook, keyed by the tracker's R id.

WHY. Which hadiths, languages and platforms are working was answered by hand, one
platform at a time, in the browser. The TikTok throttle of 2026-11-23..25 was found
only because someone looked. A table per R id, kept over time, answers it every two
days and shows a stall the day it starts.

HOW
  1. Telegram is read here, from the public page t.me/s/<channel> (no login).
  2. YouTube, TikTok, Instagram and Facebook need the operator's signed-in browser.
     The scheduled run (or a person) runs the browser collectors first, each saving
     JSON with browser_evaluate's `filename`:
       scripts/views/yt.js    -> views-yt.json   (YouTube Studio, Shorts list)
       scripts/views/tt.js    -> views-tt.json   (TikTok Studio, Posts)
       scripts/views/meta.js  -> views-ig.json   (Business Suite Content, filter "Лента Instagram")
       scripts/views/meta.js  -> views-fb.json   (same page, filter "Лента Facebook")
     A missing or stale (>6 h) file is reported, never guessed.
  3. This script joins everything to reel-tracker.md:
       Telegram  - by the message id in the row's notes ("TG 329")
       YouTube   - by the video id in the row's notes (".../shorts/<id>")
       TikTok, Instagram, Facebook - the caption starts with the reel's title (the
       YouTube title before " | "); when a title repeats, the post nearest the R date.
  4. Writes out/views/<date>.csv, appends out/views/history.csv and prints the report
     (also out/views/<date>-report.md).

USAGE
  python scripts/views/collect.py                  # needs the four browser files
  python scripts/views/collect.py --raw <dir>      # where the browser files are
  python scripts/views/collect.py --skip tt,fb     # report without some platforms
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DEFAULT = os.environ.get('HR_PLAYWRIGHT_DIR',
                             r'C:\Users\Farhod\AppData\Local\AnthropicClaude\app-6.28899.6\.playwright-mcp')
OUT = os.path.join(ROOT, 'out', 'views')
CHANNEL = 'SahihHadithReels'
PLATFORMS = ('tg', 'yt', 'tt', 'ig', 'fb')
NAMES = {'tg': 'Telegram', 'yt': 'YouTube', 'tt': 'TikTok', 'ig': 'Instagram', 'fb': 'Facebook (проверить, не в итоге)'}
RU_MONTHS = {'январ': 1, 'феврал': 2, 'март': 3, 'апрел': 4, 'ма': 5, 'июн': 6, 'июл': 7,
             'август': 8, 'сентябр': 9, 'октябр': 10, 'ноябр': 11, 'декабр': 12}
EN_MONTHS = {m: i + 1 for i, m in enumerate(
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}
STALE_HOURS = 6


def num(s):
    """'2 281' / '1,234' / '1.2K' / '3,4 тыс.' / '‑‑' -> int or None."""
    if s is None:
        return None
    t = str(s).replace('\u00a0', ' ').replace('\u202f', ' ').strip()
    if not t or set(t) <= set('-‑–— '):
        return None
    m = re.match(r'^([\d.,\s]+)\s*([KkMmКкМм]|тыс\.?|млн\.?)?', t)
    if not m:
        return None
    body, suf = m.group(1).replace(' ', ''), (m.group(2) or '').lower()
    if suf:
        v = float(body.replace(',', '.'))
        v *= 1_000_000 if suf.startswith(('m', 'м')) else 1000
        return int(round(v))
    return int(re.sub(r'[.,]', '', body) or 0)


def norm(s):
    s = (s or '').lower().replace('ё', 'е')
    s = re.sub(r'[«»"“”„\'’`ʼ|#.,:;!?()\[\]\-–—]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def parse_tracker(path=os.path.join(ROOT, 'reel-tracker.md')):
    reels = []
    for line in io.open(path, encoding='utf-8'):
        if not re.match(r'^\| R\d+ \|', line):
            continue
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        notes = c[-1]
        tg = re.search(r'\bTG (\d+)', notes)
        yt = re.search(r'shorts/([\w-]{11})', notes)
        d = re.match(r'(\d{4}-\d{2}-\d{2})', c[1])
        reels.append({'r': c[0], 'date': d.group(1) if d else '', 'ref': c[2], 'narrator': c[3],
                      'grade': c[4], 'theme': c[5], 'lang': c[7], 'slug': c[9] if len(c) > 9 else '',
                      'tg': int(tg.group(1)) if tg else None, 'yt': yt.group(1) if yt else None})
    return reels


def fetch_tg(oldest, pages=60):
    """{message_id: views} from t.me/s, walking back until `oldest` is passed."""
    out, url = {}, 'https://t.me/s/%s' % CHANNEL
    for _ in range(pages):
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        h = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'replace')
        for m in re.finditer(r'data-post="%s/(\d+)"[\s\S]*?tgme_widget_message_views">([^<]+)<' % CHANNEL, h):
            out[int(m.group(1))] = num(m.group(2))
        prev = re.search(r'<link rel="prev" href="([^"]+)"', h)
        if not prev or (out and min(out) <= oldest):
            break
        url = 'https://t.me' + prev.group(1)
    return out


def load_raw(raw, name):
    p = os.path.join(raw, 'views-%s.json' % name)
    if not os.path.exists(p):
        return None, 'missing'
    age = (dt.datetime.now().timestamp() - os.path.getmtime(p)) / 3600
    d = json.load(io.open(p, encoding='utf-8'))
    if isinstance(d, str):          # browser_evaluate saves the result JSON-encoded
        d = json.loads(d)
    return d, ('stale %.0f h' % age if age > STALE_HOURS else 'ok')


def post_date(s, today):
    """TikTok 'Nov 25, 10:15 AM' (year implied) or Meta '25 ноябрь 2026 г. 14:05' -> date."""
    s = (s or '').strip()
    m = re.match(r'([A-Z][a-z]{2})\s(\d{1,2}),\s(?:(\d{4})\s)?', s)
    if m:
        y = int(m.group(3)) if m.group(3) else today.year
        d = dt.date(y, EN_MONTHS[m.group(1)], int(m.group(2)))
        return d if d <= today else d.replace(year=y - 1)
    m = re.match(r'(\d{1,2})\s(\w+)\s(\d{4})', s)
    if m:
        mon = next((v for k, v in sorted(RU_MONTHS.items(), key=lambda kv: -len(kv[0]))
                    if m.group(2).lower().startswith(k)), None)
        if mon:
            return dt.date(int(m.group(3)), mon, int(m.group(1)))
    return None


def match_captions(reels, titles, rows, views_key, today):
    """{R: views} - a post belongs to the reel whose title its caption starts with."""
    by_title = {}
    for r in reels:
        t = titles.get(r['r'])
        if t:
            by_title.setdefault(norm(t), []).append(r)
    out = {}
    for row in rows:
        cap = norm(row.get('caption'))
        hits = [t for t in by_title if t and cap.startswith(t)]
        if not hits:
            continue
        cands = by_title[max(hits, key=len)]
        pd = post_date(row.get('date'), today)
        if pd and len(cands) > 1:
            cands = sorted(cands, key=lambda r: abs((dt.date.fromisoformat(r['date']) - pd).days)
                           if r['date'] else 9999)
        r = cands[0]
        if pd and r['date'] and abs((dt.date.fromisoformat(r['date']) - pd).days) > 3:
            continue
        if not row.get('date'):
            continue
        v = num(row.get(views_key))
        if v is not None:
            out[r['r']] = max(out.get(r['r'], 0), v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', default=RAW_DEFAULT)
    ap.add_argument('--skip', default='')
    a = ap.parse_args()
    skip = set(x for x in a.skip.split(',') if x)
    today = dt.date.today()
    reels = parse_tracker()
    status, data = {}, {p: {} for p in PLATFORMS}

    if 'tg' not in skip:
        ids = [r['tg'] for r in reels if r['tg']]
        try:
            tgv = fetch_tg(min(ids))
            data['tg'] = {r['r']: tgv.get(r['tg']) for r in reels if r['tg'] and tgv.get(r['tg']) is not None}
            status['tg'] = 'ok'
        except Exception as e:  # noqa: BLE001
            status['tg'] = 'FAILED %s' % e

    titles = {}
    yt, st = (None, 'skipped') if 'yt' in skip else load_raw(a.raw, 'yt')
    status['yt'] = st
    if yt:
        byid = {x['id']: x for x in yt['rows']}
        for r in reels:
            x = byid.get(r['yt'])
            if x:
                titles[r['r']] = x['title'].split(' | ')[0]
                if num(x['views']) is not None:
                    data['yt'][r['r']] = num(x['views'])
    for p, key in (('tt', 'views'), ('ig', 'Просмотры'), ('fb', 'Просмотры')):
        d, st = (None, 'skipped') if p in skip else load_raw(a.raw, p)
        status[p] = st
        if d:
            data[p] = match_captions(reels, titles, d['rows'], key, today)

    os.makedirs(OUT, exist_ok=True)
    stamp = today.isoformat()
    rows = []
    for r in reels:
        vals = {p: data[p].get(r['r']) for p in PLATFORMS}
        # Facebook stays out of the total: for a reel cross-posted from Instagram, Business Suite's FB
        # 'Просмотры' runs within a few views of the IG figure (2 261 vs 2 254 on R299), i.e. it looks
        # like the shared counter, and adding it would count the same views twice. Shown, not summed.
        rows.append(dict(r, **vals, total=sum(v for p, v in vals.items() if v and p != 'fb')))
    fields = ['r', 'date', 'ref', 'theme', 'lang', 'slug'] + list(PLATFORMS) + ['total']
    with io.open(os.path.join(OUT, stamp + '.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    hist = os.path.join(OUT, 'history.csv')
    prev = {}
    if os.path.exists(hist):
        for x in csv.DictReader(io.open(hist, encoding='utf-8-sig')):
            if x['snapshot'] != stamp:
                prev[(x['r'], x['platform'])] = (x['snapshot'], int(x['views']))
    new = not os.path.exists(hist)
    with io.open(hist, 'a', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(['snapshot', 'r', 'platform', 'views'])
        for x in rows:
            for p in PLATFORMS:
                if x[p] is not None:
                    w.writerow([stamp, x['r'], p, x[p]])

    rep = report(rows, status, prev, today)
    io.open(os.path.join(OUT, stamp + '-report.md'), 'w', encoding='utf-8').write(rep)
    print(rep)


def report(rows, status, prev, today):
    L = ['# Просмотры рилсов - %s' % today.isoformat(), '']
    L.append('Источники: ' + ', '.join('%s %s' % (NAMES[p], status.get(p, '-')) for p in PLATFORMS))
    L.append('')
    tot = {p: sum(x[p] or 0 for x in rows) for p in PLATFORMS}
    L.append('**Всего по площадкам:** ' + ', '.join('%s %s' % (NAMES[p], f'{tot[p]:,}'.replace(',', ' '))
                                                for p in PLATFORMS))
    grow = {}
    for x in rows:
        for p in PLATFORMS:
            pv = prev.get((x['r'], p))
            if pv and x[p] is not None:
                grow[p] = grow.get(p, 0) + x[p] - pv[1]
    if grow:
        L.append('**Прирост с прошлого замера:** ' + ', '.join(
            '%s +%s' % (NAMES[p], grow[p]) for p in PLATFORMS if p in grow))
    L.append('')

    def recent(days):
        return [x for x in rows if x['date'] and (today - dt.date.fromisoformat(x['date'])).days <= days]
    r7 = recent(7)
    L.append('## Последние 7 дней (%d рилсов)' % len(r7))
    for p in PLATFORMS:
        have = [x for x in r7 if x[p] is not None]
        zero = [x['r'] for x in have if x[p] == 0]
        if have:
            L.append('- %s: всего %d, в среднем %d на рилс; ноль у %d из %d%s' % (
                NAMES[p], sum(x[p] for x in have), sum(x[p] for x in have) // len(have),
                len(zero), len(have), (' (' + ', '.join(zero[:12]) + ')') if zero else ''))
    L.append('')
    r14 = sorted(recent(14), key=lambda x: -x['total'])[:10]
    L.append('## Топ-10 за 14 дней')
    for x in r14:
        L.append('- %s %s %s (%s): %d - %s' % (x['r'], x['lang'], x['ref'], x['theme'], x['total'], ', '.join(
            '%s %s' % (p.upper(), x[p]) for p in PLATFORMS if x[p] is not None)))
    L.append('')
    r30 = recent(30)
    for key, title in (('lang', 'По языкам (30 дней, среднее на рилс)'), ('theme', 'По темам (30 дней, среднее на рилс)')):
        g = {}
        for x in r30:
            g.setdefault(x[key], []).append(x['total'])
        L.append('## ' + title)
        for k, v in sorted(g.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))[:12]:
            L.append('- %s: %d (%d рилсов)' % (k, sum(v) // len(v), len(v)))
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    sys.exit(main())
