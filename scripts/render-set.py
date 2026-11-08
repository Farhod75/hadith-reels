#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render-set.py - render one reel set, all languages, from a plan file.

Replaces the per-set out/r<n>.ps1 render scripts (automation, OPEN_ITEMS item 2, 2026-11-03).

The plan, out/render-<slug>.json:
    {"slug": "muslim-2749",
     "scenes":      ["m2749-footprints-a.mp4", "m2749-people.mp4", "m2749-dua.mp4", "m2749-bloom.mp4"],
     "scenes_slow": ["m2749-footprints-a-s.mp4", "m2749-people-s.mp4", "m2749-dua-s.mp4", "m2749-bloom-s.mp4"],
     "langs": {"en": {"bed": "aswati-Gentle-Reflection.mp3", "gain": 0.98},
               "uz": {"bed": "aswati-Peaceful-Contemplation.mp3", "gain": "auto"}}}

Per language, before anything renders:
  - P240: -FitScenes needs (narration + tailPad) / clips seconds of every clip. The plan picks
    `scenes`, or `scenes_slow` when a normal clip is too short; if neither covers the narration
    it stops BEFORE the first render and says how long the clips must be.
  - gain "auto" asks mix-gap.py for the -NasheedGain that lands the P338 target.
Then (only with --render) it runs render-reel.ps1 -Style adults -FitScenes -NoReview per
language, logs to out/render-<slug>.log, and finishes with mix-gap.py's after-render check.
A render stopped by a gate (P339 subtitles, P319 matn) is reported and the set continues with
the next language; fix and re-run just that one with --langs.

Long run - start it detached (P350):
    Start-Process pwsh -ArgumentList '-NoProfile','-Command','python scripts/render-set.py --plan out/render-muslim-2749.json --render *> out/render-set.out' -WorkingDirectory (Get-Location).Path
