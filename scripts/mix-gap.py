#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mix-gap.py - how far the nasheed sits under the narration, and the -NasheedGain that puts it at the target.

Replaces the per-set out/mix_gap<n>.py and out/w43_gap_rh.py (automation, OPEN_ITEMS item 2, 2026-11-03).

The gap is narration loudness minus bed loudness, in LU, both integrated over the SAME seconds -
the narration (story + moral) at the mix's narration volume, and the bed from its start at its
mix volume, which is what plays under the voice. Bigger gap = quieter nasheed.

Targets per language are P338's: the gaps the operator called fine on tirmidhi-1161
(RU 10.8, UZ 15.7) and the two he corrected to (EN 13.3, TJ 13.4). The voices differ by
~5 dB, so one target for all four would be wrong (P338).

Two modes:
  BEFORE the render - pass --bed. The bed's mix volume is render-reel's base x the bed's
  registry gain; the trim printed is the -NasheedGain to render with.
      python scripts/mix-gap.py --slug muslim-2749 --lang uz --bed aswati-Peaceful-Contemplation.mp3

  AFTER the render - no --bed. Bed and volume come from each language's render sidecar
  (adults-<lang>-<slug>-render.json: nasheed, nasheedVol, nasheedGain), so a stale log
  cannot be read by mistake (the r223.log trap of 2026-11-03).
      python scripts/mix-gap.py --slug muslim-2749

Read-only. The base volume and the narration volume are parsed from render-reel.ps1, not
copied here, so a change there cannot leave this script measuring a different mix.
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
KNOWN_FFMPEG = r"C:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"

TARGETS = {'en': 13.3, 'ru': 10.8, 'uz': 15.7, 'tj': 13.4}   # P338
LANGS = ('en', 'ru', 'uz', 'tj')


def read_mix_constants(render_reel_text):
    """(base nasheed volume, narration volume) as render-reel.ps1 sets them."""
    base = re.search(r'^\s*\$nasheedVol\s*=\s*([0-9.]+)\s*$', render_reel_text, re.M)
    narr = re.search(r'\[1:a\]volume=([0-9.]+),apad', render_reel_text)
    if not base or not narr:
        raise ValueError('cannot find $nasheedVol or the narration volume in render-reel.ps1')
    return float(base.group(1)), float(narr.group(1))


def parse_lufs(stderr):
    """Integrated loudness from ffmpeg's ebur128 summary (the last 'I:' line)."""
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', stderr or '')
    return float(m[-1]) if m else None


def trim_for(gap, target):
    """The volume factor that moves the bed so the gap lands on target (gap grows as the bed drops)."""
    return 10 ** (-(target - gap) / 20)


def ffmpeg_bin():
    found = shutil.which('ffmpeg')
    if found:
        return found
    if os.path.exists(KNOWN_FFMPEG):
        return KNOWN_FFMPEG
    raise SystemExit('FAILED: ffmpeg not found on PATH or at ' + KNOWN_FFMPEG)


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stderr


def duration(ff, path):
    m = re.search(r'Duration: (\d+):(\d+):([\d.]+)', _run([ff, '-hide_banner', '-i', path]))
    if not m:
        raise SystemExit('FAILED: no duration for ' + path)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def narration_lufs(ff, parts, narr_vol, work):
    lst = os.path.join(work, '_mixgap_concat.txt')
    io.open(lst, 'w', encoding='utf-8').write(
        ''.join("file '%s'\n" % os.path.abspath(p).replace('\\', '/') for p in parts))
    try:
        err = _run([ff, '-hide_banner', '-nostats', '-f', 'concat', '-safe', '0', '-i', lst,
                    '-af', 'volume=%s,ebur128=framelog=quiet' % narr_vol, '-f', 'null', '-'])
    finally:
        os.remove(lst)
    return parse_lufs(err)


def bed_lufs(ff, bed_path, vol, seconds):
    return parse_lufs(_run([ff, '-hide_banner', '-nostats', '-t', '%.2f' % seconds, '-i', bed_path,
                            '-af', 'volume=%s,ebur128=framelog=quiet' % vol, '-f', 'null', '-']))


