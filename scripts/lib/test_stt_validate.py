# scripts/lib/test_stt_validate.py - P342: the narrator lead-in, the honorifics and
# the matn's quotation marks are HIGH in stt-validate.py. Fixtures are the real
# SRTs of abudawud-4811 and tirmidhi-1161, before and after their hand fixes.
import importlib.util
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, '..', 'stt-validate.py')
_spec = importlib.util.spec_from_file_location('stt_validate', SCRIPT)
sv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sv)

DRAFT_4811_RU = (
    'S: Абу Хурайра, да будет доволен им Аллах, передал, что Пророк ﷺ сказал: '
    '«Кто не благодарит людей, тот не благодарит Аллаха».\n'
    'M: Благодари людей за добро, которое они тебе сделали: в этом хадисе '
    'благодарность им связана с благодарностью Аллаху.\n'
    'H: Хадис передан Абу Хурайрой.\nC: Кто не благодарит людей\n')
DRAFT_4811_EN = (
    'S: Abu Hurairah (may Allah be pleased with him) narrated that the Prophet ﷺ '
    'said: "Whoever does not thank people does not thank Allah."\n'
    'M: Thank the people who do you good. In this hadith, thanks to them is tied '
    'to thanks to Allah.\nH: x\nC: Whoever Does Not Thank People\n')
DRAFT_1161_RU = (
    'S: Умм Салама, да будет доволен ею Аллах, передала, что Пророк ﷺ сказал: '
    '«Любая женщина, которая умрёт, а муж её ею доволен, войдёт в Рай».\n'
    'M: Храни довольство своего супруга, ведь Пророк ﷺ назвал это путём, '
    'ведущим в Рай, который обещал Аллах.\nH: x\nC: x\n')


def srt(*cues):
    out = []
    for i, text in enumerate(cues, 1):
        out.append('%d\n00:00:%02d,000 --> 00:00:%02d,000\n%s\n' % (i, i * 2, i * 2 + 2, text))
    return '\n'.join(out)


RU_4811_WHISPER = srt(
    'Абхурайра, добудет доволен им Аллах, передал, что Пророк,',
    'да благословит его Аллах и приветствует, сказал.',
    '«Кто не благодарит людей, тот не благодарит Аллаха.',
    'Благодари людей за добро, которое они тебе сделали».',
    'В этом хадисе благодарность им связана с благодарностью Аллаху.')
RU_4811_FIXED = srt(
    'Абу Хурайра, да будет доволен им Аллах, передал, что Пророк,',
    'да благословит его Аллах и приветствует, сказал:',
    '«Кто не благодарит людей, тот не благодарит Аллаха».',
    'Благодари людей за добро, которое они тебе сделали.',
    'В этом хадисе благодарность им связана с благодарностью Аллаху.')
EN_4811_WHISPER = srt(
    'Abu Hurairah, may Allah be pleased with him,',
    'narrated that the Prophet, peace be upon him, said,',
    'Whoever does not thank people, does not thank Allah.',
    'Thank the people who do you good.',
    'In this hadith, thanks to them is tied to thanks to Allah.')
EN_4811_FIXED = srt(
    'Abu Hurairah, may Allah be pleased with him,',
    'narrated that the Prophet, peace be upon him, said:',
    '"Whoever does not thank people does not thank Allah."',
    'Thank the people who do you good.',
    'In this hadith, thanks to them is tied to thanks to Allah.')
RU_1161_SHIPPED = srt(
    'Умм Салама, да будет доволен ею Аллах, передала, что',
    'Пророк, да благословит его Аллах и приветствует,', 'сказал.',
    'Любая женщина, которая умрёт, а муж её ею доволен,', 'войдёт в Рай.',
    'Храни довольство своего супруга, ведь Пророк, да',
    'благословит его Аллах и приветствует, назвал это',
    'путём, ведущим в Рай, который обещал Аллах.')
RU_1161_WHISPER = RU_1161_SHIPPED.replace('Умм Салама, да будет', 'Ум соляма, добудет')


def run(tmp_path, draft, sub, lang):
    d = tmp_path / 'draft.txt'
    s = tmp_path / 'n.srt'
    d.write_text(draft, encoding='utf-8')
    s.write_text(sub, encoding='utf-8')
    cues, _ = sv.parse_srt(str(s))
    source, _ = sv.parse_source(str(d))
    source = sv.expand_prophet(source, lang)
    blocks = sv.parse_blocks(str(d))
    f = (sv.check_leadin(cues, blocks.get('S', ''), lang)
         + sv.check_honorifics(cues, source, lang)
         + sv.check_quote_boundary(cues, blocks, lang))
    return {(x.severity, x.code) for x in f}, (d, s)


def test_4811_ru_whisper_is_high_three_ways(tmp_path):
    got, _ = run(tmp_path, DRAFT_4811_RU, RU_4811_WHISPER, 'ru')
    assert ('high', 'leadin_garbled') in got
    assert ('high', 'honorific_garbled') in got
    assert ('high', 'quote_boundary') in got


def test_4811_ru_fixed_is_clean(tmp_path):
    got, _ = run(tmp_path, DRAFT_4811_RU, RU_4811_FIXED, 'ru')
    assert got == set()


def test_4811_en_whisper_missing_quotes_is_high_only(tmp_path):
    # P352 (operator 2026-11-03): quote_missing is HIGH - it was MEDIUM under P342.
    got, _ = run(tmp_path, DRAFT_4811_EN, EN_4811_WHISPER, 'en')
    assert got == {('high', 'quote_missing')}


def test_4811_en_fixed_is_clean(tmp_path):
    got, _ = run(tmp_path, DRAFT_4811_EN, EN_4811_FIXED, 'en')
    assert got == set()


def test_1161_ru_shipped_only_lacks_quotes(tmp_path):
    # The shipped 1161 RU SRT carried no quotation marks. Under P342 that was a
    # MEDIUM and the file passed; under P352 it is the one HIGH, and nothing else.
    got, _ = run(tmp_path, DRAFT_1161_RU, RU_1161_SHIPPED, 'ru')
    assert [g for g in got if g[0] == 'high'] == [('high', 'quote_missing')]


def test_1161_ru_whisper_leadin_is_high(tmp_path):
    got, _ = run(tmp_path, DRAFT_1161_RU, RU_1161_WHISPER, 'ru')
    assert ('high', 'leadin_garbled') in got
    assert ('high', 'honorific_garbled') in got


def test_no_leadin_in_draft_skips_the_check(tmp_path):
    draft = 'S: «Кто не благодарит людей, тот не благодарит Аллаха».\nM: x\n'
    got, _ = run(tmp_path, draft, srt('Кто не благодарит людей, тот не благодарит Аллаха.', 'x'), 'ru')
    assert ('high', 'leadin_garbled') not in got


def test_strict_exits_1_end_to_end(tmp_path):
    _, (d, s) = run(tmp_path, DRAFT_4811_RU, RU_4811_WHISPER, 'ru')
    r = subprocess.run([sys.executable, SCRIPT, '--srt', str(s), '--source', str(d),
                        '--lang', 'ru', '--strict'], capture_output=True, text=True,
                       encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    assert r.returncode == 1, r.stdout
    assert 'leadin_garbled' in r.stdout and 'quote_boundary' in r.stdout
