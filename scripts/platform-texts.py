#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
platform-texts.py - every publishing field for a set, built from its Telegram captions.

  python scripts/platform-texts.py --number 5984
  python scripts/platform-texts.py --number 5984 --langs en ru

Reads out/caption-<n>-<lang>.txt (build-caption.ts output; also found under
out/published/**/_files/ after tidy-out) and writes out/platform-<n>.md: for each
language, ready-to-paste text for Instagram, Facebook, YouTube Shorts and TikTok,
following reel-creation-pipeline.md "Publishing". Read-only otherwise; posts nothing.

P368: on 2026-11-04 these fields were composed by hand, from memory, without
reading the publishing section - and the rules written there were broken on two
sets: '#' in the YouTube titles ("#Shorts"), and the Arabic matn in the TikTok
captions. The rules now live in code, and scripts/lib/test_platform_texts.py
pins them:
  - YouTube TITLE: no '#' at all; the number goes in bare.
  - TikTok: the Telegram caption, Arabic included (operator 2026-11-05, P371: the
    Studio editor and the app show the matn correctly; the 2026-10-05 no-Arabic rule
    is withdrawn). The title (the hadith's point) stays first.
  - Instagram: the Telegram caption unchanged (Facebook gets the same body).
  - Tags (YouTube / Facebook): comma-separated words, never '#'.
"""
import argparse
import glob
import io
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LANGS = ('en', 'ru', 'uz', 'tj')
ARABIC = re.compile(r'[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]')
LANG_MARKERS = {'english', 'русский', 'ўзбекча', 'тоҷикӣ'}


def find_caption(number, lang, root=REPO):
    name = 'caption-%s-%s.txt' % (number, lang)
    direct = os.path.join(root, 'out', name)
    if os.path.isfile(direct):
        return direct
    hits = sorted(glob.glob(os.path.join(root, 'out', 'published', '**', name), recursive=True))
    return hits[0] if hits else None


def parse(caption):
    """Split a build-caption.ts caption into its parts."""
    lines = [l.rstrip() for l in caption.strip().split('\n')]
    title = lines[0].strip()
    body = [l for l in lines[1:]]
    ref = next((l for l in lines if l.startswith(u'\U0001F4D6')), '')
    verify = next((l for l in lines if l.startswith(u'\U0001F50D')), '')
    tags = next((l for l in reversed(lines) if l.startswith('#')), '')
    arabic = [l for l in lines if ARABIC.search(l)]
    matn = next((l for l in lines if l.startswith(u'«') or l.startswith('"')), '')
    known = {title, ref, verify, tags, matn} | set(arabic)
    moral = ' '.join(l for l in lines[1:] if l.strip() and l not in known)
    return {'title': title, 'body': body, 'ref': ref, 'verify': verify, 'tags': tags,
            'arabic': arabic, 'matn': matn, 'moral': moral, 'lines': lines}


def collection_and_number(ref):
    """'📖 Сахих аль-Бухари (Sahih al-Bukhari) №5984, Джубайр' -> ('Сахих аль-Бухари', '5984')."""
    text = ref.lstrip(u'\U0001F4D6').strip()
    m = re.search(r'(?:#|№)\s*(\d+)', text)
    num = m.group(1) if m else ''
    coll = text[:m.start()] if m else text.split(',')[0]
    coll = re.sub(r'\s*\([^)]*\)\s*$', '', coll.strip())
    return coll.strip(), num


def tag_words(tags_line):
    out = []
    for t in tags_line.split():
        w = t.lstrip('#').strip()
        if w and w.lower() not in LANG_MARKERS and w not in out:
            out.append(w)
    return out


def build(caption, lang):
    p = parse(caption)
    coll, num = collection_and_number(p['ref'])
    narrator = p['ref'].split(',', 1)[1].strip() if ',' in p['ref'] else ''
    words = tag_words(p['tags'])
    tag_list = []
    short = re.sub(r'^(al|an|at|as|ad|аль|ал|ат|ан|ас|ад)-', '', coll.split()[-1].lower()) if coll else ''
    for t in (['hadith', coll.lower(), ('%s %s' % (short, num)).strip(), narrator.lower()]
              + words):
        t = t.strip().replace('#', '')
        if t and t not in tag_list:
            tag_list.append(t)
    yt_title = ('%s | %s %s' % (p['title'], coll, num)).replace('#', '').strip()
    yt_desc_parts = [p['matn'], p['moral'], p['ref'] + '\n' + p['verify'], '#Shorts ' + p['tags']]
    yt_desc = '\n\n'.join(x for x in yt_desc_parts if x.strip())
    fb_desc = '\n'.join(p['body']).strip()
    # P371: the Arabic stays (operator 2026-11-05); the caption goes in unchanged.
    tiktok = caption.strip()
    return {
        'instagram': caption.strip(),
        'facebook_title': yt_title,
        'facebook_description': fb_desc,
        'youtube_title': yt_title,
        'youtube_description': yt_desc,
        'tags': ', '.join(tag_list),
        'tiktok': tiktok,
    }


def _script(ch):
    o = ord(ch)
    if 0x0400 <= o <= 0x052F:
        return 'cyrillic'
    if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0xFB50 <= o <= 0xFEFF:
        return 'arabic'
    if ch.isalpha() and o < 0x0250:
        return 'latin'
    return None


def mixed_script_words(text):
    """[(word, scripts)] - words that mix Cyrillic, Arabic and Latin letters (P375).

    Each one seen so far was a defect: a Cyrillic 'х' inside an Arabic word on the #2581
    TikTok TJ caption, a Persian letter inside a Tajik word (#6724), '#парents' in a
    retyped YouTube block. A word is a run between whitespace; punctuation, digits and
    the Arabic marks that are not letters do not count. Pure."""
    out = []
    for word in text.split():
        scripts = sorted({s for s in map(_script, word) if s})
        if len(scripts) > 1:
            out.append((word, scripts))
    return out


def fenced_blocks(text):
    """The contents of the ``` blocks of a markdown text, line endings normalised and in NFC:
    an Arabic shadda written before or after its fatha is the same letter on screen, and
    the chat reorders them (every #2581 TikTok block did). Pure."""
    text = unicodedata.normalize('NFC', text.replace('\r\n', '\n'))
    return [b.strip('\n') for b in re.findall(r'```[^\n]*\n(.*?)```', text, re.S)]


def blocks_not_in(sent, platform_md):
    """The fenced blocks of `sent` that are not, byte for byte, a block of platform_md.

    P375: the text in out/platform-<n>.md is right, but a block reaches the chat by being
    written out again by the model, and a letter can change on the way. Run this on the
    message as sent. Pure."""
    known = set(fenced_blocks(platform_md))
    return [b for b in fenced_blocks(sent) if b not in known]


# P385 (operator 2026-11-09): the order the #6405 set was published in, kept fixed.
SEQUENCE = ('Sequence (fixed, P385): 1. Telegram, all four languages, posted by the agent '
            '(tg-post-set.py) on the operator\'s command. 2. Then EN -> RU -> UZ -> TJ, and for each '
            'language IG + FB -> YouTube Shorts -> TikTok. 3. One platform at a time: the next block '
            'is given after the operator\'s "d".')
# P385: Meta Business Suite's Create reel has no Facebook title field any more (2026-11-09);
# the Facebook tab's "Text" takes the whole caption, the same as Instagram's.
FB_TEXT_NOTE = 'Text (Facebook tab AND Instagram tab - the same caption; there is no title field):'
SHARE_STEP = ('Share step: Closed captions OFF, Translate your voice with Meta AI OFF, '
              'Remixing: don\'t allow.')


def render_md(number, results, covers=None):
    """covers {lang: path} - the YouTube cover make-covers.py wrote (P374), named in that
    language's YouTube block."""
    out = ['# Platform texts - #%s' % number, '',
           'Generated by scripts/platform-texts.py from the Telegram captions. Rules:',
           'reel-creation-pipeline.md "Publishing" (P368). Paste each block as is.', '',
           SEQUENCE, '']
    for lang, r in results:
        L = lang.upper()
        out += ['## %s' % L, '',
                '### Instagram + Facebook (Meta Business Suite: Create reel, post to both)', '',
                FB_TEXT_NOTE, '```', r['instagram'], '```', '',
                'Tags (Метки):', '```', r['tags'], '```', '',
                SHARE_STEP, '',
                '### YouTube Shorts (No, not made for kids - Public)', '',
                'Title:', '```', r['youtube_title'], '```', '',
                'Description:', '```', r['youtube_description'], '```', '',
                'Tags (SHOW MORE):', '```', r['tags'], '```', '']
        if covers and covers.get(lang):
            out += ['Cover (Thumbnail -> Upload file): `%s`' % covers[lang], '']
        out += ['### TikTok (AI label ON, Reuse of content OFF, Everyone)', '',
                '```', r['tiktok'], '```', '']
    return '\n'.join(out) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--number', required=True)
    ap.add_argument('--langs', nargs='*', choices=LANGS, default=list(LANGS))
    ap.add_argument('--check-sent', metavar='FILE',
                    help='P375: a message as sent to the chat; every ``` block in it must be a '
                         'block of out/platform-<n>.md, byte for byte. Writes nothing.')
    a = ap.parse_args(argv)
    if a.check_sent:
        src = os.path.join(REPO, 'out', 'platform-%s.md' % a.number)
        if not os.path.isfile(src):
            hits = glob.glob(os.path.join(REPO, 'out', 'published', '**', 'platform-%s.md' % a.number),
                             recursive=True)
            src = hits[0] if hits else None
        if not src:
            print('MISSING platform-%s.md' % a.number)
            return 1
        sent = io.open(a.check_sent, encoding='utf-8').read()
        n = len(fenced_blocks(sent))
        bad = blocks_not_in(sent, io.open(src, encoding='utf-8').read())
        for b in bad:
            print('NOT IN platform-%s.md:\n%s\n' % (a.number, b))
        mixed = mixed_script_words(sent)
        for word, scripts in mixed:
            print('MIXED SCRIPT  %s  (%s)' % (word, ' + '.join(scripts)))
        print('%s - %d block(s) checked, %d differ, %d mixed-script word(s)'
              % ('FAILED' if bad or mixed else 'OK', n, len(bad), len(mixed)))
        return 1 if bad or mixed else 0
    results = []
    for lang in a.langs:
        path = find_caption(a.number, lang)
        if not path:
            print('MISSING caption-%s-%s.txt (run build-caption.ts first)' % (a.number, lang))
            return 1
        results.append((lang, build(io.open(path, encoding='utf-8').read(), lang)))
    covers = {}
    for lang, _ in results:
        name = 'cover-%s-%s.jpg' % (a.number, lang)
        hits = sorted(glob.glob(os.path.join(REPO, 'out', 'work', '**', name), recursive=True))
        hits += [p for p in [os.path.join(REPO, 'out', name)] if os.path.isfile(p)]
        if hits:                                    # the reel folder first (P376), then out/
            covers[lang] = os.path.relpath(hits[0], REPO).replace(os.sep, '\\')
    md = render_md(a.number, results, covers)
    bad = mixed_script_words(md)
    if bad:
        for word, scripts in bad:
            print('MIXED SCRIPT  %s  (%s)' % (word, ' + '.join(scripts)))
        print('FAILED - fix the caption (build-caption.ts input), then run again. Nothing written.')
        return 1
    dest = os.path.join(REPO, 'out', 'platform-%s.md' % a.number)
    io.open(dest, 'w', encoding='utf-8', newline='\n').write(md)
    print('wrote %s (%d language(s))' % (dest, len(results)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
