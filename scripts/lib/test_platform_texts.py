"""P368: scripts/platform-texts.py - the per-platform publishing fields.

The rules in reel-creation-pipeline.md "Publishing" were broken by hand on
2026-11-04 ('#' in YouTube titles, Arabic in TikTok captions). These tests pin
them, using the real #5984 captions' shape in EN and RU.
"""
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('platform_texts',
                                               os.path.join(HERE, '..', 'platform-texts.py'))
pt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pt)

EN = """The Tie You Must Not Cut

«One who severs ties of kinship will not enter Paradise.»

لَا يَدْخُلُ الْجَنَّةَ قَاطِعٌ

A relative who has grown distant is still family. Take the first step today: a call, a visit, a kind word.

\U0001F4D6 Sahih al-Bukhari #5984, Jubayr ibn Mutim
\U0001F50D Verify: hadithverifier.com

#kindness #family #jannah #hadith #islamic #authentic #english
"""

RU = """Связь, которую нельзя рвать

«Не войдёт в Рай тот, кто разрывает родственные связи».

لَا يَدْخُلُ الْجَنَّةَ قَاطِعٌ

Отдалившийся родственник — всё равно родной.

\U0001F4D6 Сахих аль-Бухари (Sahih al-Bukhari) №5984, Джубайр ибн Мутим
\U0001F50D Проверить хадис: hadithverifier.com

#доброта #kindness #семья #family #хадис #русский
"""


def test_youtube_title_has_no_hash_and_a_bare_number():
    for cap, lang in ((EN, 'en'), (RU, 'ru')):
        t = pt.build(cap, lang)['youtube_title']
        assert '#' not in t
        assert t.endswith(' 5984')
    assert pt.build(EN, 'en')['youtube_title'] == 'The Tie You Must Not Cut | Sahih al-Bukhari 5984'
    assert pt.build(RU, 'ru')['youtube_title'].endswith('| Сахих аль-Бухари 5984')


def test_tiktok_is_the_caption_with_the_arabic_and_opens_with_the_title():
    # P371: the no-Arabic rule was withdrawn on 2026-11-05 (the operator's screenshot).
    for cap, lang in ((EN, 'en'), (RU, 'ru')):
        tk = pt.build(cap, lang)['tiktok']
        assert tk == cap.strip()
        assert pt.ARABIC.search(tk)
        assert tk.split('\n')[0] == cap.split('\n')[0]


def test_instagram_is_the_telegram_caption_unchanged():
    assert pt.build(EN, 'en')['instagram'] == EN.strip()


def test_facebook_description_is_the_caption_without_its_title_line():
    r = pt.build(EN, 'en')
    assert r['facebook_description'].startswith('«One who severs')
    assert 'The Tie You Must Not Cut' not in r['facebook_description']


def test_youtube_description_starts_with_shorts_hashtags_last_and_has_the_matn():
    d = pt.build(EN, 'en')['youtube_description']
    assert d.split('\n')[-1].startswith('#Shorts ')
    assert '«One who severs' in d
    assert '\U0001F4D6 Sahih al-Bukhari #5984' in d


def test_tags_are_plain_words_without_hash_or_language_marker():
    tags = pt.build(RU, 'ru')['tags']
    assert '#' not in tags
    parts = [x.strip() for x in tags.split(',')]
    assert 'русский' not in parts
    assert 'бухари 5984' in parts
    assert len(parts) == len(set(parts))


def test_reference_parse_handles_hash_and_numero():
    assert pt.collection_and_number('\U0001F4D6 Sahih al-Bukhari #38, Abu Hurairah') == ('Sahih al-Bukhari', '38')
    assert pt.collection_and_number('\U0001F4D6 Сахих Муслим (Sahih Muslim) №2749, X') == ('Сахих Муслим', '2749')
