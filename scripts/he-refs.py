#!/usr/bin/env python3
# scripts/he-refs.py
# ============================================================
# Build a refs file for source-candidates.py --provider hadeethenc.
#
# HadeethEnc organises by CATEGORY, so a slot in the four-slot content cycle
# (mercy, deed, accountability, character) maps to a set of category ids and a
# refs file falls out of a query rather than out of browsing.
#
#   python scripts/he-refs.py --slot mercy --limit 20
#   python scripts/he-refs.py --category 321 --out out/source-refs.txt
#   python scripts/he-refs.py --slot deed --exclude-langs   # drop ids missing uz/tg
#
# Writes ids one per line, "#" comments carrying the title, so the file is
# readable and source-candidates.py skips the comments.
# Stdlib only.
# ============================================================
import os
import sys
import argparse

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, "lib"))
from source_hadeethenc import fetch_list  # noqa: E402

# Slot -> HadeethEnc category ids. Mercy is the THINNEST slot at 57 hadeeths
# and the best-performing one; accountability and character have 4-5x the
# supply, so the constraint is not the same in every slot.
SLOTS = {
    "mercy":          ["321", "318", "322"],
    "deed":           ["277", "511", "273", "274", "297", "341"],
    "accountability": ["63", "324", "85", "83", "312"],
    "character":      ["282", "283", "287", "286", "290", "314", "316", "281", "280"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", choices=sorted(SLOTS))
    ap.add_argument("--category", action="append", default=[],
                    help="raw HadeethEnc category id; repeatable")
    ap.add_argument("--limit", type=int, default=25, help="max refs to write")
    ap.add_argument("--per-page", type=int, default=50)
    ap.add_argument("--out", default="out/source-refs.txt")
    ap.add_argument("--exclude-langs", action="store_true",
                    help="skip ids whose translations list lacks uz or tg")
    args = ap.parse_args()

    cats = list(args.category) + (SLOTS[args.slot] if args.slot else [])
    if not cats:
        ap.error("give --slot or --category")

    rows, seen = [], set()
    for cat in cats:
        try:
            env = fetch_list(cat, language="en", page=1, per_page=args.per_page)
        except Exception as e:
            print(f"  ! category {cat}: {e}")
            continue
        for item in (env.get("data") or []):
            hid = str(item.get("id") or "").strip()
            if not hid or hid in seen:
                continue
            langs = item.get("translations") or []
            # Coverage is PER HADITH, not uniform across the site (P165). A
            # candidate missing uz or tg would need machine translation, which
            # is the thing this source exists to avoid.
            if args.exclude_langs and not ({"uz", "tg"} <= set(langs)):
                continue
            seen.add(hid)
            rows.append((hid, cat, (item.get("title") or "").strip()))

    rows = rows[:args.limit]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"# HadeethEnc refs — slot={args.slot or '-'} categories={','.join(cats)}\n")
        f.write("# id per line; run: python scripts/source-candidates.py --provider hadeethenc\n")
        for hid, cat, title in rows:
            f.write(f"\n# [{cat}] {title[:90]}\n{hid}\n")

    print(f"wrote {len(rows)} refs -> {args.out}")
    if args.exclude_langs:
        print("  (filtered to ids carrying both uz and tg)")


if __name__ == "__main__":
    main()