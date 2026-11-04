"""P362: scripts/publish-narration.py - which narration may stand behind Listen."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('publish_narration',
                                               os.path.join(HERE, '..', 'publish-narration.py'))
pn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pn)

ROW = {'id': 'r1', 'collection': 'Sahih al-Bukhari', 'hadith_number': '6412',
       'text_english': 'There are two blessings which many people lose.',
       'text_russian': 'Два блага', 'text_uzbek_cyrillic': '', 'text_tajik': ''}


def _take(tmp_path, folder, lang, slug, spoken, mtime, audio=b'ID3audio'):
    d = tmp_path / folder
    d.mkdir(parents=True, exist_ok=True)
    mp3 = d / ('adults-%s-%s-story.mp3' % (lang, slug))
    mp3.write_bytes(audio)
    (d / ('adults-%s-%s-story.txt' % (lang, slug))).write_text(spoken, encoding='utf-8')
    os.utime(mp3, (mtime, mtime))
    return mp3


def test_collection_names_and_slugs_meet():
    assert pn.coll_key('Sahih al-Bukhari') == pn.coll_key('bukhari')
    assert pn.coll_key('Jami at-Tirmidhi') == pn.coll_key('at-tirmidhi')
    assert pn.coll_key('Sunan Abu Dawud') == pn.coll_key('abu-dawud')


def test_a_take_that_contains_the_matn_is_used(tmp_path):
    _take(tmp_path, 'a', 'en', 'bukhari-6412',
          'Ibn Abbas narrated that the Prophet said: "There are two blessings which many people lose."', 2e9)
    best = pn.find_takes([ROW], [str(tmp_path)], 1e9, 0.9)
    assert set(best) == {('r1', 'en')}


def test_a_story_about_the_hadith_is_not_the_hadith(tmp_path):
    _take(tmp_path, 'a', 'en', 'bukhari-6412', 'A man once wasted his free time and regretted it.', 2e9)
    assert pn.find_takes([ROW], [str(tmp_path)], 1e9, 0.9) == {}


def test_takes_older_than_the_voice_cutoff_are_skipped(tmp_path):
    _take(tmp_path, 'a', 'en', 'bukhari-6412', ROW['text_english'], 5e8)
    assert pn.find_takes([ROW], [str(tmp_path)], 1e9, 0.9) == {}


def test_the_newest_usable_take_wins(tmp_path):
    _take(tmp_path, 'old', 'en', 'bukhari-6412', ROW['text_english'], 2e9, b'old')
    new = _take(tmp_path, 'new', 'en', 'bukhari-6412', ROW['text_english'], 3e9, b'new')
    assert pn.find_takes([ROW], [str(tmp_path)], 1e9, 0.9)[('r1', 'en')]['mp3'] == str(new)


def test_plan_uploads_only_changed_audio_under_a_content_address(tmp_path):
    _take(tmp_path, 'a', 'en', 'bukhari-6412', ROW['text_english'], 2e9, b'same')
    best = pn.find_takes([ROW], [str(tmp_path)], 1e9, 0.9)
    uploads, index = pn.plan(best, {'items': {}})
    assert len(uploads) == 1 and uploads[0][1].startswith('r1/en-')
    again, _ = pn.plan(best, index)
    assert again == []
