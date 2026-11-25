# -*- coding: utf-8 -*-
"""
al_mudarris.py - the Al-Mudarris line under the HV line in every new reel description (P433).

Operator task 2026-11-24 (project doc HR-handoff-al-mudarris-link.md): one line about
Al-Mudarris (free Arabic lessons) goes straight after the 🔍 hadithverifier.com line, on
every platform and in every language. The HV line and the rest of the text are not changed.

  Telegram, YouTube   - the line carries a link with UTM tags, utm_content = the reel id (R...).
  Instagram/Facebook  - links in a reel caption are not clickable: a short line without a link;
  TikTok                the tagged link sits in the profile (set once by the operator).

The lines below are copied VERBATIM from the operator's doc. Do not re-translate or improve
them; test_al_mudarris.py pins them byte for byte.

TikTok is OFF until the operator adds the profile link there (2026-11-24: the TikTok account
needs a Business account for a bio link; decided to wait for the posting-schedule test first).
"""
import io
import json
import os
import re

HV_PREFIX = u'\U0001F50D'
DOMAIN = 'al-mudarris.com'
URL = ('https://al-mudarris.com/?utm_source={source}&utm_medium=reel'
       '&utm_campaign=hv_reels&utm_content={reel_id}')

# Telegram and YouTube: the text before the link, verbatim.
LINK_TEXT = {
    'uz': u'📖 Араб тили, сарф ва наҳв — бепул дарслар: ',
    'ru': u'📖 Арабский язык, сарф и нахв — бесплатные уроки (на узбекском, русском, таджикском): ',
    'tj': u'📖 Забони арабӣ, сарф ва наҳв — дарсҳои ройгон: ',
    'en': u'📖 Free Arabic grammar lessons — sarf and nahw (in Uzbek, Russian, Tajik): ',
}
# Instagram/Facebook and TikTok: no link in the caption, verbatim.
BIO_LINE = {
    'uz': u'📖 Араб тили бўйича бепул дарслар — ҳавола профилда (al-mudarris.com)',
    'ru': u'📖 Бесплатные уроки арабского — ссылка в профиле (al-mudarris.com)',
    'tj': u'📖 Дарсҳои ройгони забони арабӣ — пайванд дар профил (al-mudarris.com)',
    'en': u'📖 Free Arabic lessons — link in bio (al-mudarris.com)',
}
# Profile links (set by the operator once; never inserted by code).
PROFILE_URL = {
    'instagram': 'https://al-mudarris.com/?utm_source=instagram&utm_medium=bio&utm_campaign=hv_reels',
    'tiktok': 'https://al-mudarris.com/?utm_source=tiktok&utm_medium=bio&utm_campaign=hv_reels',
}
# Which platforms get the line. TikTok waits for its profile link (see the module docstring).
ENABLED = {'telegram': True, 'youtube': True, 'instagram': True, 'tiktok': False}
LANG_ORDER = ('en', 'ru', 'uz', 'tj')    # the order R numbers are given within a set


def line_for(platform, lang, reel_id=None):
    """The one Al-Mudarris line for this platform and language, or '' when the platform is off."""
    if not ENABLED.get(platform):
        return ''
    if platform in ('telegram', 'youtube'):
        if not reel_id or not re.match(r'^R\d{3,}$', reel_id):
            raise ValueError('reel id like R294 needed for the %s link, got %r' % (platform, reel_id))
        return LINK_TEXT[lang] + URL.format(source=platform, reel_id=reel_id)
    return BIO_LINE[lang]


def insert_after_hv(text, line):
    """Put `line` straight after the first 🔍 line. One Al-Mudarris line per description:
    a text that already has one is returned unchanged. No 🔍 line -> ValueError (the line
    has no defined place, and a caption without the HV line is itself a defect)."""
    if not line or DOMAIN in text:
        return text
    lines = text.split('\n')
    for i, l in enumerate(lines):
        if l.startswith(HV_PREFIX):
            return '\n'.join(lines[:i + 1] + [line] + lines[i + 1:])
    raise ValueError('no 🔍 hadithverifier line to put the Al-Mudarris line after')


def apply(text, platform, lang, reel_id=None):
    return insert_after_hv(text, line_for(platform, lang, reel_id))


def reel_ids(number, root):
    """{lang: 'R294', ...} for hadith <number>. From out/set-<n>.json "r_first" (R ids of a set
    run EN, RU, UZ, TJ - the same order docs-set.py uses), else from the set's rows already in
    reel-tracker.md. Neither -> ValueError: a guessed id would mislabel the analytics."""
    sp = os.path.join(root, 'out', 'set-%s.json' % number)
    if os.path.isfile(sp):
        s = json.load(io.open(sp, encoding='utf-8'))
        if s.get('r_first'):
            first = int(str(s['r_first']).lstrip('R'))
            return {l: 'R%03d' % (first + i) for i, l in enumerate(LANG_ORDER)}
    tp = os.path.join(root, 'reel-tracker.md')
    found = {}
    if os.path.isfile(tp):
        for row in io.open(tp, encoding='utf-8'):
            cells = [c.strip() for c in row.split('|')]
            if len(cells) > 8 and re.match(r'^R\d{3,}$', cells[1]) and re.search(r'#%s$' % re.escape(str(number)), cells[3]):
                lang = cells[8].lower()
                if lang in LANG_ORDER and 'adults' in row.lower():
                    found.setdefault(lang, cells[1])
    if found:
        return found
    raise ValueError('no reel ids for #%s: add "r_first" (e.g. 294) to out/set-%s.json' % (number, number))
