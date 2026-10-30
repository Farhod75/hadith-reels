# backfill_book.py - fill hadith_library.book from the Tier 1 page.
#
# DRY RUN BY DEFAULT. Pass --commit to write.
#
# WHY THIS EXISTS (P287). Sunan Abu Dawud #1488's UZ and TJ H blocks each
# invented a book subdivision - «дуо китобида» / «китоби дуо» - because Du'a is
# the BAB and the KITAB is at-Tafri' li-abwab al-Witr. fix_patterns records the
# cause exactly: "The library row's `book` column is EMPTY, so the generator
# produced the subdivision out of nothing." The mitigation that shipped was a
# `book-claim` WARN in lint-content.py, which catches the symptom and cannot
# supply the fact. P287 also states where the fact lives: "the only authority
# for one is the `book` column and a Tier 1 page." On 2026-10-30 the column was
# empty on 69 of 72 rows, so the generator had no authority for 96% of the
# library.
#
# FORMAT: the Tier 1 page's own English book title, VERBATIM. Chosen 2026-10-30
# over a `Kitab an-Nikah` transliteration for one reason: the page does not
# publish transliterations, so that form would be MY derivation - 40-60 invented
# strings in the one field whose entire job is to be the authority against
# invention. The three rows that were already filled make the argument by
# themselves: 'The Book on Faith' is tohed's English form copied from the source
# and it matches; 'Kitab as-Sawm' and 'Ar-Riqaq' were hand-derived and produced
# two different conventions.
#
# EXTRACTION: the page publishes the book twice in JSON-LD - BreadcrumbList
# position 4, and the Article's about[0].name. This script requires BOTH and
# requires them to AGREE. One missing or the two disagreeing is reported, never
# resolved by preferring one. Structured data is parsed as JSON, not scraped
# with a regex over rendered text (P326).
#
# Reuses verify-matn-number.py's target_url() and fetch(), so URLs are not
# guessed and out/source-cache is reused instead of refetched.
import argparse
import html
import importlib.util
import json
import os
import re
import sys
import time
import urllib.request

ROOT = r"C:\QA\Hadith verification AI app\hadith-reels"
os.chdir(ROOT)

LD = re.compile(r'(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>')


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


vmn = load("vmn", os.path.join("scripts", "verify-matn-number.py"))
al = load("al", os.path.join("scripts", "audit-library.py"))


def ld_blocks(body):
    """Every JSON-LD object on the page, flattened through @graph."""
    out = []
    for m in LD.finditer(body):
        raw = m.group(1).strip()
        try:
            doc = json.loads(raw)
        except Exception:
            continue
        stack = [doc]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                out.append(d)
                if "@graph" in d:
                    stack.append(d["@graph"])
    return out


def clean(s):
    if not isinstance(s, str):
        return None
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def book_from_breadcrumb(blocks):
    """BreadcrumbList position 4 is Hadith > <collection> > <book>."""
    for d in blocks:
        if d.get("@type") != "BreadcrumbList":
            continue
        for it in (d.get("itemListElement") or []):
            if not isinstance(it, dict):
                continue
            if it.get("position") in (4, "4"):
                nm = it.get("name")
                if isinstance(nm, dict):
                    nm = nm.get("name")
                return clean(nm)
    return None


def book_from_about(blocks):
    """The Article's about[0].name repeats the book."""
    for d in blocks:
        ab = d.get("about")
        if not ab:
            continue
        if isinstance(ab, dict):
            ab = [ab]
        if isinstance(ab, list) and ab and isinstance(ab[0], dict):
            return clean(ab[0].get("name"))
    return None


