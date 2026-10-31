# scripts/lib/test_narrator_leadin.py - P337. Offline: reads lib/refs.ts only.
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from narrator_leadin import load_narrators, leadin, check_story

T = load_narrators()

# The four texts the operator approved for tirmidhi-1161 on 2026-10-31.
APPROVED = {
    'en': 'Umm Salamah (may Allah be pleased with her) narrated that the Prophet \ufdfa said: "Whichever woman dies while her husband is pleased with her, she will enter Paradise."',
    'ru': 'Умм Салама, да будет доволен ею Аллах, передала, что Пророк \ufdfa сказал: «Любая женщина, которая умрёт, а муж её ею доволен, войдёт в Рай».',
    'uz': 'Умму Салама розияллоҳу анҳодан ривоят қилинади: Пайғамбар соллаллоҳу алайҳи ва саллам айтдилар: "Қайси бир аёл эри ундан рози бўлган ҳолда вафот этса, у жаннатга киради."',
    'tj': 'Аз Уммӣ Салама розияллоҳу анҳо ривоят аст, ки Пайғамбар соллаллоҳу алайҳи ва саллам фармуданд: «Ҳар зане ки бимирад ва шавҳараш аз ӯ розӣ бошад, ба биҳишт дохил мешавад».',
}


def test_table_parses_whole():
    assert len(T) >= 27
    assert T['Umm Salamah'] == {'ru': 'Умм Салама', 'uz': 'Умму Салама',
                                'tj': 'Уммӣ Салама', 'h': 'f'}
    assert T['Aisha']['h'] == 'f'
    assert T['Abu Hurairah']['h'] == 'm'


def test_pair_honorific():
    assert 'анҳумо' in leadin('Ibn Umar', 'uz', T)
    assert 'анҳумо' in leadin('Ibn Abbas', 'tj', T)


def test_approved_texts_pass():
    for lang, s in APPROVED.items():
        assert check_story(s, 'Umm Salamah', lang, T) == [], lang


def test_omitted_narrator_refused():
    old = 'The Prophet \ufdfa said: "Whichever woman dies while her husband is pleased with her, she will enter Paradise."'
    assert check_story(old, 'Umm Salamah', 'en', T)


def test_wrong_narrator_refused():
    # Abu Bakra is not Abu Bakr as-Siddiq; any narrator other than the row's fails
    s = APPROVED['uz'].replace('Умму Салама', 'Абу Бакра')
    assert check_story(s, 'Umm Salamah', 'uz', T)


def test_unknown_narrator_refused():
    assert 'not in lib/refs.ts' in check_story(APPROVED['en'], 'Somebody New', 'en', T)[0]


def test_masculine_ru_verb():
    assert leadin('Abu Hurairah', 'ru', T).startswith('Абу Хурайра, да будет доволен им Аллах, передал,')


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
