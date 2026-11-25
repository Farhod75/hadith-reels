"""scripts/lib/set_grade.py - P438: the tracker grade comes from the library row."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import set_grade as g


def test_hasan_row_is_written_hasan(tmp_path):
    # Tirmidhi #3479: al-Albani hasan - docs-set used to write Sahih
    assert g.set_grade({"number": "3479", "library_id": "c0d58e8c"}, str(tmp_path), fetch=lambda lid, r: "hasan") == "Hasan"


def test_library_id_comes_from_the_set_file(tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "set-7536.json").write_text(json.dumps({"library_id": "bc0728b6"}), encoding="utf-8")
    seen = []
    assert g.set_grade({"number": "7536"}, str(tmp_path), fetch=lambda lid, r: seen.append(lid) or "Sahih") == "Sahih"
    assert seen == ["bc0728b6"]


def test_config_grade_overrides_without_a_fetch(tmp_path):
    def boom(*a):
        raise AssertionError("fetched")
    assert g.set_grade({"number": "1", "grade": "HASAN"}, str(tmp_path), fetch=boom) == "Hasan"


@pytest.mark.parametrize("raw", ["daif", "", None, "mawdu"])
def test_anything_but_sahih_or_hasan_stops(tmp_path, raw):
    with pytest.raises(SystemExit):
        g.set_grade({"number": "1", "library_id": "x"}, str(tmp_path), fetch=lambda lid, r: raw)


def test_no_library_id_stops(tmp_path):
    with pytest.raises(SystemExit):
        g.set_grade({"number": "9999"}, str(tmp_path), fetch=lambda lid, r: "sahih")