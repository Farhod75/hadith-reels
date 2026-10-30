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
