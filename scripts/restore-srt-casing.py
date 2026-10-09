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


def norm(w):
    """Casefold, and collapse Russian yo onto ye. The only two axes we allow."""
    return w.casefold().replace("\u0451", "\u0435")


def read_text(path):
    with io.open(path, encoding="utf-8-sig", newline="") as fh:
        return fh.read()


def dominant_newline(raw):
    return "\r\n" if raw.count("\r\n") >= raw.count("\n") - raw.count("\r\n") else "\n"


def source_forms(text):
    """normalised form -> the set of spellings the source uses for it."""
    forms = defaultdict(set)
    for line in text.splitlines():
        line = BLOCK_LABEL.sub("", line)
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
    forms = source_forms(read_text(args.source))
    if not forms:
        print("FAILED: no words found in %s" % args.source)
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
