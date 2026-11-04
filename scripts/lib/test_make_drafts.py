"""scripts/make-drafts.py - quoting and the draft shape, offline."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("make_drafts", os.path.join(os.path.dirname(HERE), "make-drafts.py"))
md = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(md)

RU_MATN = u"Клянусь Тем, и Он прощал бы им."
BLOCK = {"title": "T", "moral": "M.", "h": "H."}


def test_en_matn_in_straight_quotes():
    assert md.quote_matn("By Him ... forgive them.", "en") == '"By Him ... forgive them."'


def test_ru_matn_in_guillemets_with_the_period_outside():
    assert md.quote_matn(RU_MATN, "ru") == u"«" + RU_MATN[:-1] + u"»."


def test_inner_quotes_are_dropped_words_kept():
    # #2747: the man's words were quoted inside the matn (P342)
    assert md.quote_matn(u'he said: «O Allah» in joy.', "uz") == u"«he said: O Allah in joy»."


def test_draft_has_the_four_blocks_in_order():
    lines = md.build_draft("Abu Hurairah (may Allah be pleased with him) narrated that the Prophet ﷺ said:",
                           "If you did not sin.", BLOCK, "en")
    assert [l[:2] for l in lines] == ["S:", "M:", "H:", "C:"]
    assert lines[0].endswith('said: "If you did not sin."')


def test_empty_block_is_refused():
    try:
        md.build_draft("x", "y.", dict(BLOCK, h=" "), "tj")
    except ValueError as e:
        assert '"h"' in str(e)
    else:
        raise AssertionError("an empty H block was accepted")


def test_caption_blocks_carry_title_and_moral_only():
    s = {"number": "2749", "library_id": "a7", "langs": {"en": BLOCK}}
    assert md.caption_blocks(s) == {"hadith_number": "2749", "id": "a7", "style": "adults",
                                    "langs": {"en": {"title": "T", "moral": "M."}}}
