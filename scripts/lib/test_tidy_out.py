"""P373: scripts/tidy-out.py must keep the files of a set being prepared.

On 2026-11-06 the #2734 set close ran tidy-out --apply while #2581 was between its
drafts and its narration: set-2581.json, caption-2581.json and the four drafts went
to out/_archive/misc as 'not read by any tool', and narrate-reel.py then refused to
run ('no draft'). A set has no work/ folder until its narration is recorded.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('tidy_out', os.path.join(HERE, '..', 'tidy-out.py'))
to = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(to)


def test_a_set_file_for_an_unpublished_number_is_in_preparation():
    names = ['set-2581.json', 'draft-muslim-2581-en.txt', 'caption-2581.json', 'set-2734.json']
    assert to.in_preparation(names, known={'2734'}) == {'2581'}


def test_other_files_do_not_make_a_set():
    names = ['caption-9999.json', 'draft-muslim-9999-en.txt', 'set-notes.json', 'set-12a.json']
    assert to.in_preparation(names, known=set()) == set()


def test_the_drafts_of_a_set_in_preparation_stay():
    to.UNPUBLISHED.clear()
    to.UNPUBLISHED.update(to.in_preparation(['set-2581.json'], known=set()))
    try:
        for name in ('set-2581.json', 'caption-2581.json', 'draft-muslim-2581-ru.txt'):
            dest, why = to.classify(name, known=set())
            assert dest is None, (name, dest, why)
    finally:
        to.UNPUBLISHED.clear()
