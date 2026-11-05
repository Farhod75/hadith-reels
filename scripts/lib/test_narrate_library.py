"""P370: scripts/narrate-library.py - which library rows get narrated for Listen.

Pure planning only: no network, no ElevenLabs. Each skip rule is a way Listen could
read the wrong thing aloud, or spend twice, so each is pinned.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('narrate_library', os.path.join(HERE, '..', 'narrate-library.py'))
nl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nl)


def row(id_, coll, num, **kw):
    r = {'id': id_, 'collection': coll, 'hadith_number': num, 'grade': 'sahih', 'narrator': 'Abu Hurairah',
         'text_english': 'Deeds are by intentions.', 'text_russian': 'Дела по намерениям.',
         'text_uzbek_cyrillic': 'Амаллар ниятларга кўра.', 'text_tajik': 'Амалҳо ба ниятҳост.'}
    r.update(kw)
    return r


def lead(narrator, lang):
    if narrator == 'Unknown':
        raise KeyError(narrator)
    return '%s said (%s):' % (narrator, lang)


def jobs_for(rows, index=None, excl=None, prod=None):
    return nl.plan(rows, index or {}, lead, excl or {}, prod or set())


def test_one_row_gives_four_takes_with_the_reel_s_block():
    jobs, skips = jobs_for([row('a', 'Sahih al-Bukhari', '1')])
    assert [j['lang'] for j in jobs] == ['en', 'ru', 'uz', 'tj']
    assert jobs[0]['text'] == 'Abu Hurairah said (en): "Deeds are by intentions."'
    assert jobs[1]['text'] == 'Abu Hurairah said (ru): «Дела по намерениям».'
    assert jobs[0]['slug'] == 'bukhari-1'
    assert skips == []


def test_already_published_language_is_not_narrated_again():
    jobs, skips = jobs_for([row('a', 'Sahih Muslim', '2749')], index={'a': {'en': {}, 'ru': {}}})
    assert [j['lang'] for j in jobs] == ['uz', 'tj']
    assert ('Sahih Muslim #2749', 'en', 'has Listen') in skips


def test_duplicate_collection_number_is_skipped_for_both_rows():
    rows = [row('a', 'Sahih al-Bukhari', '1469'), row('b', 'Sahih al-Bukhari', '1469')]
    jobs, skips = jobs_for(rows)
    assert jobs == []
    assert all('not unique' in why for _, _, why in skips)


def test_weak_grade_empty_text_unknown_narrator_and_exclusion():
    rows = [row('w', 'Sunan Ibn Majah', '1', grade='daif'),
            row('e', 'Sunan Ibn Majah', '2', text_tajik=''),
            row('n', 'Sunan Ibn Majah', '3', narrator='Unknown'),
            row('x', 'Sahih Muslim', '1510')]
    jobs, skips = jobs_for(rows, excl={('x', 'uz'): 'jazo reads as punishment'})
    langs = {(j['id'], j['lang']) for j in jobs}
    assert not any(i == 'w' for i, _ in langs)
    assert ('e', 'tj') not in langs and ('e', 'en') in langs
    assert not any(i == 'n' for i, _ in langs)
    assert ('x', 'uz') not in langs and ('x', 'ru') in langs
    assert any(why.startswith('excluded: jazo') for _, _, why in skips)


def test_reel_in_production_and_over_the_tts_limit_are_skipped():
    rows = [row('p', 'Sahih al-Bukhari', '6675'), row('l', 'Jami at-Tirmidhi', '2616', text_english='x ' * 600)]
    jobs, skips = jobs_for(rows, prod={'bukhari-6675'})
    assert not any(j['id'] == 'p' for j in jobs)
    assert ('Jami at-Tirmidhi #2616', 'en') in {(r, l) for r, l, w in skips if 'P354' in w}


def test_slug_matches_publish_narration_key():
    assert nl.slug_for(row('a', 'Sunan Ibn Majah', '4251')) == 'ibnmajah-4251'
    assert nl.slug_for(row('a', 'Jami at-Tirmidhi', '1161')) == 'tirmidhi-1161'
    assert nl.coll_key('Sunan an-Nasai') == 'nasai'


def test_exclusions_file_parses_and_defaults_to_all_languages():
    ex = nl.load_exclusions(os.path.join(HERE, '..', 'narration-exclusions.json'))
    assert ex[('f9401679-728a-4352-9196-7557bb955f33', 'uz')]
    assert ('f9401679-728a-4352-9196-7557bb955f33', 'en') not in ex
    assert ('ce411224-c8ef-4dff-a733-53e19c8256b5', 'ru') in ex
