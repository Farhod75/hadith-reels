# -*- coding: utf-8 -*-
"""P422/P423: write the narration SRT for a UZ, TJ, EN or RU reel from our text + Scribe word timings.

    python scripts/scribe-srt.py --lang uz --slug muslim-105 [--style adults] [--force]

Reads out/work/<style>/<slug>/<lang>/<base>-story.mp3|.txt and -moral.mp3|.txt (the text that
was sent to TTS), asks ElevenLabs Scribe v3 for word timings of each mp3 (cached beside the mp3,
re-asked only when the mp3 changes), lines our words up with Scribe's (lib/scribe_align.py) and
writes <base>-narration.srt on render-reel's timeline: story, 0.5 s pause (P135), moral.
It also writes render-reel's P211 stamp (<srt>.src), so render-reel keeps the file and a
re-narration discards it. Exit 0 written or already fresh; 3 alignment too poor to burn; 2 error.
Cost: Scribe at the speech-to-text rate, cents per reel.
"""
import argparse, importlib.util, io, json, os, re, subprocess, sys, urllib.error, urllib.request, uuid

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'scripts', 'lib'))
import scribe_align as sa  # noqa: E402

FFPROBE = r'C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe'
PAUSE = 0.5                       # render-reel Step 4 apad (P135)
SCRIBE_LANG = {'uz': 'uz', 'tj': 'tg', 'en': 'en', 'ru': 'ru'}   # en/ru since P423
MAX_COST, MAX_UNMATCHED = 0.25, 0.10
# P423: formulas a cue must not be split inside (the spoken honorifics; spelled variants as TTS got them)
HOLD = ['peace be upon him', 'may allah be pleased with him', 'да благословит его аллах и приветствует',
        'да будет доволен им аллах', 'соллаллоҳу алайҳи ва саллам', 'саллаллоҳу алайҳи васаллам',
        'салаллоҳу алайҳи васаллам', 'розияллоҳу анҳу', 'розияллоҳу анҳудан']


def hold_indices(words, spoken):
    norm = [re.sub(r'[^\w]', '', w.lower()) for w in words]
    out = set()
    for ph in HOLD + [spoken.lower()]:
        toks = [re.sub(r'[^\w]', '', x) for x in ph.split()]
        n = len(toks)
        for i in range(len(norm) - n + 1):
            if norm[i:i + n] == toks:
                out.update(range(i, i + n - 1))
    return out


def _stt_validate():
    spec = importlib.util.spec_from_file_location('stt_validate', os.path.join(REPO, 'scripts', 'stt-validate.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def api_key():
    for line in io.open(os.path.join(REPO, '.env.local'), encoding='utf-8', errors='replace'):
        m = re.match(r'\s*ELEVENLABS_API_KEY\s*=\s*(.+?)\s*$', line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    raise SystemExit('ELEVENLABS_API_KEY not in .env.local')


def ticks(path):
    """render-reel's P211 fingerprint uses .NET LastWriteTimeUtc.Ticks."""
    return os.stat(path).st_mtime_ns // 100 + 621355968000000000


def fingerprint(story, moral):
    return '%d:%d|%d:%d' % (os.path.getsize(story), ticks(story), os.path.getsize(moral), ticks(moral))


def duration(path):
    return float(subprocess.check_output([FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
                                          '-of', 'csv=p=0', path]).decode().strip())


def scribe(path, lang, key):
    cache = path + '.scribe.json'
    fp = '%d:%d' % (os.path.getsize(path), ticks(path))
    if os.path.exists(cache):
        c = json.load(io.open(cache, encoding='utf-8'))
        if c.get('fp') == fp:
            return c['words']
    b = '----s' + uuid.uuid4().hex
    parts = [('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (b, n, v)).encode('utf-8')
             for n, v in (('model_id', 'scribe_v3'), ('language_code', SCRIBE_LANG[lang]),
                          ('timestamps_granularity', 'word'))]
    parts += [('--%s\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\n'
               'Content-Type: audio/mpeg\r\n\r\n' % b).encode(), open(path, 'rb').read(),
              ('\r\n--%s--\r\n' % b).encode()]
    req = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text', data=b''.join(parts),
                                 headers={'xi-api-key': key, 'Content-Type': 'multipart/form-data; boundary=' + b})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        raise SystemExit('Scribe %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]))
    words = [{'text': w['text'], 'start': w['start'], 'end': w['end']}
             for w in r.get('words', []) if w.get('type', 'word') == 'word']
    io.open(cache, 'w', encoding='utf-8').write(json.dumps({'fp': fp, 'model': 'scribe_v3', 'words': words},
                                                           ensure_ascii=False))
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', required=True, choices=sorted(SCRIBE_LANG))
    ap.add_argument('--slug', required=True)
    ap.add_argument('--style', default='adults')
    ap.add_argument('--force', action='store_true', help='rewrite even when the SRT is fresh')
    ap.add_argument('--out', help='write here instead of the narration SRT (a trial; no stamp)')
    a = ap.parse_args()
    base = '%s-%s-%s' % (a.style, a.lang, a.slug)
    w = os.path.join(REPO, 'out', 'work', a.style, a.slug, a.lang)
    story, moral = os.path.join(w, base + '-story.mp3'), os.path.join(w, base + '-moral.mp3')
    srt = os.path.join(w, base + '-narration.srt')
    trial = bool(a.out)
    if trial:
        srt = os.path.abspath(a.out)
    for p in (story, moral, story[:-4] + '.txt', moral[:-4] + '.txt'):
        if not os.path.exists(p):
            print('scribe-srt: missing %s' % p); return 2
    fp = fingerprint(story, moral)
    stamp = srt + '.src'
    if not a.force and not trial and os.path.exists(srt) and os.path.exists(stamp) and io.open(stamp).read().strip() == fp:
        print('scribe-srt %s %s: SRT fresh - kept' % (a.slug, a.lang)); return 0
    spoken = _stt_validate().PROPHET_SPOKEN[a.lang]
    key = api_key()
    offset = duration(story) + PAUSE
    words, times, worst = [], [], []
    for mp3, off in ((story, 0.0), (moral, offset)):
        text = io.open(mp3[:-4] + '.txt', encoding='utf-8-sig').read().strip()
        text = re.sub(r'\s*(ﷺ|\ufdfa)\s*', ' %s ' % spoken, text)
        # P425: the expansion leaves a space before a following , or : - «приветствует :»
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        src = text.split()
        t, cost, miss_s, miss_h = sa.align(src, scribe(mp3, a.lang, key))
        worst.append((cost, (miss_s + miss_h) / float(max(len(src), 1))))
        words += src
        times += [(s + off, e + off) for s, e in t]
    cost = max(c for c, _ in worst); miss = max(m for _, m in worst)
    print('scribe-srt %s %s: %d words, alignment cost %.2f, unmatched %.0f%%' % (a.slug, a.lang, len(words), cost, miss * 100))
    if cost > MAX_COST or miss > MAX_UNMATCHED:
        print('  REFUSED: timings too uncertain to burn (limits cost %.2f, unmatched %.0f%%) - P078 stays for this reel'
              % (MAX_COST, MAX_UNMATCHED * 100))
        return 3
    io.open(srt, 'w', encoding='utf-8', newline='\n').write(sa.to_srt(sa.cues(words, times, hold=hold_indices(words, spoken))))
    if not trial:
        io.open(stamp, 'w', encoding='utf-8', newline='').write(fp)
    print('  wrote %s' % os.path.relpath(srt, REPO))
    return 0


if __name__ == '__main__':
    sys.exit(main())
