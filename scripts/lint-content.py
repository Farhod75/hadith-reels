#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint-content.py - deterministic pre-TTS checks on generated reel text.

Encodes the defects caught by human review in P105, P111 and P115. Warn-only:
it never blocks and never edits. Every finding is a heuristic - read the line
it points at and decide. A clean run does NOT mean the text is correct; it
means these five known failure modes are absent.

USAGE
  python scripts/lint-content.py draft.txt --lang uz
  python scripts/lint-content.py draft.txt --lang tj --matn "Банда ба Парвардигораш..."

INPUT FORMAT - the same S:/M:/H:/C: blocks you already paste:

  S: story text...
  M: moral text...
  H: seerah text...
  C: caption text...

A block runs until the next label or end of file.

  --lang   en | ru | uz | tj | ar   (required)
  --matn   the hadith text from hadith_library, for the simile check.
           Without it, check 4 flags every simile marker.
"""

import argparse
import re
import sys
import unicodedata

# ---------------------------------------------------------------- config

DIVINE_NAME = {
    'en': 'Allah',
    'ru': 'Аллах',
    'uz': 'Аллоҳ',
    'tj': 'Аллоҳ',
    'ar': 'الله',
}

# Substitutes for the divine name. NOT the same as Rabb/Lord, which is a
# different word in the matn and is allowed - see ALLOWED_RABB.
DIVINE_SUBSTITUTES = {
    'en': [r'\bGod\b', r"\bGod's\b"],
    'ru': [r'\bБог\b', r'\bБога\b', r'\bБогу\b', r'\bБогом\b', r'\bБоге\b'],
    'uz': [r'\bХудо\b', r'\bХудога\b', r'\bХудони\b', r'\bXudo\b'],
    'tj': [r'\bХудо\b', r'\bХудоро\b', r'\bХудованд\b'],
    'ar': [],
}

ALLOWED_RABB = {
    'en': ['Lord'],
    'ru': ['Господь', 'Господу', 'Господа', 'Господом'],
    'uz': ['Рабби', 'Раббига', 'Раббим', 'Парвардигор'],
    'tj': ['Парвардигор', 'Парвардигораш', 'Раббаш'],
    'ar': ['رب', 'ربه'],
}

# P111 / P105: appeals to unnamed scholarly authority.
UNNAMED_AUTHORITY = {
    'en': [r'\bscholars\s+(say|explain|teach|hold|note|agree)',
           r'\bthe\s+ulama\b', r'\bscholars\s+of\s+hadith\b',
           r'\bit\s+is\s+said\s+that\b', r'\bsome\s+scholars\b'],
    'ru': [r'\bУчён?ые\b', r'\bучён?ые\s+(говорят|объясняют|считают|пишут)',
           r'\bуламо\b', r'\bбогословы\b'],
    'uz': [r'\bУламолар\b', r'\bолимлар\s+(айтади|тушунтир|дейди)',
           r'\bуламо\b'],
    'tj': [r'\bОлимон\b', r'\bуламо\b', r'\bолимон\s+(мегӯянд|шарҳ)'],
    'ar': [r'العلماء'],
}

# P115: seerah titles must not appear at all unless a passage is cited -
# including in negative claims ("neither X nor Y records...").
SEERAH_TITLES = [
    'Ar-Raheeq', 'Al-Makhtum', 'Raheeq Al-Makhtum', 'Sealed Nectar',
    'Ар-Рахик', 'Аль-Махтум', 'Усва', 'Усваи', 'Хасана', 'Ҳасана',
    'Uswa', 'Hasana', 'Усва аль-Хасана', 'Сират', 'Sirah', 'Seerah',
    'Ибн Хишам', 'Ibn Hisham', 'Ибн Исхак', 'Ibn Ishaq',
]

NEGATION_NEAR_SOURCE = [
    'not', 'no ', 'neither', 'nor', 'nothing', "doesn't", 'does not',
    'не ', 'ни ', 'нет', 'без',
    'эмас', 'йўқ', 'келтирилмаган', 'кўрсатилмаган',
    'нест', 'накардааст', 'намекунад', 'сабт накард',
]

# P111 rule 14: comparisons not present in the matn.
SIMILE_MARKERS = {
    'en': [r'\blike\b', r'\bas if\b', r'\bimagine\b', r'\bit is as\b',
           r'\bsimilar to\b', r'\bjust as\b'],
    'ru': [r'\bподобно\b', r'\bсловно\b', r'\bкак будто\b', r'\bбудто\b',
           r'\bпредставь', r'\bнапоминает\b'],
    'uz': [r'\bкаби\b', r'\bкабидир\b', r'\bўхшаш\b', r'\bхудди\b',
           r'\bтасаввур қил', r'\bмисоли\b'],
    'tj': [r'\bмонанди\b', r'\bмисли\b', r'\bчун\b', r'\bҳамчун\b',
           r'\bтасаввур кун', r'\bгӯё\b'],
    'ar': [r'كأن', r'مثل'],
}

# P111 rule 15: rendering a station of closeness as lowly.
INVERSION_TERMS = {
    'en': [r'\blowest\b', r'\blowly\b', r'\bleast\b', r'\binferior\b'],
    'ru': [r'\bнизшее\b', r'\bнизшая\b', r'\bсамое низкое\b', r'\bничтожн'],
    'uz': [r'\bпастки\b', r'\bэng паст\b', r'\bқуйи даража'],
    'tj': [r'\bпоинтарин\b', r'\bпасттарин\b', r'\bкамтарин\b'],
    'ar': [],
}

BLOCK_NAMES = {'S': 'STORY', 'M': 'MORAL', 'H': 'SEERAH', 'C': 'CAPTION'}

# ---------------------------------------------------------------- helpers


class Finding:
    def __init__(self, level, check, block, line_no, line, note):
        self.level = level
        self.check = check
        self.block = block
        self.line_no = line_no
        self.line = line.strip()
        self.note = note


def parse_blocks(text):
    """Split S:/M:/H:/C: labelled text into blocks, keeping line numbers."""
    blocks = {}
    current = None
    for i, raw in enumerate(text.splitlines(), start=1):
        m = re.match(r'^\s*([SMHC])\s*:\s*(.*)$', raw)
        if m:
            current = m.group(1)
            blocks.setdefault(current, []).append((i, m.group(2)))
        elif current:
            blocks[current].append((i, raw))
    return blocks


def sentences(line):
    """Rough sentence split that works across Latin and Cyrillic."""
    return [s for s in re.split(r'(?<=[.!?。])\s+', line) if s.strip()]


def scan(blocks, patterns, level, check, note, flags=re.IGNORECASE):
    out = []
    for key, lines in blocks.items():
        for line_no, line in lines:
            for pat in patterns:
                if re.search(pat, line, flags):
                    out.append(Finding(level, check, BLOCK_NAMES[key],
                                       line_no, line, note))
                    break
    return out


def normalise(s):
    """Casefold + strip diacritics for loose matn comparison."""
    s = unicodedata.normalize('NFKD', s.casefold())
    return ''.join(c for c in s if not unicodedata.combining(c))


# ---------------------------------------------------------------- checks


def check_divine_name(blocks, lang):
    subs = DIVINE_SUBSTITUTES.get(lang, [])
    if not subs:
        return []
    correct = DIVINE_NAME[lang]
    allowed = ', '.join(ALLOWED_RABB.get(lang, []))
    note = (f'substitute for the divine name - use "{correct}". '
            f'(Rabb/Lord IS allowed where the matn says it: {allowed})')
    return scan(blocks, subs, 'FAIL', 'divine-name', note, flags=0)


def check_unnamed_authority(blocks, lang):
    pats = UNNAMED_AUTHORITY.get(lang, [])
    note = ('appeal to unnamed authority (P111/P105) - state the meaning '
            'directly, with no speaker, or name and verify a real source')
    return scan(blocks, pats, 'FAIL', 'unnamed-authority', note)


def check_seerah_source(blocks):
    """P115: a seerah title may not appear unless a passage is cited -
    including inside a negative claim."""
    out = []
    for key, lines in blocks.items():
        for line_no, line in lines:
            for title in SEERAH_TITLES:
                if title.lower() in line.lower():
                    negated = any(n in line.lower()
                                  for n in NEGATION_NEAR_SOURCE)
                    if negated:
                        note = ('P115: seerah source named in a NEGATIVE '
                                'claim - implies you consulted it. Say '
                                'nothing about sources at all.')
                        lvl = 'FAIL'
                    else:
                        note = ('seerah source named - confirm a specific '
                                'documented passage about THIS hadith is '
                                'actually being cited')
                        lvl = 'WARN'
                    out.append(Finding(lvl, 'seerah-source',
                                       BLOCK_NAMES[key], line_no, line, note))
                    break
    return out


def check_simile(blocks, lang, matn):
    """P111 rule 14: comparisons not in the matn."""
    pats = SIMILE_MARKERS.get(lang, [])
    matn_n = normalise(matn) if matn else None
    out = []
    for key, lines in blocks.items():
        for line_no, line in lines:
            for sent in sentences(line):
                hit = None
                for pat in pats:
                    if re.search(pat, sent, re.IGNORECASE):
                        hit = pat
                        break
                if not hit:
                    continue
                if matn_n:
                    # the matn's OWN comparison is fine - if the sentence
                    # shares substantial vocabulary with the matn, downgrade.
                    words = [w for w in re.findall(r'\w{5,}', normalise(sent))]
                    shared = sum(1 for w in words if w in matn_n)
                    if words and shared >= 2:
                        lvl, note = ('INFO',
                                     'comparison appears to come from the '
                                     'matn itself - verify, then ignore')
                    else:
                        lvl, note = ('WARN',
                                     'P111 r14: comparison NOT found in the '
                                     'matn - inventing what something is '
                                     'LIKE is fabrication')
                else:
                    lvl, note = ('WARN',
                                 'simile marker - pass --matn to check it '
                                 'against the hadith text')
                out.append(Finding(lvl, 'simile', BLOCK_NAMES[key],
                                   line_no, sent, note))
    return out


def check_inversion(blocks, lang):
    pats = INVERSION_TERMS.get(lang, [])
    note = ('P111 r15: possible meaning inversion - if the hadith describes '
            'closeness, honour or elevation, do not render it as lowly')
    return scan(blocks, pats, 'WARN', 'inversion', note)


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(
        description='Deterministic pre-TTS checks on generated reel text.')
    ap.add_argument('file', help='text file with S:/M:/H:/C: blocks')
    ap.add_argument('--lang', required=True,
                    choices=['en', 'ru', 'uz', 'tj', 'ar'])
    ap.add_argument('--matn', default='',
                    help='hadith text from hadith_library (simile check)')
    args = ap.parse_args()

    try:
        with open(args.file, encoding='utf-8') as fh:
            text = fh.read()
    except FileNotFoundError:
        print(f'FAILED: no such file: {args.file}')
        return 2
    except UnicodeDecodeError:
        print(f'FAILED: {args.file} is not UTF-8. Re-save it as UTF-8.')
        return 2

    blocks = parse_blocks(text)
    if not blocks:
        print('FAILED: no S:/M:/H:/C: blocks found. Check the input format.')
        return 2

    missing = [k for k in 'SMHC' if k not in blocks]

    findings = []
    findings += check_divine_name(blocks, args.lang)
    findings += check_unnamed_authority(blocks, args.lang)
    findings += check_seerah_source(blocks)
    findings += check_simile(blocks, args.lang, args.matn)
    findings += check_inversion(blocks, args.lang)

    order = {'FAIL': 0, 'WARN': 1, 'INFO': 2}
    findings.sort(key=lambda f: (order[f.level], f.line_no))

    width = 64
    print()
    print('=' * width)
    print(f' content lint - {args.file}  (lang: {args.lang})')
    print('=' * width)

    if missing:
        print(f'  note: no {", ".join(missing)} block(s) in this file')

    if not findings:
        print('  no findings.')
    else:
        for f in findings:
            print()
            print(f'  [{f.level}] {f.check}  -  {f.block}, line {f.line_no}')
            print(f'    {f.line[:150]}')
            print(f'    -> {f.note}')

    counts = {lvl: sum(1 for f in findings if f.level == lvl)
              for lvl in ('FAIL', 'WARN', 'INFO')}
    print()
    print('-' * width)
    print(f"  {counts['FAIL']} fail   {counts['WARN']} warn   "
          f"{counts['INFO']} info")
    if not args.matn:
        print('  (no --matn given; simile findings are unverified)')
    print('  warn-only: nothing was blocked or changed. Human review still')
    print('  decides - a clean run only means these five checks passed.')
    print('-' * width)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())