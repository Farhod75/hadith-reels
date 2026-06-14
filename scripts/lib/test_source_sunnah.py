# scripts/lib/test_source_sunnah.py
# Run:  python scripts/lib/test_source_sunnah.py   (no pytest needed)
#  or:  pytest scripts/lib/test_source_sunnah.py -v
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from source_sunnah import parse_sunnah_hadith, classify_grade, build_source_url

# ---- Fixtures shaped like the Sunnah.com API hadith object ----
SAHIH = {
    "collection": "bukhari",
    "hadithNumber": "1",
    "hadith": [
        {"lang": "ar", "body": "<p>إنما الأعمال بالنيات</p>",
         "grades": [{"graded_by": "", "grade": "Sahih"}]},
        {"lang": "en", "body": "Actions are but by intention",
         "grades": [{"graded_by": "", "grade": "Sahih"}]},
    ],
}

DAIF = {
    "collection": "tirmidhi",
    "hadithNumber": "999",
    "hadith": [
        {"lang": "ar", "body": "نص ضعيف", "grades": [{"grade": "Da'if"}]},
    ],
}

HASAN_SAHIH = {  # Tirmidhi-style combined grade
    "collection": "tirmidhi",
    "hadithNumber": "2",
    "hadith": [{"lang": "ar", "body": "نص", "grades": [{"grade": "Hasan Sahih"}]}],
}

CONFLICT = {  # one grader sahih, one daif
    "collection": "abudawud",
    "hadithNumber": "3",
    "hadith": [{"lang": "ar", "body": "نص",
                "grades": [{"grade": "Sahih"}, {"grade": "Da'if"}]}],
}

NO_ARABIC = {"collection": "bukhari", "hadithNumber": "4",
             "hadith": [{"lang": "en", "body": "english only", "grades": [{"grade": "Sahih"}]}]}

UNGRADED = {"collection": "bukhari", "hadithNumber": "5",
            "hadith": [{"lang": "ar", "body": "نص", "grades": []}]}


def test_sahih_becomes_candidate():
    r = parse_sunnah_hadith(SAHIH)
    assert r["status"] == "candidate"
    c = r["candidate"]
    assert c["grade"] == "sahih"
    assert c["collection"] == "bukhari" and c["hadith_number"] == "1"
    assert c["text_arabic"] == "إنما الأعمال بالنيات"   # tags stripped
    assert c["text_english"].startswith("Actions are")
    assert c["source_urls"]["sunnah"] == "https://sunnah.com/bukhari:1"

def test_daif_is_dropped():
    r = parse_sunnah_hadith(DAIF)
    assert r["status"] == "dropped"
    assert "grade=daif" in r["reason"]
    assert r["candidate"] is None

def test_hasan_sahih_classified_sahih():
    assert classify_grade([{"grade": "Hasan Sahih"}])[0] == "sahih"
    r = parse_sunnah_hadith(HASAN_SAHIH)
    assert r["status"] == "candidate" and r["candidate"]["grade"] == "sahih"

def test_conflict_kept_but_flagged():
    r = parse_sunnah_hadith(CONFLICT)
    assert r["status"] == "candidate"           # has a sahih grade → not dropped
    assert r["candidate"]["grade_conflict"] is True

def test_no_arabic_dropped():
    r = parse_sunnah_hadith(NO_ARABIC)
    assert r["status"] == "dropped"
    assert "no Arabic" in r["reason"]

def test_ungraded_dropped():
    r = parse_sunnah_hadith(UNGRADED)
    assert r["status"] == "dropped"
    assert "unknown" in r["reason"]

def test_deeplink_not_homepage():
    assert build_source_url("muslim", "223") == "https://sunnah.com/muslim:223"


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
