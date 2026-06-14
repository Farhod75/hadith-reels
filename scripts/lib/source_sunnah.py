# scripts/lib/source_sunnah.py
# ============================================================
# Stage-0 source adapter: Sunnah.com  [sourcing-pipeline-design.md §4, §5 Stage 0]
#
# Role per the curated authority table (§4):
#   Sunnah.com = Tier-1 for Arabic matn + citation + English translation.
#   Grade is captured PRELIMINARILY (its `grades` array) — enough to drop daif
#   at the door — but Dorar remains the grading AUTHORITY (confirmed at verify).
#
# Split:
#   parse_sunnah_hadith(obj)  -> PURE, offline-testable. Drops daif here.
#   fetch_hadith(...)         -> thin stdlib (urllib) network wrapper.
#
# Stdlib only: re, json, html, urllib.
# ============================================================
import re
import json
import html
import urllib.request
import urllib.error

API_BASE = "https://api.sunnah.com/v1"
MOCK_BASE = "https://stoplight.io/mocks/sunnah/api/352643496"  # no key needed (testing)

_TAG = re.compile(r"<[^>]+>")


def _clean_body(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", text))).strip()


def classify_grade(grades: list) -> tuple:
    """
    Map Sunnah's grade strings to a canonical bucket.
    Returns (bucket, conflict) where bucket in {sahih, hasan, daif, unknown}.
    Priority sahih > hasan > daif. `conflict` is True if graders disagree
    (e.g. one sahih + one daif) — surfaced for the human / Dorar, not resolved here.
    """
    cats = set()
    for g in grades or []:
        s = (g.get("grade") if isinstance(g, dict) else str(g)) or ""
        s = s.lower()
        if "sahih" in s or "sahih" in s.replace("ḥ", "h"):
            cats.add("sahih")
        elif "hasan" in s:
            cats.add("hasan")
        elif any(k in s for k in ("da'if", "daif", "da’if", "weak", "munkar", "mawdu", "fabricat")):
            cats.add("daif")
    if not cats:
        return ("unknown", False)
    conflict = "daif" in cats and ("sahih" in cats or "hasan" in cats)
    if "sahih" in cats:
        return ("sahih", conflict)
    if "hasan" in cats:
        return ("hasan", conflict)
    return ("daif", conflict)


def build_source_url(collection: str, number: str) -> str:
    """Canonical DEEP-LINK (not a homepage) — reused by reel captions later."""
    return f"https://sunnah.com/{collection}:{number}"


def parse_sunnah_hadith(obj: dict) -> dict:
    """
    Parse one Sunnah.com hadith object into a Stage-0 result.
    Returns {status, reason, candidate} where:
      status   = 'candidate' | 'dropped'
      reason   = drop reason (when dropped) or ''
      candidate= dict ready for hadith_candidates, or None
    Daif / ungraded are DROPPED at the door (G: sahih/hasan only).
    """
    collection = (obj.get("collection") or "").strip().lower()
    number = str(obj.get("hadithNumber") or obj.get("hadith_number") or "").strip()
    entries = obj.get("hadith") or []

    ar = en = ""
    grades = []
    for e in entries:
        lang = (e.get("lang") or "").lower()
        body = _clean_body(e.get("body", ""))
        if lang == "ar" and not ar:
            ar = body
        elif lang == "en" and not en:
            en = body
        for gr in e.get("grades") or []:
            grades.append(gr)

    if not ar:
        return {"status": "dropped", "reason": "no Arabic matn", "candidate": None}

    bucket, conflict = classify_grade(grades)
    if bucket not in ("sahih", "hasan"):
        return {"status": "dropped", "reason": f"grade={bucket} (sahih/hasan only)", "candidate": None}

    candidate = {
        "collection": collection,
        "hadith_number": number,
        "narrator": None,  # Sunnah embeds isnad in body; not split out
        "grade": bucket,
        "grading_source": "sunnah.com (preliminary — confirm via Dorar)",
        "grade_conflict": conflict,
        "raw_grades": grades,
        "source_urls": {"sunnah": build_source_url(collection, number)},
        "text_arabic": ar,
        "text_english": en,
    }
    return {"status": "candidate", "reason": "", "candidate": candidate}


def fetch_hadith(collection: str, number: str, *, api_key: str | None = None,
                 base_url: str = API_BASE, timeout: int = 20) -> dict:
    """
    Thin network wrapper. Use base_url=MOCK_BASE (no key) to test plumbing.
    Verify the exact path against sunnah.stoplight.io if the API changes.
    """
    url = f"{base_url}/collections/{collection}/hadiths/{number}"
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))
