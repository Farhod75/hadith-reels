"""P358 (Sol 6.1 R3): render-reel.ps1's record of a render is complete and required.

Read from the script, no PowerShell needed. Pins: the reel must postdate THIS
run (not merely be under five minutes old); the sidecar records the scenes that
were actually drawn and a hash of every input that decides what was published;
and a sidecar that cannot be written fails the run. mix-gap.py reads three of
its fields, so those must keep their names.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, '..', '..', 'render-reel.ps1')


def _src():
    with open(SCRIPT, encoding='utf-8') as fh:
        return fh.read()


def _sidecar_block(src):
    start = src.index('$sidecar = [ordered]@{')
    return src[start:src.index('ConvertTo-Json', start)]


def test_reel_must_postdate_this_run():
    src = _src()
    assert '$runStart = Get-Date' in src
    assert 'LastWriteTime -lt $runStart' in src
    assert 'TotalMinutes' not in src[src.index('final merge failed'):src.index('STEP 7b')]


def test_sidecar_records_the_scenes_actually_drawn():
    block = _sidecar_block(_src())
    assert re.search(r'scenes\s*=\s*@\(\$picked', block)


def test_sidecar_hashes_every_input():
    block = _sidecar_block(_src())
    for field in ('reel', 'narration', 'draft', 'srt', 'nasheed'):
        assert re.search(r'\b%s\s*=' % field, block), field


def test_fields_mix_gap_reads_are_still_there():
    block = _sidecar_block(_src())
    for field in ('nasheed', 'nasheedVol', 'nasheedGain'):
        assert re.search(r'\b%s\s*=' % field, block), field


def test_a_sidecar_that_cannot_be_written_fails_the_run():
    src = _src()
    catch = src[src.index('[System.IO.File]::WriteAllText($sidecarPath'):]
    catch = catch[:catch.index('}', catch.index('catch {')) + 1]
    assert 'Die "could not write $base-render.json' in catch
