"""scripts/publish-js.py - P439: the Meta/TikTok/YouTube scripts come from one tracked generator."""
import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("publish_js", os.path.join(os.path.dirname(HERE), "publish-js.py"))
pj = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pj)

TEXTS = {"en": {"meta": 'Line "one"\nﷺ', "tt": "tt text #x", "yt_title": "T | Sahih",
                "yt_desc": "desc", "yt_tags": "a,b"}}


def test_meta_text_is_a_json_literal():
    js = pj.meta_js(TEXTS, "en")
    assert "const TXT=" + json.dumps(TEXTS["en"]["meta"], ensure_ascii=False) + ";" in js


def test_yt_waits_90s_and_does_not_throw_on_a_slow_check():
    js = pj.yt_js(TEXTS, "en", "7536", "bukhari-7536", repo="R")
    assert "waitFor({timeout:90000}).catch(()=>{})" in js
    assert "{name:'Create', exact:true}" in js   # 'Create' alone also matched 'Create playlist'


def test_yt_points_at_the_reel_and_the_cover_of_its_language():
    js = pj.yt_js(TEXTS, "en", "7536", "bukhari-7536", repo="R")
    assert json.dumps(os.path.join("R", "out", "work", "adults", "bukhari-7536", "en", "adults-en-bukhari-7536-reel.mp4")) in js
    assert json.dumps(os.path.join("R", "out", "work", "adults", "bukhari-7536", "en", "cover-7536-en.jpg")) in js


def test_a_missing_text_stops():
    with pytest.raises(SystemExit):
        pj.tt_js({"en": {"tt": "  "}}, "en")
    with pytest.raises(SystemExit):
        pj.yt_js({"en": {"yt_title": "t"}}, "en", "1", "s")


def test_newest_app_folder_wins(tmp_path):
    for n, t in (("app-6.6395.0", 1000), ("app-6.28899.6", 2000)):
        d = tmp_path / n / ".playwright-mcp"
        d.mkdir(parents=True)
        os.utime(str(d), (t, t))
    assert pj.playwright_dir(str(tmp_path)).endswith(os.path.join("app-6.28899.6", ".playwright-mcp"))


def test_no_app_folder_stops(tmp_path):
    with pytest.raises(SystemExit):
        pj.playwright_dir(str(tmp_path))

def test_yt_dismisses_leave_site_and_never_navigates_away_from_a_running_upload():
    # P445: #2589 RU hung on the "leave site?" prompt while EN was still uploading
    js = pj.yt_js(TEXTS, "en", "7536", "bukhari-7536", repo="R")
    assert "d.dismiss()" in js and "d.accept" not in js
    assert "return {blocked:" in js
    assert js.index("page.off('dialog'") < js.index("Upload videos")


def test_meta_share_refuses_without_a_cover_and_checks_the_audience():
    js = pj.meta_share_js()
    assert "if (!cov) return {stop:" in js
    assert js.index("if (!cov)") < js.index("Поделиться")
    assert '"[false,false,true,true,false]"' in js and '"[false,true,false,false,false]"' in js


def test_meta_upload_and_cover_point_at_the_given_files():
    assert json.dumps("U/adults-en-x-reel.mp4") in pj.meta_up_js("U/adults-en-x-reel.mp4")
    assert json.dumps("U/cover-1-en.jpg") in pj.meta_cover_js("U/cover-1-en.jpg")
