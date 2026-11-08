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


def test_covers_and_platform_texts_stay_with_an_unpublished_set_and_move_with_a_published_one():
    # P374: cover-<n>-<lang>.jpg and platform-<n>.md belong to the set - they stay at the
    # top of out/ until it is published (not 'deliverables', not 'not read by any tool').
    to.UNPUBLISHED.clear()
    to.UNPUBLISHED.add('223')
    try:
        for name in ('cover-223-uz.jpg', 'cover-223-tj.jpg', 'platform-223.md'):
            dest, why = to.classify(name, known={'2581'})
            assert dest is None, (name, dest, why)
        dest, _ = to.classify('cover-2581-uz.jpg', known={'2581'})
        assert dest.replace('\\', '/') == '_archive/sets/2581'
    finally:
        to.UNPUBLISHED.clear()


def test_one_offs_of_a_set_in_work_stay_until_it_is_published():
    # P378: tidy-out at #6114's close archived #6405's Kling runner and its open logs
    to.UNPUBLISHED.clear()
    to.UNPUBLISHED.add('6405')
    try:
        assert to.classify('run-b6405-kling.ps1', set())[0] is None
        assert to.classify('b6405-foam-kling.log', set())[0] is None
        assert to.classify('kling-6405-draft.md', set())[0] is None
        assert to.classify('run-b6114-kling.ps1', {'6114'})[0] == os.path.join('_archive', 'sets', '6114')
    finally:
        to.UNPUBLISHED.clear()
