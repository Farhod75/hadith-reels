# scripts/lib/source_dorar.py
# ============================================================
# Stage-0/Verify adapter: Dorar.net  [sourcing-pipeline-design.md §4]
#
# Role: Dorar is the GRADING AUTHORITY. Given a candidate's Arabic matn, we
# search Dorar, match the right card by text similarity, and take ITS grade.
# The grade comes from Dorar verbatim (authority); similarity is used ONLY to
# match the correct card — it never decides the grade (G2).
#
# Split:
#   classify_dorar_grade(ar)   -> PURE bucket: sahih|hasan|daif|unknown
#   parse_dorar(raw)           -> PURE: cards out of the HTML-in-JSON blob
#   confirm_grade(matn, cards) -> matches best card, returns its grade
#   fetch_dorar(query)         -> thin stdlib network wrapper
#
# Stdlib only + sibling dedup module. No third-party deps.
# ============================================================
import re
import json
import html
import difflib
import urllib.request
import urllib.parse

from dedup import normalize_arabic

API = "https://dorar.net/dorar_api.json"
_TAG = re.compile(r"<[^>]+>")

# Daif markers checked BEFORE positive ones so negations like "غير صحيح" /
# "لا يصح" don't get mis-read as sahih.
_DAIF_RAW = [
    "موضوع", "باطل", "منكر", "لا يصح", "لا اصل", "غير صحيح", "ليس بصحيح",
    "ضعيف", "واه", "شاذ", "متروك", "لا يثبت",
]
_DAIF_N = [normalize_arabic(x) for x in _DAIF_RAW]
_SAHIH_N = normalize_arabic("صحيح")
_HASAN_N = normalize_arabic("حسن")


def classify_dorar_grade(grade_ar: str) -> str:
    n = normalize_arabic(grade_ar)
    if not n:
        return "unknown"
    if any(m and m in n for m in _DAIF_N):
        return "daif"
    if _SAHIH_N in n:
        return "sahih"
    if _HASAN_N in n:
        return "hasan"
    return "unknown"


# Each Dorar card: matn, then labelled metadata. Field values are text nodes
# that end at the next tag ("[^<]+"), which prevents a grade from swallowing the
# following card's matn. Matn = text between the previous card's end and this one.
_BLOCK = re.compile(
    r"الراوي\s*:?\s*(?:<[^>]*>)?\s*(?P<rawi>[^<]+).*?"
    r"المحدث\s*:?\s*(?:<[^>]*>)?\s*(?P<muhaddith>[^<]+).*?"
    r"المصدر\s*:?\s*(?:<[^>]*>)?\s*(?P<source>[^<]+).*?"
    r"(?:الصفحة أو الرقم|الرقم)\s*:?\s*(?:<[^>]*>)?\s*(?P<number>[^<]+).*?"
    r"(?:خلاصة )?حكم المحدث\s*:?\s*(?:<[^>]*>)?\s*(?P<grade>[^<]+)",
    re.DOTALL,
)


def _strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", s))).strip()


def parse_dorar(raw) -> list:
    data = json.loads(raw) if isinstance(raw, str) else raw
    blob = ""
    if isinstance(data, dict):
        blob = (data.get("ahadith") or {}).get("result", "") or ""
    cards, prev_end = [], 0
    for m in _BLOCK.finditer(blob):
        cards.append({
            "matn": _strip_html(blob[prev_end:m.start()]),
            "rawi": m.group("rawi").strip(),
            "muhaddith": m.group("muhaddith").strip(),
            "source": m.group("source").strip(),
            "number": m.group("number").strip(),
            "grade": m.group("grade").strip(),
        })
        prev_end = m.end()
    return cards


def _match_score(candidate: str, card_matn: str) -> float:
    """
    Robust matn-match for grade confirmation. Dorar often returns the FULLER
    hadith, so a length-penalizing ratio under-scores a shorter candidate.
    We blend sequence ratio with token coverage (share of candidate words present
    in the card) and take the max, so a shorter candidate still matches its
    fuller Dorar entry. Used ONLY to pick the right card — never to grade (G2).
    """
    a, b = normalize_arabic(candidate), normalize_arabic(card_matn)
    if not a or not b:
        return 0.0
    seq = difflib.SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    coverage = len(ta & tb) / len(ta) if ta else 0.0
    return max(seq, coverage)


def confirm_grade(candidate_arabic: str, cards: list, threshold: float = 0.7) -> dict:
    """
    Match the candidate matn to the best Dorar card, return its grade. threshold
    is looser than dedup's (Dorar matn may carry extra isnad / fuller wording).
    """
    best, best_score = None, 0.0
    for c in cards:
        sc = _match_score(candidate_arabic, c.get("matn", ""))
        if sc > best_score:
            best, best_score = c, sc
    if best and best_score >= threshold:
        return {
            "matched": True,
            "score": round(best_score, 3),
            "grade_bucket": classify_dorar_grade(best.get("grade", "")),
            "grade_raw": best.get("grade"),
            "muhaddith": best.get("muhaddith"),
            "source": best.get("source"),
            "number": best.get("number"),
        }
    return {"matched": False, "score": round(best_score, 3), "grade_bucket": "unknown"}


def fetch_dorar(query: str, *, timeout: int = 20) -> dict:
    """Thin wrapper. Validate the param shape against live dorar.net once."""
    url = f"{API}?{urllib.parse.urlencode({'skey': query})}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))
