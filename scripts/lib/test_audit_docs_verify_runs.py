"""scripts/audit-docs.py - P442: verify-runs reports left out of git are drift after a day."""
import importlib.util
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("audit_docs", os.path.join(os.path.dirname(HERE), "audit-docs.py"))
ad = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ad)


def _repo(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    (tmp_path / 'verify-runs').mkdir()
    return tmp_path


def _report(repo, name, age, now):
    p = repo / 'verify-runs' / name
    p.write_text('{}', encoding='utf-8')
    os.utime(str(p), (now - age, now - age))


def test_old_untracked_report_is_stale_new_one_is_fresh(tmp_path):
    repo, now = _repo(tmp_path), 2_000_000_000
    _report(repo, 'candidate-verdicts-old.json', 3 * 86400, now)
    _report(repo, 'candidate-verdicts-new.json', 3600, now)
    stale, fresh = ad.untracked_reports(str(repo), now=now)
    assert stale == ['candidate-verdicts-old.json'] and fresh == ['candidate-verdicts-new.json']


def test_committed_reports_are_not_reported(tmp_path):
    repo, now = _repo(tmp_path), 2_000_000_000
    _report(repo, 'candidate-verdicts-old.json', 3 * 86400, now)
    subprocess.run(['git', 'add', 'verify-runs'], cwd=str(repo), check=True)
    assert ad.untracked_reports(str(repo), now=now) == ([], [])