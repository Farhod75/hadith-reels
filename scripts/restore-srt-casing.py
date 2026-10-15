#!/usr/bin/env python
"""restore-srt-casing.py - put back what Whisper could not hear (P200).

Whisper transcribes SOUND. Capitalisation and Russian yo are properties of the
TEXT, and the text was never given to it, so every en/ru reel comes back with
divine pronouns lowercased (His, He; Svoyu, On) and yo flattened to ye. On the
#2759 set that was four of five RU findings and two of three EN ones, all
corrected by hand at the review pause.

This does NOT use a word list. A list cannot tell which "on" means Allah and
which means a man, and a list has to be maintained. The correct text is already
on disk: draft.txt, the same file stt-validate.py compares against. So this
aligns the SRT to the source and takes the source's spelling.

SAFETY. A replacement is made only when the SRT token and the source token are
identical after normalising case and yo. It can never introduce a word Whisper
did not hear, never change one word into another, and never touch timings. Two
further guards:

  - If one normalised form appears in the source under two different spellings
    (both "On" and "on"), it is AMBIGUOUS and is left alone, and reported.
  - The first word of a cue is never lowercased. Whisper capitalises cue
    openings and that is correct even where the source has the word mid-sentence.

Exit codes follow the audit contract (P093): 0 clean or changed, 2 could not run.
"""

import argparse
import io
import re
import sys
from collections import defaultdict

WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
TIMECODE = re.compile(r"^\s*\d{2}:\d{2}:\d{2},\d{3}\s*-->")
INDEX = re.compile(r"^\s*\d+\s*$")
BLOCK_LABEL = re.compile(r"^\s*[SMHC]\s*:\s*", re.IGNORECASE)
BLOCK_TAG = re.compile(r"^\s*([SMHC])\s*:\s*", re.IGNORECASE)

# P243: only S and M are narrated. H and C sit in the same draft.txt and are
# never spoken. On Bukhari #13 RU the H block opened a sentence with "Его
# понимают как" - the only standalone его/Его in the file - and this script
# took that capital as the source spelling for the mid-sentence его inside the
# prophet-symbol expansion, rewriting a correct subtitle into one that reads as
# ALLAH being blessed rather than the Prophet. The ambiguity guard never fired,
# because there was exactly one spelling to find and it was the wrong one.
NARRATED_BLOCKS = ("S", "M")

# P243: cleanForTTS replaces the symbol with spoken words BEFORE the audio is
# made, so Whisper hears words and the source still holds the symbol. Without
# expanding it here, every word of the phrase is in the AUDIO but absent from
# the SOURCE - which is how its casing came to be decided by an unrelated
# block. Values mirror stt-validate.py; keep them in step.
PROPHET_SPOKEN = {
    "ru": "да благословит его Аллах и приветствует",
    "en": "peace be upon him",
    "ar": "صلى الله عليه وسلم",
    "uz": "Саллаллоҳу алайҳи васаллам",
    "tj": "Салаллоҳу алайҳи васаллам",
}
PROPHET_SYMBOLS = ["\ufdfa", "ﷺ", "صلى الله عليه وسلم"]


# P246: a verifier must never report agreement with a source it cannot read.
# draft.txt is a SCRATCH file that every generation overwrites, so a reel held
# across a later generation is re-rendered against another language's blocks.
# On 2026-10-15 an EN re-render of #6570 ran against a Cyrillic draft.txt left
# by #13: zero words could match, so zero were changed, and this script printed
#   "nothing to restore - the SRT already matches the source."
# That sentence was false. Nothing had been compared at all. A check that
# passes on an unusable input is worse than one that errors, because the
# operator reads the pass and stops looking.
CYRILLIC = re.compile(r"[\u0400-\u04FF]")
ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F\ufb50-\ufdff\ufe70-\ufeff]")
LATIN = re.compile(r"[A-Za-z]")
MIN_COVERAGE = 0.40


def dominant_script(text):
    """Which writing system this text is mostly in."""
    counts = {
        "cyrillic": len(CYRILLIC.findall(text)),
        "arabic": len(ARABIC.findall(text)),
        "latin": len(LATIN.findall(text)),
    }
    top = max(counts, key=counts.get)
    return top if counts[top] else "none"


def cue_text(raw):
    """The spoken lines of an SRT - no indices, no timecodes, no blanks."""
    keep = []
    for line in raw.splitlines():
        if not line.strip() or INDEX.match(line) or TIMECODE.match(line):
            continue
        keep.append(line)
    return " ".join(keep)


def norm(w):
    """Casefold, and collapse Russian yo onto ye. The only two axes we allow."""
    return w.casefold().replace("\u0451", "\u0435")


def read_text(path):
    with io.open(path, encoding="utf-8-sig", newline="") as fh:
        return fh.read()


def dominant_newline(raw):
    return "\r\n" if raw.count("\r\n") >= raw.count("\n") - raw.count("\r\n") else "\n"


