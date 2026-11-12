"""P412: the -Name collection-prefix check (scripts/lib/SetName.ps1), run through
PowerShell. Pure: the library collections are passed in, nothing is fetched."""
import json
import os
import shutil
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PS1 = os.path.join(HERE, 'SetName.ps1')
SHELL = shutil.which('pwsh') or shutil.which('powershell')
pytestmark = pytest.mark.skipif(SHELL is None, reason='no PowerShell on this machine')


def verdict(name, collections):
    cols = '$null' if collections is None else '@(' + ','.join(f"'{c}'" for c in collections) + ')'
    cmd = f". '{PS1}'; Test-SetName -Name '{name}' -Collections {cols} | ConvertTo-Json -Compress"
    out = subprocess.run([SHELL, '-NoProfile', '-Command', cmd], capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_the_1987_case_is_refused_and_names_the_right_prefix():
    v = verdict('b1987-sand', ['Jami at-Tirmidhi'])
    assert v['Ok'] is False
    assert 't1987-' in v['Message']


def test_the_right_prefix_passes():
    assert verdict('t1987-sand', ['Jami at-Tirmidhi'])['Ok'] is True
    assert verdict('ad1488-dawn', ['Sunan Abu Dawud'])['Ok'] is True
    assert verdict('m2564-x', ['Sahih al-Bukhari', 'Sahih Muslim'])['Ok'] is True


def test_no_library_row_and_unknown_prefix_are_refused():
    assert verdict('b99999-x', [])['Ok'] is False
    assert verdict('zz12-x', ['Sahih Muslim'])['Ok'] is False


def test_unreadable_library_and_non_set_names_do_not_block():
    assert verdict('b1-x', None)['Ok'] is True
    assert verdict('lamb-wave', None)['Ok'] is True
