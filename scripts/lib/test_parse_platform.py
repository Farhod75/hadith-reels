"""scripts/parse-platform.py - platform-<n>.md blocks to texts-<n>.json fields, offline."""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("parse_platform", os.path.join(os.path.dirname(HERE), "parse-platform.py"))
pp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp)

F = "```\n%s\n```\n"


def _lang(code, texts):
    return "## %s\n\n" % code + "".join("**x**\n" + F % t for t in texts)


def test_six_blocks_per_language_map_to_the_fields():
    md = "# Platform texts\n\n" + _lang("EN", ["cap", "tags", "Title", "Desc\n\nline", "t1, t2", "tt"]) \
         + _lang("UZ", list("abcdef"))
    out = pp.parse(md)
    assert set(out) == {"en", "uz"}
    assert out["en"]["yt_desc"] == "Desc\n\nline" and out["en"]["tt"] == "tt"
    assert out["uz"]["meta"] == "a" and out["uz"]["tt"] == "f"


def test_a_missing_block_stops_the_run():
    try:
        pp.parse(_lang("RU", list("abcde")))
    except ValueError as e:
        assert "RU" in str(e)
    else:
        raise AssertionError("accepted five blocks")
