#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make-covers.py - a YouTube cover per language, so the legs of one set do not look like one video.

  python scripts/make-covers.py --number 223                  # UZ and TJ (the default)
  python scripts/make-covers.py --number 223 --langs uz tj en
  python scripts/make-covers.py --number 223 --scene uz=iftar  # override the scene for a language

P374 (operator 2026-11-06): desktop YouTube Studio offers three frames of its own choosing or
"Upload file". Search, the home page and the channel page show the cover, and four identical
covers read as one video - a viewer opens one and never learns the hadith is there in his
friend's language. EN and RU are told apart by their burned-in subtitles; UZ and TJ are not,
so they get a cover each: a DIFFERENT scene from the set and the title in that language.

The scenes come from each leg's render sidecar (adults-<lang>-<slug>-render.json, what that
reel actually shows - the UZ leg's slowed -s copies included), else from out/clips-<n>.json.
The title comes from out/set-<n>.json, else from the first line of out/caption-<n>-<lang>.txt,
which also gives the source line. All are found at the top of out/, under out/work/** or under
out/published/** (after tidy-out). Grabs one frame from each chosen clip
(out/backgrounds/new or normalized, 1080x1920) with ffmpeg and writes
out/cover-<n>-<lang>.jpg (1080x1920, under 2 MB). Free: no API is called.

The text sits in the middle band (y 560-1360) so a crop to 3:2 or 1:1 keeps it. A title with
a character the font cannot draw stops the run (no tofu boxes on a cover).
"""
import argparse
import glob
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, 'out')
LANGS = ('en', 'ru', 'uz', 'tj')
DEFAULT_LANGS = ('uz', 'tj')          # operator 2026-11-06: EN/RU have subtitles
LABEL = {'en': 'ENGLISH', 'ru': 'РУССКИЙ', 'uz': 'ЎЗБЕКЧА', 'tj': 'ТОҶИКӢ'}
W, H = 1080, 1920
TEXT_W = 940
FONTS = [r'C:\Windows\Fonts\arialbd.ttf', r'C:\Windows\Fonts\segoeuib.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']


# ---------------------------------------------------------------- pure helpers (tested)

def pick_scenes(clips, langs, overrides=None):
    """{lang: clip} - one clip per language, all different, spread across the set and never
    the first clip when there are enough (the reel opens on it, so YouTube's own suggestions
    tend to come from it). overrides {lang: substring} wins. Pure."""
    overrides = overrides or {}
    n, m = len(clips), len(langs)
    if n < m:
        raise ValueError('%d clips for %d covers - each language needs its own scene' % (n, m))
    out = {}
    for i, lang in enumerate(langs):
        idx = int(round((i + 1) * n / float(m + 1)))
        if n > m and idx == 0:
            idx = 1
        out[lang] = clips[min(idx, n - 1)]
    for lang, key in overrides.items():
        hits = [c for c in clips if key in c]
        if len(hits) != 1:
            raise ValueError('--scene %s=%s matches %d clips: %s' % (lang, key, len(hits), hits))
        out[lang] = hits[0]
    used = list(out.values())
    if len(set(used)) != len(used):
        raise ValueError('two languages on one scene: %s' % out)
    return out


def wrap(words, fits):
    """Greedy line wrap: fits(text) -> bool says whether a line is narrow enough. Pure."""
    lines, cur = [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if cur and not fits(trial):
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def parse_overrides(items):
    out = {}
    for it in items or []:
        if '=' not in it:
            raise ValueError('--scene takes lang=name, got %r' % it)
        k, v = it.split('=', 1)
        out[k.strip()] = v.strip()
    return out


# ---------------------------------------------------------------- files

def same_position(base, picks, scenes_by_lang):
    """{lang: clip} - each language's own clip at the position its pick holds in `base`, so a
    leg rendered on slowed copies (-s) gets its own file of the same scene. Pure."""
    out = {}
    for lang, clip in picks.items():
        own = scenes_by_lang.get(lang) or base
        out[lang] = own[base.index(clip)] if len(own) == len(base) else clip
    return out


def find_one(name):
    direct = os.path.join(OUT, name)
    if os.path.isfile(direct):
        return direct
    hits = sorted(glob.glob(os.path.join(OUT, 'work', '**', name), recursive=True)
                  + glob.glob(os.path.join(OUT, 'published', '**', name), recursive=True))
    return hits[0] if hits else None


def render_sidecars(number):
    """{lang: scenes} from adults-<lang>-<slug>-render.json files of this set."""
    out = {}
    for root in ('work', 'published'):
        for p in glob.glob(os.path.join(OUT, root, '**', '*-%s-render.json' % number), recursive=True):
            m = re.match(r'^[a-z]+-([a-z]{2})-[a-z-]+-%s-render\.json$' % number, os.path.basename(p))
            if m and m.group(1) not in out:
                out[m.group(1)] = json.load(io.open(p, encoding='utf-8-sig')).get('scenes') or []
    return out


def title_for(number, lang, st):
    if st and lang in st.get('langs', {}):
        return st['langs'][lang]['title']
    cap = find_one('caption-%s-%s.txt' % (number, lang))
    if cap:
        return io.open(cap, encoding='utf-8').read().strip().split('\n')[0].strip()
    return None


def clip_path(name):
    for sub in ('new', 'normalized'):
        p = os.path.join(OUT, 'backgrounds', sub, name)
        if os.path.isfile(p):
            return p
    return None


def source_line(number, lang):
    cap = find_one('caption-%s-%s.txt' % (number, lang))
    if not cap:
        return ''
    spec = importlib.util.spec_from_file_location('platform_texts', os.path.join(HERE, 'platform-texts.py'))
    pt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pt)
    coll, num = pt.collection_and_number(pt.parse(io.open(cap, encoding='utf-8').read())['ref'])
    return ('%s %s' % (coll, num)).strip()


def ffmpeg_bin():
    spec = importlib.util.spec_from_file_location('mix_gap', os.path.join(HERE, 'mix-gap.py'))
    mg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mg)
    return mg.ffmpeg_bin()


def grab_frame(clip, at, dest):
    r = subprocess.run([ffmpeg_bin(), '-y', '-v', 'error', '-ss', str(at), '-i', clip,
                        '-frames:v', '1', dest], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(dest):
        raise SystemExit('FAILED: frame from %s: %s' % (clip, r.stderr.strip()))


# ---------------------------------------------------------------- drawing

def load_font(size):
    from PIL import ImageFont
    for f in FONTS:
        if os.path.isfile(f):
            return ImageFont.truetype(f, size)
    raise SystemExit('FAILED: no bold font found (%s)' % ', '.join(FONTS))


def missing_glyphs(font, text):
    """Characters the font draws as its .notdef box."""
    from PIL import Image, ImageDraw

    def ink(c):
        im = Image.new('L', (font.size * 2, font.size * 2), 0)
        ImageDraw.Draw(im).text((font.size // 2, font.size // 2), c, font=font, fill=255)
        return im.tobytes()
    notdef = ink(u'\U000F0000')
    return sorted({c for c in text if not c.isspace() and ink(c) == notdef})


def compose(frame_path, title, label, source, dest):
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
    im = Image.open(frame_path).convert('RGB')
    s = max(W / float(im.width), H / float(im.height))
    im = im.resize((int(im.width * s + 0.5), int(im.height * s + 0.5)), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((l, t, l + W, t + H))

    shade = Image.new('L', (W, H), 60)                     # whole frame a little darker
    band = Image.new('L', (W, H), 0)
    ImageDraw.Draw(band).rectangle((0, 560, W, 1360), fill=150)
    band = band.filter(ImageFilter.GaussianBlur(70))
    alpha = ImageChops.lighter(shade, band)
    im = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), im, alpha)
    d = ImageDraw.Draw(im)

    # title: the largest size that fits in at most 3 lines
    for size in range(120, 59, -4):
        f = load_font(size)
        lines = wrap(title.split(), lambda x: d.textlength(x, font=f) <= TEXT_W)
        if len(lines) <= 3 and all(d.textlength(x, font=f) <= TEXT_W for x in lines):
            break
    bad = missing_glyphs(f, title + label + source)
    if bad:
        raise SystemExit('FAILED: the font cannot draw %s' % ' '.join(bad))
    lh = int(size * 1.18)
    block = lh * len(lines)
    y = 980 - block // 2

    lf = load_font(52)                                       # language label, above the title
    lw = d.textlength(label, font=lf)
    px, py = 34, 16
    ly = y - 52 - 2 * py - 40
    d.rounded_rectangle(((W - lw) / 2 - px, ly, (W + lw) / 2 + px, ly + 52 + 2 * py + 6),
                        radius=40, fill=(255, 255, 255))
    d.text((W / 2, ly + py + 30), label, font=lf, fill=(25, 25, 25), anchor='mm')

    for i, line in enumerate(lines):
        d.text((W / 2, y + i * lh + lh / 2), line, font=f, fill=(255, 255, 255), anchor='mm',
               stroke_width=5, stroke_fill=(0, 0, 0))
    if source:
        sf = load_font(50)
        d.text((W / 2, y + block + 60), source, font=sf, fill=(240, 220, 160), anchor='mm',
               stroke_width=3, stroke_fill=(0, 0, 0))
    bf = load_font(34)
    d.text((W / 2, 70), 'Hadith Reels', font=bf, fill=(255, 255, 255), anchor='mm',
           stroke_width=2, stroke_fill=(0, 0, 0))
    for q in (90, 85, 80, 75):
        im.save(dest, 'JPEG', quality=q, optimize=True)
        if os.path.getsize(dest) < 2 * 1024 * 1024:
            break
    return lines, size


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--number', required=True)
    ap.add_argument('--langs', nargs='*', choices=LANGS, default=list(DEFAULT_LANGS))
    ap.add_argument('--scene', nargs='*', help='lang=part-of-clip-name, e.g. uz=iftar')
    ap.add_argument('--at', type=float, default=2.0, help='seconds into the clip (default 2.0)')
    a = ap.parse_args(argv)

    set_path = find_one('set-%s.json' % a.number)
    st = json.load(io.open(set_path, encoding='utf-8')) if set_path else None
    by_lang = render_sidecars(a.number)
    clips_path = find_one('clips-%s.json' % a.number)
    if clips_path:
        base = [c['file'] for c in json.load(io.open(clips_path, encoding='utf-8'))['clips']]
    else:
        base = next((by_lang[l] for l in ('en', 'ru', 'tj', 'uz') if by_lang.get(l)), None)
    if not base:
        print('MISSING the scenes: no clips-%s.json and no render sidecar for #%s' % (a.number, a.number))
        return 1
    picks = same_position(base, pick_scenes(base, a.langs, parse_overrides(a.scene)), by_lang)
    tmp = tempfile.mkdtemp(prefix='covers-')
    for lang in a.langs:
        title = title_for(a.number, lang, st)
        if not title:
            print('MISSING the %s title: no set-%s.json and no caption-%s-%s.txt' % (lang, a.number, a.number, lang))
            return 1
        clip = clip_path(picks[lang])
        if not clip:
            print('MISSING clip %s in out/backgrounds/new or normalized' % picks[lang])
            return 1
        frame = os.path.join(tmp, '%s.png' % lang)
        grab_frame(clip, a.at, frame)
        dest = os.path.join(OUT, 'cover-%s-%s.jpg' % (a.number, lang))
        lines, size = compose(frame, title, LABEL[lang], source_line(a.number, lang), dest)
        print('%s  %-28s <- %s @%.1fs  (%d line(s), %dpx, %d KB)' % (
            lang.upper(), os.path.basename(dest), picks[lang], a.at, len(lines), size,
            os.path.getsize(dest) // 1024))
    print('Upload in YouTube Studio: Details -> Thumbnail -> Upload file.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
