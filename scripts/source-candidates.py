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
#
# refs file: one "collection:number" per line (e.g. bukhari:1), # for comments.
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
from dedup import find_duplicates  # noqa: E402


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["mock", "live"], default="mock")
    ap.add_argument("--refs", default="out/source-refs.txt")
    args = ap.parse_args()

    env = {**load_env(), **os.environ}
    url, key = env.get("NEXT_PUBLIC_SUPABASE_URL"), env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("❌ Missing NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env.local")
        sys.exit(1)

    base = MOCK_BASE if args.source == "mock" else API_BASE
    api_key = "123" if args.source == "mock" else env.get("SUNNAH_API_KEY")  # mock accepts any key presence
    if args.source == "live" and not api_key:
        print("❌ --source live needs SUNNAH_API_KEY in .env.local")
        sys.exit(1)

    try:
        with open(args.refs, encoding="utf-8") as f:
            refs = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        refs = ["bukhari:1", "muslim:223"]
        print(f"ℹ {args.refs} not found — using sample refs: {refs}")

    print("📚 Reading live hadith_library (dedup baseline, read-only)...")
    library = read_library(url, key)
    print(f"   {len(library)} rows.")

    results, dropped = [], []
    for ref in refs:
        try:
            c, n = parse_ref(ref)
            obj = fetch_hadith(c, n, api_key=api_key, base_url=base)
        except Exception as e:
            dropped.append({"ref": ref, "reason": f"fetch/parse error: {e}"})
            continue
        parsed = parse_sunnah_hadith(obj)
        if parsed["status"] == "dropped":
            dropped.append({"ref": ref, "reason": parsed["reason"]})
            continue
        results.append(annotate_candidate(parsed["candidate"], library))

    os.makedirs("out", exist_ok=True)
    out = "out/candidates.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    new = sum(1 for r in results if r["queue_status"] == "new")
    dup = sum(1 for r in results if r["queue_status"] == "duplicate")
    fz = sum(1 for r in results if r["queue_status"] == "review_fuzzy")
    print("━" * 40)
    print(f"✅ {len(results)} candidates → {out}  (NO DB writes)")
    print(f"   new: {new}  ·  hard-duplicate: {dup}  ·  fuzzy-review: {fz}")
    print(f"🗑  dropped at door: {len(dropped)}")
    for d in dropped[:10]:
        print(f"    {d['ref']}: {d['reason']}")
    print("━" * 40)


if __name__ == "__main__":
    main()
