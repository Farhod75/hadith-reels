"""P387: scripts/fetch-explanation.py and the explanation files it writes.

Offline. The second half re-reads every content/explanations/<slug>.json against
the raw HadeethEnc bytes stored beside it: a hand edit of an explanation, a lesson
or the references fails here, because the source's terms forbid modification and
the project's rule forbids writing commentary ourselves.
"""
import hashlib
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
_spec = importlib.util.spec_from_file_location('fetch_explanation',
                                               os.path.join(HERE, '..', 'fetch-explanation.py'))
fe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fe)

CONTENT = os.path.join(ROOT, 'content', 'explanations')
COLLS = {'Sahih Muslim': 'muslim', 'Sahih al-Bukhari': 'bukhari'}

LIB_AR = 'إِنَّ اللَّهَ لاَ يَنْظُرُ إِلَى صُوَرِكُمْ وَأَمْوَالِكُمْ وَلَكِنْ يَنْظُرُ إِلَى قُلُوبِكُمْ وَأَعْمَالِكُمْ'
SRC_AR = ('عن أبي هريرة رضي الله عنه قال: قال رسول الله صلى الله عليه وسلم: «إِنَّ اللهَ لَا يَنْظُرُ '
          'إِلَى صُوَرِكُمْ وَأَمْوَالِكُمْ، وَلَكِنْ يَنْظُرُ إِلَى قُلُوبِكُمْ وَأَعْمَالِكُمْ».')


def test_slug_is_collection_and_number():
    assert fe.slug_for('Sahih Muslim', '2564', COLLS) == 'muslim-2564'
    assert fe.slug_for('Sahih al-Bukhari', 6405, COLLS) == 'bukhari-6405'


def test_unmapped_collection_or_odd_number_is_refused():
    for coll, num in (('Riyad as-Salihin', '1'), ('Sahih Muslim', '2564 d'), ('Sahih Muslim', '')):
        try:
            fe.slug_for(coll, num, COLLS)
        except ValueError:
            continue
        raise AssertionError('accepted %r %r' % (coll, num))


def test_same_hadith_ignores_diacritics_punctuation_and_isnad():
    assert fe.same_hadith(LIB_AR, SRC_AR)


def test_a_different_hadith_or_an_empty_side_is_not_the_same():
    assert not fe.same_hadith(LIB_AR, 'عن أبي هريرة: «إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ»')
    assert not fe.same_hadith('', SRC_AR)
    assert not fe.same_hadith(LIB_AR, '')


def _payload(lang, expl='E', hints=('h1\r', 'h2')):
    return {'id': '4555', 'title': 'T-' + lang, 'hadeeth': SRC_AR, 'explanation': expl,
            'hints': list(hints), 'attribution': 'A', 'grade': 'G', 'reference': 'R-ar'}


def test_build_doc_copies_text_unchanged_and_maps_tajik():
    row = {'id': 'lib1', 'collection': 'Sahih Muslim', 'hadith_number': '2564'}
    pl = {l: _payload(l, expl=' Ex %s\n' % l) for l in fe.LANGS}
    doc = fe.build_doc(row, pl, {l: 'h' + l for l in fe.LANGS}, '4555', '2026-11-10', COLLS)
    c = doc['commentaries'][0]
    assert doc['slug'] == 'muslim-2564' and doc['occasion'] is None
    assert set(c['langs']) == {'ar', 'en', 'ru', 'uz', 'tj'}
    assert c['langs']['tj']['url'] == 'https://hadeethenc.com/tg/browse/hadith/4555'
    assert c['langs']['ru']['explanation'] == ' Ex ru\n'          # not trimmed
    assert c['langs']['en']['lessons'] == ['h1\r', 'h2']          # not cleaned
    assert c['references_ar'] == 'R-ar' and c['publisher'] == 'HadeethEnc.com'


def test_a_language_without_an_explanation_is_left_out_not_filled():
    row = {'id': 'lib1', 'collection': 'Sahih Muslim', 'hadith_number': '2564'}
    pl = {l: _payload(l) for l in fe.LANGS}
    pl['tg'] = _payload('tg', expl='  ')
    doc = fe.build_doc(row, pl, {l: 'x' for l in fe.LANGS}, '4555', 'd', COLLS)
    assert 'tj' not in doc['commentaries'][0]['langs']


def test_registry_imports_each_slug():
    ts = fe.registry_ts(['muslim-2564', 'bukhari-6405'])
    assert "import x_muslim_2564 from '@/content/explanations/muslim-2564.json'" in ts
    assert "'bukhari-6405': x_bukhari_6405 as Explanation," in ts


# ---- the committed files -------------------------------------------------
def _docs():
    for f in sorted(os.listdir(CONTENT)):
        if f.endswith('.json') and f not in ('index.json', 'collections.json'):
            with open(os.path.join(CONTENT, f), encoding='utf-8') as fh:
                yield f[:-5], json.load(fh)


def test_every_explanation_is_verbatim_from_its_raw_source():
    seen = 0
    for slug, doc in _docs():
        assert doc['slug'] == slug
        for c in doc['commentaries']:
            assert c['source'] == 'hadeethenc', 'only HadeethEnc has a verbatim check so far'
            for site_lang, x in c['langs'].items():
                with open(os.path.join(CONTENT, x['raw']), 'rb') as fh:
                    b = fh.read()
                assert hashlib.sha256(b).hexdigest() == x['raw_sha256'], (slug, site_lang)
                raw = json.loads(b.decode('utf-8'))
                assert x['explanation'] == raw['explanation'], (slug, site_lang)
                assert x['lessons'] == raw.get('hints', []), (slug, site_lang)
                assert x['word_meanings'] == raw.get('words_meanings', []), (slug, site_lang)
                assert x['title'] == raw['title'], (slug, site_lang)
                if site_lang == 'ar':
                    assert c['references_ar'] == raw.get('reference', '')
                seen += 1
    assert seen, 'no explanation files checked'


def test_index_and_registry_list_exactly_the_files():
    slugs = sorted(s for s, _ in _docs())
    with open(os.path.join(CONTENT, 'index.json'), encoding='utf-8') as fh:
        assert json.load(fh) == slugs
    with open(os.path.join(ROOT, 'lib', 'explanations-registry.ts'), encoding='utf-8') as fh:
        assert fh.read() == fe.registry_ts(slugs)


def test_no_occasion_without_a_cited_source():
    for slug, doc in _docs():
        occ = doc.get('occasion')
        if occ is not None:
            assert occ.get('source') and occ.get('url') and occ.get('text'), slug
