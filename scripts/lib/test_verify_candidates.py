"""P357 (Sol 6.1 R11): verify-candidates.py must not call a partial row verified,
and must not report a lost write as WRITTEN.

main() runs end to end with every network call replaced: no Supabase, no model,
no key. The test runs in a temp directory so the report file it writes cannot
overwrite a real out/candidate-verdicts.json.
"""
import importlib.util
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, '..', 'verify-candidates.py')
_spec = importlib.util.spec_from_file_location('verify_candidates', SCRIPT)
vc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vc)

PASS = {'verdict': 'pass', 'issues': [], 'confidence': 'high'}
FULL = {'candidate_id': 'c-1', 'collection': 'Sahih Muslim', 'hadith_number': '1',
        'text_arabic': 'نص', 'text_english': 'e', 'text_russian': 'r',
        'text_uzbek_cyrillic': 'u', 'text_tajik': 't'}


@pytest.fixture
def harness(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(vc, 'load_env', lambda *a, **k: {})
    monkeypatch.setattr(vc, 'pick', lambda env, names: 'x')
    monkeypatch.setattr(vc, 'pass_a', lambda *a: dict(PASS))
    monkeypatch.setattr(vc, 'pass_b', lambda *a: dict(PASS))
    monkeypatch.setattr(vc.time, 'sleep', lambda s: None)
    writes = []

    def run(rows, patch_result=lambda payload: [{'candidate_id': 'c-1'}], argv=('--commit',)):
        monkeypatch.setattr(vc, 'sb_get', lambda *a, **k: rows)

        def fake_patch(base, key, table, match, payload):
            writes.append(payload)
            res = patch_result(payload)
            if isinstance(res, Exception):
                raise res
            return res
        monkeypatch.setattr(vc, 'sb_patch', fake_patch)
        monkeypatch.setattr(sys, 'argv', ['verify-candidates.py', *argv])
        return vc.main()
    run.writes = writes
    return run


def test_roll_up_missing_language_is_incomplete_not_pass():
    per = {'en': {'agreement': 'pass'}, 'ru': {'agreement': 'missing'}}
    assert vc.roll_up(per) == 'incomplete'
    per['tj'] = {'agreement': 'disagree'}
    assert vc.roll_up(per) == 'disagree'      # a real verdict still outranks it


def test_full_candidate_passes_and_is_written(harness):
    assert harness([dict(FULL)]) == 0
    assert harness.writes[-1]['status'] == 'verified'


def test_english_only_candidate_is_not_verified(harness):
    row = dict(FULL, text_russian='', text_uzbek_cyrillic=None, text_tajik='')
    assert harness([row]) == 0
    payload = harness.writes[-1]
    assert payload['verify_agreement'] == 'incomplete'
    assert payload['status'] != 'verified'
    assert set(payload['verify_a']) == {'en'}   # nothing recorded for unchecked languages


def test_failed_write_exits_nonzero(harness, capsys):
    rc = harness([dict(FULL)], patch_result=lambda p: RuntimeError('503'))
    assert rc == 1
    out = capsys.readouterr().out
    assert 'WRITE FAILED for 1 row' in out
    assert "  WRITTEN." not in out


@pytest.mark.parametrize('rows_back', [[], [{'candidate_id': 'c-1'}, {'candidate_id': 'c-2'}]])
def test_a_write_that_did_not_hit_exactly_one_row_is_a_failure(harness, rows_back):
    assert harness([dict(FULL)], patch_result=lambda p: rows_back) == 1


def test_from_json_still_scores_a_one_language_proposal(harness, tmp_path):
    import json
    prop = tmp_path / 'proposed.json'
    prop.write_text(json.dumps([{'ref': 'Sahih Muslim #1', 'text_arabic': 'نص',
                                 'proposed': {'text_russian': 'r'}}]), encoding='utf-8')
    assert harness([], argv=('--from-json', str(prop))) == 0
    with open(os.path.join('out', 'candidate-verdicts.json'), encoding='utf-8') as fh:
        report = json.load(fh)
    assert report[0]['agreement'] == 'pass'
    assert harness.writes == []


def test_each_run_keeps_its_own_report_with_models_and_input_hashes(harness):
    import glob
    import json
    harness([dict(FULL)], argv=())
    runs = glob.glob(os.path.join('verify-runs', 'candidate-verdicts-*.json'))   # P408: tracked
    assert len(runs) == 1
    with open(runs[0], encoding='utf-8') as fh:
        entry = json.load(fh)[0]
    assert entry['models'] == {'a': vc.MODEL_A, 'b': vc.MODEL_B}
    assert set(entry['input_sha256']) == {'text_arabic', 'text_english', 'text_russian',
                                          'text_uzbek_cyrillic', 'text_tajik'}


def test_an_interrupted_batch_keeps_the_rows_already_paid_for(harness, monkeypatch):
    # P359 (Sol R4): the report used to be written once, after the whole batch.
    import json
    calls = {'n': 0}

    def a_then_interrupt(*a):
        calls['n'] += 1
        if calls['n'] > 4:            # row 1 = four languages; row 2 is cut off
            raise KeyboardInterrupt
        return dict(PASS)
    monkeypatch.setattr(vc, 'pass_a', a_then_interrupt)
    with pytest.raises(KeyboardInterrupt):
        harness([dict(FULL), dict(FULL, candidate_id='c-2', hadith_number='2')], argv=())
    with open(os.path.join('out', 'candidate-verdicts.json'), encoding='utf-8') as fh:
        saved = json.load(fh)
    assert [r['ref'] for r in saved] == ['Sahih Muslim #1']
