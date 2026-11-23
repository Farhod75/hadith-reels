"""docs_set.py <config.json> - tracker/retro/changelog/open-items for a published adults set."""
import json, io, os, re, sys
cfg = json.load(io.open(sys.argv[1], encoding='utf-8'))
def rd(p): return io.open(p, encoding='utf-8').read()
def wr(p, s): io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
def rep(s, a, b):
    assert s.count(a) == 1, (a[:80], s.count(a)); return s.replace(a, b)
slug, num, date = cfg['slug'], cfg['number'], cfg['date']
L = ['en', 'ru', 'uz', 'tj']
R = cfg['r_first']; rn = {l: 'R%d' % (R + i) for i, l in enumerate(L)}
rng = 'R%d-R%d' % (R, R + 3)
sub = {'en': 'YES - scribe-srt.py (P423, P425); stt-validate clean', 'ru': 'YES - scribe-srt.py (P423, P425); stt-validate clean',
       'uz': 'YES - scribe-srt.py (P422); stt-validate clean', 'tj': 'YES - scribe-srt.py (P422); stt-validate clean'}
W = 'out/work/adults/%s/%%s/adults-%%s-%s-%%s' % (slug, slug)
rows = []
for i, l in enumerate(L):
    j = json.load(io.open(W % (l, l, 'render.json'), encoding='utf-8'))
    dur = round(sum(j['sceneDurations']), 1); mb = round(os.path.getsize(W % (l, l, 'reel.mp4')) / 1048576, 1)
    rows.append('| %s | %s | %s #%s | %s | Sahih | %s | %s | %s | Adults | %s | adults-%s-%s-story.mp3 | adults-%s-%s-moral.mp3 | adults-%s-%s-narration.mp3 | %s | adults-%s-%s-bg-mixed.mp4 | %s | %s | adults-%s-%s-reel.mp4 | %ss | %s MB | TG %d. %sCover on %s. YouTube https://youtube.com/shorts/%s. |' % (
        rn[l], date, cfg['collection'], num, cfg['narrator'], cfg['theme'], cfg['tags'], l.upper(), slug, l, slug, l, slug, l, slug,
        ', '.join(j['scenes']), l, slug, cfg['beds'][l], sub[l], l, slug, dur, mb, cfg['tg_first'] + i, cfg['notes'][l], cfg['covers'][l], cfg['yt'][l]))
t = rd('reel-tracker.md')
last = [x for x in t.split('\n') if x.startswith('| R%d |' % (R - 1))][0]
t = rep(t, last + '\n', last + '\n' + '\n'.join(rows) + '\n')
h = [x for x in t.split('\n') if x.startswith(cfg['after_hadith'])][0]
t = rep(t, h + '\n', h + '\n' + cfg['hadith_row'] + '\n')
s = [x for x in t.split('\n') if x.startswith(cfg['after_scene'])][0]
t = rep(t, s + '\n', s + '\n' + cfg['scene_row'] + '\n')
m = re.search(r'^\| %s \| (\d+) \| ([^|]+) \|' % re.escape(cfg['theme']), t, re.M)
if m:
    t = t[:m.start()] + '| %s | %d | %s, %s |' % (cfg['theme'], int(m.group(1)) + 4, m.group(2).strip(), rng) + t[m.end():]
else:
    raise SystemExit('theme row missing: ' + cfg['theme'])
for l in L:
    name = cfg['beds'][l]
    m = re.search(r'^\| %s \| (\d+) \| R\d+ \| ([^|\n]*?) \|$' % re.escape(name), t, re.M); assert m, name
    t = t[:m.start()] + '| %s | %d | %s | %s, %s |' % (name, int(m.group(1)) + 1, rn[l], m.group(2), rn[l]) + t[m.end():]
def bump(pat, f):
    global t
    m = re.search(pat, t, re.M); assert m, pat
    t = t[:m.start()] + f(m) + t[m.end():]
bump(r'\| Total reels posted \| (\d+) \|', lambda m: '| Total reels posted | %d |' % (int(m.group(1)) + 4))
bump(r'\| Adults reels \| (\d+) \|', lambda m: '| Adults reels | %d |' % (int(m.group(1)) + 4))
bump(r'\| Hadiths used \(unique\) \| (\d+) \|', lambda m: '| Hadiths used (unique) | %d |' % (int(m.group(1)) + 1))
bump(r'\| Library rows \| (\d+) \((\d+) used, (\d+) unused[^)]*\) \|', lambda m: '| Library rows | %s (%d used, %d unused - %s) |' % (m.group(1), int(m.group(2)) + 1, int(m.group(3)) - 1, date))
bump(re.escape(cfg['collection']) + r' ×(\d+)', lambda m: '%s ×%d' % (cfg['collection'], int(m.group(1)) + 4))
bump(re.escape(cfg['narrator']) + r' ×(\d+)', lambda m: '%s ×%d' % (cfg['narrator'], int(m.group(1)) + 4))
bump(r'\*\*(\d+) reels \((\d+) adults\) from (\d+) hadiths\.\*\* (\d+) of (\d+) library rows',
     lambda m: '**%d reels (%d adults) from %d hadiths.** %d of %s library rows' % (int(m.group(1)) + 4, int(m.group(2)) + 4, int(m.group(3)) + 1, int(m.group(4)) + 1, m.group(5)))
bump(r'\);\s*\n(\d+) remain\.', lambda m: ');\n%d remain.' % (int(m.group(1)) - 1))
wr('reel-tracker.md', t)
r = rd('reel-retro.md').rstrip('\n') + '\n\n## %s - %s #%s - %s\n\n%s\n\n---\n' % (rng, cfg['collection'], num, date, cfg['retro'].strip())
wr('reel-retro.md', r)
c = rd('CHANGELOG.md'); wr('CHANGELOG.md', cfg['changelog'].strip() + '\n\n---\n\n' + c)
o = rd('OPEN_ITEMS.md'); a = [x for x in o.split('\n') if x.startswith(cfg['after_open'])][0]
o = rep(o, a + '\n', cfg['open_line'].rstrip('\n') + '\n' + a + '\n'); wr('OPEN_ITEMS.md', o)
print('docs ok', rng)