def expand_prophet(text, lang):
    """P243: mirror cleanForTTS so the spoken words have a source spelling."""
    spoken = PROPHET_SPOKEN.get(lang, "")
    if not spoken:
        return text
    for sym in PROPHET_SYMBOLS:
        text = text.replace(sym, " %s " % spoken)
    return text


def source_forms(text, lang=None):
    """normalised form -> the set of spellings the source uses for it.

    P243: NARRATED blocks only. H and C are in draft.txt and are never spoken,
    so a sentence-initial capital in one of them is not evidence about a
    mid-sentence word in another. Lines without a label continue the block
    above them, so the current block is tracked rather than assumed.
    """
    forms = defaultdict(set)
    block = None
    for line in text.splitlines():
        m = BLOCK_TAG.match(line)
        if m:
            block = m.group(1).upper()
            line = BLOCK_TAG.sub("", line)
        if block not in NARRATED_BLOCKS:
            continue
        if lang:
            line = expand_prophet(line, lang)
        for w in WORD.findall(line):
            forms[norm(w)].add(w)
    return forms


def main():
    ap = argparse.ArgumentParser(
        description="Restore casing and yo in an SRT from its source text.")
    ap.add_argument("--srt", required=True)
    ap.add_argument("--source", required=True, help="draft.txt with S:/M: blocks")
    ap.add_argument("--lang", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for path in (args.srt, args.source):
        try:
            open(path, "rb").close()
        except OSError as e:
            print("FAILED: cannot read %s (%s)" % (path, e))
            return 2

    raw = read_text(args.srt)
    nl = dominant_newline(raw)
    src_text = read_text(args.source)
    forms = source_forms(src_text, args.lang)
    if not forms:
        print("FAILED: no words found in %s" % args.source)
        return 2

    # P246: refuse rather than agree. See the note above dominant_script().
    srt_text = cue_text(raw)
    toks = [norm(w) for w in WORD.findall(srt_text)]
    covered = sum(1 for t in toks if t in forms)
    coverage = (covered / float(len(toks))) if toks else 0.0
    src_script = dominant_script(src_text)
    srt_script = dominant_script(srt_text)
    if src_script != srt_script or coverage < MIN_COVERAGE:
        print()
        print("FAILED: --source does not match this SRT. NOTHING WAS VERIFIED.")
        print("  SRT script: %-11s source script: %s" % (srt_script, src_script))
        print("  the source accounts for %d of %d SRT words (%.0f%%, need %.0f%%)"
              % (covered, len(toks), coverage * 100, MIN_COVERAGE * 100))
        print("  %s is overwritten by every generation (P246), so a reel held" % args.source)
        print("  across a later generation sees the WRONG language's blocks.")
        print("  Re-sync it from the admin for lang=%s, then re-run." % args.lang)
        print("  Until then the subtitles are UNCHECKED - read every cue.")
        return 2

    changes = []
    ambiguous = set()
    out_lines = []
    at_cue_start = True

    for line in raw.splitlines():
        if INDEX.match(line) or TIMECODE.match(line) or not line.strip():
            out_lines.append(line)
            if not line.strip():
                at_cue_start = True
            continue

        first = [at_cue_start]

        def fix(m):
            tok = m.group(0)
            is_first = first[0]
            first[0] = False
            cand = forms.get(norm(tok))
            if not cand or tok in cand:
                return tok
            if len(cand) > 1:
                ambiguous.add((tok, tuple(sorted(cand))))
                return tok
            want = next(iter(cand))
            # guard: never lowercase the first word of a cue
            if is_first and tok[:1].isupper() and want[:1].islower():
                return tok
            changes.append((tok, want))
            return want

        out_lines.append(WORD.sub(fix, line))
        at_cue_start = False

    width = 64
    print()
    print("=" * width)
    print(" srt casing restore - %s  (lang: %s)" % (args.srt, args.lang))
    print("=" * width)

    if not changes and not ambiguous:
        print("  nothing to restore - the SRT already matches the source.")
    for tok, want in sorted(set(changes)):
        n = changes.count((tok, want))
        print("  %-28s -> %-28s x%d" % (tok, want, n))
    for tok, cand in sorted(ambiguous):
        print("  [skipped] %-20s source uses %s - ambiguous, left alone"
              % (tok, " / ".join(cand)))

    print()
    print("-" * width)
    print("  %d restored   %d ambiguous" % (len(changes), len(ambiguous)))
    print("  Timings untouched. Only case and yo were changed, and only where")
    print("  the source has the same word. Read the cues anyway.")
    print("-" * width)
    print()

    if changes and not args.dry_run:
        with io.open(args.srt, "w", encoding="utf-8", newline="") as fh:
            fh.write(nl.join(out_lines) + nl)
    return 0


if __name__ == "__main__":
    sys.exit(main())
