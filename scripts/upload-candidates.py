#!/usr/bin/env python3
# scripts/upload-candidates.py
# ============================================================
# Stage 0→3 upload runner.  [sourcing-pipeline-design.md]
#   queries → search_dorar → dedup vs LIVE library → hadith_candidates
#
# Dorar is public + authoritative, so this produces REAL graded candidates
# with no API key. daif dropped at the source; grade already confirmed.
#
# Dry-run (default):  python scripts/upload-candidates.py
# Persist:            python scripts/upload-candidates.py --commit
# Diagnose parser:    python scripts/upload-candidates.py --debug
#
# Writes a review checkpoint to out/candidates-dorar.json either way.
# Stdlib only.
# ============================================================
import os
import sys
import json
import argparse
import hashlib
import urllib.request
import urllib.error

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, "lib"))
sys.path.insert(0, _here)
from source_dorar import search_dorar, fetch_dorar  # noqa: E402
from dedup import find_duplicates, normalize_arabic  # noqa: E402


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


def read_text_lines(path: str) -> list:
    """Read a text file tolerant of encoding. Arabic query files written via
    PowerShell `echo > file` come out UTF-16/BOM, not UTF-8 — handle both."""
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return raw.decode(enc).splitlines()
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").splitlines()


def read_library(url: str, key: str) -> list:
    endpoint = f"{url}/rest/v1/hadith_library?select=id,collection,hadith_number,text_arabic"
    req = urllib.request.Request(
        endpoint, headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def syn_number(number: str, matn: str) -> str:
    """Stable hadith_number; if Dorar gave none, derive one from the matn so the
    UNIQUE(collection, hadith_number) key can't collapse distinct hadiths."""
    return number if number else "auto-" + hashlib.sha1(normalize_arabic(matn).encode("utf-8")).hexdigest()[:10]


def to_row(cand: dict, dd: dict) -> dict:
    """PURE: candidate + dedup result → hadith_candidates row."""
    status = "needs_human" if (dd["fuzzy_hits"] and not dd["hard_hit"]) else "deduped"
    return {
        "collection": cand["collection"],
        "hadith_number": syn_number(cand.get("hadith_number", ""), cand["text_arabic"]),
        "narrator": cand.get("narrator"),
        "grade": cand["grade"],
        "grading_source": cand["grading_source"],
        "grade_confirmed": cand.get("grade_confirmed", True),
        "source_urls": cand.get("source_urls", {}),
        "text_arabic": cand["text_arabic"],
        "status": status,
        "dedup_hard_hit": dd["hard_hit"],
        "dedup_fuzzy_hits": dd["fuzzy_hits"],
    }


def insert_candidates(url: str, key: str, rows: list) -> int:
    endpoint = f"{url}/rest/v1/hadith_candidates"
    data = json.dumps(rows, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=data, method="POST",
        headers={
            "apikey": key, "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal,resolution=ignore-duplicates",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default="out/source-queries.txt")
    ap.add_argument("--commit", action="store_true", help="insert into hadith_candidates")
    ap.add_argument("--max-per-query", type=int, default=20)
    ap.add_argument("--debug", action="store_true", help="print raw Dorar response for the first query")
    args = ap.parse_args()

    env = {**load_env(), **os.environ}
    url, key = env.get("NEXT_PUBLIC_SUPABASE_URL"), env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("❌ Missing NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env.local")
        sys.exit(1)

    try:
        lines = read_text_lines(args.queries)
        queries = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        queries = ["إنما الأعمال بالنيات", "الطهور شطر الإيمان"]
        print(f"ℹ {args.queries} not found — using sample queries.")

    if args.debug and queries:
        raw = fetch_dorar(queries[0])
        blob = (raw.get("ahadith") or {}).get("result", "") if isinstance(raw, dict) else ""
        print("DEBUG keys:", list(raw.keys()) if isinstance(raw, dict) else type(raw))
        print("DEBUG result length:", len(blob))
        print("DEBUG snippet:\n", blob[:900])
        return

    print("📚 Reading live hadith_library (dedup baseline, read-only)...")
    library = read_library(url, key)
    print(f"   {len(library)} rows.")

    seen, rows, dropped = set(), [], []
    hard = fuzzy = 0
    for q in queries:
        try:
            res = search_dorar(q)
        except Exception as e:
            dropped.append({"query": q, "reason": f"dorar error: {e}"})
            continue
        dropped += [{"query": q, "reason": r} for r in res["dropped"]]
        for cand in res["candidates"][: args.max_per_query]:
            kid = normalize_arabic(cand["text_arabic"])
            if kid in seen:
                continue  # cross-query dedupe
            seen.add(kid)
            dd = find_duplicates(cand, library)
            if dd["hard_hit"]:
                hard += 1
                continue  # already in library
            if dd["fuzzy_hits"]:
                fuzzy += 1
            rows.append(to_row(cand, dd))

    os.makedirs("out", exist_ok=True)
    with open("out/candidates-dorar.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print("━" * 44)
    print(f"📥 rows ready: {len(rows)}  → out/candidates-dorar.json")
    print(f"   fuzzy-flagged (needs_human): {fuzzy}")
    print(f"   skipped, already in library (hard dup): {hard}")
    print(f"   dropped (daif/empty/errors): {len(dropped)}")
    if args.commit and rows:
        try:
            st = insert_candidates(url, key, rows)
            print(f"✅ COMMIT: inserted into hadith_candidates (HTTP {st}; duplicates ignored).")
        except urllib.error.HTTPError as e:
            print(f"❌ insert failed: HTTP {e.code} — {e.read().decode()[:300]}")
    else:
        print("🧪 DRY RUN — re-run with --commit to insert into hadith_candidates.")
    print("━" * 44)


if __name__ == "__main__":
    main()
