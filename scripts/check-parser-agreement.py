#!/usr/bin/env python
"""check-parser-agreement.py - do lint-content and stt-validate read the same draft?

Two tools parse draft.txt independently. lint-content.py keeps line numbers so
it can report where a finding is; stt-validate.py returns the narrated text
(S + M only) so it can compare against the SRT. Different shapes, on purpose.

Nothing has ever checked that they agree on what the blocks ARE. If they drift,
the linter passes a draft whose narrated half the validator reads differently,
and the disagreement is invisible: each tool is self-consistent and neither
can see the other.

Written 2026-10-10 INSTEAD of merging the two parsers into a shared module.
The merge was the item on record; it refactors two working scripts to serve a
programmatic agent that does not exist. This answers the question the merge was
really for - are they the same? - and risks nothing.

    python scripts/check-parser-agreement.py [draft.txt]

Exit 0 agree, 1 disagree, 2 could not run (P093).
"""
import importlib.util
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def compare(lint_keys, lint_narrated, stt_keys, stt_narrated):
    """Return a list of disagreement lines; empty means the two parsers agree.

    Factored out of main so the DISAGREE path can be exercised. Before this,
    every run of this script had agreed, which meant the reporting branch had
    never executed even once - the same weakness as P210, where a threshold
    that had never been checked against a known-different input was a number
    rather than a gate. --self-test feeds it inputs that MUST disagree.
    """
    bad = []
    if set(lint_keys) != set(stt_keys):
        bad.append("block sets differ: lint %s vs stt %s"
                   % (sorted(lint_keys), sorted(stt_keys)))
    if lint_narrated != stt_narrated:
        bad.append("narrated text differs (S + M)")
        for i, (a, c) in enumerate(zip(lint_narrated, stt_narrated)):
            if a != c:
                lo = max(0, i - 40)
                bad.append("  first difference at char %d" % i)
                bad.append("  lint: ...%s" % lint_narrated[lo:i + 40])
                bad.append("  stt : ...%s" % stt_narrated[lo:i + 40])
                break
        else:
            bad.append("  one is a prefix of the other: lint %d chars, stt %d"
                       % (len(lint_narrated), len(stt_narrated)))
    return bad


def self_test():
    """The failure path must be able to fire. Three inputs that MUST disagree."""
    cases = [
        ("differing text", ("SM", "the best of you", "SM", "the best of them")),
        ("prefix",         ("SM", "abc def", "SM", "abc def ghi")),
        ("block sets",     ("SMHC", "x", "SM", "x")),
    ]
    ok = True
    for name, (lk, lt, sk, st) in cases:
        bad = compare(lk, lt, sk, st)
        print("  %-16s %s" % (name, "DISAGREE reported" if bad else "*** NO REPORT ***"))
        ok = ok and bool(bad)
    # and one that must NOT fire
    clean = compare("SM", "same text", "SM", "same text")
    print("  %-16s %s" % ("identical", "silent" if not clean else "*** FALSE POSITIVE ***"))
    ok = ok and not clean
    return 0 if ok else 1


def main():
    if "--self-test" in sys.argv:
        print("\n  self-test: can the DISAGREE path fire?")
        rc = self_test()
        print("  %s\n" % ("all four behaved correctly" if rc == 0
                          else "SELF-TEST FAILED - this script cannot report a real difference"))
        return rc
    draft = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "draft.txt")
    if not os.path.exists(draft):
        print("FAILED: no such draft: %s" % draft)
        return 2
    try:
        lint = load("lc", os.path.join(REPO, "scripts", "lint-content.py"))
        stt = load("sv", os.path.join(REPO, "scripts", "stt-validate.py"))
    except Exception as exc:
        print("FAILED: could not load one of the two parsers: %s" % exc)
        return 2

    with io.open(draft, encoding="utf-8-sig") as fh:
        text = fh.read()

    lint_blocks = lint.parse_blocks(text)
    lint_narrated = norm(" ".join(
        " ".join(l for _n, l in lint_blocks.get(k, [])) for k in ("S", "M")))

    stt_narrated, stt_keys = stt.parse_source(draft)
    stt_narrated = norm(stt.expand_prophet(stt_narrated, "en"))
    # lint keeps the glyph; expand it the same way so the comparison is fair
    lint_narrated = norm(stt.expand_prophet(lint_narrated, "en"))

    width = 70
    print()
    print("=" * width)
    print(" parser agreement - %s" % os.path.basename(draft))
    print("=" * width)

    bad = compare(lint_blocks, lint_narrated, stt_keys, stt_narrated)

    if bad:
        for line in bad:
            print("  [DISAGREE] " + line if not line.startswith(" ") else line)
        print("-" * width)
        print("  the two tools do not read this draft the same way.")
        print("-" * width)
        print()
        return 1

    print("  blocks: %s" % ", ".join(sorted(lint_blocks)))
    print("  narrated (S + M): %d chars, identical in both parsers" % len(lint_narrated))
    print("-" * width)
    print("  agree. This says they read the SAME text, not that either is right.")
    print("-" * width)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
