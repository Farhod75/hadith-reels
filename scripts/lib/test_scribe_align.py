# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scribe_align as sa


def W(*items):
    return [{'text': t, 'start': s, 'end': e} for t, s, e in items]


def test_skeleton_matches_across_scripts():
    assert sa.skeleton('Ҳузайфа') == sa.skeleton('Huzayfa')
    assert sa.skeleton('ташувчи') == sa.skeleton('tashuvchi')
    assert sa.skeleton('Ҳузайфа') == sa.skeleton('حذیفه')


def test_uzbek_latin_merge_takes_the_timings():
    src = 'Расулуллоҳ соллаллоҳу алайҳи ва саллам: «Гап ташувчи'.split()
    hyp = W(('Rasululloh', 11.16, 11.8), ('sallallohu', 11.9, 12.58), ('alayhi', 12.64, 12.98),
            ('vasallam', 13.02, 13.62), ('gap', 14.28, 14.5), ('tashuvchi', 14.54, 15.02))
    t, cost, ms, mh = sa.align(src, hyp)
    assert (ms, mh) == (0, 0) and cost < 0.2
    assert t[0] == (11.16, 11.8)
    assert abs(t[3][0] - 13.02) < 1e-9 and abs(t[4][1] - 13.62) < 1e-9   # 'ва саллам' share 'vasallam'
    assert t[5] == (14.28, 14.5)


def test_tajik_persian_split_spans_the_words():
    src = 'Расули Аллоҳ Салаллоҳу алайҳи васаллам мегуфт:'.split()
    hyp = W(('رسول', 8.64, 9.02), ('الله', 9.08, 9.6), ('صلی', 9.66, 9.9), ('الله', 9.94, 10.3),
            ('علیه', 10.36, 10.66), ('و', 10.7, 10.8), ('سلم', 10.86, 11.26), ('می‌گفت', 11.34, 11.82))
    t, cost, ms, mh = sa.align(src, hyp)
    assert ms == 0 and t[-1] == (11.34, 11.82) and t[0][0] == 8.64
    assert all(t[i][0] <= t[i + 1][0] for i in range(len(t) - 1))


def test_cues_keep_our_words_and_fold_a_lone_word():
    words = 'Ривоят қилинади: Унга бир кишининг гап'.split()
    times = [(i, i + 0.5) for i in range(len(words))]
    c = sa.cues(words, times)
    assert ' '.join(x[2] for x in c) == ' '.join(words)
    assert all(len(x[2].split()) > 1 for x in c)
    assert '00:00:01,500' in sa.to_srt(c) or c[0][1] >= 1.5


def test_a_clause_ending_one_word_later_is_not_split():
    words = 'Ҳузайфа ибн Яман розияллоҳу анҳудан ривоят қилинади: Унга бир кишининг'.split()
    c = sa.cues(words, [(i, i + 0.5) for i in range(len(words))])
    assert c[1][2].endswith('қилинади:') and len(c[1][2].split()) > 1


def test_parenthesis_stays_on_one_cue():
    words = 'Abu Hurairah (may Allah be pleased with him) narrated that the Prophet said:'.split()
    c = sa.cues(words, [(i, i + 0.5) for i in range(len(words))])
    assert any('(may Allah be pleased with him)' in x[2] for x in c)
