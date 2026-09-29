# scripts/lib/test_source_hadeethenc.py
# Run:  python scripts/lib/test_source_hadeethenc.py   (no pytest needed)
#  or:  pytest scripts/lib/test_source_hadeethenc.py -v
#
# Offline only. Every fixture is shaped from a REAL response captured on
# 2026-09-10 (ids 66511 and 1751) -- no network in this file, so the pre-push
# hook stays fast.
#
# Contract as of 2026-09-29 (P178 + P179): HadeethEnc supplies DISCOVERY, the
# ARABIC MATN and the CITATION deep link, and nothing else. Their translations
# are not carried, narrator is not derived, and an isnad intro that cannot be
# cut cleanly flags the row instead of being guessed at.
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from source_hadeethenc import (parse_hadeeth, classify_grade, build_source_url,
                               present, _clean_body)

# ---- Fixtures shaped like the HadeethEnc /hadeeths/one/ payload ----

# Fetched with language=ar: there is NO hadeeth_ar key, the Arabic is in
# `hadeeth`, and the isnad opener is in `hadeeth_intro`. This asymmetry cost a
# debugging round on 2026-09-10 -- it is the reason this fixture exists.
#
# Note also that hadeeth_intro is NOT a byte prefix of hadeeth here: the intro
# carries the honorific and the body does not. That is load-bearing for P179.
AR_PAYLOAD = {
    "id": "66511",
    "_language": "ar",
    "hadeeth": "عَنْ عُمَرَ بْنِ الخَطَّابِ قَالَ: إنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
    "hadeeth_intro": "عَنْ عُمَرَ بْنِ الخَطَّابِ رضي الله عنه قَالَ:",
    "grade": "صحيح",
    "attribution": "رواه البخاري ومسلم",
    "reference": "صحيح البخاري (9/ 22) (6953)، (1/ 6) (1).\nصحيح مسلم (3/ 1515) (1907).",
    "translations": ["ar", "en", "ru", "uz", "tg"],
}

# Fetched with a non-Arabic language: hadeeth_ar and grade_ar ARE present.
RU_PAYLOAD = {
    "id": "66511",
    "_language": "ru",
    "hadeeth": "Поистине, все дела оцениваются только по намерениям",
    "hadeeth_ar": "إنَّمَا الأَعْمَالُ بِالنِّيَّاتِ",
    "hadeeth_intro_ar": "عَنْ عُمَرَ بْنِ الخَطَّابِ رضي الله عنه قَالَ:",
    "grade": "Достоверный хадис",
    "grade_ar": "صحيح",
    "attribution_ar": "متفق عليه",
    "translations": ["ar", "en", "ru", "uz", "tg"],
}

UZ_PAYLOAD = {"id": "66511", "_language": "uz",
              "hadeeth": "Амаллар фақатгина ниятлар билан",
              "hadeeth_ar": "إنَّمَا الأَعْمَالُ بِالنِّيَّاتِ", "grade_ar": "صحيح"}

TG_PAYLOAD = {"id": "66511", "_language": "tg",
              "hadeeth": "Савоби амалҳо вобаста бо ният аст",
              "hadeeth_ar": "إنَّمَا الأَعْمَالُ بِالنِّيَّاتِ", "grade_ar": "صحيح"}

# A language this hadeeth does not have. The API returns 200 with EMPTY
# STRINGS, not a 404 and not null -- verified on id 1751, which has no uz/tg.
EMPTY_PAYLOAD = {"id": "1751", "_language": "uz", "hadeeth": "",
                 "hadeeth_ar": "", "grade_ar": ""}

DAIF_PAYLOAD = dict(RU_PAYLOAD, id="9001", grade_ar="ضعيف", grade="Слабый хадис")
UNGRADED_PAYLOAD = dict(RU_PAYLOAD, id="9002", grade_ar="", grade="")
NO_ARABIC_PAYLOAD = {"id": "9003", "_language": "ru", "hadeeth": "текст",
                     "hadeeth_ar": "", "grade_ar": "صحيح"}
NO_ID_PAYLOAD = dict(RU_PAYLOAD, id="")

