#!/usr/bin/env python3
"""review-sheet.py - P450: what the operator reviews, in one command per step.

Three review points in every set were built by hand each time (an ad-hoc PIL script, an ffmpeg
loop): the stills to pick from, the Kling clips to check for people/hands, and the 540p previews.

  python scripts/review-sheet.py --number 6019 --mode stills     # out/sheet-<N>-stills.jpg
  python scripts/review-sheet.py --number 6019 --mode clips      # out/sheet-<N>-clips.jpg
  python scripts/review-sheet.py --number 6019 --mode previews   # out/prev<N>/prev-<N>-<l>.mp4

stills:   every out/refs/<prefix><N>-<scene>-<k>.jpg, one row per scene, variants side by side.
clips:    the plan's scenes (out/render-<slug>.json), frames at 1 s, the middle and 0.5 s before
          the end - one row per clip.
previews: each language's reel scaled to 540 px wide (H.264 veryfast, CRF 30, AAC 96k).
The slug comes from out/set-<N>.json. Nothing is uploaded or sent; the operator gets the files.
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
THUMB_W = 240


def still_groups(names, number):
    """PURE. {scene: [file, ...]} for '<prefix><N>-<scene>-<k>.jpg' names, variants in order."""
    pat = re.compile(r'^[a-z]+%s-(.+)-(\d+)\.jpe?g$' % re.escape(str(number)), re.I)
    groups = {}
    for n in names:
        m = pat.match(n)
        if m:
            groups.setdefault(m.group(1), []).append((int(m.group(2)), n))
    return {k: [n for _, n in sorted(v)] for k, v in sorted(groups.items())}


def frame_times(duration):
    """PURE. Three frames that show a clip's start, middle and end."""
    return [round(min(1.0, duration / 4), 2), round(duration / 2, 2), round(max(0.0, duration - 0.5), 2)]


def ffmpeg_bin():
    spec = importlib.util.spec_from_file_location('mix_gap', os.path.join(HERE, 'mix-gap.py'))
    mg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mg)
    return mg, mg.ffmpeg_bin()


def sheet(rows, path, labels):
    """rows: [[image path, ...], ...] -> one JPEG, rows top to bottom, labels above each image."""
    from PIL import Image, ImageDraw
    ims = [[Image.open(p).convert('RGB') for p in r] for r in rows]
    h = max(int(im.height * THUMB_W / im.width) for r in ims for im in r)
    cols = max(len(r) for r in ims)
    out = Image.new('RGB', (cols * (THUMB_W + 10), len(ims) * (h + 20)), 'white')
    d = ImageDraw.Draw(out)
    for y, (r, lr) in enumerate(zip(ims, labels)):
        for x, (im, lab) in enumerate(zip(r, lr)):
            out.paste(im.resize((THUMB_W, int(im.height * THUMB_W / im.width))), (x * (THUMB_W + 10), y * (h + 20) + 18))
            d.text((x * (THUMB_W + 10) + 3, y * (h + 20) + 3), lab, fill='black')
    out.save(path, quality=85)
    return path


def slug_of(number):
    p = os.path.join(OUT, 'set-%s.json' % number)
    if not os.path.exists(p):
        raise SystemExit('FAILED: %s not found' % p)
    return json.load(io.open(p, encoding='utf-8-sig'))['slug']


def do_stills(number):
    refs = os.path.join(OUT, 'refs')
    groups = still_groups(os.listdir(refs), number)
    if not groups:
        raise SystemExit('FAILED: no out/refs/*%s-<scene>-<k>.jpg' % number)
    rows = [[os.path.join(refs, n) for n in v] for v in groups.values()]
    labels = [[os.path.splitext(n)[0] for n in v] for v in groups.values()]
    return sheet(rows, os.path.join(OUT, 'sheet-%s-stills.jpg' % number), labels)


def do_clips(number):
    slug = slug_of(number)
    plan = json.load(io.open(os.path.join(OUT, 'render-%s.json' % slug), encoding='utf-8-sig'))
    mg, ff = ffmpeg_bin()
    tmp = tempfile.mkdtemp(prefix='sheet-%s-' % number)
    rows, labels = [], []
    for clip in plan['scenes']:
        src = os.path.join(OUT, 'backgrounds', 'new', clip)
        if not os.path.exists(src):
            src = os.path.join(OUT, 'backgrounds', 'normalized', clip)
        r, lr = [], []
        for t in frame_times(mg.duration(ff, src)):
            f = os.path.join(tmp, '%s-%s.jpg' % (clip, t))
            subprocess.run([ff, '-v', 'error', '-y', '-ss', str(t), '-i', src, '-frames:v', '1', f], check=True)
            r.append(f); lr.append('%s %ss' % (os.path.splitext(clip)[0], t))
        rows.append(r); labels.append(lr)
    return sheet(rows, os.path.join(OUT, 'sheet-%s-clips.jpg' % number), labels)


def do_previews(number):
    slug = slug_of(number)
    _, ff = ffmpeg_bin()
    d = os.path.join(OUT, 'prev%s' % number)
    os.makedirs(d, exist_ok=True)
    made = []
    for l in LANGS:
        src = os.path.join(OUT, 'work', 'adults', slug, l, 'adults-%s-%s-reel.mp4' % (l, slug))
        if not os.path.exists(src):
            print('  %s  no reel yet - skipped' % l)
            continue
        dst = os.path.join(d, 'prev-%s-%s.mp4' % (number, l))
        subprocess.run([ff, '-v', 'error', '-y', '-i', src, '-vf', 'scale=540:-2', '-c:v', 'libx264',
                        '-preset', 'veryfast', '-crf', '30', '-c:a', 'aac', '-b:a', '96k', dst], check=True)
        made.append(dst)
    return made


def main(argv=None):
    ap = argparse.ArgumentParser(description='Review sheets and previews for a set (P450).')
    ap.add_argument('--number', required=True)
    ap.add_argument('--mode', required=True, choices=('stills', 'clips', 'previews'))
    a = ap.parse_args(argv)
    res = {'stills': do_stills, 'clips': do_clips, 'previews': do_previews}[a.mode](a.number)
    for p in (res if isinstance(res, list) else [res]):
        print(p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
