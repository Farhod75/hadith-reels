#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tg-post-set.py - post a rendered reel set to the Telegram channel, one language after another.

Replaces the per-set out/tg_<n>.py scripts (automation, OPEN_ITEMS item 2, 2026-11-03).

What it does, per language, in the order given (default en ru uz tj):
  caption <= 1024  ->  one video message with the full caption.
  caption  > 1024  ->  the video with a SHORT caption, then the full caption as a reply to it
                       (operator 2026-11-02: split, never trim the matn or Arabic - P184).
                       The short caption is out/caption-<n>-<lang>-tg-video.txt when it exists,
                       otherwise derived from the full one: title, the 📖 and 🔍 lines, the first
                       four hashtags.

Safety, all from P350 (the #2747 publish that died with the remote call that started it):
  - DRY RUN by default. --post sends.
  - Every message id is written to out/tg-<n>.json the moment Telegram returns it, and a
    language already recorded there is REFUSED - a half-finished run is resumed, never
    repeated blind. --redo <lang> drops one language's record on purpose.
  - Stops at the first failure.
  - It is a long run: start it detached and read the log -
        Start-Process pwsh -ArgumentList '-NoProfile','-Command','python scripts/tg-post-set.py --number 2749 --slug muslim-2749 --post *> out/tg-2749.out' -WorkingDirectory (Get-Location).Path

Posting goes through the local dev server's /api/telegram/post (the bot token never leaves
.env.local). The server must be running: `npm run dev` (port 3002).
"""
import argparse
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
API = 'http://localhost:3002/api/telegram/post'
CAPTION_LIMIT = 1024          # Telegram's limit for a video caption
MESSAGE_LIMIT = 4096          # and for a text message (the reply)
LANGS = ('en', 'ru', 'uz', 'tj')


def needs_split(caption):
    return len(caption) > CAPTION_LIMIT


def derive_short(full):
    """Title, the source and verify lines, and the first four hashtags of the full caption."""
    lines = [l.rstrip() for l in full.strip().split('\n')]
    title = lines[0].strip()
    src = [l for l in lines if l.startswith(u'\U0001F4D6') or l.startswith(u'\U0001F50D')]
    tags = [l for l in lines if l.startswith('#')]
    tagline = ' '.join(tags[-1].split()[:4]) if tags else ''
    out = title + '\n\n' + '\n'.join(src)
    if tagline:
        out += '\n\n' + tagline
    return out


def plan_language(number, slug, lang, root=REPO):
    """Everything needed to post one language, or a reason it cannot be posted."""
    full_p = os.path.join(root, 'out', 'caption-%s-%s.txt' % (number, lang))
    short_p = os.path.join(root, 'out', 'caption-%s-%s-tg-video.txt' % (number, lang))
    reel = 'out/work/adults/%s/%s/adults-%s-%s-reel.mp4' % (slug, lang, lang, slug)
    if not os.path.exists(full_p):
        return {'lang': lang, 'error': 'missing ' + os.path.relpath(full_p, root)}
    if not os.path.exists(os.path.join(root, reel)):
        return {'lang': lang, 'error': 'missing ' + reel}
    full = io.open(full_p, encoding='utf-8-sig').read().strip()
    if len(full) > MESSAGE_LIMIT:
        return {'lang': lang, 'error': 'caption %d chars - over even the 4096 message limit' % len(full)}
    p = {'lang': lang, 'reel': reel, 'full': full, 'split': needs_split(full)}
    if p['split']:
        if os.path.exists(short_p):
            p['short'] = io.open(short_p, encoding='utf-8-sig').read().strip()
            p['short_source'] = os.path.relpath(short_p, root)
        else:
            p['short'] = derive_short(full)
            p['short_source'] = 'derived'
        if len(p['short']) > CAPTION_LIMIT:
            return {'lang': lang, 'error': 'short caption still %d chars' % len(p['short'])}
    return p


def load_state(path):
    if os.path.exists(path):
        return json.load(io.open(path, encoding='utf-8'))
    return {}


def save_state(path, state):
    tmp = path + '.tmp'
    io.open(tmp, 'w', encoding='utf-8').write(json.dumps(state, ensure_ascii=False, indent=2))
    os.replace(tmp, path)


def call(payload, api=API):
    req = urllib.request.Request(api, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(req, timeout=600)
        return r.getcode(), json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        b = e.read().decode('utf-8', 'replace')
        try:
            return e.code, json.loads(b)
        except ValueError:
            return e.code, {'error': b[:300]}


def main(argv=None):
    ap = argparse.ArgumentParser(description='Post a reel set to Telegram (dry run unless --post).')
    ap.add_argument('--number', required=True, help='hadith number, as in out/caption-<number>-<lang>.txt')
    ap.add_argument('--slug', required=True, help='e.g. muslim-2749')
    ap.add_argument('--langs', nargs='*', choices=LANGS, default=list(LANGS))
    ap.add_argument('--post', action='store_true', help='actually send (default: dry run)')
    ap.add_argument('--redo', nargs='*', choices=LANGS, default=[],
                    help="forget these languages' recorded posts first (deliberate re-post)")
    args = ap.parse_args(argv)

    state_p = os.path.join(REPO, 'out', 'tg-%s.json' % args.number)
    log_p = os.path.join(REPO, 'out', 'tg-%s.log' % args.number)
    state = load_state(state_p)
    for l in args.redo:
        state.pop(l, None)

    plans = [plan_language(args.number, args.slug, l) for l in args.langs]
    bad = [p for p in plans if 'error' in p]
    print('tg-post-set %s (%s) - %s' % (args.number, args.slug, 'POST' if args.post else 'DRY RUN'))
    for p in plans:
        l = p['lang']
        if 'error' in p:
            print('  %s  CANNOT POST: %s' % (l, p['error']))
        elif l in state:
            print('  %s  already posted: %s - skipped (pass --redo %s to post again)' % (l, state[l], l))
        else:
            how = ('video + reply (%d > %d; short caption %s, %d chars)'
                   % (len(p['full']), CAPTION_LIMIT, p['short_source'], len(p['short']))
                   if p['split'] else 'one video message, %d chars' % len(p['full']))
            print('  %s  %s  <- %s' % (l, how, p['reel']))
    if bad:
        print('FAILED: fix the above first - nothing was posted.')
        return 1
    if not args.post:
        print('dry run - nothing sent. Add --post (and run it detached, P350).')
        return 0

    log = io.open(log_p, 'a', encoding='utf-8')
    def note(*a):
        log.write(' '.join(str(x) for x in a) + '\n'); log.flush(); print('  ' + ' '.join(str(x) for x in a))
    for p in plans:
        l = p['lang']
        if l in state:
            continue
        c, d = call({'caption': p['short'] if p['split'] else p['full'], 'videoPath': p['reel']})
        if not (c == 200 and d.get('ok') and d.get('mode') == 'video'):
            note(l, 'VIDEO NOT POSTED', c, d.get('error')); return 2
        state[l] = {'video': d['message_id']}
        save_state(state_p, state)
        note(l, 'video posted: message_id', d['message_id'])
        if p['split']:
            c2, d2 = call({'caption': p['full'], 'replyTo': d['message_id']})
            if not (c2 == 200 and d2.get('ok')):
                note(l, 'REPLY NOT POSTED', c2, d2.get('error'),
                     '- the video is up; post the full text as a reply by hand or re-run with --redo %s' % l)
                return 2
            state[l]['reply'] = d2['message_id']
            save_state(state_p, state)
            note(l, 'full text reply posted: message_id', d2['message_id'])
    note('DONE', json.dumps(state))
    return 0


if __name__ == '__main__':
    sys.exit(main())
