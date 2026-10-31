#!/usr/bin/env python3
"""scripts/build-pattern-index.py - generate PATTERN_INDEX.md from fix_patterns.md.

WHY THIS EXISTS
---------------
fix_patterns.md is 817 KB / 14103 lines. Nothing reads a file that size at the
start of a session, so the patterns get consulted only when someone already
suspects which one applies - exactly backwards. P326, P329 and P332 were each a
repeat of something already written in that file:

  P329  the camera rule was in self_upskilling.md AND in the b5185 registry
        notes, and the camera was moved anyway - $2.24 of re-rolls.
  P332  CLAUDE.md carried three wrong stack facts for weeks under a green audit.

The index is one line per pattern, so the whole corpus fits in a session's
opening context; the full text is then read by number.

TWO AXES, BOTH COUNTABLE
------------------------
1. By number - the verbatim title. Nothing here paraphrases a pattern: a
   summary is a second source of truth, and P327 is about what happens when a
   derived field drifts from what it was derived from.

2. By file - which patterns mention which script or doc, extracted from the
   backticked filenames in each pattern's body. This is the lookup that would
   have stopped P329: before touching `generate-scene.ps1`, see every pattern
   that ever touched it.

A KEYWORD TOPIC TABLE WAS TRIED FIRST AND REMOVED.
Nine topics over the titles left 113 of 269 entries in "Unsorted", because the
later titles are aphorisms: "A key that identifies nothing", "The check
existed. Nothing ran it." A regex cannot read those, and audit-docs.py's own
charter already says so - "checks only what is COUNTABLE, where wrong is wrong
with no opinion involved". That is the second time in one day a regex was
pointed at prose (see P332's removed check). A filename is countable; a theme
is not.

The file ends with a stamp line:

    <!-- pattern-index-stamp entries=269 patterns=262 frontier=332 sha1=... -->

`audit-docs.py` recomputes it from fix_patterns.md and fails the push when it
differs, so a new pattern cannot be added without regenerating the index. That
is the whole point: this must not depend on anyone remembering.

Run:  python scripts/build-pattern-index.py            (writes PATTERN_INDEX.md)
      python scripts/build-pattern-index.py --check    (exit 1 if out of date)
"""
import hashlib
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "fix_patterns.md")
OUT = os.path.join(ROOT, "PATTERN_INDEX.md")
CRLF = "\r\n"

HEADING = re.compile(r"^##\s*PATTERN\s+(\d+)\s*[:—\-]?\s*(.*?)\s*$")

# A backticked token that looks like a file. Extensions the project actually
# uses - an open-ended rule would collect prose like `true` or `--number`.
FILE_TOKEN = re.compile(
    r"`([A-Za-z0-9_][A-Za-z0-9_./\\-]*\."
    r"(?:py|ps1|ts|tsx|js|mjs|json|md|yml|yaml|sql|srt|mp3|mp4|env\.local))`")

# Appear in nearly every pattern or are not a project file; listing them would
# bury the signal.
FILE_IGNORE = {"package.json", "package-lock.json", "tsconfig.json"}

MIN_FILE_HITS = 3   # a file named by one or two patterns is not a cross-reference


def read(path):
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def parse(text):
    """[(num, title, body)] in file order; titles verbatim."""
    lines = text.replace("\r\n", "\n").split("\n")
    marks = []
    for i, line in enumerate(lines):
        m = HEADING.match(line)
        if m:
            marks.append((i, int(m.group(1)), m.group(2).strip()))
    out = []
    for j, (i, num, title) in enumerate(marks):
        end = marks[j + 1][0] if j + 1 < len(marks) else len(lines)
        out.append((num, title, "\n".join(lines[i:end])))
    return out


def stamp_of(entries):
    nums = [n for n, _, _ in entries]
    payload = "\n".join("%d:%s" % (n, t) for n, t, _ in entries)
    return {
        "entries": len(entries),
        "patterns": len(set(nums)),
        "frontier": max(nums) if nums else 0,
        "sha1": hashlib.sha1(payload.encode("utf-8")).hexdigest(),
    }


def stamp_line(s):
    return ("<!-- pattern-index-stamp entries=%(entries)d patterns=%(patterns)d "
            "frontier=%(frontier)d sha1=%(sha1)s -->" % s)


