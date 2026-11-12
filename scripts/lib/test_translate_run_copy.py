"""P408 (Sol R4): translate-candidates keeps a tracked copy of each proposal and each
review signature in verify-runs/, beside verify-candidates' verdicts. Runs in a temp
directory; no network, no key."""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, '..', 'translate-candidates.py')
_spec = importlib.util.spec_from_file_location('translate_candidates', SCRIPT)
tc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tc)


def test_a_signed_review_is_kept_in_verify_runs(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    os.makedirs('out')
    rows = [{'ref': 'Sahih Muslim #1', 'proposed': {'text_russian': 'r'}}]
    with open(tc.OUT_PATH, 'w', encoding='utf-8') as fh:
        json.dump(rows, fh)
    assert tc.sign_review() == 0
    kept = [f for f in os.listdir('verify-runs') if f.startswith('candidate-translations-reviewed-')]
    assert len(kept) == 1
    with open(os.path.join('verify-runs', kept[0]), encoding='utf-8') as fh:
        assert json.load(fh)['refs'] == ['Sahih Muslim #1']


def test_keep_run_copy_never_overwrites_the_tracked_folder_layout(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / 'p.json'
    src.write_text('[]', encoding='utf-8')
    dst = tc.keep_run_copy(str(src), 'candidate-translations')
    assert os.path.dirname(dst) == 'verify-runs'
    assert os.path.basename(dst).startswith('candidate-translations-2')
