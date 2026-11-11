"""P400: lint-content.py's S/M seam check (OPEN_ITEMS P315). Offline."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('lint_content', os.path.join(HERE, '..', 'lint-content.py'))
lc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lc)


def test_the_r158_seam_is_caught():
    s = 'The Messenger of Allah said: "Treat women well, for woman was created from a rib. So treat women well."'
    m = 'Treat women well. Kindness at home is part of faith.'
    assert 'treat women well' in lc.seam_overlap(s, m)


def test_a_moral_that_echoes_the_meaning_in_other_words_passes():
    s = ('Abu Hurairah narrated that the Prophet, peace be upon him, said: "Charity does not decrease wealth; '
         'and no one humbles himself for the sake of Allah but that Allah raises him."')
    m = 'Giving does not make you poorer. Today, give something, forgive someone, and do it for Allah.'
    assert lc.seam_overlap(s, m) == []


def test_russian_and_case_and_punctuation():
    s = 'Пророк ﷺ сказал: «Обращайтесь с женщинами хорошо!»'
    m = 'Обращайтесь с женщинами хорошо - это часть веры.'
    assert lc.seam_overlap(s, m) == ['обращаитесь с женщинами', 'с женщинами хорошо']


def test_the_check_reports_one_warning_on_the_moral():
    blocks = lc.parse_blocks('S: He said: "So treat women well."\nM: Treat women well, every day.\n')
    found = lc.check_seam(blocks)
    assert len(found) == 1 and found[0].level == 'WARN' and found[0].check == 'seam-repeat'
    assert lc.check_seam(lc.parse_blocks('S: He said: "Be kind."\nM: Kindness is faith.\n')) == []