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


def test_sunnah_link_added_for_a_real_number():
    """P322: Dorar only ever gives a search URL, so to_row must add the page."""
    dd = {"hard_hit": False, "fuzzy_hits": []}
    row = uc.to_row(CAND, dd)
    assert row["source_urls"]["sunnah"] == "https://sunnah.com/bukhari:1"
    assert row["source_urls"]["dorar"] == "https://dorar.net/..."

def test_no_sunnah_link_for_a_synthetic_number():
    """An auto- number has no page; inventing a URL for it would be a lie."""
    cand = dict(CAND); cand["hadith_number"] = ""
    row = uc.to_row(cand, {"hard_hit": False, "fuzzy_hits": []})
    assert row["hadith_number"].startswith("auto-")
    assert "sunnah" not in row["source_urls"]

def test_existing_sunnah_link_is_not_overwritten():
    """A candidate sourced from sunnah.com already has the real link."""
    cand = dict(CAND)
    cand["source_urls"] = {"sunnah": "https://sunnah.com/bukhari:6502"}
    row = uc.to_row(cand, {"hard_hit": False, "fuzzy_hits": []})
    assert row["source_urls"]["sunnah"] == "https://sunnah.com/bukhari:6502"

def test_with_sunnah_link_does_not_mutate_its_input():
    """to_row is documented PURE - the helper must not reach back into cand."""
    src = {"dorar": "https://dorar.net/x"}
    out = uc.with_sunnah_link(src, "muslim", "223")
    assert out["sunnah"] == "https://sunnah.com/muslim:223"
    assert "sunnah" not in src


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
