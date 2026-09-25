#!/usr/bin/env python3
# scripts/source-candidates.py
# ============================================================
# Stage 0 → Stage 1 batch runner.  [sourcing-pipeline-design.md §5]
#   refs → fetch (Sunnah) → parse + drop daif → dedup vs LIVE library → JSON
#
# READ-ONLY: reads hadith_library for the dedup baseline; writes proposals to
# out/candidates.json for human review. NO writes to hadith_library or
# hadith_candidates (that insert is a later, gated step).
#
# Usage:
#   python scripts/source-candidates.py --source mock                # keyless plumbing test
#   python scripts/source-candidates.py --source live --refs out/source-refs.txt
#   python scripts/source-candidates.py --provider hadeethenc --refs out/he-refs.txt
#
# refs file: one "collection:number" per line (e.g. bukhari:1), # for comments.
# With --provider hadeethenc the refs are HadeethEnc ids instead (e.g. 66511).
#
# P172: HadeethEnc is keyless, so this path works without Sunnah API issue
# #3675, and it carries AUTHORITATIVE translations (uz Cyrillic, tg real Tajik)
# rather than machine ones. It gives no hadith NUMBER, so Dorar supplies the
# citation as well as the grade; a candidate whose citation never resolves is
# dropped rather than promoted uncitable.
# Stdlib only: os, sys, json, argparse, urllib.
# ============================================================
import os
import sys
import json
import argparse
import urllib.request

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, "lib"))
sys.path.insert(0, _here)
from source_sunnah import fetch_hadith, parse_sunnah_hadith, API_BASE, MOCK_BASE  # noqa: E402
from source_dorar import fetch_dorar, parse_dorar, confirm_grade  # noqa: E402
from dedup import find_duplicates, canonical_collection  # noqa: E402
from source_hadeethenc import (fetch_hadeeth as he_fetch,      # noqa: E402
                               fetch_langs as he_langs,
                               parse_hadeeth as he_parse)


def load_env(path=".env.local") -> dict:
    env = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


def parse_ref(ref: str):
    if ":" not in ref:
        raise ValueError(f"bad ref '{ref}' (expected collection:number)")
    c, n = ref.split(":", 1)
    return c.strip().lower(), n.strip()


