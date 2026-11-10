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


class _R:
    def __init__(self, code, out):
        self.returncode, self.stdout = code, out


def test_asset_gate_reports_a_claimed_bed_once():
    # #6114 RU: the plan named a Content-ID-claimed bed; render-set only found out mid-set (P377)
    calls = []

    def run(cmd, **kw):
        calls.append(cmd[3])
        if cmd[3] == 'claimed.mp3':
            return _R(1, 'BLOCKED: claimed.mp3 - Content ID has CLAIMED this audio.\n')
        return _R(0, 'OK\n')
    got = rs.asset_gate(['ok.mp3', 'claimed.mp3', 'ok.mp3', 'a.mp4'], run=run)
    assert calls == ['ok.mp3', 'claimed.mp3', 'a.mp4']
    assert got == [('claimed.mp3', 'BLOCKED: claimed.mp3 - Content ID has CLAIMED this audio.')]


def test_reads_render_reels_gain_cap():
    # P384: bukhari-6405 UZ asked for 2.14 and render-reel.ps1 refused it mid-set
    text = io.open(os.path.join(os.path.dirname(SCRIPTS), "render-reel.ps1"), encoding="utf-8-sig").read()
    assert rs.read_gain_max(text) == 2.0


def test_gain_inside_the_range_passes():
    assert rs.gain_problem(0.6, 2.0) is None
    assert rs.gain_problem(2.0, 2.0) is None


def test_gain_above_the_cap_stops_with_the_shortfall():
    why = rs.gain_problem(2.14, 2.0)
    assert why and '"gain": 2.00' in why and '0.6 dB' in why


def test_gain_not_above_zero_stops():
    assert rs.gain_problem(0.0, 2.0)


# ---- P386: clips placed where the narration says what they show ----

EN_S = ('Abu Hurairah (may Allah be pleased with him) narrated that the Prophet \ufdfa said: '
        '"Allah does not look at your forms or wealth, but He looks at your hearts and deeds."')

SRT_EN = """1
00:00:00,000 --> 00:00:03,042
Abu Hurairah, may Allah be pleased with him,

2
00:00:03,042 --> 00:00:06,500
narrated that the Prophet peace be upon him said:

3
00:00:06,500 --> 00:00:09,719
"Allah does not look at your forms or wealth,

4
00:00:09,719 --> 00:00:12,500
but He looks at your hearts and deeds."
"""


def test_matn_start_comes_from_the_first_quoted_cue():
    assert rs.matn_start_from_srt(SRT_EN) == 6.5
    assert rs.matn_start_from_srt("1\n00:00:00,000 --> 00:00:02,000\nno quote here\n") is None


def test_letter_share_lands_near_the_subtitles():
    # muslim-2564 EN: story 12.04 s, the subtitles put the matn at 6.50 s
    est = 12.04 * rs.lead_in_fraction(EN_S, 'en')
    assert abs(est - 6.5) < 0.8, est


def test_saw_glyph_counts_as_spoken_words():
    with_glyph = rs.lead_in_fraction(EN_S, 'en')
    without = rs.lead_in_fraction(EN_S.replace('\ufdfa', ''), 'en')
    assert with_glyph > without


def test_aligned_durations_follow_the_anchors_and_cover_the_tail():
    d = rs.aligned_durations(['start', 'matn', 'matn:0.6', 'moral'], story=12.04, moral=10.69,
                             matn_start=6.5, total=23.23, tail_pad=1.0)
    assert d[0] == 6.5
    assert abs(d[1] - 0.6 * (12.04 - 6.5)) < 0.002
    assert abs(sum(d) - 24.23) < 0.01
    assert abs((d[0] + d[1] + d[2]) - (12.04 + 0.5)) < 0.002   # the moral clip starts with the moral


def test_bad_anchors_stop_before_rendering():
    for anchors in (['matn', 'moral'], ['start', 'moral', 'matn'], ['start', 'matn:1.2'], ['start', 'later']):
        try:
            rs.aligned_durations(anchors, 12.0, 10.0, 6.0, 23.0, 1.0)
        except ValueError:
            continue
        raise AssertionError('accepted %r' % anchors)
    try:
        rs.aligned_durations(['start', 'matn', 'matn:0.1'], 12.0, 10.0, 6.0, 23.0, 1.0)
    except ValueError as e:
        assert 'shorter than' in str(e)
    else:
        raise AssertionError('accepted a 0.6 s slot')


def test_render_command_passes_durations_instead_of_fitscenes():
    cmd = rs.build_render_command('muslim-2564', 'en', 'bed.mp3', 0.78, ['a.mp4', 'b.mp4'], repo='C:/r',
                                  durations=[6.5, 17.73])
    assert '-SceneDurations @(6.500,17.730)' in cmd[-1] and '-FitScenes' not in cmd[-1]
    plain = rs.build_render_command('muslim-2564', 'en', 'bed.mp3', 0.78, ['a.mp4', 'b.mp4'], repo='C:/r')
    assert '-FitScenes' in plain[-1] and 'SceneDurations' not in plain[-1]


def test_render_reel_takes_scene_durations_and_checks_them():
    text = io.open(os.path.join(os.path.dirname(SCRIPTS), "render-reel.ps1"), encoding="utf-8-sig").read()
    assert '[double[]]$SceneDurations' in text
    assert 'one per clip, in -Scenes order (P386)' in text
    assert 'would wrap to clip 1 (P240/P386)' in text
    assert '$durs[$idx-1]' in text
