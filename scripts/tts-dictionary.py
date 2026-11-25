"""tts-dictionary.py - P441: sync tts/pronunciation-<lang>.json to an ElevenLabs pronunciation dictionary.

  python scripts/tts-dictionary.py --lang tj            # dry run: shows the rules and whether the dictionary is current
  python scripts/tts-dictionary.py --lang tj --apply    # creates a new dictionary when the rules changed

/api/tts reads tts/pronunciation-dictionaries.json and sends the language's locator with every
request, so the stored text, the subtitles and the library never change (P095 holds). A new
dictionary is created per rule change (name hr-<lang>-<sha6>); the old one is left in the account.
The API key needs Pronunciation Dictionaries: Write.
"""
import argparse
import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCATORS = os.path.join(REPO, 'tts', 'pronunciation-dictionaries.json')


def load_rules(lang, repo=REPO):
    p = os.path.join(repo, 'tts', 'pronunciation-%s.json' % lang)
    rules = json.load(io.open(p, encoding='utf-8'))['rules']
    for r in rules:
        if not r.get('word', '').strip() or not r.get('ipa', '').strip():
            raise SystemExit('%s: a rule without word or ipa: %r' % (p, r))
    return rules


def api_rules(rules):
    """Both casings: a word that opens a sentence is capitalised (P284 broke exactly there)."""
    out, seen = [], set()
    for r in rules:
        w = r['word'].strip()
        for form in (w.lower(), w[:1].upper() + w[1:].lower()):
            if form not in seen:
                seen.add(form)
                out.append({'type': 'phoneme', 'string_to_replace': form, 'phoneme': r['ipa'].strip(), 'alphabet': 'ipa'})
    return out


def rules_sha(rules):
    return hashlib.sha256(json.dumps(api_rules(rules), ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def load_locators(path=LOCATORS):
    return json.load(io.open(path, encoding='utf-8')) if os.path.exists(path) else {}


def api_key(repo=REPO):
    for line in io.open(os.path.join(repo, '.env.local'), encoding='utf-8'):
        line = line.strip()
        if line.startswith('ELEVENLABS_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    raise SystemExit('ELEVENLABS_API_KEY not in .env.local')


def create(lang, rules, sha):
    body = json.dumps({'name': 'hr-%s-%s' % (lang, sha[:6]), 'rules': api_rules(rules)}).encode('utf-8')
    req = urllib.request.Request('https://api.elevenlabs.io/v1/pronunciation-dictionaries/add-from-rules', data=body,
                                 headers={'xi-api-key': api_key(), 'Content-Type': 'application/json'})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        raise SystemExit('ElevenLabs %s: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300]))
    return {'id': r['id'], 'version_id': r['version_id'], 'rules_sha': sha}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', required=True)
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    rules = load_rules(a.lang)
    sha = rules_sha(rules)
    locs = load_locators()
    for r in rules:
        print('  %s -> /%s/' % (r['word'], r['ipa']))
    if locs.get(a.lang, {}).get('rules_sha') == sha:
        print('%s: dictionary current (%s)' % (a.lang, locs[a.lang]['id']))
        return 0
    if not a.apply:
        print('%s: rules changed - run with --apply' % a.lang)
        return 1
    locs[a.lang] = create(a.lang, rules, sha)
    io.open(LOCATORS, 'w', encoding='utf-8', newline='\n').write(json.dumps(locs, indent=2, sort_keys=True) + '\n')
    print('%s: created %s' % (a.lang, locs[a.lang]['id']))
    return 0


if __name__ == '__main__':
    sys.exit(main())