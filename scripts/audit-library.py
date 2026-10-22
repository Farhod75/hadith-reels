#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit-library.py - deterministic per-language checks over hadith_library.

Sibling to lint-content.py, but a different target. lint-content.py reads
draft.txt (GENERATED reel text) and catches what the generator does wrong.
This reads the LIBRARY and catches what the source rows have wrong - defects
that exist upstream of any reel and survive into every reel made from them.

Grounding cases:
  - P050  text_tajik held a Russian fallback. Undetectable at reel time,
          because the generator paraphrases; the DB sentence never appears
          verbatim in draft.txt.
  - R037  text_tajik read «Неки» where Tajik requires «Некӣ» (U+04E3).
          Caught by a human reading it, after the kids reel was produced.
  - R039  text_russian «Аллахом» where the sentence wanted «Аллаху».
  - R024  caption pulled Latin text_uzbek into a Cyrillic body (5 occurrences).
  - R027  Latin homoglyphs inside Cyrillic words, invisible on screen.

READ-ONLY. Never writes, never edits. Warn-only by default; --strict makes
HIGH findings exit non-zero so it can be used as a gate.

A clean run does NOT mean the library is correct. It means these checks
found nothing.

USAGE
  python scripts/audit-library.py                 # audit hadith_library
  python scripts/audit-library.py --table hadith_candidates
  python scripts/audit-library.py --row 527       # one hadith_number
  python scripts/audit-library.py --lang tj       # one language's checks
  python scripts/audit-library.py --strict        # exit 1 on any HIGH

