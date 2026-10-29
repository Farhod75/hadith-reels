#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post a rendered reel to the Telegram channel in one command.

    python scripts\\post-telegram.py --lang en --slug bukhari-3559
    python scripts\\post-telegram.py --lang en --slug bukhari-3559 --dry-run

Telegram is the only one of the four platforms with a real publishing API, so
it is the only one where the upload-and-paste step can go away. Instagram,
YouTube Shorts and TikTok still need hands.

This is NOT wired into render-reel.ps1 on purpose. The project's hard rule is
human approval before every publish, so the operator still decides; what
changes is that deciding now costs one command instead of an upload and a
paste. Nothing here runs by itself.

The caption comes from out/caption-<number>-<lang>.txt, which build-caption.ts
writes from the library row and the approved blocks - so the posted caption is
the same text the narration and the database carry, not a retyped copy.

--dry-run checks everything the real run checks, including that the dev server
answers and that Telegram is configured, without sending anything.
"""
import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.environ.get('HR_DEV_ORIGIN', 'http://localhost:3002')
CAPTION_LIMIT = 1024


def die(msg):
    print('ABORT: %s' % msg)
    sys.exit(2)


ap = argparse.ArgumentParser()
ap.add_argument('--lang', required=True, choices=('en', 'ru', 'uz', 'tj'))
ap.add_argument('--slug', required=True, help='collection-number, e.g. bukhari-3559')
ap.add_argument('--style', default='adults', choices=('adults', 'kids'))
ap.add_argument('--dry-run', action='store_true')
a = ap.parse_args()

number = a.slug.rsplit('-', 1)[-1]
if not number.isdigit():
    die('--slug must end in the hadith number, got %r' % a.slug)

cap_path = os.path.join(ROOT, 'out', 'caption-%s-%s.txt' % (number, a.lang))
if not os.path.exists(cap_path):
    die('no caption at %s - run build-caption.ts first'
        % os.path.relpath(cap_path, ROOT))
with io.open(cap_path, encoding='utf-8-sig') as fh:
    caption = fh.read().strip()
if not caption:
    die('%s is empty' % os.path.relpath(cap_path, ROOT))
if len(caption) > CAPTION_LIMIT:
    die('caption is %d chars, Telegram caps a video caption at %d'
        % (len(caption), CAPTION_LIMIT))

rel = os.path.join('out', 'work', a.style, a.slug, a.lang,
                   '%s-%s-%s-reel.mp4' % (a.style, a.lang, a.slug))
reel = os.path.join(ROOT, rel)
if not os.path.exists(reel):
    die('no reel at %s - render it first' % rel)
size = os.path.getsize(reel)
if size < 100000:
    die('%s is only %d bytes - looks unfinished' % (rel, size))
if size > 50 * 1024 * 1024:
    die('%s is %.1f MB; Telegram bot uploads cap at 50 MB'
        % (rel, size / 1048576.0))

print('lang           : %s' % a.lang)
print('slug           : %s' % a.slug)
print('caption        : %s (%d chars)'
      % (os.path.relpath(cap_path, ROOT), len(caption)))
print('reel           : %s (%.1f MB)' % (rel, size / 1048576.0))
print('first line     : %s' % caption.split('\n')[0])


def call(payload):
    req = urllib.request.Request(
        API + '/api/telegram/post',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=600)
        return resp.getcode(), json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', 'replace')
        try:
            return exc.code, json.loads(body)
        except ValueError:
            return exc.code, {'error': body[:400]}
    except urllib.error.URLError as exc:
        die('cannot reach %s - is the dev server running? (%s)'
            % (API, exc.reason))


if a.dry_run:
    # Send a request the route is guaranteed to reject before it posts
    # anything, purely to learn whether the token and chat id are set.
    code, data = call({'caption': ''})
    if code == 503:
        print('\nTelegram is NOT configured: %s' % data.get('error'))
        sys.exit(1)
    if code == 400:
        print('\nDRY RUN ok - Telegram is configured and the dev server '
              'answers. Nothing was posted.')
        sys.exit(0)
    print('\nunexpected dry-run reply: HTTP %d %s' % (code, data))
    sys.exit(1)

code, data = call({'caption': caption, 'videoPath': rel.replace('\\', '/')})
print('\nHTTP %d' % code)
for k in ('ok', 'mode', 'message_id', 'chat_id', 'bytes', 'caption_chars',
          'error'):
    if k in data:
        print('   %-14s %s' % (k, data[k]))

ok = code == 200 and data.get('ok') and data.get('mode') == 'video' \
    and data.get('message_id')
print('posted to Telegram' if ok else 'NOT POSTED')
sys.exit(0 if ok else 1)
