"""scripts/mix-gap.py - the pure parts, and that it reads render-reel.ps1's real mix (OPEN_ITEMS item 2)."""
import importlib.util
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("mix_gap", os.path.join(SCRIPTS, "mix-gap.py"))
mg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mg)


def test_reads_the_mix_render_reel_actually_uses():
    text = io.open(os.path.join(os.path.dirname(SCRIPTS), "render-reel.ps1"), encoding="utf-8-sig").read()
    base, narr = mg.read_mix_constants(text)
    assert (base, narr) == (0.12, 1.4)


def test_parse_lufs_takes_the_summary_line():
    err = "[Parsed_ebur128_0] t: 1.0 M: -30 S: -30 I: -31.0 LUFS\nSummary:\n  Integrated loudness:\n    I:         -32.7 LUFS\n"
    assert mg.parse_lufs(err) == -32.7
    assert mg.parse_lufs("no loudness here") is None


def test_trim_moves_the_gap_onto_the_target():
    # #2749 UZ: gap 15.3 before the render, target 15.7 -> 0.95 (rendered, measured 15.7 after)
    assert round(mg.trim_for(15.3, 15.7), 2) == 0.95
    assert mg.trim_for(13.3, 13.3) == 1.0
    assert mg.trim_for(14.0, 13.4) > 1.0          # too quiet -> louder


def test_targets_are_p338s():
    assert mg.TARGETS == {"en": 13.3, "ru": 10.8, "uz": 15.7, "tj": 13.4}