# Built from parts rather than typed out, so the fixture cannot drift from the
# assertion by one diacritic. The strippable case depends on byte equality.
INTRO_EXACT = "عَنْ عُمَرَ قَالَ:"
MATN = "إنَّمَا الأَعْمَالُ بِالنِّيَّاتِ"


def test_arabic_language_payload_parses():
    """language=ar has no hadeeth_ar key; the Arabic must be taken from
    `hadeeth` instead. Regression test for the 'no Arabic matn' drop."""
    r = parse_hadeeth(AR_PAYLOAD)
    assert r["status"] == "candidate", r["reason"]
    c = r["candidate"]
    assert c["text_arabic"].startswith("عَنْ عُمَرَ")
    assert c["narrator"] is None          # P179: no narrator NAME in the payload
    assert c["grade"] == "sahih"


def test_intro_not_a_byte_prefix_is_flagged_not_guessed():
    """P179. Real capture: hadeeth_intro carries «رضي الله عنه» and the body
    does not, so the intro is not a byte prefix of the matn. The adapter must
    refuse to guess the boundary -- it leaves text_arabic alone and flags the
    row, and upload-candidates.py rejects it on that flag."""
    c = parse_hadeeth(AR_PAYLOAD)["candidate"]
    assert c["matn_intro_stripped"] is False
    assert c["matn_intro_raw"].startswith("عَنْ عُمَرَ")
    assert c["text_arabic"].startswith("عَنْ عُمَرَ")     # still there, on purpose


def test_intro_that_is_an_exact_prefix_is_stripped():
    """The 2026-09-27 batch shape: the intro repeated verbatim at the head of
    the matn. That one is safe to cut, and must be -- those five rows ran
    300-450 characters against a library average under 130."""
    c = parse_hadeeth(dict(RU_PAYLOAD, id="66512",
                           hadeeth_intro_ar=INTRO_EXACT,
                           hadeeth_ar=f"{INTRO_EXACT} {MATN}"))["candidate"]
    assert c["matn_intro_stripped"] is True
    assert c["text_arabic"] == MATN


def test_no_intro_field_leaves_the_flag_unset():
    """Three states, not two: None means there was no intro to act on, so the
    gate has nothing to hold the row for."""
    c = parse_hadeeth(dict(RU_PAYLOAD, id="66513",
                           hadeeth_intro_ar=""))["candidate"]
    assert c["matn_intro_stripped"] is None
    assert c["matn_intro_raw"] is None


def test_their_translations_are_not_carried():
    """P178: measured EN 3/5, RU 0/5, UZ 0/5, TJ 1/5 clean against 8/8
    in-house. The defects are interpretive expansion; the worst added
    «бегуноҳ» (innocent) to قتل النفس on #6871 in both UZ and TJ, which changes
    the ruling. `translations` is still accepted -- it remains the Arabic
    fallback -- but nothing from it reaches a text column, and
    translation_source stays NULL so a row holding our own text never credits
    them."""
    r = parse_hadeeth(RU_PAYLOAD, {"uz": UZ_PAYLOAD, "tg": TG_PAYLOAD})
    c = r["candidate"]
    assert r["status"] == "candidate"
    assert c["text_english"] == ""
    assert c["text_russian"] == ""
    assert c["text_uzbek_cyrillic"] == ""
    assert c["text_tajik"] == ""
    assert c["translation_source"] is None
    assert c["text_arabic"].startswith("إنَّمَا")          # the Arabic still lands


def test_empty_string_is_absent_not_content():
    """The trap this adapter exists to avoid: a missing language returns 200
    with '', so a parser that trusts the response writes blank fields. Still
    load-bearing for the Arabic even though every text column is empty by
    design now -- EMPTY_PAYLOAD must not satisfy the matn requirement."""
    assert present("") is False
    assert present("   ") is False
    assert present(None) is False
    assert present("текст") is True
    r = parse_hadeeth(EMPTY_PAYLOAD)
    assert r["status"] == "dropped"
    assert "no Arabic" in r["reason"]


def test_daif_is_dropped():
    r = parse_hadeeth(DAIF_PAYLOAD)
    assert r["status"] == "dropped"
    assert "grade=daif" in r["reason"]
    assert r["candidate"] is None


def test_ungraded_dropped():
    r = parse_hadeeth(UNGRADED_PAYLOAD)
    assert r["status"] == "dropped"
    assert "unknown" in r["reason"]


