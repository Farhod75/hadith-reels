# scripts/lib/test_source_candidates.py
# Tests the runner's offline glue (parse_ref + dedup→queue_status).
# Run:  python scripts/lib/test_source_candidates.py   (no pytest needed)
import os, sys, importlib.util

_lib = os.path.dirname(__file__)
_scripts = os.path.dirname(_lib)
sys.path.insert(0, _lib)
sys.path.insert(0, _scripts)

# import the runner module by path (filename has a hyphen)
_path = os.path.join(_scripts, "source-candidates.py")
_spec = importlib.util.spec_from_file_location("source_candidates", _path)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)

LIB = [
    {"id": "a", "collection": "Sahih al-Bukhari", "hadith_number": "1",
     "text_arabic": "إنما الأعمال بالنيات"},
    {"id": "b", "collection": "Sahih Muslim", "hadith_number": "223",
     "text_arabic": "الطهور شطر الإيمان"},
]


def test_parse_ref():
    assert sc.parse_ref("bukhari:1") == ("bukhari", "1")
    assert sc.parse_ref("Muslim:223") == ("muslim", "223")

def test_parse_ref_bad():
    try:
        sc.parse_ref("bukhari1")
        assert False, "should have raised"
    except ValueError:
        pass

def test_queue_status_duplicate():
    cand = {"collection": "Bukhari", "hadith_number": "1",
            "text_arabic": "إنّما الأعمالُ بالنيّاتِ"}
    out = sc.annotate_candidate(cand, LIB)
    assert out["queue_status"] == "duplicate"
    assert out["dedup"]["hard_hit"] is True

def test_queue_status_fuzzy():
    cand = {"collection": "Bukhari", "hadith_number": "9999",  # same text, new citation
            "text_arabic": "إنما الأعمال بالنيات"}
    out = sc.annotate_candidate(cand, LIB)
    assert out["queue_status"] == "review_fuzzy"
    assert out["dedup"]["hard_hit"] is False

def test_queue_status_new():
    cand = {"collection": "Abu Dawud", "hadith_number": "5",
            "text_arabic": "من حسن إسلام المرء تركه ما لا يعنيه"}
    out = sc.annotate_candidate(cand, LIB)
    assert out["queue_status"] == "new"


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
