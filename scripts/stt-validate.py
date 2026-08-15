#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stt-validate.py - diff a Whisper-generated .srt against the narration text it
was transcribed from.

This is NOT blind speech-to-text validation. The source text is known exactly -
it is what the human approved in the admin - so the primary method is word-level
alignment, not similarity scoring.

Grounding case (R027, Abu Dawud #3641 RU): narration said "благороднейших
деяний"; Whisper produced "благороднейших в Диянии" - a common noun split into a
preposition plus a capitalised non-word that reads as a proper noun. Whole-text
similarity rates that ~0.97 and passes it. Alignment flags it immediately.

Warn-only. Never edits the SRT. The human gate in render-reel.ps1 still decides.

USAGE
  python scripts/stt-validate.py --srt out\\work\\adults\\<slug>\\ru\\...-narration.srt \\
                                 --source draft.txt --lang ru \\
                                 [--narration ...-narration.mp3]

  --srt        the generated .srt
  --source     draft.txt (S:/M:/H:/C: blocks; only S and M are narrated)
  --lang       en | ru | ar   (uz/tj skip subtitles per P078)
  --narration  optional .mp3, for the duration check (needs ffprobe)
"""

import argparse
import difflib
import re
import subprocess
import sys
import unicodedata

SUB_LANGS = {'en', 'ru', 'ar'}          # P078
MIN_CUE_SEC = 0.3
AUDIO_TOLERANCE_SEC = 0.5
SIM_WARN = 0.90
SIM_DIVERGED = 0.75

# Known proper nouns that legitimately appear in transcripts but may not appear
# verbatim in the source (declined forms, transliterations). Extend as needed -
# this is references/proper-nouns.md in the SKILL spec.
KNOWN_PROPER = {
    'аллах', 'аллаха', 'аллаху', 'аллахом', 'аллахе',
    'пророк', 'пророка', 'пророку', 'хадис', 'хадиса', 'хадисе',
    'муслим', 'муслима', 'бухари', 'дауд', 'дауда', 'довуд',
    'абу', 'дарда', 'дардо', 'хурайра', 'хурайры', 'сунан', 'сахих',
    'ильм', 'ильму', 'ильма', 'сунна', 'сунны',
    'allah', 'prophet', 'hadith', 'muslim', 'bukhari', 'dawud',
    'darda', 'hurairah', 'sunan', 'sahih', 'ilm', 'sunnah', 'sujud',
    'ra', 'pbuh',
    '\u0001pbuh\u0001',
}

SEV = {'high': 0, 'medium': 1, 'info': 2}

# cleanForTTS() replaces the Prophet symbol with spoken words BEFORE the audio
# is made, so Whisper transcribes the words. The source still holds the symbol.
# Expand the source the same way before aligning, or every word of the phrase
# reads as an unknown word.
PROPHET_SPOKEN = {
    'ru': 'да благословит его Аллах и приветствует',
    'en': 'peace be upon him',
    'ar': 'صلى الله عليه وسلم',
    'uz': 'Саллаллоҳу алайҳи васаллам',
    'tj': 'Салаллоҳу алайҳи васаллам',
}
PROPHET_SYMBOLS = ['\ufdfa', 'ﷺ', 'صلى الله عليه وسلم']


class Finding:
    def __init__(self, severity, code, note, cue=None, line_no=None,
                 srt_text='', source_text=''):
        self.severity = severity
        self.code = code
        self.note = note
        self.cue = cue
        self.line_no = line_no
        self.srt_text = srt_text
        self.source_text = source_text


# ------------------------------------------------------------------ parsing

TS = re.compile(
    r'^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*'
    r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})')


def to_sec(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_srt(path):
    """Return (cues, findings). Each cue: index, start, end, text, line_no."""
    findings = []
    with open(path, encoding='utf-8-sig') as fh:
        lines = fh.read().splitlines()

    cues, i, n = [], 0, len(lines)
    while i < n:
        while i < n and not lines[i].strip():
            i += 1
        if i >= n:
            break
        idx_line_no = i + 1
        idx_raw = lines[i].strip()
        if not idx_raw.isdigit():
            findings.append(Finding(
                'high', 'srt_malformed',
                f'expected a cue number, found: {idx_raw[:40]!r}',
                line_no=idx_line_no))
            i += 1
            continue
        i += 1
        if i >= n:
            findings.append(Finding('high', 'srt_malformed',
                                    'file ends after a cue number',
                                    line_no=idx_line_no))
            break
        m = TS.match(lines[i].strip())
        if not m:
            findings.append(Finding(
                'high', 'srt_malformed',
                f'bad timestamp line: {lines[i].strip()[:60]!r}',
                cue=int(idx_raw), line_no=i + 1))
            i += 1
            continue
        start = to_sec(*m.groups()[:4])
        end = to_sec(*m.groups()[4:])
        i += 1
        text_lines, first_text_line = [], i + 1
        while i < n and lines[i].strip():
            text_lines.append(lines[i].strip())
            i += 1
        text = ' '.join(text_lines)
        if not text:
            findings.append(Finding('high', 'srt_malformed',
                                    'cue has no text',
                                    cue=int(idx_raw), line_no=first_text_line))
        cues.append({'index': int(idx_raw), 'start': start, 'end': end,
                     'text': text, 'line_no': first_text_line})
    return cues, findings


def parse_source(path):
    """Return the narrated text: S and M blocks only (H is not narrated)."""
    with open(path, encoding='utf-8-sig') as fh:
        text = fh.read()
    blocks, current = {}, None
    for raw in text.splitlines():
        m = re.match(r'^\s*([SMHC])\s*:\s*(.*)$', raw)
        if m:
            current = m.group(1)
            blocks.setdefault(current, []).append(m.group(2))
        elif current:
            blocks[current].append(raw)
    narrated = []
    for key in ('S', 'M'):
        if key in blocks:
            narrated.append(' '.join(blocks[key]))
    return ' '.join(narrated).strip(), set(blocks)


def expand_prophet(source, lang):
    """Mirror cleanForTTS: the audio said the words, not the symbol. Kept as a
    single placeholder so an SRT that shows the symbol and one that shows the
    spoken words both align against the same source."""
    spoken = PROPHET_SPOKEN.get(lang, '')
    for sym in PROPHET_SYMBOLS:
        source = source.replace(sym, f' {spoken} ')
    return re.sub(r'\s+', ' ', source).strip()


# ------------------------------------------------------------------ helpers

def norm(s):
    # U+FDFA (ﷺ) NFKC-decomposes into صلى الله عليه وسلم. Replace it with the
    # spoken form FIRST or the comparison sees four Arabic tokens that were
    # never in the source.
    for sym in PROPHET_SYMBOLS:
        s = s.replace(sym, ' \u0001PBUH\u0001 ')
    s = unicodedata.normalize('NFKC', s)
    s = s.replace('\u02bb', "'").replace('\u02bc', "'").replace('\u2019', "'")
    s = re.sub(r'[^\w\s\'\u0001]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip().casefold()


# Latin letters that are visually identical to Cyrillic ones. Hand-editing an
# SRT on a Latin keyboard layout silently substitutes these; the result looks
# correct on screen and is a different word to every machine that reads it.
HOMOGLYPHS = {
    'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х', 'y': 'у',
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К', 'M': 'М',
    'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х',
}


def check_homoglyphs(cues, source_script):
    """Latin characters hiding inside otherwise-Cyrillic words."""
    out = []
    if source_script != 'cyrillic':
        return out
    for c in cues:
        for word in c['text'].split():
            w = re.sub(r'^\W+|\W+$', '', word)
            if not w:
                continue
            has_cyr = re.search(r'[\u0400-\u04FF]', w)
            bad = [ch for ch in w if ch in HOMOGLYPHS]
            if has_cyr and bad:
                fixed = ''.join(HOMOGLYPHS.get(ch, ch) for ch in w)
                out.append(Finding(
                    'high', 'homoglyph',
                    f'Latin {", ".join(repr(b) for b in bad)} inside a '
                    f'Cyrillic word - looks identical on screen, reads as a '
                    f'different word. Should be {fixed!r}.',
                    c['index'], c['line_no'], w, fixed))
    return out


def tokens(s):
    return [t for t in norm(s).split() if t]


def similarity(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def duration_of(path):
    try:
        out = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', path],
            capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip())
    except Exception:
        return None


def script_of(s):
    cyr = len(re.findall(r'[\u0400-\u04FF]', s))
    lat = len(re.findall(r'[A-Za-z]', s))
    if cyr > lat * 2:
        return 'cyrillic'
    if lat > cyr * 2:
        return 'latin'
    return 'mixed'


def cue_for_token_index(cues, tok_index):
    """Map a token position in the joined SRT back to its cue."""
    seen = 0
    for c in cues:
        count = len(tokens(c['text']))
        if tok_index < seen + count:
            return c
        seen += count
    return cues[-1] if cues else None


# ------------------------------------------------------------------- checks

def check_timing(cues, narration_dur):
    out = []
    for j, c in enumerate(cues):
        if c['end'] <= c['start']:
            out.append(Finding('medium', 'cue_too_short',
                               'cue end is not after its start',
                               c['index'], c['line_no'], c['text']))
        elif c['end'] - c['start'] < MIN_CUE_SEC:
            out.append(Finding(
                'medium', 'cue_too_short',
                f"cue lasts {c['end'] - c['start']:.2f}s "
                f'(min {MIN_CUE_SEC}s)',
                c['index'], c['line_no'], c['text']))
        if j + 1 < len(cues) and c['end'] > cues[j + 1]['start'] + 0.001:
            out.append(Finding('medium', 'timing_overlap',
                               f"overlaps cue {cues[j + 1]['index']}",
                               c['index'], c['line_no'], c['text']))
    if narration_dur and cues:
        if cues[-1]['end'] > narration_dur + AUDIO_TOLERANCE_SEC:
            out.append(Finding(
                'high', 'srt_exceeds_audio',
                f"SRT ends at {cues[-1]['end']:.1f}s but the narration is "
                f'{narration_dur:.1f}s - the SRT is probably stale',
                cues[-1]['index'], cues[-1]['line_no']))
    return out


def check_alignment(cues, source):
    """Step 4 - the primary check."""
    out = []
    srt_toks = tokens(' '.join(c['text'] for c in cues))
    src_toks = tokens(source)
    src_set = set(src_toks)
    raw_srt = ' '.join(c['text'] for c in cues).split()

    sm = difflib.SequenceMatcher(None, src_toks, srt_toks)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        got = srt_toks[j1:j2]
        want = src_toks[i1:i2]
        if not got:
            continue

        cue = cue_for_token_index(cues, j1)
        want_s = ' '.join(want)
        got_s = ' '.join(got)

        # digits <-> words is acceptable in subtitles
        if any(t.isdigit() for t in got) and want:
            out.append(Finding('info', 'number_format',
                               f'{want_s!r} rendered as {got_s!r}',
                               cue['index'] if cue else None,
                               cue['line_no'] if cue else None,
                               got_s, want_s))
            continue

        if len(got) > len(want) and want:
            out.append(Finding(
                'high', 'split_or_merged',
                f'source {want_s!r} became {got_s!r} in the subtitle',
                cue['index'] if cue else None,
                cue['line_no'] if cue else None, got_s, want_s))

        for t in got:
            if t in src_set or t in KNOWN_PROPER:
                continue
            close = difflib.get_close_matches(t, src_toks, n=1, cutoff=0.75)
            if close:
                out.append(Finding(
                    'medium', 'near_miss',
                    f'{close[0]!r} in the source, {t!r} in the subtitle - '
                    f'different word, check the meaning',
                    cue['index'] if cue else None,
                    cue['line_no'] if cue else None, t, close[0]))
            else:
                out.append(Finding(
                    'high', 'unknown_word',
                    f'{t!r} does not appear in the source text',
                    cue['index'] if cue else None,
                    cue['line_no'] if cue else None, t, want_s))

            # capitalised mid-sentence and not in source: highest signal
            for w in raw_srt:
                stripped = re.sub(r'^\W+|\W+$', '', w)
                if norm(stripped) == t and stripped[:1].isupper():
                    if raw_srt.index(w) > 0:
                        out.append(Finding(
                            'high', 'capitalised_non_source',
                            f'{stripped!r} is capitalised mid-sentence and is '
                            f'not in the source - Whisper may have invented a '
                            f'proper noun',
                            cue['index'] if cue else None,
                            cue['line_no'] if cue else None, stripped, want_s))
                    break
    return out


def check_script(cues, source):
    out = []
    want = script_of(source)
    if want == 'mixed':
        return out
    other = r'[A-Za-z]{3,}' if want == 'cyrillic' else r'[\u0400-\u04FF]{3,}'
    for c in cues:
        hits = [h for h in re.findall(other, c['text'])
                if norm(h) not in KNOWN_PROPER]
        if hits:
            out.append(Finding(
                'medium', 'script_mismatch',
                f'source is {want}; cue contains {", ".join(hits[:3])}',
                c['index'], c['line_no'], c['text']))
    return out


def check_prophet_symbol(cues):
    forms, out = set(), []
    joined = ' '.join(c['text'] for c in cues)
    if '\ufdfa' in joined or 'ﷺ' in joined:
        forms.add('symbol')
    spoken = [r'peace be upon him', r'да благословит его',
              r'saw|pbuh|sallallahu', r'صلى الله عليه']
    for pat in spoken:
        if re.search(pat, joined, re.IGNORECASE):
            forms.add('spoken words')
            break
    if len(forms) > 1:
        out.append(Finding(
            'medium', 'prophet_symbol_inconsistent',
            f'both {" and ".join(sorted(forms))} appear - pick one convention '
            f'for burned subtitles (currently unset)'))
    return out, forms


# --------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description='Diff a Whisper .srt against its source narration text.')
    ap.add_argument('--srt', required=True)
    ap.add_argument('--source', required=True, help='draft.txt (S:/M: blocks)')
    ap.add_argument('--lang', required=True,
                    choices=['en', 'ru', 'ar', 'uz', 'tj'])
    ap.add_argument('--narration', default=None, help='.mp3 for duration check')
    args = ap.parse_args()

    width = 66
    print()
    print('=' * width)
    print(f' stt lint - {args.srt}  (lang: {args.lang})')
    print('=' * width)

    if args.lang not in SUB_LANGS:
        print(f'  [HIGH] p078_violation')
        print(f'    {args.lang} skips subtitles per P078, but an SRT was passed.')
        print('    Check $subLangs, or delete a stale SRT from the work tree.')
        print()
        return 1

    try:
        cues, findings = parse_srt(args.srt)
    except FileNotFoundError:
        print(f'FAILED: no such file: {args.srt}')
        return 2
    except UnicodeDecodeError:
        print(f'FAILED: {args.srt} is not UTF-8.')
        return 2

    try:
        source, blocks = parse_source(args.source)
    except FileNotFoundError:
        print(f'FAILED: no such file: {args.source}')
        return 2
    if not source:
        print(f'FAILED: no S: or M: block in {args.source}')
        return 2
    if not cues:
        print('FAILED: no cues parsed from the SRT.')
        return 2

    source = expand_prophet(source, args.lang)
    dur = duration_of(args.narration) if args.narration else None
    sim = similarity(' '.join(c['text'] for c in cues), source)

    findings += check_timing(cues, dur)
    if sim < SIM_DIVERGED:
        findings.append(Finding(
            'high', 'transcript_diverged',
            f'whole-text similarity {sim:.2f} - the SRT may have been made '
            f'from different audio'))
    else:
        findings += check_alignment(cues, source)
    findings += check_script(cues, source)
    findings += check_homoglyphs(cues, script_of(source))
    sym, forms = check_prophet_symbol(cues)
    findings += sym

    # de-duplicate
    seen, unique = set(), []
    for f in findings:
        key = (f.code, f.cue, f.srt_text, f.source_text)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    unique.sort(key=lambda f: (SEV[f.severity], f.cue or 0))

    if not unique:
        print('  no findings.')
    for f in unique:
        loc = ''
        if f.cue is not None:
            loc = f'  -  cue {f.cue}'
            if f.line_no:
                loc += f', line {f.line_no}'
        print()
        print(f'  [{f.severity.upper()}] {f.code}{loc}')
        if f.source_text:
            print(f'    source:   {f.source_text[:110]}')
        if f.srt_text:
            print(f'    subtitle: {f.srt_text[:110]}')
        print(f'    -> {f.note}')

    counts = {s: sum(1 for f in unique if f.severity == s)
              for s in ('high', 'medium', 'info')}
    print()
    print('-' * width)
    print(f"  {counts['high']} high   {counts['medium']} medium   "
          f"{counts['info']} info")
    print(f'  cues: {len(cues)}   similarity: {sim:.3f}', end='')
    print(f'   narration: {dur:.1f}s' if dur else '')
    if forms:
        print(f"  prophet symbol rendered as: {', '.join(sorted(forms))}")
    print('  warn-only: nothing was blocked or changed. A clean run means')
    print('  these checks passed, NOT that the subtitles are correct.')
    print('-' * width)
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())