# scripts/lib/test_dedup.py
# Run with pytest:   pytest scripts/lib/test_dedup.py -v
# Or standalone:     python scripts/lib/test_dedup.py   (no pytest needed)
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dedup import (
    normalize_arabic, similarity, normalize_collection,
    normalize_number, hard_key, find_duplicates,
)

# ---- Arabic normalization: diacritics don't matter ----
def test_diacritics_stripped():
    assert normalize_arabic("قَالَ رَسُولُ اللَّهِ") == normalize_arabic("قال رسول الله")

def test_hamza_and_alef_variants():
    # إنّما الأعمال  ==  انما الاعمال  after normalization
    assert normalize_arabic("إنّما الأعمال") == normalize_arabic("انما الاعمال")

def test_tatweel_and_tamarbuta():
    assert normalize_arabic("صـدقـة") == normalize_arabic("صدقة")  # tatweel removed
    assert normalize_arabic("صدقة") == normalize_arabic("صدقه")    # ta marbuta -> ha

# ---- Similarity: advisory metric behaves sanely ----
def test_similarity_same_text_diacritics_differ():
    a = "إنّما الأعمالُ بالنيّاتِ"
    b = "إنما الأعمال بالنيات"
    assert similarity(a, b) > 0.95

def test_similarity_different_hadiths_low():
    a = "إنما الأعمال بالنيات"
    b = "الطهور شطر الإيمان"
    assert similarity(a, b) < 0.6

# ---- Collection normalization: curated aliases ----
def test_collection_aliases_latin():
    assert normalize_collection("Sahih al-Bukhari") == "bukhari"
    assert normalize_collection("Bukhari") == "bukhari"
    assert normalize_collection("Jami` at-Tirmidhi") == "tirmidhi"

def test_collection_aliases_arabic():
    assert normalize_collection("صحيح البخاري") == "bukhari"
    assert normalize_collection("صحيح مسلم") == "muslim"

def test_collection_unknown_gets_stable_slug():
    # unknown collection must not crash; returns a stable, comparable slug
    k = normalize_collection("Some New Collection")
    assert k and k == normalize_collection("some new collection")

# ---- Number normalization ----
def test_number_normalization():
    assert normalize_number("#1956") == "1956"
    assert normalize_number("01956") == "1956"
    assert normalize_number("1956a") == "1956a"
    assert normalize_number("١٩٥٦") == "1956"   # arabic-indic digits

# ---- Hard key ----
def test_hard_key_match_across_spelling():
    assert hard_key("Sahih al-Bukhari", "#1956") == hard_key("Bukhari", "1956")

# ---- find_duplicates ----
LIB = [
    {"id": "a", "collection": "Sahih al-Bukhari", "hadith_number": "1",
     "text_arabic": "إنما الأعمال بالنيات"},
    {"id": "b", "collection": "Sahih Muslim", "hadith_number": "223",
     "text_arabic": "الطهور شطر الإيمان"},
]

def test_find_dup_hard_hit():
    cand = {"id": "x", "collection": "Bukhari", "hadith_number": "#1",
            "text_arabic": "إنّما الأعمالُ بالنيّاتِ"}
    res = find_duplicates(cand, LIB)
    assert res["hard_hit"] is True
    assert res["hard_match_id"] == "a"

def test_find_dup_fuzzy_is_advisory_list():
    # same text, DIFFERENT citation -> no hard hit, but fuzzy should surface it
    cand = {"id": "x", "collection": "Bukhari", "hadith_number": "9999",
            "text_arabic": "إنما الأعمال بالنيات"}
    res = find_duplicates(cand, LIB)
    assert res["hard_hit"] is False              # never auto-decided
    assert isinstance(res["fuzzy_hits"], list)
    assert any(h["id"] == "a" for h in res["fuzzy_hits"])

def test_find_dup_clean_new_hadith():
    cand = {"id": "x", "collection": "Abu Dawud", "hadith_number": "5",
            "text_arabic": "من حسن إسلام المرء تركه ما لا يعنيه"}
    res = find_duplicates(cand, LIB)
    assert res["hard_hit"] is False
    assert res["fuzzy_hits"] == []


# ---- standalone runner (no pytest required) ----
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
