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


def test_a_cover_is_named_in_its_language_youtube_block_only():
    # P374: make-covers.py writes out/cover-<n>-<lang>.jpg for UZ/TJ; the YouTube block
    # of that language says which file to upload, the other languages say nothing.
    res = [('en', pt.build(EN, 'en')), ('ru', pt.build(RU, 'ru'))]
    md = pt.render_md('5984', res, {'ru': 'out\\cover-5984-ru.jpg'})
    en_part, ru_part = md.split('## RU')
    assert 'cover-5984' not in en_part
    yt, tiktok = ru_part.split('### TikTok')
    assert 'Upload file): `out\\cover-5984-ru.jpg`' in yt
    assert 'cover' not in tiktok
    assert 'cover' not in pt.render_md('5984', res)


def test_mixed_script_words_catches_the_three_defects_seen():
    # P375: the #2581 TikTok TJ slip, the #6724 Persian letter, the '#парents' retype.
    assert pt.mixed_script_words('وهذا مِن хَسَناتِه،') == [('хَسَناتِه،', ['arabic', 'cyrillic'])]
    assert pt.mixed_script_words('#парents') == [('#парents', ['cyrillic', 'latin'])]
    assert pt.mixed_script_words('Мардگон') == [('Мардگон', ['arabic', 'cyrillic'])]


def test_mixed_script_words_passes_the_real_captions():
    assert pt.mixed_script_words(EN) == []
    assert pt.mixed_script_words(RU) == []
    assert pt.mixed_script_words('Сахих Муслим (Sahih Muslim) №2581, #хадис #kindness') == []


def test_a_sent_block_must_match_a_platform_block_byte_for_byte():
    md = pt.render_md('5984', [('en', pt.build(EN, 'en')), ('ru', pt.build(RU, 'ru'))])
    good = [b for b in pt.fenced_blocks(md) if 'Paradise' in b][0]
    assert pt.blocks_not_in('text\n```\n%s\n```\nmore' % good, md) == []
    bad = good.replace('Paradise', 'Paradice')
    assert pt.blocks_not_in('```\n%s\n```' % bad, md) == [bad]
    assert pt.blocks_not_in('```\r\n%s\r\n```' % good.replace('\n', '\r\n'), md) == []


def test_shadda_and_fatha_in_either_order_are_the_same_block():
    # P375: the chat wrote every #2581 TikTok block with fatha before shadda; NFC agrees.
    md = '```\nإنَّ\n```'
    assert pt.blocks_not_in('```\nإن\u064e\u0651\n```', md) == []


def test_meta_block_has_no_facebook_title_and_the_caption_goes_in_whole():
    # P385: Meta Business Suite dropped the Facebook title field (2026-11-09); the Facebook
    # "Text" field takes the full caption, the same as Instagram's.
    md = pt.render_md('5984', [('en', pt.build(EN, 'en'))])
    meta, rest = md.split('### YouTube Shorts')
    assert 'Facebook title' not in md
    assert pt.FB_TEXT_NOTE in meta
    assert EN.strip() in meta
    assert 'Closed captions OFF' in meta


def test_the_publishing_sequence_heads_every_platform_file():
    # P385: TG (agent, all languages) -> per language EN, RU, UZ, TJ: IG+FB -> YT -> TikTok.
    md = pt.render_md('5984', [('en', pt.build(EN, 'en')), ('ru', pt.build(RU, 'ru'))])
    assert md.index(pt.SEQUENCE) < md.index('## EN') < md.index('## RU')
    en = md.split('## RU')[0]
    assert en.index('### Instagram + Facebook') < en.index('### YouTube Shorts') < en.index('### TikTok')
