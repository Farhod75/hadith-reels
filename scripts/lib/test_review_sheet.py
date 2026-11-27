"""P450: scripts/review-sheet.py - grouping the stills and picking clip frames. Offline."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('review_sheet', os.path.join(HERE, '..', 'review-sheet.py'))
rv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rv)


def test_stills_group_by_scene_with_variants_in_order():
    names = ['b6019-doors-2.jpg', 'b6019-doors-1.jpg', 'b6019-light-v2-3.jpg', 'b6019-doors-10.jpg',
             'm2589-door-1.jpg', 'b60190-x-1.jpg', 'b6019-doors.log', 'b6019-today-1.jpg']
    g = rv.still_groups(names, '6019')
    assert list(g) == ['doors', 'light-v2', 'today']
    assert g['doors'] == ['b6019-doors-1.jpg', 'b6019-doors-2.jpg', 'b6019-doors-10.jpg']


def test_frame_times_show_start_middle_and_end():
    assert rv.frame_times(10.04) == [1.0, 5.02, 9.54]
    assert rv.frame_times(2.0) == [0.5, 1.0, 1.5]
