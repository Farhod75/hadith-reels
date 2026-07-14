#!/usr/bin/env python3
# scripts/promote-candidates.py
# ============================================================
# Stage 5 promote runner.  [sourcing-pipeline-design.md]
#   hadith_candidates(status='approved') -> hadith_library
#     + hadith_promotions audit row
#     + mark candidate status='promoted', promoted_library_id=<id>
#
# Human gate (Stage 4) runs in SQL and sets status='approved' first.
# This script ONLY moves already-approved, grade-confirmed candidates.
#
# Dry-run (default):  python scripts/promote-candidates.py
# Persist:            python scripts/promote-candidates.py --commit
# Preview mapping:    python scripts/promote-candidates.py --show
#
# Idempotent: a candidate with status='promoted' is skipped; re-running is safe.
# Stdlib only. Uses SUPABASE_SERVICE_ROLE_KEY (bypasses RLS, server-side).
# ============================================================
import os
import sys
import json
import argparse
import urllib.request
import urllib.error

_here = os.path.dirname(os.path.abspath(__file__))


# ── env loader (mirrors upload-candidates.py) ────────────────────────────────
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
    # allow real environment to override / supply
    for k in ("NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


# ── PostgREST helpers (stdlib urllib) ────────────────────────────────────────
def _headers(key: str, extra: dict = None) -> dict:
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def rest_get(url: str, key: str, table: str, query: str) -> list:
    endpoint = f"{url}/rest/v1/{table}?{query}"
    req = urllib.request.Request(endpoint, headers=_headers(key), method="GET")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


def rest_insert(url: str, key: str, table: str, row: dict) -> dict:
    endpoint = f"{url}/rest/v1/{table}"
    body = json.dumps(row, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=body,
        headers=_headers(key, {"Prefer": "return=representation"}),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.loads(r.read().decode("utf-8"))
        return out[0] if isinstance(out, list) and out else out


def rest_patch(url: str, key: str, table: str, query: str, patch: dict) -> None:
    endpoint = f"{url}/rest/v1/{table}?{query}"
    body = json.dumps(patch, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=body,
        headers=_headers(key, {"Prefer": "return=minimal"}),
        method="PATCH",
    )
    urllib.request.urlopen(req, timeout=30).read()


# ── source_urls (jsonb) -> one canonical deep-link ───────────────────────────
def pick_deeplink(source_urls) -> str:
    """Prefer Dorar, then Sunnah, then any first URL."""
    if not source_urls:
        return ""
    if isinstance(source_urls, str):
        try:
            source_urls = json.loads(source_urls)
        except Exception:
            return source_urls
    if isinstance(source_urls, dict):
        for pref in ("dorar", "sunnah", "hadeethenc"):
            if source_urls.get(pref):
                return source_urls[pref]
        # else first value
        for v in source_urls.values():
            if v:
                return v
    if isinstance(source_urls, list) and source_urls:
        return source_urls[0]
    return ""


# ── candidate -> hadith_library row (the mapping) ────────────────────────────
def map_to_library(c: dict) -> dict:
    cyr = c.get("text_uzbek_cyrillic")
    return {
        "text_arabic":         c.get("text_arabic"),
        "text_english":        c.get("text_english"),
        "text_russian":        c.get("text_russian"),
        "text_uzbek_cyrillic": cyr,
        "text_uzbek_latin":    c.get("text_uzbek_latin"),
        "text_uzbek":          cyr,                       # legacy col = Cyrillic (canonical)
        "text_tajik":          c.get("text_tajik"),
        "narrator":            c.get("narrator"),
        "collection":          c.get("collection"),
        "book":                None,                      # not in candidates
        "hadith_number":       c.get("hadith_number"),
        "grade":               c.get("grade"),
        "tags":                [],                        # empty — red_flags is a verifier concept
        "source_url":          pick_deeplink(c.get("source_urls")),
        "authority":           c.get("grading_source"),
        # created_at: let DB default / or set explicitly if no default
    }


LIBRARY_COLS = [
    "text_arabic", "text_english", "text_russian", "text_uzbek_cyrillic",
    "text_uzbek_latin", "text_uzbek", "text_tajik", "narrator", "collection",
    "book", "hadith_number", "grade", "tags", "source_url", "authority",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="actually write (default: dry-run)")
    ap.add_argument("--show", action="store_true", help="print full mapping for each candidate")
    ap.add_argument("--reviewer", default="farhod", help="reviewed_by value for audit")
    args = ap.parse_args()

    env = load_env()
    url = env.get("NEXT_PUBLIC_SUPABASE_URL")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("❌ Missing NEXT_PUBLIC_SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env.local")
        sys.exit(1)

    # Read approved, grade-confirmed, not-yet-promoted candidates
    q = ("select=*&status=eq.approved&grade_confirmed=eq.true"
         "&grade=in.(sahih,hasan)&promoted_library_id=is.null")
    candidates = rest_get(url, key, "hadith_candidates", q)

    print("━" * 42)
    print(f"📥 approved & ready to promote: {len(candidates)}")
    if not candidates:
        print("   nothing to do.")
        print("🧪 DRY RUN" if not args.commit else "✅ COMMIT")
        return

    promoted = 0
    skipped = 0
    for c in candidates:
        cid = c.get("candidate_id")
        coll = c.get("collection")
        num = c.get("hadith_number")
        grade = c.get("grade")

        # belt-and-suspenders guard (gate should have caught these)
        if grade not in ("sahih", "hasan") or not c.get("grade_confirmed"):
            print(f"   ⏭  skip {coll} {num}: grade guard ({grade})")
            skipped += 1
            continue

        lib_row = map_to_library(c)
        deeplink = lib_row["source_url"]

        print(f"   → {coll} {num} [{grade}]  uzbek_cyr={'✓' if lib_row['text_uzbek_cyrillic'] else '—'} "
              f"en={'✓' if lib_row['text_english'] else '—'} deeplink={'✓' if deeplink else '—'}")
        if args.show:
            print(json.dumps(lib_row, ensure_ascii=False, indent=2))

        if not args.commit:
            continue

        # 1. insert into library
        new_row = rest_insert(url, key, "hadith_library", lib_row)
        library_id = str(new_row.get("id"))

        # 2. audit row
        rest_insert(url, key, "hadith_promotions", {
            "candidate_id":    cid,
            "library_id":      library_id,
            "promote_mode":    "insert",
            "reviewed_by":     args.reviewer,
            "source_deeplink": deeplink,
            "columns_written": [k for k in LIBRARY_COLS if lib_row.get(k) not in (None, [], "")],
        })

        # 3. stamp candidate promoted (idempotency)
        rest_patch(url, key, "hadith_candidates",
                   f"candidate_id=eq.{cid}",
                   {"status": "promoted", "promote_mode": "insert",
                    "promoted_library_id": library_id})

        promoted += 1

    print("━" * 42)
    if args.commit:
        print(f"✅ promoted: {promoted}   skipped: {skipped}")
    else:
        print(f"🧪 DRY RUN — {len(candidates)} would promote (skipped {skipped}). Re-run with --commit.")


if __name__ == "__main__":
    main()