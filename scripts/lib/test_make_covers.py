"""P374: scripts/make-covers.py - a distinct YouTube cover per UZ/TJ leg.

Operator 2026-11-06: desktop Studio offers three frames of its own choice or an uploaded
file, and four identical covers read as one video in search. Each language that gets a
cover must get a DIFFERENT scene of the set, never the opening one when the set has more.
"""
import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('make_covers', os.path.join(HERE, '..', 'make-covers.py'))
mc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mc)

SIX = ['m2581-empty.mp4', 'm2581-salah.mp4', 'm2581-iftar.mp4', 'm2581-zakat.mp4',
       'm2581-spilt.mp4', 'm2581-road.mp4']
FOUR = ['a.mp4', 'b.mp4', 'c.mp4', 'd.mp4']


def test_default_is_uz_and_tj():
    assert mc.DEFAULT_LANGS == ('uz', 'tj')


def test_two_languages_get_two_different_scenes_spread_across_the_set():
    assert mc.pick_scenes(SIX, ['uz', 'tj']) == {'uz': 'm2581-iftar.mp4', 'tj': 'm2581-spilt.mp4'}
    assert mc.pick_scenes(FOUR, ['uz', 'tj']) == {'uz': 'b.mp4', 'tj': 'd.mp4'}


def test_the_opening_clip_is_not_used_while_others_remain():
    for n in range(2, 8):
        clips = ['c%d.mp4' % i for i in range(n)]
        for m in range(1, n):
            picks = mc.pick_scenes(clips, ['l%d' % i for i in range(m)])
            assert 'c0.mp4' not in picks.values(), (n, m, picks)
            assert len(set(picks.values())) == m


def test_an_override_picks_the_named_scene():
    assert mc.pick_scenes(SIX, ['uz', 'tj'], {'uz': 'zakat'})['uz'] == 'm2581-zakat.mp4'


def test_an_override_onto_the_other_language_scene_is_refused():
    with pytest.raises(ValueError):
        mc.pick_scenes(SIX, ['uz', 'tj'], {'uz': 'spilt'})


def test_an_ambiguous_or_unknown_override_is_refused():
    with pytest.raises(ValueError):
        mc.pick_scenes(SIX, ['uz'], {'uz': 'm2581'})
    with pytest.raises(ValueError):
        mc.pick_scenes(SIX, ['uz'], {'uz': 'moon'})


def test_fewer_clips_than_covers_is_refused():
    with pytest.raises(ValueError):
        mc.pick_scenes(['a.mp4'], ['uz', 'tj'])


def test_wrap_keeps_words_whole_and_respects_the_width():
    lines = mc.wrap('Муфлиси ҳақиқӣ кист?'.split(), lambda s: len(s) <= 14)
    assert lines == ['Муфлиси ҳақиқӣ', 'кист?']
    assert mc.wrap(['Supercalifragilistic'], lambda s: len(s) <= 5) == ['Supercalifragilistic']


def test_scene_argument_parsing():
    assert mc.parse_overrides(['uz=iftar', 'tj = road']) == {'uz': 'iftar', 'tj': 'road'}
    with pytest.raises(ValueError):
        mc.parse_overrides(['uz'])


def test_a_leg_on_slowed_copies_gets_its_own_file_of_the_same_scene():
    base = ['m223-wudu.mp4', 'b6406-scalesky-r.mp4', 'm223-horizon.mp4', 'm223-lamp.mp4']
    uz = ['m223-wudu-s.mp4', 'b6406-scalesky-r-s.mp4', 'm223-horizon-s.mp4', 'm223-lamp-s.mp4']
    picks = mc.pick_scenes(base, ['uz', 'tj'])
    assert mc.same_position(base, picks, {'uz': uz, 'tj': base}) == {
        'uz': 'b6406-scalesky-r-s.mp4', 'tj': 'm223-lamp.mp4'}


def test_a_leg_whose_list_differs_in_length_keeps_the_base_clip():
    base = ['a.mp4', 'b.mp4', 'c.mp4']
    assert mc.same_position(base, {'uz': 'b.mp4'}, {'uz': ['x.mp4']}) == {'uz': 'b.mp4'}
