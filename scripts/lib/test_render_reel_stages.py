"""P355 (Sol 6.1 R1): every ffmpeg stage in render-reel.ps1 must fail loudly.

The renderer's intermediate stages checked only that their output EXISTED. ffmpeg
can exit non-zero without touching an existing file, so a failed stage handed the
next one the previous run's narration or background, and the final merge built a
new-looking reel around it. These tests read the script itself (no PowerShell, no
ffmpeg needed) and pin the two halves of the fix for every ffmpeg call:

  - its exit code is checked, and
  - an intermediate output is deleted before the call, so "exists" can only mean
    "this run wrote it".
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, '..', '..', 'render-reel.ps1')

INTERMEDIATES = ('$narr', '$tmp', '$bgMixed')


def _lines():
    with open(SCRIPT, encoding='utf-8') as fh:
        return fh.read().splitlines()


def _ffmpeg_calls(lines):
    return [i for i, l in enumerate(lines) if re.search(r'\$rc = Run "ffmpeg"', l)]


def _call_text(lines, i):
    """The call and its continuation lines, up to the closing paren of @( ... )."""
    out, depth = [], 0
    for l in lines[i:i + 25]:
        out.append(l)
        depth += l.count('(') - l.count(')')
        if depth <= 0:
            break
    return '\n'.join(out)


def test_there_are_ffmpeg_stages_to_check():
    assert len(_ffmpeg_calls(_lines())) >= 4


def test_every_ffmpeg_call_has_its_exit_code_checked():
    lines = _lines()
    for i in _ffmpeg_calls(lines):
        window = lines[i:i + 25]
        assert any('$rc -ne 0' in l for l in window), (
            'render-reel.ps1:%d - ffmpeg result never checked (P355)' % (i + 1))


def test_every_intermediate_output_is_deleted_before_it_is_written():
    lines = _lines()
    checked = 0
    for i in _ffmpeg_calls(lines):
        call = _call_text(lines, i)
        if 'ffArgs' in call:          # the normalize loop: output appended as $tmp
            target = '$tmp'
        else:
            target = next((v for v in INTERMEDIATES
                           if re.search(re.escape(v) + r'\)\s*$', call.strip())), None)
        if target is None:
            continue                  # the final merge: guarded by exit code + file age
        before = '\n'.join(lines[max(0, i - 8):i])
        assert re.search(r'Remove-Item ' + re.escape(target) + r'\b', before), (
            'render-reel.ps1:%d writes %s without deleting the old one first (P355)'
            % (i + 1, target))
        checked += 1
    assert checked >= 4               # narration, normalize, both background branches
