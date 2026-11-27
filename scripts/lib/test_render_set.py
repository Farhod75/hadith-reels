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


def test_story_anchor_places_clips_before_a_late_matn():
    # P420: Muslim #105 - the Prophet's words are the last 2.8 s of a 15.8 s story
    d = rs.aligned_durations(['start', 'story:0.4', 'matn', 'moral'], story=15.8, moral=15.0,
                             matn_start=13.0, total=31.3, tail_pad=1.0)
    assert abs(d[0] - 6.32) < 0.002
    assert abs(d[1] - (13.0 - 6.32)) < 0.002
    assert abs(d[2] - (15.8 + 0.5 - 13.0)) < 0.002
    try:
        rs.aligned_durations(['start', 'story:1.0'], 15.8, 15.0, 13.0, 31.3, 1.0)
    except ValueError:
        pass
    else:
        raise AssertionError('accepted story:1.0')


# P426 - loudness match after each leg
EBUR = """[Parsed_ebur128_0 @ 0x1] Summary:

  Integrated loudness:
    I:         -23.1 LUFS
    Threshold: -33.4 LUFS
"""


def test_parses_the_integrated_loudness():
    assert rs.parse_integrated_lufs(EBUR) == -23.1
    assert rs.parse_integrated_lufs("no summary") is None


def test_a_loud_leg_is_brought_to_the_target():
    # muslim-2592 UZ rendered at -23.1 and was lowered by hand to -28.1
    assert rs.loudness_gain(-23.1) == -4.9
    assert rs.loudness_gain(-25.5) == -2.5


def test_a_leg_near_or_under_the_target_is_kept():
    assert rs.loudness_gain(-27.6) == 0.0
    assert rs.loudness_gain(-28.3) == 0.0
    assert rs.loudness_gain(-31.0) == 0.0   # never boosted - could clip the voice


# ---- P437: a narration.mp3 older than story/moral is the previous narration ----
def _touch(path, t):
    io.open(path, "wb").close()
    os.utime(path, (t, t))


def test_concat_newer_than_both_parts_is_fresh(tmp_path):
    s, m, n = (str(tmp_path / x) for x in ("s.mp3", "m.mp3", "n.mp3"))
    _touch(s, 1000); _touch(m, 1000); _touch(n, 2000)
    assert rs.narration_is_stale(n, [s, m]) is False


def test_re_narrated_moral_makes_the_concat_stale(tmp_path):
    # #2664 UZ: moral re-narrated after the last render - narration.mp3 still held the old one
    s, m, n = (str(tmp_path / x) for x in ("s.mp3", "m.mp3", "n.mp3"))
    _touch(s, 1000); _touch(n, 2000); _touch(m, 3000)
    assert rs.narration_is_stale(n, [s, m]) is True


def test_missing_concat_counts_as_stale(tmp_path):
    s, m = str(tmp_path / "s.mp3"), str(tmp_path / "m.mp3")
    _touch(s, 1000); _touch(m, 1000)
    assert rs.narration_is_stale(str(tmp_path / "none.mp3"), [s, m]) is True

# P449: #6019 took five hand-tuned dry runs; UZ (64 s) did not fit with one clip on the moral
_LANGS_6019 = {'uz': (40.0, 23.5, 5.0, 64.2), 'en': (34.0, 20.4, 4.0, 55.2)}
_CAPS = [14.04] * 7
_PLAN = ['start', 'matn:0.2', 'matn:0.42', 'matn:0.56', 'matn:0.7', 'matn:0.84', 'moral']


def test_the_plan_that_failed_is_still_refused():
    durs = rs.aligned_durations(_PLAN, *_LANGS_6019['uz'], 1.0)
    assert max(durs) > 14.04


def test_suggest_align_fits_every_language_and_keeps_the_kinds():
    sug, res = rs.suggest_align(_PLAN, _LANGS_6019, _CAPS, 1.0)
    assert sug is not None and sug[0] == 'start'
    for durs in res.values():
        assert max(durs) <= 14.04 and min(durs) >= rs.MIN_SLOT


def test_suggest_align_says_so_when_nothing_fits():
    sug, over = rs.suggest_align(['start', 'moral'], _LANGS_6019, [14.04, 14.04], 1.0)
    assert sug is None and over > 0


def test_when_the_plans_kinds_fit_they_are_kept():
    plan = ['start', 'matn:0.5', 'moral']
    sug, _ = rs.suggest_align(plan, {'en': (20.0, 10.0, 3.0, 30.6)}, [14.04] * 3, 1.0)
    assert [a.split(':')[0] for a in sug] == ['start', 'matn', 'moral']


def test_the_matn_moral_boundary_moves_when_the_kinds_cannot_fit(monkeypatch):
    # #6019: the plan's kinds could not fit; making the last matn anchor a moral one did
    calls = []
    def fake(v, *a, **k):
        calls.append(list(v))
        return (v, {}) if [x.split(':')[0] for x in v].count('moral') == 2 else (None, 1.0)
    monkeypatch.setattr(rs, '_fit_align', fake)
    plan = ['start', 'matn:0.2', 'matn:0.5', 'matn:0.8', 'moral']
    sug, _ = rs.suggest_align(plan, {}, [], 1.0)
    assert calls[0] == plan
    assert sug == ['start', 'matn:0.2', 'matn:0.5', 'moral', 'moral']
