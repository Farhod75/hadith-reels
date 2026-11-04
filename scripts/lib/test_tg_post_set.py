"""scripts/tg-post-set.py - planning and the refuse-to-repeat state, offline (no Telegram call)."""
import importlib.util
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("tg_post_set", os.path.join(os.path.dirname(HERE), "tg-post-set.py"))
tg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tg)

FULL = (u"If You Did Not Sin\n\n«By Him in Whose Hand is my soul...»\n\n"
        u"والذي نفسي بيده\n\n"
        u"This is not permission to sin.\n\n"
        u"\U0001F4D6 Sahih Muslim #2749, Abu Hurairah\n\U0001F50D Verify: hadithverifier.com\n\n"
        u"#tawbah #forgiveness #sins #mercy #allah #hadith")


def _set(tmp_path, lang, caption, reel=True, short=None):
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    (out / ("caption-2749-%s.txt" % lang)).write_text(caption, encoding="utf-8")
    if short is not None:
        (out / ("caption-2749-%s-tg-video.txt" % lang)).write_text(short, encoding="utf-8")
    if reel:
        d = out / "work" / "adults" / "muslim-2749" / lang
        d.mkdir(parents=True, exist_ok=True)
        (d / ("adults-%s-muslim-2749-reel.mp4" % lang)).write_bytes(b"x")


def test_split_threshold_is_telegrams_caption_limit():
    assert not tg.needs_split("x" * 1024)
    assert tg.needs_split("x" * 1025)


def test_derived_short_caption_keeps_title_source_and_four_tags():
    s = tg.derive_short(FULL)
    assert s.startswith("If You Did Not Sin\n\n\U0001F4D6 Sahih Muslim #2749")
    assert "\U0001F50D Verify: hadithverifier.com" in s
    assert s.endswith("#tawbah #forgiveness #sins #mercy")
    assert "والذي" not in s           # the Arabic stays in the full reply


def test_short_caption_file_wins_over_derivation(tmp_path):
    _set(tmp_path, "en", FULL + "\n" + "#x " * 400, short="SHORT")
    p = tg.plan_language("2749", "muslim-2749", "en", root=str(tmp_path))
    assert p["split"] and p["short"] == "SHORT"


def test_missing_reel_is_refused(tmp_path):
    _set(tmp_path, "ru", FULL, reel=False)
    p = tg.plan_language("2749", "muslim-2749", "ru", root=str(tmp_path))
    assert "error" in p and "reel.mp4" in p["error"]


def test_state_survives_a_round_trip(tmp_path):
    path = str(tmp_path / "tg-2749.json")
    tg.save_state(path, {"en": {"video": 196}})
    assert tg.load_state(path) == {"en": {"video": 196}}
    assert tg.load_state(str(tmp_path / "none.json")) == {}
