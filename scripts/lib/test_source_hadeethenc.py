# scripts/lib/test_source_hadeethenc.py
# Run:  python scripts/lib/test_source_hadeethenc.py   (no pytest needed)
#  or:  pytest scripts/lib/test_source_hadeethenc.py -v
#
# Offline only. Every fixture is shaped from a REAL response captured on
# 2026-09-10 (ids 66511 and 1751) -- no network in this file, so the pre-push
# hook stays fast.
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from source_hadeethenc import (parse_hadeeth, classify_grade, build_source_url,
                               present)

# ---- Fixtures shaped like the HadeethEnc /hadeeths/one/ payload ----

# Fetched with language=ar: there is NO hadeeth_ar key, the Arabic is in
# `hadeeth`, and the isnad opener is in `hadeeth_intro`. This asymmetry cost a
# debugging round on 2026-09-10 -- it is the reason this fixture exists.
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

HTML_PAYLOAD = dict(RU_PAYLOAD, id="9004",
                    hadeeth="<p>Поистине,&nbsp;все дела</p>\r\n  оцениваются")


def test_arabic_language_payload_parses():
    """language=ar has no hadeeth_ar key; the Arabic must be taken from
    `hadeeth` instead. Regression test for the 'no Arabic matn' drop."""
    r = parse_hadeeth(AR_PAYLOAD)
    assert r["status"] == "candidate", r["reason"]
    c = r["candidate"]
    assert c["text_arabic"].startswith("عَنْ عُمَرَ")
    assert c["narrator"].startswith("عَنْ عُمَرَ")      # from hadeeth_intro
    assert c["grade"] == "sahih"


def test_translations_collected():
    r = parse_hadeeth(RU_PAYLOAD, {"uz": UZ_PAYLOAD, "tg": TG_PAYLOAD})
    c = r["candidate"]
    assert r["status"] == "candidate"
    assert c["text_russian"].startswith("Поистине")      # own language
    assert c["text_uzbek_cyrillic"].startswith("Амаллар")
    assert c["text_tajik"].startswith("Савоби")
    assert c["translation_source"] == "hadeethenc.com"


def test_empty_string_is_absent_not_content():
    """The trap this adapter exists to avoid: a missing language returns 200
    with '', so a parser that trusts the response writes blank fields."""
    assert present("") is False
    assert present("   ") is False
    assert present(None) is False
    assert present("текст") is True
    r = parse_hadeeth(RU_PAYLOAD, {"uz": EMPTY_PAYLOAD})
    assert r["candidate"]["text_uzbek_cyrillic"] == ""
    assert "uz" not in [k for k, v in r["candidate"].items() if v == "Амаллар"]


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
    number before promotion -- a candidate from here is never citable alone."""
    c = parse_hadeeth(RU_PAYLOAD, {})["candidate"]
    assert c["citation_pending"] is True
    assert c["collection"] == "" and c["hadith_number"] == ""
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
    c = parse_hadeeth(HTML_PAYLOAD)["candidate"]
    assert "<p>" not in c["text_russian"]
    assert "\r" not in c["text_russian"] and "\n" not in c["text_russian"]
    assert "&nbsp;" not in c["text_russian"]
    assert c["text_russian"] == "Поистине, все дела оцениваются"


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
    assert c["text_tajik"] == ""               # but not fetched


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    passed = failed = 0
    for n, f in fns:
        try:
            f(); passed += 1; print(f"PASS {n}")
        except AssertionError as e:
            failed += 1; print(f"FAIL {n}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