def arabic_kitab(body):
    """The Arabic line '<collection> / كتاب ... / <number>' - reported only,
    never written, so the operator can see what the English corresponds to."""
    m = re.search(r"/\s*(كتاب[^/<>]{1,60}?)\s*/", body)
    return clean(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true",
                    help="write the column. Without this, nothing is written.")
    ap.add_argument("--row", help="one hadith_number only (P325: a write tool "
                                  "you cannot aim gets pointed at everything)")
    ap.add_argument("--include-filled", action="store_true",
                    help="also report rows that already have a book value, so "
                         "the two hand-derived ones can be compared with the "
                         "source. Never writes over them unless --overwrite.")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace an existing book value (needs --include-filled)")
    ap.add_argument("--sleep", type=float, default=1.5,
                    help="seconds between UNCACHED fetches (politeness)")
    a = ap.parse_args()

    env = al.load_env(os.path.join(ROOT, ".env.local"))
    base, _ = al.pick(env, ("NEXT_PUBLIC_SUPABASE_URL",))
    key, _ = al.pick(env, ("SUPABASE_SERVICE_ROLE_KEY",
                           "NEXT_PUBLIC_SUPABASE_ANON_KEY"))
    if not base or not key:
        sys.exit("ABORT: supabase credentials missing from .env.local")
    base = base.rstrip("/")
    H = {"apikey": key, "Authorization": "Bearer " + key}

    q = (base + "/rest/v1/hadith_library?select=id,collection,hadith_number,"
         "book,source_url&order=collection")
    rows = json.loads(urllib.request.urlopen(
        urllib.request.Request(q, headers=H), timeout=40).read().decode())

    if a.row:
        rows = [r for r in rows if str(r.get("hadith_number")) == str(a.row)]
    todo = [r for r in rows
            if a.include_filled or not (r.get("book") or "").strip()]

    print("=" * 78)
    print(" backfill hadith_library.book from Tier 1   [%s]"
          % ("COMMIT" if a.commit else "DRY RUN"))
    print(" format: the page's own English book title, VERBATIM (P287)")
    print("=" * 78)
    print("  library rows: %d   in scope: %d" % (len(rows), len(todo)))
    print()

    ok, problems, skipped = [], [], []
    fetched = 0
    for r in todo:
        ref = "%s #%s" % (r["collection"], r["hadith_number"])
        url, how = vmn.target_url(r)
        if not url:
            problems.append((ref, "no page: %s" % how, None, None))
            continue
        try:
            body, cached = vmn.fetch(url, use_cache=True)
        except Exception as e:
            problems.append((ref, "fetch failed: %s" % e, None, None))
            continue
        if not cached:
            fetched += 1
            time.sleep(a.sleep)

        blocks = ld_blocks(body)
        b1 = book_from_breadcrumb(blocks)
        b2 = book_from_about(blocks)
        ar = arabic_kitab(body)

        if not b1 and not b2:
            problems.append((ref, "no book in the page's JSON-LD", None, ar))
            continue
        if not b1 or not b2:
            problems.append((ref, "only one of the two sources carried it "
                                  "(breadcrumb=%r about=%r)" % (b1, b2), None, ar))
            continue
        if b1 != b2:
            problems.append((ref, "the page's two sources DISAGREE "
                                  "(breadcrumb=%r about=%r)" % (b1, b2), None, ar))
            continue
        ok.append((ref, r, b1, ar, cached))

    print("=" * 78)
    print(" AGREED on both page sources: %d" % len(ok))
    print("=" * 78)
    for ref, r, b, ar, cached in ok:
        cur = (r.get("book") or "").strip()
        mark = "    " if not cur else ("same" if cur == b else "DIFF")
        print("  %-4s %-24s %-46s %s" % (mark, ref, b, ar or ""))
        if cur and cur != b:
            print("       existing value: %r" % cur)
    print()

    if problems:
        print("=" * 78)
        print(" NOT RESOLVED - reported, never guessed: %d" % len(problems))
        print("=" * 78)
        for ref, why, _b, ar in problems:
            print("  %-24s %s" % (ref, why))
            if ar:
                print("       arabic on page: %s" % ar)
        print()

    if not a.commit:
        print("DRY RUN - nothing written. %d page(s) fetched, rest from cache."
              % fetched)
        print("Read the titles above, then re-run with --commit.")
        return

    # ------------------------------------------------------------- WRITE
    wrote, failed, left = 0, 0, 0
    for ref, r, b, ar, cached in ok:
        cur = (r.get("book") or "").strip()
        if cur == b:
            left += 1
            continue
        if cur and not a.overwrite:
            print("  SKIP %-24s already has %r (--overwrite to replace)"
                  % (ref, cur))
            left += 1
            continue
        payload = json.dumps({"book": b}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            "%s/rest/v1/hadith_library?id=eq.%s" % (base, r["id"]),
            data=payload,
            headers=dict(H, **{"Content-Type": "application/json",
                               "Prefer": "return=representation"}),
            method="PATCH")
        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=30)
                              .read().decode())
        except Exception as e:
            print("  FAIL %-24s %s" % (ref, e))
            failed += 1
            continue
        # P096: a write that matched no row must never read as success.
        if not resp:
            print("  FAIL %-24s PATCH matched 0 rows" % ref)
            failed += 1
            continue
        got = (resp[0].get("book") or "")
        if got != b:
            print("  FAIL %-24s read-back got %r, wanted %r" % (ref, got, b))
            failed += 1
            continue
        wrote += 1
    print()
    print("  written: %d   unchanged: %d   failed: %d" % (wrote, left, failed))

    # independent read-back across the whole table
    rows2 = json.loads(urllib.request.urlopen(
        urllib.request.Request(q, headers=H), timeout=40).read().decode())
    still = [r for r in rows2 if not (r.get("book") or "").strip()]
    print("  rows still empty after the write: %d" % len(still))
    for r in still:
        print("     %s #%s" % (r["collection"], r["hadith_number"]))
    if failed:
        sys.exit(2)


main()
