"""P356 (Sol 6.1 R2): the subtitle check in render-reel.ps1 cannot be skipped.

Three ways round it existed: no draft -> the validator skipped itself with a
yellow line; -AcceptSubtitleFindings accepted "could not run" as readily as
"found something"; and the SRT the operator edited at the review pause was
burned without being checked again. These tests read the script (no PowerShell
needed) and pin each closed path, plus the exit-code contract it relies on.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, '..', '..', 'render-reel.ps1')
VALIDATOR = os.path.join(HERE, '..', 'stt-validate.py')


def _src(path=SCRIPT):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def _review_block(src):
    start = src.index('# --- SUBTITLE REVIEW CHECKPOINT')
    end = src.index('# --- STEP 6:')
    return src[start:end]


def test_a_missing_draft_no_longer_skips_the_validator():
    src = _src()
    assert '[skip] subtitle validator' not in src
    assert re.search(r'elseif \(\$useSubs\) \{[^}]*Die "\$Draft not found', src, re.S)


def test_the_set_draft_is_the_default():
    assert 'out\\draft-$Slug-$Lang.txt' in _src()


def test_accept_findings_covers_findings_only():
    src = _src()
    # a failed run dies before -AcceptSubtitleFindings is even consulted
    fail = src.index('if ($sttRc -ne 0 -and $sttRc -ne 3)')
    accept = src.index('if ($NoReview -and $sttRc -eq 3)')
    assert fail < accept
    assert 'Die "the subtitle validator did not run properly' in src[fail:accept]


def test_the_saved_srt_is_validated_again_after_the_pause():
    block = _review_block(_src())
    pause = block.index('Read-Host "Press ENTER to burn')
    recheck = block.index('Invoke-SttValidate -Strict')
    assert pause < recheck
    assert 'Assert-ValidSrt $srt' in block[pause:recheck]


def test_validator_findings_exit_code_matches_what_the_renderer_expects():
    assert 'EXIT_HIGH_FINDINGS = 3' in _src(VALIDATOR)
