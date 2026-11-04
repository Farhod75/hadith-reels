"""scripts/render-set.py - the P240 clip choice and the tailPad it reads, offline."""
import importlib.util
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("render_set", os.path.join(SCRIPTS, "render-set.py"))
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)

STD = [("a.mp4", 10.04), ("b.mp4", 10.04), ("c.mp4", 10.04), ("d.mp4", 10.29)]
SLOW = [("a-s.mp4", 10.58), ("b-s.mp4", 10.58), ("c-s.mp4", 10.58), ("d-s.mp4", 10.79)]


def test_reads_render_reels_tail_pad():
    text = io.open(os.path.join(os.path.dirname(SCRIPTS), "render-reel.ps1"), encoding="utf-8-sig").read()
    assert rs.read_tail_pad(text) == 1.0


def test_short_narration_takes_the_normal_clips():
    # muslim-2749 EN: 32.89 s narration -> 8.47 s per clip
    which, scenes, need = rs.choose_scenes(32.89, 1.0, STD, SLOW)
    assert which == "scenes" and scenes[0] == "a.mp4" and abs(need - 8.4725) < 0.001


def test_long_narration_takes_the_slow_copies():
    # muslim-2749 UZ: 40.57 s -> 10.39 s per clip, above the 10.04 s Kling clips (P240)
    which, scenes, _ = rs.choose_scenes(40.57, 1.0, STD, SLOW)
    assert which == "scenes_slow" and scenes[0] == "a-s.mp4"


def test_too_long_for_both_stops_before_rendering():
    which, scenes, need = rs.choose_scenes(44.0, 1.0, STD, SLOW)
    assert which is None and scenes is None and need == 11.25


def test_no_slow_copies_stops_when_normal_clips_are_short():
    assert rs.choose_scenes(40.57, 1.0, STD, [])[0] is None


def test_render_command_passes_scenes_as_a_powershell_array():
    cmd = rs.build_render_command("muslim-2749", "uz", "aswati-X.mp3", 0.94, ["a-s.mp4", "b-s.mp4"], repo="C:/repo")
    assert cmd[:3] == ["pwsh", "-NoProfile", "-Command"]
    assert "-Scenes @('a-s.mp4','b-s.mp4')" in cmd[3]
    assert "-NasheedGain 0.94" in cmd[3] and cmd[3].endswith("exit $LASTEXITCODE")
