"""narrator_ar - Dorar's Arabic narrator names to lib/refs.ts NARRATORS keys (P344)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import narrator_ar as na  # noqa: E402


def test_dorar_forms_seen_in_this_repo_map():
    assert na.to_english(u"أبو هريرة") == "Abu Hurairah"                 # Muslim #2749 candidate
    assert na.to_english(u"عبادة بن الصامت") == u"عبادة بن الصامت"        # #3435: not in NARRATORS - unchanged
    assert na.to_english(u"أَنَسُ بْنُ مَالِكٍ") == "Anas ibn Malik"     # with harakat


def test_spelling_variants_normalise():
    assert na.to_english(u"ابو هريرة رضي الله عنه") == "Abu Hurairah"
    assert na.to_english(u"عبدالله بن مسعود") == "Abdullah ibn Masud"
    assert na.to_english(u"أبو موسى الأشعري") == na.to_english(u"ابو موسي الاشعري") == "Abu Musa al-Ashari"


def test_ibn_umar_and_ibn_amr_stay_apart():
    assert na.to_english(u"عبد الله بن عمر") == "Ibn Umar"
    assert na.to_english(u"عبد الله بن عمرو") == "Abdullah ibn Amr"


def test_ambiguous_or_english_names_pass_through():
    assert na.to_english(u"عمر") == u"عمر"
    assert na.to_english("Abu Hurairah") == "Abu Hurairah"
    assert na.to_english(None) is None


def test_every_value_is_a_narrators_key():
    try:
        import narrator_leadin as nl
        keys = set(nl.load_narrators())
    except FileNotFoundError:                     # lib/refs.ts absent outside the repo
        return
    assert set(na.TABLE.values()) <= keys