"""
import argparse
import importlib.util
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LANGS = ('en', 'ru', 'uz', 'tj')
CONCAT_GAP_GUARD = 0.6   # render-reel's narration.mp3 ran ~0.5 s longer than story+moral on muslim-2749

_spec = importlib.util.spec_from_file_location('mix_gap', os.path.join(HERE, 'mix-gap.py'))
mg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mg)


def read_tail_pad(render_reel_text):
    m = re.search(r'^\s*\$tailPad\s*=\s*([0-9.]+)', render_reel_text, re.M)
    if not m:
        raise ValueError('no $tailPad in render-reel.ps1')
    return float(m.group(1))


def choose_scenes(narration, tail_pad, std, slow):
    """(which, list, need) - the clip list -FitScenes can cover, or (None, None, need).

    std/slow are lists of (name, seconds)."""
    need = round((narration + tail_pad) / len(std), 3)
    if min(s for _, s in std) >= need:
        return 'scenes', [n for n, _ in std], need
    if slow and len(slow) == len(std) and min(s for _, s in slow) >= need:
        return 'scenes_slow', [n for n, _ in slow], need
    return None, None, need


def narration_seconds(ff, slug, lang):
    w = os.path.join(REPO, 'out', 'work', 'adults', slug, lang)
    full = os.path.join(w, 'adults-%s-%s-narration.mp3' % (lang, slug))
    if os.path.exists(full):
        return mg.duration(ff, full), 'narration.mp3'
    parts = [os.path.join(w, 'adults-%s-%s-%s.mp3' % (lang, slug, s)) for s in ('story', 'moral')]
    missing = [p for p in parts if not os.path.exists(p)]
    if missing:
        raise SystemExit('FAILED: %s has no narration yet (%s)' % (lang, ', '.join(os.path.basename(p) for p in missing)))
    return sum(mg.duration(ff, p) for p in parts) + CONCAT_GAP_GUARD, 'story+moral +%.1fs guard' % CONCAT_GAP_GUARD


def clip_seconds(ff, names):
    out = []
    for n in names:
        p = os.path.join(REPO, 'out', 'backgrounds', 'new', n)
        if not os.path.exists(p):
            p = os.path.join(REPO, 'out', 'backgrounds', 'normalized', n)
        if not os.path.exists(p):
            raise SystemExit('FAILED: clip %s not found in out/backgrounds/new or normalized' % n)
        out.append((n, mg.duration(ff, p)))
    return out


def _ps_quote(s):
    return "'" + str(s).replace("'", "''") + "'"


def build_render_command(slug, lang, bed, gain, scenes, repo=REPO):
    """pwsh -Command, not -File: under -File a comma list reaches [string[]]$Scenes as ONE string."""
    script = ("& %s -Style adults -Lang %s -Slug %s -Nasheed %s -NasheedGain %.2f -Scenes @(%s) "
              "-FitScenes -NoReview -Draft %s; exit $LASTEXITCODE"
              % (_ps_quote(os.path.join(repo, 'render-reel.ps1')), lang, _ps_quote(slug), _ps_quote(bed), gain,
                 ','.join(_ps_quote(s) for s in scenes),
                 _ps_quote(os.path.join('out', 'draft-%s-%s.txt' % (slug, lang)))))
    return ['pwsh', '-NoProfile', '-Command', script]


def asset_gate(names, lane='adults', run=subprocess.run):
    """[(name, reason)] for every file the render gate would refuse (P377): audit-assets.py
    --check is the gate render-reel.ps1 runs, so the plan is checked by the same rule before
    the first render instead of failing one language in the middle of the set."""
    blocked = []
    for name in dict.fromkeys(names):
        r = run([sys.executable, os.path.join(HERE, 'audit-assets.py'), '--check', name, '--lane', lane],
                capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=REPO,
                env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        if r.returncode:
            line = next((l for l in r.stdout.splitlines() if 'BLOCKED' in l), r.stdout.strip()[:200])
            blocked.append((name, line.strip()))
    return blocked


def main(argv=None):
    ap = argparse.ArgumentParser(description='Render a reel set from a plan (dry run unless --render).')
    ap.add_argument('--plan', required=True)
    ap.add_argument('--langs', nargs='*', choices=LANGS, default=None)
    ap.add_argument('--render', action='store_true')
    args = ap.parse_args(argv)

    plan = json.load(io.open(args.plan, encoding='utf-8-sig'))
    slug = plan['slug']
    langs = [l for l in (args.langs or LANGS) if l in plan['langs']]
    rr = io.open(os.path.join(REPO, 'render-reel.ps1'), encoding='utf-8-sig').read()
    tail_pad = read_tail_pad(rr)
    ff = mg.ffmpeg_bin()
    std = clip_seconds(ff, plan['scenes'])
    slow = clip_seconds(ff, plan['scenes_slow']) if plan.get('scenes_slow') else []
    if len(std) < 4:
        print('WARNING: %d clips - the operator wants at least four per reel' % len(std))

    print('render-set %s - %s' % (slug, 'RENDER' if args.render else 'DRY RUN'))
    jobs, bad = [], 0
    gated = asset_gate([plan['langs'][l]['bed'] for l in langs] + plan['scenes'] + plan.get('scenes_slow', []))
    for name, why in gated:
        print('  STOP (asset gate, P377): %s' % why[:300])
    bad += len(gated)
    for lang in langs:
        cfg = plan['langs'][lang]
        nar, src = narration_seconds(ff, slug, lang)
        which, scenes, need = choose_scenes(nar, tail_pad, std, slow)
        if which is None:
            print('  %s  STOP: %.2fs narration (%s) needs %.2fs per clip; shortest is %.2fs%s'
                  % (lang, nar, src, need, min(s for _, s in std),
                     ', slow copies %.2fs' % min(s for _, s in slow) if slow else ', no slow copies'))
            bad += 1
            continue
        gain = cfg.get('gain', 1.0)
        if gain == 'auto':
            r = subprocess.run([sys.executable, os.path.join(HERE, 'mix-gap.py'), '--slug', slug, '--lang', lang,
                                '--bed', cfg['bed'], '--json'], capture_output=True, text=True,
                               encoding='utf-8', errors='replace', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
            rows = [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
            if r.returncode or not rows:
                print('  %s  STOP: mix-gap failed: %s' % (lang, (r.stdout + r.stderr).strip()[-300:])); bad += 1; continue
            gain = rows[0]['nasheed_gain']
        print('  %s  narration %.2fs (%s) -> %.2fs per clip, %s | bed %s x%.2f'
              % (lang, nar, src, need, which, cfg['bed'], float(gain)))
        jobs.append((lang, scenes, cfg['bed'], float(gain)))
    if bad:
        print('FAILED: fix the above - nothing rendered.')
        return 1
    if not args.render:
        print('dry run - add --render (detached, P350).')
        return 0

    log = io.open(os.path.join(REPO, 'out', 'render-%s.log' % slug), 'a', encoding='utf-8')
    def note(s):
        log.write(s + '\n'); log.flush(); print(s)
    results = {}
    for lang, scenes, bed, gain in jobs:
        note('=============== RENDER %s  bed=%s  gain=%.2f  scenes=%s' % (lang, bed, gain, ','.join(scenes)))
        cmd = build_render_command(slug, lang, bed, gain, scenes)
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding='utf-8', errors='replace')
        for l in (p.stdout + p.stderr).splitlines():
            log.write('  ' + l + '\n')
        log.flush()
        results[lang] = p.returncode
        note('RENDER_%s_EXIT=%d' % (lang, p.returncode))
    r = subprocess.run([sys.executable, os.path.join(HERE, 'mix-gap.py'), '--slug', slug, '--lang'] +
                       [l for l, c in results.items() if c == 0], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    note(r.stdout.strip())
    failed = [l for l, c in results.items() if c]
    note('DONE - rendered %s%s' % (', '.join(l for l, c in results.items() if c == 0) or 'nothing',
                                  '; STOPPED by a gate: ' + ', '.join(failed) + ' (see the log)' if failed else ''))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
