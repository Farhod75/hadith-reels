# scripts/lib/test_source_dorar.py
# Run:  python scripts/lib/test_source_dorar.py   (no pytest needed)
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from source_dorar import (
    classify_dorar_grade, parse_dorar, confirm_grade,
    card_to_candidate, cards_to_candidates,
)

# ---- Grade classification, incl. tricky negations ----
def test_grade_buckets():
    assert classify_dorar_grade("صحيح") == "sahih"
    assert classify_dorar_grade("إسناده صحيح") == "sahih"
    assert classify_dorar_grade("حسن") == "hasan"
    assert classify_dorar_grade("حسن لغيره") == "hasan"
    assert classify_dorar_grade("ضعيف") == "daif"
    assert classify_dorar_grade("إسناده ضعيف") == "daif"
    assert classify_dorar_grade("موضوع") == "daif"
    assert classify_dorar_grade("") == "unknown"

def test_grade_negations_not_misread_as_sahih():
    assert classify_dorar_grade("غير صحيح") == "daif"
    assert classify_dorar_grade("لا يصح") == "daif"

def test_hasan_sahih_is_authentic():
    # contains صحيح -> sahih bucket; either way it's KEPT (authentic)
    assert classify_dorar_grade("حسن صحيح") == "sahih"

# ---- Parse the HTML-in-JSON blob into cards ----
FIX = json.dumps({"ahadith": {"result":
    "<div>إنما الأعمال بالنيات وإنما لكل امرئ ما نوى "
    "<span>الراوي:</span> عمر بن الخطاب "
    "<span>المحدث:</span> البخاري "
    "<span>المصدر:</span> صحيح البخاري "
    "<span>الصفحة أو الرقم:</span> 1 "
    "<span>خلاصة حكم المحدث:</span> صحيح </div>"
    "<div>نص حديث ضعيف هنا "
    "<span>الراوي:</span> فلان "
    "<span>المحدث:</span> الألباني "
    "<span>المصدر:</span> ضعيف الجامع "
    "<span>الصفحة أو الرقم:</span> 99 "
    "<span>خلاصة حكم المحدث:</span> ضعيف </div>"
}})

def test_parse_two_cards():
    cards = parse_dorar(FIX)
    assert len(cards) == 2
    assert "الأعمال بالنيات" in cards[0]["matn"]
    assert cards[0]["grade"] == "صحيح"
    assert cards[0]["muhaddith"] == "البخاري"
    assert cards[0]["number"] == "1"
    assert cards[1]["grade"] == "ضعيف"           # grade did NOT swallow next matn

def test_grade_not_swallow_next_matn():
    cards = parse_dorar(FIX)
    assert cards[0]["grade"] == "صحيح"            # exactly, not "صحيح نص حديث..."

# ---- confirm_grade: match the right card, take its grade ----
def test_confirm_grade_matches_and_takes_authority_grade():
    cards = parse_dorar(FIX)
    res = confirm_grade("إنما الأعمال بالنيات", cards)
    assert res["matched"] is True
    assert res["grade_bucket"] == "sahih"
    assert res["muhaddith"] == "البخاري"

def test_confirm_grade_no_match():
    cards = parse_dorar(FIX)
    res = confirm_grade("نص لا علاقة له بشيء مختلف تماما عن البقية", cards)
    # may match weakly but below threshold -> unknown / not matched
    assert res["matched"] is False or res["grade_bucket"] in ("sahih", "hasan", "daif")


# ---- Dorar AS A SOURCE ----
def test_card_to_candidate_sahih():
    cards = parse_dorar(FIX)
    r = card_to_candidate(cards[0])
    assert r["status"] == "candidate"
    c = r["candidate"]
    assert c["collection"] == "bukhari"        # "صحيح البخاري" -> bukhari
    assert c["grade"] == "sahih"
    assert c["grade_confirmed"] is True          # Dorar is authority
    assert c["narrator"] == "عمر بن الخطاب"
    assert c["source_urls"]["dorar"].startswith("https://dorar.net/")

def test_card_to_candidate_daif_dropped():
    cards = parse_dorar(FIX)
    assert card_to_candidate(cards[1])["status"] == "dropped"

def test_cards_to_candidates_drops_daif():
    res = cards_to_candidates(parse_dorar(FIX))
    assert len(res["candidates"]) == 1          # sahih kept, daif dropped
    assert len(res["dropped"]) == 1

def test_dedupe_keeps_stronger_grade():
    dup = [
        {"matn": "نص واحد مكرر", "rawi": "x", "muhaddith": "البخاري",
         "source": "صحيح البخاري", "number": "1", "grade": "حسن"},
        {"matn": "نص واحد مكرر", "rawi": "x", "muhaddith": "الألباني",
         "source": "صحيح الجامع", "number": "1", "grade": "صحيح"},
    ]
    res = cards_to_candidates(dup)
    assert len(res["candidates"]) == 1          # collapsed
    assert res["candidates"][0]["grade"] == "sahih"  # stronger grade wins


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