def file_xref(entries):
    """{filename: [labels]} - mechanical, from backticked tokens in each body."""
    hits = {}
    for num, _, body in entries:
        label = "P%03d" % num
        for name in set(m.group(1) for m in FILE_TOKEN.finditer(body)):
            base = name.replace("\\", "/").split("/")[-1]
            if base in FILE_IGNORE:
                continue
            hits.setdefault(base, [])
            if label not in hits[base]:
                hits[base].append(label)
    return {k: v for k, v in hits.items() if len(v) >= MIN_FILE_HITS}


def build(entries):
    s = stamp_of(entries)
    seen = {}
    rows = []
    for num, title, _ in entries:
        seen[num] = seen.get(num, 0) + 1
        label = "P%03d" % num
        if seen[num] > 1:
            label += " (addendum %d)" % seen[num]
        rows.append((label, title))

    xref = file_xref(entries)

    L = []
    L.append("# PATTERN_INDEX.md")
    L.append("")
    L.append("**Generated. Do not hand-edit** - run `python scripts/build-pattern-index.py`.")
    L.append("`audit-docs.py` fails the push when this file and `fix_patterns.md` disagree.")
    L.append("")
    L.append("%d patterns in %d entries, frontier **P%d**. The P-sequence is shared with"
             % (s["patterns"], s["entries"], s["frontier"]))
    L.append("hadith-verifier, so the count here is lower than the frontier.")
    L.append("")
    L.append("**Read the pattern, never this line.** Full text: search `## PATTERN <n>`")
    L.append("in `fix_patterns.md`. A one-line title is a pointer, not the lesson.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## By file - every pattern that touched it")
    L.append("")
    L.append("Extracted from the backticked filenames in each pattern's body; files")
    L.append("named by fewer than %d patterns are left out. Check the line for a file"
             % MIN_FILE_HITS)
    L.append("BEFORE changing it.")
    L.append("")
    for name in sorted(xref, key=lambda k: (-len(xref[k]), k)):
        L.append("- `%s` (%d) - %s" % (name, len(xref[name]), ", ".join(xref[name])))
    L.append("")
    L.append("---")
    L.append("")
    L.append("## By number")
    L.append("")
    for label, title in rows:
        L.append("- **%s** - %s" % (label, title))
    L.append("")
    L.append(stamp_line(s))
    L.append("")
    return CRLF.join(L), s, xref


def main():
    if not os.path.exists(SRC):
        print("FAIL: %s not found" % SRC)
        return 1
    entries = parse(read(SRC))
    if len(entries) < 200:
        print("FAIL: only %d pattern headings parsed - refusing to write that"
              % len(entries))
        return 1
    body, s, xref = build(entries)

    if "--check" in sys.argv:
        if not os.path.exists(OUT):
            print("FAIL: PATTERN_INDEX.md is missing")
            return 1
        cur = read(OUT)
        want = stamp_line(s)
        if want not in cur:
            print("FAIL: PATTERN_INDEX.md is out of date")
            print("  want: %s" % want)
            got = [l for l in cur.split("\n") if "pattern-index-stamp" in l]
            print("  got : %s" % (got[0].strip() if got else "(no stamp line)"))
            print("  fix : python scripts/build-pattern-index.py")
            return 1
        print("PATTERN_INDEX.md is current (%d entries, frontier P%d)"
              % (s["entries"], s["frontier"]))
        return 0

    before = len(read(OUT).encode("utf-8")) if os.path.exists(OUT) else 0
    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(body)
    after = read(OUT)
    if (after.count("\n") - after.count("\r\n")) != 0:
        print("FAIL: bare LF written into a CRLF doc")
        return 2
    if stamp_line(s) not in after:
        print("FAIL: read-back is missing the stamp")
        return 2
    size = len(after.encode("utf-8"))
    print("PATTERN_INDEX.md  %d -> %d bytes" % (before, size))
    print("  entries=%d patterns=%d frontier=P%d  files cross-referenced=%d"
          % (s["entries"], s["patterns"], s["frontier"], len(xref)))
    if size > 60000:
        print("  WARNING: over 60 KB - this is injected at session start, trim it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
