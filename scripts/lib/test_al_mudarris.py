# -*- coding: utf-8 -*-
"""P433: the Al-Mudarris line under the HV line (operator doc HR-handoff-al-mudarris-link.md)."""
import importlib.util
import json
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


am = _load('al_mudarris', os.path.join(HERE, 'al_mudarris.py'))
pt = _load('platform_texts_433', os.path.join(HERE, '..', 'platform-texts.py'))
tg = _load('tg_post_set_433', os.path.join(HERE, '..', 'tg-post-set.py'))

CAP = (u"Title\n\n«Matn.»\n\nالحديث\n\nMoral.\n\n"
       u"\U0001F4D6 Jami at-Tirmidhi #3479, Abu Hurairah\n\U0001F50D Verify: hadithverifier.com\n\n#dua #hadith #english")


def test_lines_are_the_operators_text_verbatim():
    assert am.LINK_TEXT['ru'] == u'📖 Арабский язык, сарф и нахв — бесплатные уроки (на узбекском, русском, таджикском): '
    assert am.BIO_LINE['uz'] == u'📖 Араб тили бўйича бепул дарслар — ҳавола профилда (al-mudarris.com)'
    assert am.line_for('telegram', 'en', 'R298') == (
        u'📖 Free Arabic grammar lessons — sarf and nahw (in Uzbek, Russian, Tajik): '
        'https://al-mudarris.com/?utm_source=telegram&utm_medium=reel&utm_campaign=hv_reels&utm_content=R298')


def test_no_latin_lookalikes_in_cyrillic_lines():
    for lang in ('uz', 'ru', 'tj'):
        for s in (am.LINK_TEXT[lang], am.BIO_LINE[lang]):
            assert not re.search(r'[A-Za-z]', s.replace(am.DOMAIN, '')), (lang, s)


def test_line_goes_straight_after_hv_and_only_once():
    out = am.apply(CAP, 'youtube', 'en', 'R298')
    lines = out.split('\n')
    i = next(k for k, l in enumerate(lines) if l.startswith(u'\U0001F50D'))
    assert 'utm_source=youtube' in lines[i + 1]
    assert out.count(am.DOMAIN) == 1
    assert am.apply(out, 'youtube', 'en', 'R298') == out          # already there -> unchanged
    assert out.replace(lines[i + 1] + '\n', '') == CAP            # nothing else changed


def test_link_platforms_need_a_reel_id():
    with pytest.raises(ValueError):
        am.line_for('telegram', 'ru', None)


def test_tiktok_is_off_until_the_profile_link_exists():
    assert am.ENABLED['tiktok'] is False
    assert am.apply(CAP, 'tiktok', 'ru') == CAP


def test_no_hv_line_is_an_error():
    with pytest.raises(ValueError):
        am.insert_after_hv('no verify line here', 'x')


def test_platform_texts_build():
    r = pt.build(CAP, 'en', reel_id='R298')
    assert 'utm_source=youtube' in r['youtube_description'] and 'utm_content=R298' in r['youtube_description']
    assert am.BIO_LINE['en'] in r['instagram'] and 'utm_' not in r['instagram']
    assert am.DOMAIN not in r['tiktok']
    assert pt.build(CAP, 'en')['instagram'] == CAP.strip()          # no reel id -> old shape


def test_tg_plan_full_and_short(tmp_path):
    out = tmp_path / 'out'
    out.mkdir()
    (out / 'caption-3479-ru.txt').write_text(CAP + u'\n' + u'x' * 1100, encoding='utf-8')
    d = out / 'work' / 'adults' / 'tirmidhi-3479' / 'ru'
    d.mkdir(parents=True)
    (d / 'adults-ru-tirmidhi-3479-reel.mp4').write_bytes(b'x')
    p = tg.plan_language('3479', 'tirmidhi-3479', 'ru', root=str(tmp_path), reel_id='R299')
    assert p['split']
    for c in (p['full'], p['short']):
        assert c.count('utm_source=telegram') == 1 and 'utm_content=R299' in c


def test_reel_ids_from_set_file(tmp_path):
    (tmp_path / 'out').mkdir()
    (tmp_path / 'out' / 'set-3479.json').write_text(json.dumps({'r_first': 298}), encoding='utf-8')
    assert am.reel_ids('3479', str(tmp_path)) == {'en': 'R298', 'ru': 'R299', 'uz': 'R300', 'tj': 'R301'}


def test_reel_ids_missing_is_an_error(tmp_path):
    with pytest.raises(ValueError):
        am.reel_ids('9999', str(tmp_path))
