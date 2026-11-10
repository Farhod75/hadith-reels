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
  - P384: the gain must be inside render-reel.ps1's own range (0 < g <= 2, read from the script).
    A bed too quiet for the target stops the dry run, with the dB the cap would leave it short,
    instead of failing that language in the middle of the render.
  - P386: an optional "align" list, one anchor per scene, puts each clip where the narration says
    what it shows instead of -FitScenes' equal slots:
        "align": ["start", "matn", "matn:0.6", "moral"]
    start = 0; matn = where the quoted matn begins; matn:F = that fraction through the matn;
    moral = where the moral begins (after render-reel's 0.5 s pause); moral:F likewise. The matn
    start comes from the language's cached subtitles when they exist (EN/RU after a render),
    otherwise from the share of the S block's letters that the lead-in takes. Each clip must be
    long enough for its slot (scenes, else scenes_slow); the result goes to -SceneDurations.
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
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LANGS = ('en', 'ru', 'uz', 'tj')
CONCAT_GAP_GUARD = 0.6   # render-reel's narration.mp3 ran ~0.5 s longer than story+moral on muslim-2749
STORY_MORAL_PAUSE = 0.5  # render-reel Step 4 (P135): silence between story and moral
OPEN_QUOTES = ('\u00ab', '\u201c', '"')
# What the TTS says for the glyph, so the letter count matches the audio (EN/RU write ﷺ;
# UZ/TJ drafts spell the formula out).
SPOKEN_SAW = {'en': 'peace be upon him', 'ru': 'да благословит его Аллах и приветствует'}
MIN_SLOT = 1.5

_spec = importlib.util.spec_from_file_location('mix_gap', os.path.join(HERE, 'mix-gap.py'))
mg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mg)


def read_tail_pad(render_reel_text):
    m = re.search(r'^\s*\$tailPad\s*=\s*([0-9.]+)', render_reel_text, re.M)
    if not m:
        raise ValueError('no $tailPad in render-reel.ps1')
    return float(m.group(1))


def read_gain_max(render_reel_text):
    """The upper bound render-reel.ps1 enforces on -NasheedGain (P384)."""
    m = re.search(r'\$NasheedGain\s+-le\s+0\s+-or\s+\$NasheedGain\s+-gt\s+([0-9.]+)', render_reel_text)
    if not m:
        raise ValueError('no -NasheedGain range check in render-reel.ps1')
    return float(m.group(1))


def gain_problem(gain, gain_max):
    """None when render-reel.ps1 accepts the gain, else the reason (P384)."""
    if gain <= 0:
        return 'gain %.2f is not above 0' % gain
    if gain > gain_max:
        return ('gain %.2f is above render-reel\'s %.2f - the bed is too quiet for the P338 target; '
                'pick a louder bed, or set "gain": %.2f in the plan (%.1f dB under the target)'
                % (gain, gain_max, gain_max, 20 * math.log10(gain / gain_max)))
    return None


def choose_scenes(narration, tail_pad, std, slow):
    """(which, list, need) - the clip list -FitScenes can cover, or (None, None, need).

    std/slow are lists of (name, seconds)."""
    need = round((narration + tail_pad) / len(std), 3)
    if min(s for _, s in std) >= need:
        return 'scenes', [n for n, _ in std], need
    if slow and len(slow) == len(std) and min(s for _, s in slow) >= need:
        return 'scenes_slow', [n for n, _ in slow], need
    return None, None, need


def draft_s_block(slug, lang, repo=None):
    p = os.path.join(repo or REPO, 'out', 'draft-%s-%s.txt' % (slug, lang))
    for line in io.open(p, encoding='utf-8-sig'):
        if line.startswith('S:'):
            return line[2:].strip()
    raise SystemExit('FAILED: no S: block in %s' % p)


def _letters(t):
    return sum(1 for ch in t if ch.isalpha())


def lead_in_fraction(s_block, lang):
    """Share of the spoken S block that comes before the matn's opening quote (P386)."""
    qs = [s_block.find(q) for q in OPEN_QUOTES if q in s_block]
    if not qs:
        raise ValueError('no opening quote in the S block - the matn start cannot be placed')
    q = min(qs)
    spoken = lambda t: t.replace('\ufdfa', ' %s ' % SPOKEN_SAW.get(lang, ''))
    lead, total = _letters(spoken(s_block[:q])), _letters(spoken(s_block))
    return lead / float(total) if total else 0.0


def _srt_seconds(t):
    h, m, rest = t.strip().split(':')
    sec, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000.0


def matn_start_from_srt(text):
    """Start of the first cue holding an opening quote, moved in by the share of the cue's
    letters before the quote. None when no cue has one."""
    for block in re.split(r'\r?\n\r?\n', text.strip()):
        lines = [l for l in block.splitlines() if l.strip()]
        if len(lines) < 3 or '-->' not in lines[1]:
            continue
        start, end = [_srt_seconds(x) for x in lines[1].split('-->')]
        cue = ' '.join(lines[2:])
        qs = [cue.find(q) for q in OPEN_QUOTES if q in cue]
        if qs:
            q = min(qs)
            frac = _letters(cue[:q]) / float(_letters(cue) or 1)
            return round(start + frac * (end - start), 3)
    return None


def anchor_seconds(anchor, story, moral, matn_start):
    if anchor == 'start':
        return 0.0
    base, _, frac = anchor.partition(':')
    f = float(frac) if frac else 0.0
    if not 0.0 <= f < 1.0:
        raise ValueError('anchor %r: the fraction must be in [0, 1)' % anchor)
    if base == 'matn':
        return matn_start + f * (story - matn_start)
    if base == 'moral':
        m0 = story + STORY_MORAL_PAUSE
        return m0 + f * moral
    raise ValueError('anchor %r: use start, matn, matn:F, moral or moral:F' % anchor)


