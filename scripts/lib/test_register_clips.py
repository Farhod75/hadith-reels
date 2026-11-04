"""scripts/register-clips.py - offline: format round-trip, refusals, verify-by-prefix."""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("register_clips", os.path.join(os.path.dirname(HERE), "register-clips.py"))
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)

REG = {"updated": "2026-11-03", "audio": {}, "scenes": {
    "m2747-tree.mp4": {"classification": "scene", "lanes": ["adults"], "verified": True, "notes": u"т"},
    "m2749-dua.mp4": {"classification": "scene", "lanes": ["adults"], "verified": False, "notes": "x"}}}


def test_round_trip_detects_crlf_and_unicode():
    raw = json.dumps(REG, indent=2, ensure_ascii=False).replace("\n", "\r\n") + "\r\n"
    fmt = rc.detect_format(raw)
    assert fmt == (False, "\r\n", "\r\n")
    assert rc.dump(json.loads(raw), fmt) == raw


def test_unreproducible_registry_is_refused():
    assert rc.detect_format('{"a":1}') is None


def test_register_refuses_a_clash_and_a_missing_file(tmp_path):
    (tmp_path / "m2749-bloom.mp4").write_bytes(b"x")
    spec = {"common": "C", "clips": [
        {"file": "m2749-dua.mp4"},                       # already registered
        {"file": "m2749-ghost.mp4"},                     # not on disk
        {"file": "m2749-bloom.mp4", "sidecar": "m2749-bloom", "note": "N"}]}
    add, problems = rc.plan_register(REG, spec, new_dir=str(tmp_path))
    assert len(problems) == 2
    assert add == {"m2749-bloom.mp4": {"classification": "scene", "lanes": ["adults"], "verified": False,
                                       "notes": "N C", "prompt_sidecar": "assets/scene-prompts/m2749-bloom.json"}}


def test_raw_take_can_be_registered_out_of_rotation(tmp_path):
    (tmp_path / "m2749-raw.mp4").write_bytes(b"x")
    add, _ = rc.plan_register(REG, {"clips": [{"file": "m2749-raw.mp4", "lanes": []}]}, new_dir=str(tmp_path))
    assert add["m2749-raw.mp4"]["lanes"] == []


def test_verify_takes_only_the_unverified_under_the_prefix():
    assert rc.plan_verify(REG, "m2749-") == ["m2749-dua.mp4"]
    assert rc.plan_verify(REG, "m2747-") == []
