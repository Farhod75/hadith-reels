"""scripts/approve-candidate.py - the Stage 4 guard, offline."""
import datetime as dt
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("approve_candidate", os.path.join(os.path.dirname(HERE), "approve-candidate.py"))
ac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ac)

ROW = {"candidate_id": "c", "hadith_number": "2749", "status": "verified"}


def test_verified_row_with_the_named_number_may_be_approved():
    assert ac.decide(ROW, "2749", "approve") is None


def test_wrong_number_is_refused():
    assert "not #2747" in ac.decide(ROW, "2747", "approve")


def test_only_a_verified_row_can_be_approved():
    assert "only a 'verified' row" in ac.decide(dict(ROW, status="translated"), "2749", "approve")
    assert ac.decide(dict(ROW, status="translated"), "2749", "reject") is None


def test_terminal_rows_are_never_touched():
    for st in ("approved", "rejected", "promoted"):
        assert "already" in ac.decide(dict(ROW, status=st), "2749", "approve")
    assert ac.decide(None, "2749", "approve") == "no candidate with that id"


def test_patch_carries_the_operators_words():
    now = dt.datetime(2026, 11, 3, 16, 32, tzinfo=dt.timezone.utc)
    p = ac.patch_for("approve", u"да", "farhod", now)
    assert p == {"status": "approved", "reviewed_by": "farhod", "reviewed_at": "2026-11-03T16:32:00+00:00",
                 "review_action": "approve", "review_reason": u"да"}