def aligned_durations(anchors, story, moral, matn_start, total, tail_pad):
    """Seconds per clip from the anchors (P386). The last clip runs to total + tail_pad."""
    if not anchors or anchors[0] != 'start':
        raise ValueError('the first anchor must be "start"')
    starts = [anchor_seconds(a, story, moral, matn_start) for a in anchors]
    if any(b <= a for a, b in zip(starts, starts[1:])):
        raise ValueError('anchors must move forward: %s -> %s' % (anchors, [round(x, 2) for x in starts]))
    ends = starts[1:] + [total + tail_pad]
    durs = [round(e - b, 3) for b, e in zip(starts, ends)]
    short = [(a, d) for a, d in zip(anchors, durs) if d < MIN_SLOT]
    if short:
        raise ValueError('slot shorter than %.1fs: %s' % (MIN_SLOT, ', '.join('%s %.2fs' % x for x in short)))
    return durs


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


def build_render_command(slug, lang, bed, gain, scenes, repo=REPO, durations=None):
    """pwsh -Command, not -File: under -File a comma list reaches [string[]]$Scenes as ONE string.
    With durations (P386) the clips get -SceneDurations instead of -FitScenes' equal split."""
    fit = ('-SceneDurations @(%s)' % ','.join('%.3f' % d for d in durations)) if durations else '-FitScenes'
    script = ("& %s -Style adults -Lang %s -Slug %s -Nasheed %s -NasheedGain %.2f -Scenes @(%s) "
              "%s -NoReview -Draft %s; exit $LASTEXITCODE"
              % (_ps_quote(os.path.join(repo, 'render-reel.ps1')), lang, _ps_quote(slug), _ps_quote(bed), gain,
                 ','.join(_ps_quote(s) for s in scenes), fit,
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
    gain_max = read_gain_max(rr)
    ff = mg.ffmpeg_bin()
    std = clip_seconds(ff, plan['scenes'])
    slow = clip_seconds(ff, plan['scenes_slow']) if plan.get('scenes_slow') else []
    if len(std) < 4:
        print('WARNING: %d clips - the operator wants at least four per reel' % len(std))
    align = plan.get('align')
    if align and len(align) != len(std):
        raise SystemExit('FAILED: "align" has %d anchors for %d scenes (P386)' % (len(align), len(std)))

    print('render-set %s - %s' % (slug, 'RENDER' if args.render else 'DRY RUN'))
    jobs, bad = [], 0
    gated = asset_gate([plan['langs'][l]['bed'] for l in langs] + plan['scenes'] + plan.get('scenes_slow', []))
    for name, why in gated:
        print('  STOP (asset gate, P377): %s' % why[:300])
    bad += len(gated)
    for lang in langs:
        cfg = plan['langs'][lang]
        nar, src = narration_seconds(ff, slug, lang)
        durations = None
        if align:
            w = os.path.join(REPO, 'out', 'work', 'adults', slug, lang)
            story = mg.duration(ff, os.path.join(w, 'adults-%s-%s-story.mp3' % (lang, slug)))
            moral = mg.duration(ff, os.path.join(w, 'adults-%s-%s-moral.mp3' % (lang, slug)))
            srt = os.path.join(w, 'adults-%s-%s-narration.srt' % (lang, slug))
            m0 = matn_start_from_srt(io.open(srt, encoding='utf-8-sig').read()) if os.path.exists(srt) else None
            how = 'subtitles'
            if m0 is None:
                m0, how = round(story * lead_in_fraction(draft_s_block(slug, lang), lang), 3), 'letter share'
            try:
                durations = aligned_durations(align, story, moral, m0, nar, tail_pad)
            except ValueError as e:
                print('  %s  STOP (P386 align): %s' % (lang, e)); bad += 1; continue
            fits = lambda clips: all(d <= s for d, (_, s) in zip(durations, clips))
            if fits(std):
                which, scenes = 'scenes', [n for n, _ in std]
            elif slow and len(slow) == len(std) and fits(slow):
                which, scenes = 'scenes_slow', [n for n, _ in slow]
            else:
                over = ['%s (%s) needs %.2fs, clip is %.2fs' % (n, a, d, c) for (n, c), a, d in zip(std, align, durations) if d > c]
                print('  %s  STOP (P386 align): %s - add a clip for that part or move an anchor'
                      % (lang, '; '.join(over))); bad += 1; continue
            need = max(durations)
            print('  %s  align (matn at %.2fs from %s): %s'
                  % (lang, m0, how, ' | '.join('%s %.2fs' % (n, d) for n, d in zip(scenes, durations))))
        else:
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
        why = gain_problem(float(gain), gain_max)
        if why:
            print('  %s  STOP (P384): bed %s - %s' % (lang, cfg['bed'], why)); bad += 1; continue
        print('  %s  narration %.2fs (%s) -> %s, %s | bed %s x%.2f'
              % (lang, nar, src, ('aligned, longest %.2fs' % need) if durations else ('%.2fs per clip' % need),
                 which, cfg['bed'], float(gain)))
        jobs.append((lang, scenes, cfg['bed'], float(gain), durations))
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
    for lang, scenes, bed, gain, durations in jobs:
        note('=============== RENDER %s  bed=%s  gain=%.2f  scenes=%s%s' % (lang, bed, gain, ','.join(scenes),
             ('  durations=' + ','.join('%.2f' % d for d in durations)) if durations else ''))
        cmd = build_render_command(slug, lang, bed, gain, scenes, durations=durations)
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
