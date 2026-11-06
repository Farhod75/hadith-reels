"""P372: scripts/list-library.py --notes - what the docs already say about a number.

#6675 went into production although reel-tracker.md and OPEN_ITEMS.md both said
it must not follow #2654 without a deliberate call: nothing put that line in front
of whoever chose the next set. notes_for() is the function that does.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('list_library',
                                               os.path.join(HERE, '..', 'list-library.py'))
ll = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ll)

TRACKER = (
    "| Sahih al-Bukhari #6675 (cited as #6871 until 2026-10-30) | - | - | DO NOT PRODUCE after #2654 |\n"
    "| Sahih al-Bukhari #2654 | EN | Adults | R094 |\n"
    "| Sahih Muslim #66750 | EN | Adults | R999 |\n"
)
OPEN = "**Sahih al-Bukhari #6675 must never follow #2654 without a deliberate call.**\n"


def test_finds_the_pairing_rule_in_both_files():
    notes = ll.notes_for('6675', {'reel-tracker.md': TRACKER, 'OPEN_ITEMS.md': OPEN})
    files = sorted({n[0] for n in notes})
    assert files == ['OPEN_ITEMS.md', 'reel-tracker.md']
    assert any('DO NOT PRODUCE' in n[2] for n in notes)


def test_a_longer_number_is_not_a_match():
    notes = ll.notes_for('6675', {'reel-tracker.md': TRACKER})
    assert [n[1] for n in notes] == [1]


def test_the_other_side_of_the_pair_sees_it_too():
    notes = ll.notes_for('2654', {'reel-tracker.md': TRACKER, 'OPEN_ITEMS.md': OPEN})
    assert len(notes) == 3


def test_cap_reports_what_was_cut():
    text = '\n'.join('line #31 n%d' % i for i in range(10))
    notes = ll.notes_for('31', {'OPEN_ITEMS.md': text}, cap=4)
    assert len(notes) == 5
    assert notes[-1] == ('OPEN_ITEMS.md', 0, '... 6 more')


def test_nothing_recorded_is_an_empty_list():
    assert ll.notes_for('1', {'OPEN_ITEMS.md': 'no numbers here'}) == []
