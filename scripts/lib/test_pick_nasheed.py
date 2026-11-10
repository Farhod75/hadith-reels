"""scripts/pick-nasheed.py - the P386 mood filter, offline."""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("pick_nasheed", os.path.join(SCRIPTS, "pick-nasheed.py"))
pn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pn)

ROWS = [{"bed": b} for b in ("march.mp3", "calm.mp3", "unrated.mp3")]
MOODS = {"march.mp3": "energetic", "calm.mp3": "calm"}


def test_no_mood_keeps_every_bed():
    kept, dropped = pn.filter_by_mood(ROWS, MOODS, None)
    assert kept == ROWS and dropped == []


def test_calm_drops_the_energetic_bed_and_keeps_unrated():
    kept, dropped = pn.filter_by_mood(ROWS, MOODS, "calm")
    assert [r["bed"] for r in kept] == ["calm.mp3", "unrated.mp3"]
    assert [r["bed"] for r in dropped] == ["march.mp3"]


def test_label_says_when_a_bed_was_never_rated():
    assert pn.mood_label(MOODS, "calm.mp3") == "mood: calm"
    assert "not rated" in pn.mood_label(MOODS, "unrated.mp3")


def test_moods_come_from_the_registry_and_ignore_unknown_values(tmp_path):
    p = tmp_path / "reg.json"
    p.write_text(json.dumps({"audio": {"a.mp3": {"mood": "calm"}, "b.mp3": {"mood": "loud"},
                                       "c.mp3": {"lanes": ["adults"]}}}), encoding="utf-8")
    assert pn.bed_moods(str(p)) == {"a.mp3": "calm"}


def test_the_real_registry_reads():
    reg = os.path.join(os.path.dirname(SCRIPTS), "assets", "asset-registry.json")
    moods = pn.bed_moods(reg)
    assert all(m in pn.MOODS for m in moods.values())
