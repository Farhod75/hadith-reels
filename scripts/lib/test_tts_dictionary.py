"""scripts/tts-dictionary.py - P441: pronunciation dictionaries in sync with their rule files."""
import glob
import importlib.util
import io
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
_spec = importlib.util.spec_from_file_location("tts_dictionary", os.path.join(os.path.dirname(HERE), "tts-dictionary.py"))
td = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(td)


def langs():
    return [re.match(r'pronunciation-(\w+)\.json$', os.path.basename(p)).group(1)
            for p in glob.glob(os.path.join(REPO, 'tts', 'pronunciation-*.json'))
            if not p.endswith('dictionaries.json')]


@pytest.mark.parametrize("lang", langs())
def test_the_route_sends_a_dictionary_built_from_the_current_rules(lang):
    # a rule edited without --apply would leave /api/tts sending the old dictionary
    loc = td.load_locators(os.path.join(REPO, 'tts', 'pronunciation-dictionaries.json'))
    assert loc.get(lang, {}).get('rules_sha') == td.rules_sha(td.load_rules(lang, REPO)), \
        'run: python scripts/tts-dictionary.py --lang %s --apply' % lang


def test_a_sentence_initial_capital_gets_its_own_rule():
    rules = td.api_rules([{"word": "давон", "ipa": "daˈvɔn"}])
    assert [r["string_to_replace"] for r in rules] == ["давон", "Давон"]
    assert all(r["alphabet"] == "ipa" and r["type"] == "phoneme" for r in rules)


def test_a_rule_without_ipa_stops(tmp_path):
    (tmp_path / "tts").mkdir()
    (tmp_path / "tts" / "pronunciation-xx.json").write_text('{"rules": [{"word": "a", "ipa": " "}]}', encoding="utf-8")
    with pytest.raises(SystemExit):
        td.load_rules("xx", str(tmp_path))


def test_route_reads_the_locator_file():
    src = io.open(os.path.join(REPO, 'app', 'api', 'tts', 'route.ts'), encoding='utf-8').read()
    assert "@/tts/pronunciation-dictionaries.json" in src and "pronunciation_dictionary_locators" in src