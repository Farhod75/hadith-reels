# scripts/lib/test_upload_candidates.py
# Run:  python scripts/lib/test_upload_candidates.py
import os, sys, importlib.util

_lib = os.path.dirname(__file__)
_scripts = os.path.dirname(_lib)
sys.path.insert(0, _lib)
sys.path.insert(0, _scripts)
_spec = importlib.util.spec_from_file_location(
    "upload_candidates", os.path.join(_scripts, "upload-candidates.py"))
uc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(uc)

CAND = {
    "collection": "bukhari", "hadith_number": "1", "narrator": "عمر",
    "grade": "sahih", "grading_source": "dorar.net (authority; البخاري)",
    "grade_confirmed": True, "source_urls": {"dorar": "https://dorar.net/..."},
    "text_arabic": "إنما الأعمال بالنيات",
}


def test_syn_number_keeps_real():
    assert uc.syn_number("1956", "x") == "1956"

def test_syn_number_derives_when_missing():
    n = uc.syn_number("", "إنما الأعمال بالنيات")
    assert n.startswith("auto-") and len(n) > 6

def test_to_row_new_is_deduped():
    dd = {"hard_hit": False, "fuzzy_hits": []}
    row = uc.to_row(CAND, dd)
    assert row["status"] == "deduped"
    assert row["grade"] == "sahih" and row["grade_confirmed"] is True
    assert row["collection"] == "bukhari"

def test_to_row_fuzzy_needs_human():
    dd = {"hard_hit": False, "fuzzy_hits": [{"id": "a", "score": 0.9}]}
    row = uc.to_row(CAND, dd)
    assert row["status"] == "needs_human"
    assert row["dedup_fuzzy_hits"]


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    passed = failed = 0
    for n, f in fns:
        try:
            f(); passed += 1; print(f"✔ {n}")
        except AssertionError as e:
            failed += 1; print(f"✘ {n}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