def test_no_arabic_dropped():
    r = parse_hadeeth(NO_ARABIC_PAYLOAD)
    assert r["status"] == "dropped"
    assert "no Arabic" in r["reason"]


def test_no_id_dropped():
    r = parse_hadeeth(NO_ID_PAYLOAD)
    assert r["status"] == "dropped"
    assert "id" in r["reason"]


def test_arabic_recovered_from_translation_payload():
    """If the primary payload lacks Arabic but a translation carries
    hadeeth_ar, use it rather than dropping a good hadeeth."""
    r = parse_hadeeth(NO_ARABIC_PAYLOAD, {"ru": RU_PAYLOAD})
    assert r["status"] == "candidate"
    assert r["candidate"]["text_arabic"].startswith("إنَّمَا")


def test_citation_always_pending():
    """HadeethEnc gives no hadith number. Dorar must supply collection and
    number before promotion -- a candidate from here is never citable alone.
    Since P179 the narrator joins that list: there is no name in the payload."""
    c = parse_hadeeth(RU_PAYLOAD, {})["candidate"]
    assert c["citation_pending"] is True
    assert c["collection"] == "" and c["hadith_number"] == ""
    assert c["narrator"] is None
    assert c["attribution_raw"] == "متفق عليه"


def test_reference_kept_raw_not_parsed():
    """reference is free-text with volume/page pairs and commentary works, and
    can list two numbers for one collection. Kept as a cross-check only."""
    c = parse_hadeeth(AR_PAYLOAD)["candidate"]
    assert "6953" in c["reference_raw"] and "1907" in c["reference_raw"]
    assert c["hadith_number"] == ""      # never inferred from it
    assert "\n" not in c["reference_raw"]   # whitespace collapsed


def test_grade_read_from_arabic_not_localized():
    """grade_ar is language-independent; the localized string is not."""
    assert classify_grade("صحيح", "Достоверный хадис")[0] == "sahih"
    assert classify_grade("حسن", "")[0] == "hasan"
    assert classify_grade("ضعيف", "")[0] == "daif"
    assert classify_grade("", "")[0] == "unknown"
    assert classify_grade("صحيح", "")[1] is False    # no conflict concept here


def test_html_and_whitespace_cleaned():
    """Tested directly now. It used to be observed through text_russian, which
    is empty by design since P178 -- the only cleaned text field left on the
    row is text_arabic."""
    assert _clean_body("<p>Поистине,&nbsp;все дела</p>\r\n  оцениваются") == \
        "Поистине, все дела оцениваются"
    c = parse_hadeeth(dict(RU_PAYLOAD, id="9004", hadeeth_intro_ar="",
                           hadeeth_ar="<p>" + MATN + "</p>\r\n  &nbsp;"))["candidate"]
    assert "<p>" not in c["text_arabic"]
    assert "\r" not in c["text_arabic"] and "\n" not in c["text_arabic"]
    assert "&nbsp;" not in c["text_arabic"]
    assert c["text_arabic"].startswith("إنَّمَا")


def test_deeplink_not_homepage():
    assert build_source_url("66511") == "https://hadeethenc.com/ar/browse/hadith/66511"
    assert build_source_url("66511", "ru") == "https://hadeethenc.com/ru/browse/hadith/66511"
    c = parse_hadeeth(RU_PAYLOAD)["candidate"]
    assert c["source_urls"]["hadeethenc"].endswith("/browse/hadith/66511")


def test_available_langs_is_what_exists_not_what_was_fetched():
    """59 languages may be listed while only four were pulled. This field
    records availability, never coverage."""
    c = parse_hadeeth(RU_PAYLOAD, {"uz": UZ_PAYLOAD})["candidate"]
    assert "tg" in c["available_langs"]        # listed
    assert c["text_tajik"] == ""               # and never carried (P178)


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    passed = failed = 0
    for n, f in fns:
        try:
            f(); passed += 1; print(f"PASS {n}")
        except AssertionError as e:
            failed += 1; print(f"FAIL {n}: {e}")
        except Exception as e:      # an AttributeError is a failed test, not a
            failed += 1             # reason to abandon the remaining ones
            print(f"ERROR {n}: {type(e).__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
