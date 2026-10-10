#!/usr/bin/env python
"""pick-nasheed.py - recommend a bed, with the reason, for reel-producing step 7.

Step 7 of the reel-producing skill: "From the tracker's Nasheed usage table,
pick the least-used file that is not already used in this language recently
and not used elsewhere in this set. STATE THE REASON. Name it explicitly on
the command line; never let the script pick."

So this RECOMMENDS and explains. It does not choose and it does not render.
render-reel.ps1 has its own picker, and that picker has drawn an ocean-ambience
track onto R044 and an adults bed onto kids reels R029 and R030. The point of
passing -Nasheed explicitly is that a human saw the name.

Eligibility comes from the registry via audit-assets.py --list, never from the
filename (P168). Usage comes from the tracker's Active reels rows, parsed by
HEADER INDEX - the Notes column holds prose and naive field splitting misreads
rows, which nearly overwrote R052's history on 2026-08-31.

Exit codes follow the audit contract (P093): 0 fine, 2 could not run.
"""

import argparse
import io
import os
import re
import subprocess
import sys
from collections import defaultdict
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def eligible_beds(lane):
    """Lane-approved audio, straight from the registry gate (P168)."""
    try:
        out = subprocess.run(
            [sys.executable, os.path.join(HERE, "audit-assets.py"),
             "--list", "--lane", lane, "--section", "audio"],
            capture_output=True, text=True, encoding="utf-8", cwd=REPO)
    except OSError as e:
        print("FAILED: cannot run audit-assets.py (%s)" % e)
        return None
    if out.returncode != 0:
        print("FAILED: audit-assets.py --list exited %d" % out.returncode)
        print((out.stderr or out.stdout or "").strip()[:400])
        return None
    return [l.strip() for l in (out.stdout or "").splitlines() if l.strip().endswith(".mp3")]


def tracker_usage(path):
    """(bed -> [(reel, lang)]) from the Active reels table, by header index."""
    try:
        text = io.open(path, encoding="utf-8-sig").read()
    except OSError as e:
        print("FAILED: cannot read %s (%s)" % (path, e))
        return None
    rows = [l for l in text.split("\n") if l.startswith("|")]
    header = None
    for l in rows:
        cells = [c.strip() for c in l.split("|")]
        if "Reel ID" in cells and "Nasheed" in cells and "Lang" in cells:
            header = cells
            break
    if not header:
        print("FAILED: no Active reels header in %s" % path)
        return None
    i_id, i_lang, i_n = (header.index("Reel ID"), header.index("Lang"),
                         header.index("Nasheed"))
    usage = defaultdict(list)
    for l in rows:
        cells = [c.strip() for c in l.split("|")]
        if len(cells) <= max(i_id, i_lang, i_n):
            continue
        rid = cells[i_id]
        if not re.match(r"^R\d+$", rid):
            continue
        bed = cells[i_n]
        if not bed.endswith(".mp3"):
            continue  # "not recorded (P201)" and friends
        usage[bed].append((int(rid[1:]), cells[i_lang].lower()))
    return usage


def main():
    ap = argparse.ArgumentParser(
        description="Recommend a nasheed, with the reason (reel-producing step 7).")
    ap.add_argument("--lane", required=True, choices=["kids", "adults"])
    ap.add_argument("--lang", required=True,
                    choices=["en", "ru", "uz", "tj", "ar"])
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="beds already assigned to other languages in THIS set")
    ap.add_argument("--tracker", default=os.path.join(REPO, "reel-tracker.md"))
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--slug", default="",
                    help="hadith slug, e.g. muslim-1631. Only used to "
                         "rotate the default when the ranking ties")
    args = ap.parse_args()

    beds = eligible_beds(args.lane)
    if beds is None:
        return 2
    if not beds:
        print("FAILED: no %s-approved audio in the registry" % args.lane)
        return 2
    usage = tracker_usage(args.tracker)
    if usage is None:
        return 2

    excluded = set(args.exclude)
    latest_reel = max((n for v in usage.values() for n, _ in v), default=0)

    rows = []
    for bed in beds:
        if bed in excluded:
            continue
        hits = usage.get(bed, [])
        total = len(hits)
        in_lang = [n for n, lg in hits if lg == args.lang]
        last_any = max((n for n, _ in hits), default=0)
        last_lang = max(in_lang, default=0)
        rows.append({"bed": bed, "total": total, "last_any": last_any,
                     "last_lang": last_lang, "in_lang": len(in_lang)})

    if not rows:
        print("FAILED: every eligible bed was excluded")
        return 2

    # least-used first; then the one longest unused in THIS language; then
    # longest unused overall. Matches step 7 word for word.
    rows.sort(key=lambda r: (r["total"], r["last_lang"], r["last_any"]))

    # A tie the ranking cannot break. On the #1631 set five beds sat at 0
    # uses, so the key (0, 0, 0) was identical for every one of them and the
    # stable sort handed back registry order - alphabetical. The same name
    # came back "RECOMMENDED" on all four legs and was overridden all four
    # times, because the recommendation carried no information: only the
    # exclusion list differed between runs. A ranking that cannot separate
    # its candidates should say so rather than emit a confident first place.
    key0 = (rows[0]["total"], rows[0]["last_lang"], rows[0]["last_any"])
    tied = [r for r in rows
            if (r["total"], r["last_lang"], r["last_any"]) == key0]
    if len(tied) > 1:
        # Deterministic so a rerun of the same leg is reproducible, varied
        # so the four legs of one set do not all land on the same bed.
        seed = int(hashlib.sha1(
            ("%s|%s|%s" % (args.slug, args.lane, args.lang)).encode("utf-8")
        ).hexdigest()[:8], 16)
        chosen = tied[seed % len(tied)]
        rows.remove(chosen)
        rows.insert(0, chosen)

    width = 74
    print()
    print("=" * width)
    print(" nasheed recommendation - lane: %s, lang: %s" % (args.lane, args.lang))
    print("=" * width)
    print("  %d bed(s) approved for %s; %d excluded as already in this set."
          % (len(beds), args.lane, len(excluded & set(beds))))
    if len(tied) > 1:
        print("  TIE: %d beds share the top score (%d use(s)). Usage cannot"
              % (len(tied), key0[0]))
        print("  separate them. The pick below is stable for this")
        print("  slug+lane+lang but otherwise arbitrary - BREAK IT ON TONE.")
    print()
    for rank, r in enumerate(rows[:args.top], 1):
        mark = "  <= RECOMMENDED" if rank == 1 else ""
        print("  %d. %-34s %d use(s)%s" % (rank, r["bed"], r["total"], mark))
        if r["total"] == 0:
            why = "never used in any language"
        else:
            gap = latest_reel - r["last_lang"] if r["last_lang"] else None
            if r["in_lang"] == 0:
                why = ("%d use(s) overall, never in %s (last anywhere R%03d)"
                       % (r["total"], args.lang.upper(), r["last_any"]))
            else:
                why = ("%d use(s) overall, %d in %s, last in %s at R%03d "
                       "(%d reels ago)" % (r["total"], r["in_lang"],
                       args.lang.upper(), args.lang.upper(), r["last_lang"], gap))
        print("     %s" % why)
    print()
    print("-" * width)
    print("  Pass it explicitly:  -Nasheed %s" % rows[0]["bed"])
    print("  This recommends; it does not choose. Letting the renderer pick is")
    print("  what put an ambience track on R044 and an adults bed on R029/R030.")
    print("-" * width)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
