"""P352: a lowercase divine pronoun, or a matn with no quotation marks, is HIGH in the
subtitles, so --strict stops the render.

Muslim #2749's first EN render burned "By him in Whose Hand is my soul": the
check found it, rated it MEDIUM, and under -NoReview a MEDIUM is never read.
"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "stt_validate", os.path.join(os.path.dirname(HERE), "stt-validate.py"))
stt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stt)

SOURCE = "By Him in Whose Hand is my soul, if you did not sin, Allah would take you away."


def _cues(text):
    return [{"index": 1, "text": text}]


def test_lowercase_divine_pronoun_is_high():
    out = stt.check_divine_pronoun_case(_cues("By him in Whose Hand is my soul,"), SOURCE, "en")
    assert [f.code for f in out] == ["divine_pronoun_case"]
    assert out[0].severity == "high"


def test_capitalised_divine_pronoun_passes():
    assert stt.check_divine_pronoun_case(_cues("By Him in Whose Hand is my soul,"), SOURCE, "en") == []


def test_prophet_pronoun_lowercase_is_not_flagged():
    src = "the Prophet, peace be upon him, said"
    assert stt.check_divine_pronoun_case(_cues("the Prophet, peace be upon him, said"), src, "en") == []


def test_missing_quotation_marks_is_high():
    blocks = {"S": 'Abu Hurairah narrated that the Prophet said: "By Him in Whose Hand is my soul."'}
    out = stt.check_quote_boundary(_cues("Abu Hurairah narrated that the Prophet said: By Him in Whose Hand is my soul."), blocks, "en")
    assert [f.code for f in out] == ["quote_missing"]
    assert out[0].severity == "high"


def test_quoted_matn_passes():
    blocks = {"S": 'Abu Hurairah narrated that the Prophet said: "By Him in Whose Hand is my soul."'}
    assert stt.check_quote_boundary(_cues('Abu Hurairah narrated that the Prophet said: "By Him in Whose Hand is my soul."'), blocks, "en") == []
