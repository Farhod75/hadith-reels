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


# ── Stage-0 JSON → hadith_candidates row (P175) ──────────────────────────────
# Deliberately NOT to_row(). to_row() is the Dorar-search path: it writes
# text_arabic only and discards every translation — which is precisely the
# thing that makes a HadeethEnc candidate worth uploading at all.
#
# No syn_number() here either. A HadeethEnc candidate reaches this stage with a
# Dorar-resolved collection + number (source-candidates.py resolves
# citation_pending before writing the JSON). Minting auto-<sha1> would only
# defer the failure: P174 refuses synthetic numbers at promotion, so the row
# would land in the table and then be permanently unpromotable.
_LANG_COLS = {
    "text_english":        "en",
    "text_russian":        "ru",
    "text_uzbek_cyrillic": "uz",
    "text_tajik":          "tg",
}


def json_to_row(c: dict, now_iso: str):
    """Map one candidates.json entry to a hadith_candidates row.
    Returns (row, None) on success, or (None, "skip reason")."""
    coll = (c.get("collection") or "").strip()
    num = str(c.get("hadith_number") or "").strip()
    if not coll or not num:
        return None, "no citation (collection/hadith_number empty)"
    if num.startswith("auto-"):
        return None, f"synthetic number {num} — not a citation"
    if c.get("citation_pending"):
        return None, "citation_pending still true — Dorar did not resolve it"
    if c.get("matn_intro_stripped") is False:
        return None, ("isnad intro present in text_arabic but not strippable — "
                      "trim it by hand and re-run (P179)")

    ar = (c.get("text_arabic") or "").strip()
    if not ar:
        return None, "no text_arabic"

    src = c.get("translation_source") or "hadeethenc.com"
    meta = {}
    row = {
        "text_arabic":     ar,
        "narrator":        c.get("narrator"),
        "collection":      coll,
        "hadith_number":   num,
        "grade":           c.get("grade"),
        "grading_source":  c.get("grading_source"),
        "grade_confirmed": bool(c.get("grade_confirmed")),
        "source_urls":     c.get("source_urls") or [],
        # 'translated', not 'verified': the text exists but has NOT been through
        # the Stage 3 A/B pass. promote-candidates.py reads status='approved'
        # only, so the human gate stays exactly where it is.
        "status":          "translated",
    }
    for col, lang in _LANG_COLS.items():
        val = (c.get(col) or "").strip()
        if not val:
            continue
        row[col] = val
        # Per-language provenance, because only ~38% of HadeethEnc rows carry
        # all four languages. A scalar source field would lie about the other 62%.
        meta[col] = {"at": now_iso, "provenance": src,
                     "source_field": "hadeethenc", "lang": lang}
    if not meta:
        return None, "no translations present — nothing this path adds"

    row["translation_meta"] = meta
    # text_uzbek_latin is deliberately left NULL. It is derived from the
    # canonical Cyrillic by scripts/derive-uzbek-latin.ts, which already owns
    # the tested deriveBothScripts + normalizeLatinApostrophes (P097). A second
    # transliterator in Python would be a second thing to keep correct.
    return row, None


def run_from_json(path: str, commit: bool, allow_fuzzy: bool) -> int:
    """--from-json path. Self-contained: own env, own POST, own exit code."""
    import datetime
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

    env = {**load_env(), **os.environ}
    url = env.get("NEXT_PUBLIC_SUPABASE_URL")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Missing NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env.local")
        return 1

    try:
        with open(path, encoding="utf-8") as f:
            cands = json.load(f)
    except FileNotFoundError:
        print(f"not found: {path}")
        print("   run:  python scripts/source-candidates.py --provider hadeethenc --refs out/source-refs.txt")
        return 1
    if not isinstance(cands, list):
        print(f"{path} is not a JSON list of candidates")
        return 1

    print("=" * 60)
    print(f"  --from-json {path}   ({len(cands)} entries)   {'COMMIT' if commit else 'DRY RUN'}")
    print("=" * 60)

    rows, skipped = [], 0
    for c in cands:
        qs = c.get("queue_status")
        if qs == "duplicate":
            print(f"   skip {c.get('collection')} {c.get('hadith_number')}: hard duplicate of library row")
            skipped += 1
            continue
        if qs == "review_fuzzy" and not allow_fuzzy:
            hits = (c.get("dedup") or {}).get("fuzzy_hits") or []
            top = hits[0]["score"] if hits else "?"
            print(f"   skip {c.get('collection')} {c.get('hadith_number')}: fuzzy {top} — pass --allow-fuzzy to override")
            skipped += 1
            continue
        row, reason = json_to_row(c, now_iso)
        if row is None:
            print(f"   skip {c.get('collection')} {c.get('hadith_number')}: {reason}")
            skipped += 1
            continue
        langs = " ".join(k.split("_", 1)[1] for k in row["translation_meta"])
        print(f"   -> {row['collection']} {row['hadith_number']} [{row['grade']}]  langs: {langs}")
        rows.append(row)

    print("-" * 60)
    print(f"   ready: {len(rows)}   skipped: {skipped}")
    if not rows:
        return 0
    if not commit:
        print("   DRY RUN — nothing written. Re-run with --commit.")
        return 0

    body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/rest/v1/hadith_candidates",
        data=body, method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            # return=representation so a zero-row insert cannot report success:
            # P096's lesson, one table over.
            "Prefer": "return=representation,resolution=ignore-duplicates",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            inserted = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"   insert failed: HTTP {e.code} {e.read().decode('utf-8', 'replace')[:500]}")
        return 1

    print(f"   inserted: {len(inserted)} of {len(rows)} "
          f"({len(rows) - len(inserted)} ignored as existing citations)")
    for r_ in inserted:
        print(f"      {r_.get('candidate_id')}  {r_.get('collection')} {r_.get('hadith_number')}")
    print("   NEXT: derive text_uzbek_latin, then Stage 3 verify, then the human gate.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default="out/source-queries.txt")
    ap.add_argument("--from-json", metavar="PATH",
                    help="upload candidates from a Stage-0 JSON (out/candidates.json) "
                         "instead of searching Dorar — keeps the translations")
    ap.add_argument("--allow-fuzzy", action="store_true",
                    help="--from-json only: also upload rows Stage 1 marked review_fuzzy "
                         "(default: skip them — G2, a human admits those)")
    ap.add_argument("--commit", action="store_true", help="insert into hadith_candidates")
    ap.add_argument("--max-per-query", type=int, default=20)
    ap.add_argument("--debug", action="store_true", help="print raw Dorar response for the first query")
    ap.add_argument("--show-drops", action="store_true", help="print why candidates were dropped")
    args = ap.parse_args()

    # P175: --from-json is its own path — different input, different mapping,
    # different table semantics. Exits before the Dorar-search flow below.
    if args.from_json:
        sys.exit(run_from_json(args.from_json, args.commit, args.allow_fuzzy))

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
    if args.show_drops and dropped:
        from collections import Counter
        cats = Counter(d["reason"].split(":")[0].strip() for d in dropped)
        print("   drop reasons:")
        for reason, n in cats.most_common():
            print(f"      {n:>3}  {reason}")
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