def main(argv=None):
    ap = argparse.ArgumentParser(description='Nasheed-under-voice gap and the -NasheedGain for the target (P338).')
    ap.add_argument('--slug', required=True, help='e.g. muslim-2749')
    ap.add_argument('--lang', nargs='*', choices=LANGS, default=None, help='default: every language with narration')
    ap.add_argument('--bed', default=None, help='BEFORE the render: the bed file name in out/backgrounds/')
    ap.add_argument('--json', action='store_true', help='also print one JSON line per language')
    args = ap.parse_args(argv)

    base, narr_vol = read_mix_constants(io.open(os.path.join(REPO, 'render-reel.ps1'), encoding='utf-8-sig').read())
    ff = ffmpeg_bin()
    reg = json.load(io.open(os.path.join(REPO, 'assets', 'asset-registry.json'), encoding='utf-8'))['audio']
    if args.bed:
        entry = reg.get(args.bed)
        if entry is None:
            raise SystemExit('FAILED: %s is not in the registry audio section' % args.bed)
        if 'adults' not in (entry.get('lanes') or []):
            raise SystemExit('FAILED: %s is not adults-approved (lanes %r) - the render gate would refuse it'
                             % (args.bed, entry.get('lanes')))

    work_root = os.path.join(REPO, 'out', 'work', 'adults', args.slug)
    langs = args.lang or [l for l in LANGS if os.path.isdir(os.path.join(work_root, l))]
    if not langs:
        raise SystemExit('FAILED: no language folders under ' + work_root)
    mode = 'before render' if args.bed else 'after render'
    print('mix-gap %s - %s  (base vol %s, narration x%s, P338 targets)' % (args.slug, mode, base, narr_vol))
    bad = 0
    for lang in langs:
        w = os.path.join(work_root, lang)
        parts = [os.path.join(w, 'adults-%s-%s-%s.mp3' % (lang, args.slug, s)) for s in ('story', 'moral')]
        missing = [p for p in parts if not os.path.exists(p)]
        if missing:
            print('  %s  FAILED: missing %s' % (lang, ', '.join(os.path.basename(p) for p in missing)))
            bad += 1
            continue
        current_gain = 1.0
        if args.bed:
            bed = args.bed
            vol = round(base * float(reg[bed].get('gain') or 1.0), 4)
        else:
            side = os.path.join(w, 'adults-%s-%s-render.json' % (lang, args.slug))
            if not os.path.exists(side):
                print('  %s  FAILED: no render sidecar - render first, or pass --bed' % lang)
                bad += 1
                continue
            man = json.load(io.open(side, encoding='utf-8-sig'))
            bed, vol = man['nasheed'], float(man['nasheedVol'])
            current_gain = float(man.get('nasheedGain') or 1.0)
        seconds = sum(duration(ff, p) for p in parts)
        nar = narration_lufs(ff, parts, narr_vol, w)
        b = bed_lufs(ff, os.path.join(REPO, 'out', 'backgrounds', bed), vol, seconds)
        if nar is None or b is None:
            print('  %s  FAILED: ffmpeg returned no loudness' % lang)
            bad += 1
            continue
        gap = nar - b
        t = trim_for(gap, TARGETS[lang])
        gain = round(current_gain * t, 2)
        print('  %s  narration %.1f LUFS | %-34s vol %.4f -> %.1f LUFS | gap %.1f vs %.1f -> -NasheedGain %.2f%s'
              % (lang, nar, bed, vol, b, gap, TARGETS[lang], gain,
                 '' if args.bed else '  (rendered at %.2f)' % current_gain))
        if args.json:
            print(json.dumps({'lang': lang, 'bed': bed, 'vol': vol, 'narration_lufs': round(nar, 2),
                              'bed_lufs': round(b, 2), 'gap': round(gap, 2), 'target': TARGETS[lang],
                              'nasheed_gain': gain, 'seconds': round(seconds, 2)}))
    return 2 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
