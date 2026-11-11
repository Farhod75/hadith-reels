"""P387 backfill: scripts/find-hadeethenc.py - offline."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('find_hadeethenc', os.path.join(HERE, '..', 'find-hadeethenc.py'))
fh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fh)

LIB = 'إِنَّ اللَّهَ لاَ يَنْظُرُ إِلَى صُوَرِكُمْ وَأَمْوَالِكُمْ وَلَكِنْ يَنْظُرُ إِلَى قُلُوبِكُمْ وَأَعْمَالِكُمْ'
SRC = 'عن أبي هريرة قال: قال رسول الله ﷺ: «إِنَّ اللهَ لَا يَنْظُرُ إِلَى صُوَرِكُمْ وَأَمْوَالِكُمْ، وَلَكِنْ يَنْظُرُ إِلَى قُلُوبِكُمْ وَأَعْمَالِكُمْ».'
OTHER = 'عن ابن عمر: «لاَ يَنْظُرُ اللَّهُ إِلَى مَنْ جَرَّ ثَوْبَهُ خُيَلاَءَ».'

TRACKER = """| # | Date | Hadith |
| R001 | 2026-06-01 | Sahih al-Bukhari #1894 | Abu Hurairah |
| R002 | 2026-06-01 | Sahih al-Bukhari #1894 | Abu Hurairah |
| R223 | 2026-11-09 | Sahih Muslim #2564 | Abu Hurairah |
| not a row | Sahih Muslim #1 |
"""


def test_published_hadiths_once_each_in_order():
    assert fh.published_hadiths(TRACKER) == [('Sahih al-Bukhari', '1894'), ('Sahih Muslim', '2564')]


def test_the_entry_containing_the_matn_is_the_match():
    assert fh.classify(LIB, [{'id': '5370', 'matn': OTHER}, {'id': '4555', 'matn': SRC}]) == ('match', '4555', '')


def test_nothing_containing_or_near_the_matn_is_none():
    assert fh.classify(LIB, [{'id': '5370', 'matn': OTHER}])[0] == 'none'


def test_a_one_word_variant_is_reported_not_matched():
    status, hid, note = fh.classify(LIB.replace('وَلَكِنْ ', ''), [{'id': '4555', 'matn': SRC}])
    assert (status, hid) == ('variant', '4555') and 'لكن' in note


def test_query_is_letters_only():
    assert fh.search_query(LIB, words=3) == 'ان الله لا'


def test_tail_query_is_the_end_of_the_matn():
    # P401: Bukhari #5971 opens like a dozen other hadiths; its end is its own
    q = fh.tail_query('جَاءَ رَجُلٌ إِلَى رَسُولِ اللَّهِ فَقَالَ مَنْ أَحَقُّ النَّاسِ بِحُسْنِ صَحَابَتِي قَالَ أُمُّكَ', words=4)
    assert q == 'بحسن صحابتي قال امك'