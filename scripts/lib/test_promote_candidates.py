# scripts/lib/test_promote_candidates.py
# Run:  python scripts/lib/test_promote_candidates.py
#
# P323: candidates carry dedup's slug, the library carries the display name.
# Nothing mapped between them, so a promoted Workflow L row would have been
# named unlike every other row AND unverifiable by the P319 matn gate, whose
# TOHED map is keyed by the display name.
import os, sys, importlib.util

_lib = os.path.dirname(__file__)
_scripts = os.path.dirname(_lib)
sys.path.insert(0, _lib)
sys.path.insert(0, _scripts)
_spec = importlib.util.spec_from_file_location(
    "promote_candidates", os.path.join(_scripts, "promote-candidates.py"))
pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pc)


def test_slug_becomes_display_name():
    assert pc.library_collection("tirmidhi") == "Jami at-Tirmidhi"
    assert pc.library_collection("bukhari") == "Sahih al-Bukhari"
    assert pc.library_collection("ahmad") == "Musnad Ahmad"

def test_display_name_passes_through_unchanged():
    """Idempotent - a row already carrying the display name must not be mangled."""
    assert pc.library_collection("Sunan Ibn Majah") == "Sunan Ibn Majah"

def test_unknown_slug_is_refused():
    """malik and darimi have no library precedent and no TOHED mapping."""
    for bad in ("malik", "darimi", "majmu-al-fatawa", ""):
        try:
            pc.library_collection(bad)
        except ValueError:
            continue
        raise AssertionError("library_collection(%r) should have raised" % bad)

def test_every_mapped_name_is_a_tohed_key():
    """The two maps must not drift. A display name the library uses that the
    gate does not recognise is a row that promotes and then cannot render."""
    spec = importlib.util.spec_from_file_location(
        "vmn", os.path.join(_scripts, "verify-matn-number.py"))
    vmn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vmn)
    missing = [v for v in pc.LIBRARY_COLLECTION.values() if v not in vmn.TOHED]
    assert not missing, "display names absent from TOHED: %s" % missing

def test_pick_deeplink_prefers_sunnah_over_a_dorar_search():
    """P322: the reason the sunnah key is now written at all."""
    got = pc.pick_deeplink({"dorar": "https://dorar.net/hadith/search?q=x",
                            "sunnah": "https://sunnah.com/tirmidhi:1161"})
    assert got == "https://sunnah.com/tirmidhi:1161"


def test_promotion_is_one_rpc_call_with_the_audit_fields():
    """P410 (Sol R10): library row, audit row and candidate stamp in ONE transaction."""
    calls = []
    def fake_rpc(url, key, fn, args):
        calls.append((fn, args)); return "lib-42"
    row = {"text_arabic": "نص", "text_english": "e", "tags": [], "source_url": "https://sunnah.com/muslim:1",
           "book": None, "collection": "Sahih Muslim", "hadith_number": "1"}
    got = pc.promote_one("u", "k", "c-1", row, "farhod", rpc=fake_rpc)
    assert got == "lib-42"
    assert len(calls) == 1 and calls[0][0] == "promote_candidate"
    a = calls[0][1]
    assert a["p_candidate_id"] == "c-1" and a["p_reviewer"] == "farhod"
    assert a["p_deeplink"] == "https://sunnah.com/muslim:1"
    assert "tags" not in a["p_columns"] and "book" not in a["p_columns"]
    assert "text_arabic" in a["p_columns"]

def test_main_no_longer_writes_the_three_tables_separately():
    src = open(os.path.join(_scripts, "promote-candidates.py"), encoding="utf-8").read()
    body = src.split("def main():", 1)[1]
    assert 'rest_insert(url, key, "hadith_library"' not in body
    assert 'rest_insert(url, key, "hadith_promotions"' not in body
    assert "promote_one(" in body


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