def read_library(url: str, key: str) -> list:
    endpoint = f"{url}/rest/v1/hadith_library?select=id,collection,hadith_number,text_arabic"
    req = urllib.request.Request(
        endpoint, headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def annotate_candidate(cand: dict, library: list, fuzzy_threshold: float = 0.85) -> dict:
    """Attach dedup result + a queue_status. Fuzzy is advisory (G2)."""
    dd = find_duplicates(cand, library, fuzzy_threshold)
    cand["dedup"] = dd
    cand["queue_status"] = (
        "duplicate" if dd["hard_hit"] else "review_fuzzy" if dd["fuzzy_hits"] else "new"
    )
    return cand


def apply_dorar_verdict(cand: dict, res: dict):
    """
    PURE: apply a confirm_grade() result to the candidate.
    Returns a DROP reason string if the candidate must be rejected, else None.
    The acquisition grade is preliminary; Dorar's is authoritative (§4).

    P172: for a HadeethEnc candidate, Dorar ALSO supplies the CITATION.
    HadeethEnc gives no hadith number — its `reference` field is a free-text
    Arabic bibliography that lists two Bukhari numbers for one hadeeth (P165)
    — so the candidate arrives with citation_pending=True and empty
    collection/hadith_number. Without a resolved citation it cannot be deduped
    (hard_key needs both) and cannot be cited in a caption, so it is DROPPED
    rather than promoted uncitable.
    """
    pending = bool(cand.get("citation_pending"))

    if not res.get("matched"):
        cand["grade_confirmed"] = False
        cand["grade_note"] = "dorar: no matching card — grade UNCONFIRMED"
        if pending:
            return "citation unresolved: no Dorar match, and HadeethEnc gives no number"
        return None

    bucket = res.get("grade_bucket")
    if bucket == "daif":
        return f"Dorar authority override: daif (source grade {cand.get('grade')})"

    if bucket in ("sahih", "hasan"):
        cand["grade"] = bucket
        cand["grading_source"] = f"dorar.net (authority; {res.get('muhaddith', '')})".strip()
        cand["grade_confirmed"] = True
        cand["dorar"] = {k: res.get(k) for k in ("score", "grade_raw", "muhaddith", "source", "number")}

        if pending:
            # canonical_collection returns None for commentaries and takhrij
            # works, so an unreliable citation is refused here rather than
            # stored — precision over recall, same rule as card_to_candidate.
            coll = canonical_collection(res.get("source") or "")
            num = (res.get("number") or "").strip()
            if not coll or not num:
                return ("citation unresolved: dorar source=%r number=%r"
                        % (res.get("source"), res.get("number")))
            cand["collection"] = coll
            cand["hadith_number"] = num
            cand["source_book"] = (res.get("source") or "").strip()
            cand["citation_pending"] = False
        return None

    cand["grade_confirmed"] = False
    cand["grade_note"] = f"dorar: matched but grade unparseable ({res.get('grade_raw')})"
    if pending:
        return f"citation unresolved: dorar grade unparseable ({res.get('grade_raw')})"
    return None


def confirm_via_dorar(cand: dict):
    """Network: fetch Dorar for this matn and confirm grade. Degrades gracefully."""
    try:
        cards = parse_dorar(fetch_dorar(cand["text_arabic"]))
        res = confirm_grade(cand["text_arabic"], cards)
    except Exception as e:
        cand["grade_confirmed"] = False
        cand["grade_note"] = f"dorar fetch error: {e}"
        return None
    return apply_dorar_verdict(cand, res)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["mock", "live"], default="mock")
    ap.add_argument("--refs", default="out/source-refs.txt")
    ap.add_argument("--no-dorar", action="store_true", help="skip Dorar grade confirmation")
    ap.add_argument("--provider", choices=["sunnah", "hadeethenc"], default="sunnah",
                    help="acquisition source. hadeethenc is keyless and supplies "
                         "authoritative EN/RU/UZ/TJ translations; refs are HadeethEnc ids.")
    args = ap.parse_args()

    # P172: HadeethEnc candidates have no citation until Dorar supplies one, so
    # --no-dorar would drop every single one. Fail loudly rather than silently.
    if args.provider == "hadeethenc" and args.no_dorar:
        ap.error("--provider hadeethenc requires Dorar: it is the only source of "
                 "collection + hadith number for these candidates")

    env = {**load_env(), **os.environ}
    url, key = env.get("NEXT_PUBLIC_SUPABASE_URL"), env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("❌ Missing NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env.local")
        sys.exit(1)

    base = MOCK_BASE if args.source == "mock" else API_BASE
    api_key = "123" if args.source == "mock" else env.get("SUNNAH_API_KEY")  # mock accepts any key presence
    if args.provider == "sunnah" and args.source == "live" and not api_key:
        print("❌ --source live needs SUNNAH_API_KEY in .env.local")
        sys.exit(1)

    try:
        with open(args.refs, encoding="utf-8") as f:
            refs = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        refs = ["66511", "66515"] if args.provider == "hadeethenc" else ["bukhari:1", "muslim:223"]
        print(f"ℹ {args.refs} not found — using sample refs: {refs}")

    print("📚 Reading live hadith_library (dedup baseline, read-only)...")
    library = read_library(url, key)
    print(f"   {len(library)} rows.")

    print(f"🔎 provider: {args.provider}")
    results, dropped = [], []
    for ref in refs:
        try:
            if args.provider == "hadeethenc":
                # Fetch the Arabic payload plus every language we ship. A
                # missing language returns 200 with an EMPTY STRING, not a 404,
                # and fetch_langs drops those rather than storing blanks (P165).
                obj = he_fetch(ref, "ar")
                parsed = he_parse(obj, he_langs(ref))
            else:
                c, n = parse_ref(ref)
                obj = fetch_hadith(c, n, api_key=api_key, base_url=base)
                parsed = parse_sunnah_hadith(obj)
        except Exception as e:
            dropped.append({"ref": ref, "reason": f"fetch/parse error: {e}"})
            continue
        if parsed["status"] == "dropped":
            dropped.append({"ref": ref, "reason": parsed["reason"]})
            continue
        cand = parsed["candidate"]
        if not args.no_dorar:
            drop_reason = confirm_via_dorar(cand)
            if drop_reason:
                dropped.append({"ref": ref, "reason": drop_reason})
                continue
        results.append(annotate_candidate(cand, library))

    os.makedirs("out", exist_ok=True)
    out = "out/candidates.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    new = sum(1 for r in results if r["queue_status"] == "new")
    dup = sum(1 for r in results if r["queue_status"] == "duplicate")
    fz = sum(1 for r in results if r["queue_status"] == "review_fuzzy")
    confirmed = sum(1 for r in results if r.get("grade_confirmed"))
    print("━" * 40)
    print(f"✅ {len(results)} candidates → {out}  (NO DB writes)")
    print(f"   new: {new}  ·  hard-duplicate: {dup}  ·  fuzzy-review: {fz}")
    print(f"   grade confirmed by Dorar: {confirmed}  ·  unconfirmed: {len(results) - confirmed}")
    pending = sum(1 for r in results if r.get("citation_pending"))
    if pending:
        print(f"   ⚠ citation still pending: {pending} (should be 0 — these cannot be promoted)")
    print(f"🗑  dropped at door: {len(dropped)}")
    for d in dropped[:10]:
        print(f"    {d['ref']}: {d['reason']}")
    print("━" * 40)


if __name__ == "__main__":
    main()
