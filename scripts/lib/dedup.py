# scripts/lib/dedup.py
# ============================================================
# Stage-1 dedup core for the hadith sourcing pipeline.
# Pure + deterministic. No network, no DB. [sourcing-pipeline-design.md §5 Stage 1]
#
# Two tiers:
#   1A HARD KEY  — (normalized collection, normalized number) exact match.
#                  Authoritative: a hard hit means "same citation".
#   1B FUZZY     — normalized-Arabic similarity. ADVISORY ONLY: surfaced for
#                  the human gate, NEVER an auto-drop. (Guardrail G2: embeddings
#                  / similarity never decide admission; a human does.)
#
# Stdlib only: re, unicodedata, difflib.
# ============================================================
import re
import unicodedata
import difflib

# ---------- Arabic matn normalization ----------
# NFD + combining-mark strip removes ALL harakat (tashkeel) and, as a bonus,
# decomposes hamza-carriers (أ إ آ ؤ ئ) to their base letters. A few letters
# that are their own code points still need explicit mapping.

def normalize_arabic(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))  # drop harakat + decomposed hamza
    s = s.replace("\u0640", "")        # tatweel (kashida)
    s = s.replace("\u0671", "\u0627")  # alef wasla  -> alef
    s = s.replace("\u0649", "\u064A")  # alef maqsura -> ya
    s = s.replace("\u0629", "\u0647")  # ta marbuta  -> ha
    s = s.replace("\u0621", "")        # standalone hamza -> drop
    s = re.sub(r"[^\u0621-\u064A\s]", " ", s)  # keep only Arabic letters + space
    s = re.sub(r"\s+", " ", s).strip()
    return s


def similarity(a: str, b: str) -> float:
    """0..1 similarity on normalized Arabic. Advisory metric only."""
    na, nb = normalize_arabic(a), normalize_arabic(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


# ---------- Collection / number normalization ----------
# Curated alias map (G2: curated, not fuzzy). Unknown collections still get a
# stable slug so they can be flagged rather than silently merged.
_COLLECTION_ALIASES = {
    "bukhari": {"bukhari", "sahih al bukhari", "sahih bukhari", "al bukhari", "صحيح البخاري", "البخاري"},
    "muslim": {"muslim", "sahih muslim", "صحيح مسلم", "مسلم"},
    "abudawud": {"abu dawud", "abi dawud", "sunan abi dawud", "sunan abu dawud", "ابو داود", "سنن ابي داود"},
    "tirmidhi": {"tirmidhi", "jami at tirmidhi", "sunan al tirmidhi", "الترمذي", "جامع الترمذي"},
    "nasai": {"nasai", "sunan an nasai", "sunan al nasai", "النسائي", "سنن النسائي"},
    "ibnmajah": {"ibn majah", "sunan ibn majah", "ابن ماجه", "سنن ابن ماجه"},
    "ahmad": {"ahmad", "musnad ahmad", "مسند احمد", "احمد"},
    "malik": {"malik", "muwatta", "muwatta malik", "موطا مالك", "مالك"},
    "darimi": {"darimi", "sunan al darimi", "الدارمي"},
}


def _clean_name(name: str) -> str:
    s = unicodedata.normalize("NFD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).replace("\u0640", "")
    s = s.lower()
    s = re.sub(r"[^a-z\u0621-\u064A]+", " ", s)  # latin + arabic letters only
    return re.sub(r"\s+", " ", s).strip()


_REVERSE = {}
for _canon, _names in _COLLECTION_ALIASES.items():
    for _n in _names:
        _REVERSE[_clean_name(_n)] = _canon


def normalize_collection(name: str) -> str:
    if not name:
        return ""
    c = _clean_name(name)
    if c in _REVERSE:
        return _REVERSE[c]
    return _REVERSE.get(c.replace(" ", ""), c.replace(" ", ""))


_AR_DIGITS = {ord("٠") + i: ord("0") + i for i in range(10)}


def normalize_number(num) -> str:
    if num is None:
        return ""
    s = str(num).strip().translate(_AR_DIGITS)
    m = re.search(r"\d+", s)
    if not m:
        return s.lower()
    n = str(int(m.group()))  # strip leading zeros
    tail = s[m.end():].strip()
    suffix = tail[0].lower() if tail[:1].isalpha() else ""
    return n + suffix


def hard_key(collection, number) -> tuple:
    return (normalize_collection(collection), normalize_number(number))


# ---------- The dedup decision ----------

def find_duplicates(candidate: dict, library: list, fuzzy_threshold: float = 0.85) -> dict:
    """
    candidate / library rows: dicts with keys
        id, collection, hadith_number, text_arabic.

    Returns:
        {
          "hard_hit": bool,           # authoritative same-citation match
          "hard_match_id": id | None,
          "fuzzy_hits": [ {id, hadith_number, score}, ... ]  # ADVISORY ONLY (G2)
        }

    NOTE: fuzzy hits are never an auto-drop. They are surfaced to the human
    gate. Only a human admits or rejects. (Guardrail G2.)
    """
    ckey = hard_key(candidate.get("collection"), candidate.get("hadith_number"))
    cand_text = candidate.get("text_arabic", "")
    hard_match_id = None
    fuzzy_hits = []
    for row in library:
        if hard_key(row.get("collection"), row.get("hadith_number")) == ckey:
            hard_match_id = row.get("id")
        score = similarity(cand_text, row.get("text_arabic", ""))
        if score >= fuzzy_threshold:
            fuzzy_hits.append(
                {"id": row.get("id"), "hadith_number": row.get("hadith_number"), "score": round(score, 3)}
            )
    fuzzy_hits.sort(key=lambda x: -x["score"])
    return {
        "hard_hit": hard_match_id is not None,
        "hard_match_id": hard_match_id,
        "fuzzy_hits": fuzzy_hits,
    }