Requires SUPABASE URL + service-role key in .env.local (same as
promote-candidates.py).
"""

import argparse
import difflib
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------- config

URL_KEYS = ('NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_URL')
SERVICE_KEYS = ('SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_KEY',
                'SERVICE_ROLE_KEY', 'SUPABASE_KEY')

# Letters that exist in Tajik Cyrillic and not in Russian Cyrillic.
TJ_LETTERS = 'ӣӯҳқғҷӢӮҲҚҒҶ'

# P050: a Tajik column that is really the Russian one. Genuine translations
# share loanwords and Cyrillic, so they score well below this; a copy scores
# at or near 1.0. Measured against the live library: the four zero-diacritic
# rows (Muslim 82, Tirmidhi 2396, Abu Dawud 1479, Bayhaqi 2318) are all
# genuine Tajik and score far under it.
TJ_RU_SIMILARITY_HIGH = 0.85

# Below this many characters, absence of Tajik-specific letters is not
# evidence of anything - short sentences legitimately use only shared
# Cyrillic. Set from the live library as it stood in August, where every row
# above 52 chars carried at least one Tajik letter. Tirmidhi #1899 is the
# first exception: 85 characters, no Tajik letter, and correct — every х in
# it is etymologically х (хушнудӣ, хашм, both from Persian خ), and izofat
# turns the ӣ of хушнудӣ into и. The threshold stays; this check is INFO
# precisely because it points at rows to read, not rows that are wrong.
TJ_DIACRITIC_MIN_LEN = 60

# G4: the okina in oʻ / gʻ is U+02BB MODIFIER LETTER TURNED COMMA.
OKINA = '\u02bb'
OKINA_WRONG = {
    '\u0027': "ASCII apostrophe '",
    '\u2018': 'left single quote \u2018',
    '\u2019': 'right single quote \u2019',
    '\u0060': 'grave accent `',
    '\u00b4': 'acute accent \u00b4',
    '\u02bc': 'modifier apostrophe \u02bc',
}

# The honorific and divine-name formulas, in their WRONG spelling and their
# right one. Uzbek and Tajik both write ҳ (U+04B3) where Russian writes х, and
# the two are visually close enough that a Russian keyboard, a Russian source
# text, or a model trained on more Russian than Uzbek produces х silently.
#
# This is deliberately a CLOSED LIST, not a rule about ҳ in general: Tajik
# legitimately uses х in ordinary words (хуб, хона, хонадон) and flagging the
# letter would bury the real findings. These formulas are fixed phrases, so
# they can be matched literally and a hit is a hit.
#
# text_russian is NOT checked — «Аллах» is correct Russian convention. Only
# the Uzbek Cyrillic and Tajik columns.
#
# Ordered longest-first within each family so the regex alternation matches
# the longest form at each position and does not double-report (анҳумо would
# otherwise also match as анҳу).
HA_FORMULAS = [
    ('субханаху',   'субҳанаҳу'),
    ('расулуллох',  'расулуллоҳ'),
    ('алхамдулиллах', 'алҳамдулиллаҳ'),
    ('иншааллах',   'иншааллоҳ'),
    ('алайхиссалом', 'алайҳиссалом'),
    ('алайхи',      'алайҳи'),
    ('анхумо',      'анҳумо'),
    ('анхом',       'анҳом'),
    ('анхо',        'анҳо'),
    ('анху',        'анҳу'),
    ('аллаху',      'аллоҳу'),
    ('аллах',       'аллоҳ'),
    ('ллоху',       'ллоҳу'),
]
HA_RE = re.compile('|'.join(re.escape(w) for w, _ in HA_FORMULAS), re.IGNORECASE)
HA_FIX = {w: r for w, r in HA_FORMULAS}

HA_FIELDS = ('text_uzbek_cyrillic', 'text_tajik')

# Latin characters that render identically to a Cyrillic letter.
HOMOGLYPHS = {
    'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х', 'y': 'у',
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К', 'M': 'М',
    'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х', 'Y': 'У',
}

CYRILLIC_FIELDS = {
    'text_russian': 'ru',
    'text_uzbek_cyrillic': 'uz',
    'text_tajik': 'tj',
}

# P262: the alphabet each Cyrillic column is allowed to use. A letter can be
# perfectly good Cyrillic and still be wrong for the language - Uzbek writes ў
# (U+045E), Tajik writes ӯ (U+04EF), and on screen they are the same shape.
# HOMOGLYPHS above only catches LATIN intruders; TJ_LETTERS only checks that
# Tajik letters are PRESENT. A Cyrillic letter from the wrong alphabet passes
# both, which is how ү (U+04AF) was nearly written into #1894's Tajik.
ALPHABETS = {
    'ru': set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя'),
    'uz': set('абвгдеёжзийклмнопрстуфхцчшъьэюяўқғҳ'),
    'tj': set('абвгдеёжзийклмнопрстуфхчшъэюяғӣқӯҳҷ'),
}

# P268: tokens that cannot exist in Uzbek or Tajik Cyrillic. Every rule here is
# an orthographic impossibility, not a judgement about wording - which is why
# each one can run at WARN with no dictionary and no model call behind it.
#
# Found by reading a derive-uzbek-latin.ts log, not by any check: six malformed
# tokens sat in published rows while out-of-alphabet, homoglyph and ha-formula
# all passed them, because every individual LETTER was legal. The defect was in
# how the letters were combined. A per-character check cannot see that.
MALFORMED_FIELDS = {'text_uzbek_cyrillic': 'uz', 'text_tajik': 'tj'}

# ё is already iotated; ъ (tutuq belgisi) cannot follow it. This is the
# signature of a Latin->Cyrillic round trip: yoʻq -> ёъқ instead of йўқ.
MALFORMED_YO_RE = re.compile(u'[ёЁ]ъ')

# ц belongs to Russian loanwords. In an Uzbek or Tajik matn it is nearly always
# a mistyped тс - туца for тутса.
MALFORMED_TS_RE = re.compile(u'[цЦ]')

# A personal ending is bound to its stem; a hyphen before one is a stray.
# Uzbek does hyphenate compounds (ота-она, мол-мулк), so only the endings match.
MALFORMED_HYPHEN_RE = re.compile(r'\w-(?:ман|сан|миз|сиз|дир|ди)$')

# Bound morphemes that can never stand as a free word. A space before one means
# a word was split: бандаси -> «банд аси».
MALFORMED_ORPHANS = {
    u'аси', u'иси', u'лари', u'нинг', u'дир', u'диган', u'ганда',
    u'моқда', u'ларини', u'идан', u'нидан', u'ини', u'ига', u'ида',
}

MALFORMED_STRIP = u'.,!?:;«»"()—-…'


ALL_TEXT_FIELDS = [
    'text_arabic', 'text_english', 'text_russian',
    'text_uzbek', 'text_uzbek_cyrillic', 'text_uzbek_latin', 'text_tajik',
]

VALID_GRADES = ('sahih', 'hasan')

LEVELS = ('HIGH', 'WARN', 'INFO')

# ---------------------------------------------------------------- helpers


class Finding:
    def __init__(self, level, check, ref, field, note, detail=''):
        self.level = level
        self.check = check
        self.ref = ref
        self.field = field
        self.note = note
        self.detail = detail


def load_env(path='.env.local'):
    """Minimal .env reader - no dependency on python-dotenv."""
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def pick(env, names):
    for n in names:
        if env.get(n):
            return env[n], n
        if os.environ.get(n):
            return os.environ[n], n
    return None, None


def fetch_rows(base_url, key, table, row=None):
    """PostgREST select. Read-only."""
    params = {'select': '*'}
    if row:
        params['hadith_number'] = f'eq.{row}'
    url = f'{base_url.rstrip("/")}/rest/v1/{table}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def patch_library_row(base_url, key, row_id, patch):
    """P290: write by ID. NEVER by hadith_number - it is not unique.

    #1469, #2616 and #6018 each have TWO rows carrying different hadiths, and
    check_duplicate_numbers has reported all three at INFO on every run since
    P147. A PATCH filtered on `hadith_number=eq.1469` matches both rows and
    PostgREST updates both without complaint: one correction, two rows written,
    and the second row silently acquires the first one's text.

    That happened on 2026-10-22. Recovery needed a 72-row before-snapshot taken
    for an unrelated reason, plus latinToCyrillic to rebuild a field the
    snapshot did not cover. There was no reason it had to be recoverable.

    Returns the updated row. Raises if the filter matched anything other than
    exactly one row, so a widened filter fails loudly instead of succeeding
    quietly.
    """
    if not re.match(r'^[0-9a-f-]{36}$', str(row_id or '')):
        raise ValueError('patch_library_row needs a uuid id, got %r' % (row_id,))
    url = '%s/rest/v1/hadith_library?%s' % (
        base_url.rstrip('/'), urllib.parse.urlencode({'id': 'eq.%s' % row_id}))
    req = urllib.request.Request(
        url, data=json.dumps(patch, ensure_ascii=False).encode('utf-8'),
        method='PATCH', headers={
            'apikey': key, 'Authorization': 'Bearer %s' % key,
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        rows = json.loads(resp.read().decode('utf-8'))
    if len(rows) != 1:
        raise RuntimeError(
            'PATCH on id=%s touched %d rows, expected exactly 1' % (row_id, len(rows)))
    return rows[0]


def ref_of(row):
    return f'{row.get("collection", "?")} #{row.get("hadith_number", "?")}'


def norm(s):
    """Casefold, strip diacritics and punctuation, collapse whitespace."""
    s = unicodedata.normalize('NFKD', (s or '').casefold())
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def is_cyrillic(ch):
    return '\u0400' <= ch <= '\u04ff'


# ---------------------------------------------------------------- checks


def check_tj_russian_fallback(row):
    """P050: text_tajik is a copy of text_russian, not a translation."""
    tj, ru = row.get('text_tajik'), row.get('text_russian')
    if not tj or not ru:
        return []
    score = difflib.SequenceMatcher(None, norm(tj), norm(ru)).ratio()
    if score >= TJ_RU_SIMILARITY_HIGH:
        return [Finding(
            'HIGH', 'tj-russian-fallback', ref_of(row), 'text_tajik',
            f'text_tajik is {score:.0%} identical to text_russian - this is '
            f'the P050 Russian fallback, not a Tajik translation',
            f'tj: {tj[:70]}\n          ru: {ru[:70]}')]
    return []


def check_tj_diacritics(row):
    """Tajik-specific letters absent from a passage long enough that their
    absence is implausible. INFO, not HIGH: short sentences legitimately
    use only shared Cyrillic."""
    tj = row.get('text_tajik')
    if not tj:
        return []
    if any(c in TJ_LETTERS for c in tj):
        return []
    if len(tj) < TJ_DIACRITIC_MIN_LEN:
        return []
    return [Finding(
        'INFO', 'tj-no-diacritics', ref_of(row), 'text_tajik',
        f'{len(tj)} characters with none of {TJ_LETTERS[:6]} - verify this '
        f'is Tajik and not Russian-with-Tajik-word-order',
        tj[:90])]


def check_uz_okina(row):
    """G4: oʻ / gʻ must use U+02BB, not an apostrophe or quote mark."""
    out = []
    for field in ('text_uzbek', 'text_uzbek_latin'):
        val = row.get(field)
        if not val:
            continue
        for wrong, name in OKINA_WRONG.items():
            for m in re.finditer(f'[oOgG]{re.escape(wrong)}', val):
                out.append(Finding(
                    'WARN', 'uz-okina', ref_of(row), field,
                    f'{name} used where the okina U+02BB ({OKINA}) belongs',
                    f'...{val[max(0, m.start() - 25):m.end() + 25]}...'))
                break
    return out


def check_uz_script_mixing(row):
    """The Cyrillic column holding Latin, or the Latin column holding
    Cyrillic. Source of the caption defect hit 5 times (R024, R036...)."""
    out = []
    cyr = row.get('text_uzbek_cyrillic')
    lat = row.get('text_uzbek_latin')
    if cyr:
        runs = re.findall(r'[A-Za-z]{3,}', cyr)
        if runs:
            out.append(Finding(
                'WARN', 'uz-script-mixed', ref_of(row), 'text_uzbek_cyrillic',
                f'Latin run(s) in the Cyrillic column: {", ".join(runs[:4])}',
                cyr[:90]))
    if lat:
        runs = re.findall(r'[\u0400-\u04ff]{3,}', lat)
        if runs:
            out.append(Finding(
                'WARN', 'uz-script-mixed', ref_of(row), 'text_uzbek_latin',
                f'Cyrillic run(s) in the Latin column: {", ".join(runs[:4])}',
                lat[:90]))
    return out


def check_homoglyphs(row):
    """R027: a Latin character hiding inside a Cyrillic word. Renders
    identically on screen and is invisible to human review by construction."""
    out = []
    for field, _lang in CYRILLIC_FIELDS.items():
        val = row.get(field)
        if not val:
            continue
        for word in re.findall(r'\S+', val):
            has_cyr = any(is_cyrillic(c) for c in word)
            if not has_cyr:
                continue
            bad = [c for c in word if c in HOMOGLYPHS]
            if bad:
                fixed = ''.join(HOMOGLYPHS.get(c, c) for c in word)
                out.append(Finding(
                    'HIGH', 'homoglyph', ref_of(row), field,
                    f'Latin {", ".join(repr(c) for c in bad)} inside a '
                    f'Cyrillic word - «{word}» should be «{fixed}»',
                    ''))
    return out


# P289: a parenthesis touching a word character on either side. A translator's
# gloss stands free between spaces - «... (Бомдод ва Аср) ...» - and is
# deliberately NOT matched; an embedded one is an unresolved alternate.
EMBEDDED_ALTERNATE = re.compile(r'\w\([^)]{1,40}\)|\([^)]{1,40}\)\w', re.UNICODE)


def check_out_of_alphabet(row):
    """P262: a Cyrillic letter that is not in the target language's alphabet.

    The sibling of check_homoglyphs one step further in: that one catches a
    LATIN character wearing a Cyrillic face, this one catches a CYRILLIC
    character from the wrong language. Uzbek ў (U+045E) and Tajik ӯ (U+04EF)
    are the dangerous pair - same shape, different codepoint, and the two
    columns sit next to each other in every row.

    Found by writing the defect: a hand-edit to #1894's Tajik typed ү (U+04AF,
    the straight u of Kazakh and Mongolian) for ӯ. The surrounding sentence was
    full of correct Tajik letters, so the diacritics check passed it, and the
    letter is not Latin, so the homoglyph check passed it too. Only reading the
    output back caught it.

    WARN, not HIGH, on its first outing - the same reasoning as check_ha_formulas.
    The alphabets above are hand-written, and a missing legitimate letter would
    block every push under --strict. A library-wide scan on 2026-10-17 returned
    zero findings across 72 rows, so raise this to HIGH once it has run clean
    for a while.
    """
    out = []
    for field, lang in CYRILLIC_FIELDS.items():
        allowed = ALPHABETS.get(lang)
        val = row.get(field)
        if not allowed or not val:
            continue
        bad = {}
        for ch in val:
            if is_cyrillic(ch) and ch.lower() not in allowed:
                bad[ch] = bad.get(ch, 0) + 1
        for ch, n in sorted(bad.items()):
            word = next((w for w in re.findall(r'\S+', val) if ch in w), '')
            out.append(Finding(
                'WARN', 'out-of-alphabet', ref_of(row), field,
                f'{ch!r} (U+{ord(ch):04X}) is not in the {lang} alphabet '
                f'- {n} occurrence(s), e.g. «{word}»',
                ''))
    return out


def check_malformed_tokens(row):
    """P268: a token whose letters are each legal but whose shape is not.

    The sibling of check_out_of_alphabet one level up: that one asks whether a
    CHARACTER belongs to the language, this one asks whether a SEQUENCE could
    occur in it. «ёъқ» is built entirely from letters in the Uzbek alphabet, so
    every character-level check waved it through; it is still not a word.

    All four rules are orthographic impossibilities rather than style, so they
    need no dictionary. Measured against the whole library before being written
    here: 6 hits across 72 rows, all 6 real, no false positives. A fifth rule
    (ъ word-initial) returned 0 and was dropped rather than shipped unexercised.

    WARN on its first outing, the same reasoning as check_ha_formulas and
    check_out_of_alphabet: promote to HIGH once a pass has been adjudicated.
    """
    out = []
    for field, lang in MALFORMED_FIELDS.items():
        val = row.get(field)
        if not val:
            continue
        for raw in re.findall(r'\S+', val):
            w = raw.strip(MALFORMED_STRIP)
            if not w:
                continue
            why = None
            if MALFORMED_YO_RE.search(w):
                why = (u'ёъ cannot occur - ё is already iotated and ъ cannot follow '
                       u'it; this is a Latin->Cyrillic round trip of yoʻ')
            elif MALFORMED_TS_RE.search(w):
                why = (u'ц belongs to Russian loanwords - in a matn it is almost '
                       u'always a mistyped тс')
            elif MALFORMED_HYPHEN_RE.search(w):
                why = u'a personal ending is bound to its stem; the hyphen is stray'
            elif w.lower() in MALFORMED_ORPHANS:
                why = (u'a bound morpheme standing alone - the preceding word was '
                       u'split by a stray space')
            if why:
                out.append(Finding(
                    'WARN', 'malformed-token', ref_of(row), field,
                    u'«%s» is not a possible %s token - %s' % (raw, lang, why),
                    ''))
    return out


def check_embedded_alternate(row):
    """P289: a parenthetical alternate wedged inside a word.

    «марг(мург)ро» sat in #2307's Tajik - "death(bird)" - and «Мен(га)» and
    «сабр(дан)» sit in #3540's and #1469's Uzbek, in BOTH scripts. Each is an
    editor in two minds, or a suffix the translator could not settle, left in a
    field that is quoted verbatim into captions and narrated aloud.

    A FREE-STANDING parenthetical is a different thing and is deliberately NOT
    flagged: «(Бомдод ва Аср)» on #574, "Dua (supplication)" on #1479 and
    «(бегуноҳ)» on #1521 are translator's glosses, which this project has always
    allowed.

    The distinction is mechanical - a parenthesis touching a word character on
    either side is embedded, one standing between spaces is a gloss - and a
    library-wide scan on 2026-10-22 separated them cleanly: 13 fields contain a
    parenthesis, 5 of those are embedded, all 5 are defects, and none of the
    other 8 is.

    Found because #2307's row passed audit-library at 0 findings while carrying
    three separate defects. WARN rather than HIGH on its first outing, the same
    reasoning as check_out_of_alphabet.
    """
    out = []
    for field in ALL_TEXT_FIELDS:
        val = row.get(field)
        if not val or '(' not in val:
            continue
        for m in EMBEDDED_ALTERNATE.finditer(val):
            frag = m.group(0)
            word = next((w for w in re.findall(r'\S+', val) if frag in w), frag)
            out.append(Finding(
                'WARN', 'embedded-alternate', ref_of(row), field,
                f'a parenthetical is wedged inside a word - «{word}». A gloss '
                f'stands free between spaces; this is an unresolved alternate, '
                f'and the field is quoted into captions and narrated aloud',
                ''))
    return out


def check_ha_formulas(row):
    """х where ҳ belongs, inside the fixed honorific and divine-name formulas.

    The sibling of check_homoglyphs: both are a wrong character that survives
    human review because it reads almost right. The difference is that a
    homoglyph is invisible by construction, while «Аллах» in an Uzbek sentence
    is merely easy to skim past — and it reaches the viewer either way.

    WARN rather than HIGH on its first outing: this check has never run, and
    an unproven check at HIGH would block pushes under --strict on findings
    nobody has reviewed yet. Promote it once the first pass is adjudicated.
    """
    out = []
    for field in HA_FIELDS:
        val = row.get(field)
        if not val:
            continue
        seen = set()
        for m in HA_RE.finditer(val):
            got = m.group(0)
            low = got.lower()
            if low in seen:
                continue
            seen.add(low)
            out.append(Finding(
                'WARN', 'ha-formula', ref_of(row), field,
                f'«{got}» should be «{HA_FIX[low]}» - Russian х where Uzbek '
                f'and Tajik take ҳ (U+04B3)',
                f'...{val[max(0, m.start() - 30):m.end() + 30]}...'))
    return out


def check_missing_translations(row):
    """Which languages this row cannot serve."""
    missing = [f for f in ('text_english', 'text_russian', 'text_tajik')
               if not (row.get(f) or '').strip()]
    if not (row.get('text_uzbek_cyrillic') or row.get('text_uzbek') or '').strip():
        missing.append('text_uzbek_cyrillic')
    if not missing:
        return []
    return [Finding(
        'INFO', 'missing-translation', ref_of(row), ', '.join(missing),
        f'{len(missing)} language field(s) empty - this row cannot produce '
        f'a full 4-language set', '')]


def check_grade(row):
    g = (row.get('grade') or '').strip().lower()
    if g in VALID_GRADES:
        return []
    return [Finding(
        'HIGH', 'grade', ref_of(row), 'grade',
        f'grade is {g!r} - only {"/".join(VALID_GRADES)} may be published', '')]


def check_source(row):
    url = (row.get('source_url') or '').strip()
    if not url:
        # hadith_candidates stores deep-links as source_urls (jsonb, plural)
        urls = row.get('source_urls') or {}
        if isinstance(urls, dict):
            for k in ('dorar', 'sunnah', 'hadeethenc'):
                if urls.get(k):
                    url = str(urls[k]).strip()
                    break
    if not url:
        return [Finding('WARN', 'source', ref_of(row), 'source_url',
                        'no source URL - the project requires deep-links', '')]
    if re.match(r'^https?://[^/]+/?$', url):
        return [Finding('WARN', 'source', ref_of(row), 'source_url',
                        'homepage, not a deep-link to this hadith', url)]
    return []



# ---------------------------------------------------------- cross-row checks
# Every check above looks at ONE row. These two compare rows against each
# other, which is where the duplicate-selection risk actually lives, and run
# once after the per-row pass rather than from CHECKS.


def documented_collisions(path='reel-tracker.md'):
    """Hadith numbers the duplicate-check index already records as colliding.

    A collision nobody has written down must block a push: it is a live
    selection hazard and the next set could walk into it. One that IS written
    down has been decided about, and blocking on it forever would turn the
    gate into noise that gets bypassed - which is how gates stop being read.
    So the acknowledgement is load-bearing: write the row, and the HIGH drops
    to INFO. Remove the row and it comes back.
    """
    try:
        with open(path, encoding='utf-8-sig') as fh:
            text = fh.read()
    except OSError:
        return set()  # no tracker reachable - everything stays HIGH
    out = set()
    for line in text.split('\n'):
        if not line.startswith('|'):
            continue
        low = line.lower()
        if 'two rows under this number' in low or 'same number, different hadith' in low:
            m = re.search(r'#\s*(\d+)', line)
            if m:
                out.add(m.group(1))
    return out

def matn_of(row):
    """The comparable text of a row: Arabic if present, else English."""
    return norm(row.get('text_arabic') or row.get('text_english') or '')


def _overlap(a, b):
    """Jaccard over word sets. Crude on purpose - this flags for a human."""
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def check_duplicate_numbers(rows):
    """P147: hadith_number is NOT unique, and the duplicate index keys on it.

    The tracker's duplicate-check index is keyed on the number, so a second
    row under a used number reads as 'already produced' and is skipped, or as
    'this one' and is produced in place of the one that was checked.
    """
    known = documented_collisions()
    by_num = {}
    for r in rows:
        by_num.setdefault(str(r.get('hadith_number', '')).strip(), []).append(r)
    out = []
    for num, group in sorted(by_num.items()):
        if len(group) < 2 or not num:
            continue
        texts = [matn_of(r) for r in group]
        same = all(_overlap(texts[0], t) > 0.9 for t in texts[1:])
        cols = ' / '.join(sorted({str(r.get('collection', '?')) for r in group}))
        if same:
            out.append(Finding(
                'WARN', 'duplicate-number', '#' + num, 'hadith_number',
                '%d rows share this number with the SAME wording (%s) - '
                'a redundant row, pick one' % (len(group), cols), ''))
        elif num in known:
            out.append(Finding(
                'INFO', 'duplicate-number', '#' + num, 'hadith_number',
                '%d rows share this number (%s) - already recorded in the '
                "tracker's duplicate-check index; match the wording, not the "
                'number, when selecting' % (len(group), cols), ''))
        else:
            out.append(Finding(
                'HIGH', 'duplicate-number', '#' + num, 'hadith_number',
                '%d rows share this number with DIFFERENT wording (%s) and it '
                'is NOT in the duplicate-check index - the index keys on the '
                'number, so one can ship believing the other was checked. '
                'Add a row to the index, then this drops to INFO (P147)'
                % (len(group), cols), ''))
    return out


# check_twin_wording was written here on 2026-10-09 and REMOVED the same day.
# The case it existed for is Bukhari #2654 and #6871 - the duplicate index
# keys on the number, so #6871 can be produced after #2654 with nothing
# noticing. Measured against the real rows: Jaccard on the matn scores that
# pair at 0.16, and the highest cross-number Jaccard anywhere in the 70 rows
# is 0.29, so any threshold that fires is a threshold that fires on
# everything. Containment (shared words over the shorter text) scores the
# pair at 0.56 - but two unrelated pairs score 0.60 and twelve score 0.50 or
# better, because short rows inflate containment. There is no cut that
# separates them.
#
# The relationship is SEMANTIC - both narrations are about al-kaba'ir - and
# not lexical. A similarity score cannot see that, and a check that never
# fires is worse than no check: it reads as coverage. Recorded instead as an
# explicit row in the tracker's duplicate-check index, which is where the
# #6018 collision already lives (P205).

CROSS_ROW_CHECKS = [check_duplicate_numbers]


CHECKS = [
    ('tj', check_tj_russian_fallback),
    ('tj', check_tj_diacritics),
    ('uz', check_uz_okina),
    ('uz', check_uz_script_mixing),
    (None, check_homoglyphs),
    (None, check_out_of_alphabet),
    (None, check_malformed_tokens),
    (None, check_embedded_alternate),
    (None, check_ha_formulas),
    (None, check_missing_translations),
    (None, check_grade),
    (None, check_source),
]

# ---------------------------------------------------------------- report


def report(findings, n_rows, table, strict):
    width = 74
    print('=' * width)
    print(f' library audit - {table}  ({n_rows} rows)')
    print('=' * width)

    if not findings:
        print('  no findings.')
    else:
        order = {l: i for i, l in enumerate(LEVELS)}
        findings.sort(key=lambda f: (order[f.level], f.check, f.ref))
        for f in findings:
            print(f'  [{f.level}] {f.check}  -  {f.ref}  ({f.field})')
            print(f'    -> {f.note}')
            if f.detail:
                for line in f.detail.splitlines():
                    print(f'       {line}')
            print()

    counts = {l: sum(1 for f in findings if f.level == l) for l in LEVELS}
    print('-' * width)
    print(f'  {counts["HIGH"]} high   {counts["WARN"]} warn   '
          f'{counts["INFO"]} info')
    if strict:
        print('  strict: HIGH findings exit non-zero.')
    else:
        print('  read-only, warn-only: nothing was changed. A clean run means')
        print('  these checks passed, NOT that the library is correct.')
    print('-' * width)

    return 1 if (strict and counts['HIGH']) else 0


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(
        description='Deterministic per-language checks over hadith_library.')
    ap.add_argument('--table', default='hadith_library',
                    choices=['hadith_library', 'hadith_candidates'])
    ap.add_argument('--row', help='audit one hadith_number only')
    ap.add_argument('--lang', choices=['ru', 'uz', 'tj'],
                    help='run only this language\'s checks')
    ap.add_argument('--strict', action='store_true',
                    help='exit 1 if any HIGH finding')
    args = ap.parse_args()

    env = load_env()
    base_url, url_name = pick(env, URL_KEYS)
    key, key_name = pick(env, SERVICE_KEYS)

    if not base_url or not key:
        print('FAILED: need a Supabase URL and service-role key in .env.local')
        print(f'  looked for URL in: {", ".join(URL_KEYS)}')
        print(f'  looked for key in: {", ".join(SERVICE_KEYS)}')
        return 2

    try:
        rows = fetch_rows(base_url, key, args.table, args.row)
    except urllib.error.HTTPError as e:
        print(f'FAILED: {e.code} {e.reason} reading {args.table}')
        print(f'  (using {url_name} + {key_name})')
        return 2
    except Exception as e:  # noqa: BLE001
        print(f'FAILED: {e}')
        return 2

    if not rows:
        print(f'no rows in {args.table}'
              + (f' for hadith_number={args.row}' if args.row else ''))
        return 0

    findings = []
    for row in rows:
        for lang, fn in CHECKS:
            if args.lang and lang and lang != args.lang:
                continue
            findings.extend(fn(row))

    # Cross-row checks need the whole table, so they are skipped when --row
    # narrowed the fetch to one hadith - a single row cannot collide.
    if not args.row:
        for xfn in CROSS_ROW_CHECKS:
            findings.extend(xfn(rows))

    return report(findings, len(rows), args.table, args.strict)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
