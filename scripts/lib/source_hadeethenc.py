# scripts/lib/source_hadeethenc.py
# ============================================================
# Stage-0 source adapter: HadeethEnc.com  [sourcing-pipeline-design.md §4, §5 Stage 0]
#
# Role per the curated authority table (§4):
#   HadeethEnc = Tier-1. Keyless public API, so this is the adapter that makes
#   Stage 0 live without Sunnah API issue #3675.
#
# What it supplies:  Arabic matn (diacriticized), isnad opener, grade,
#                    attribution, and AUTHORITATIVE translations in ~60 langs
#                    including ru / uz (Cyrillic) / tg.
# What it does NOT:  the hadith NUMBER. Attribution is collection-level only
#                    ("متفق عليه", "رواه البخاري"). Dorar must supply collection
#                    + number before a candidate can be cited, so a candidate
#                    from here carries citation_pending=True and MUST NOT be
#                    promoted until that is resolved.
#
# Licence (hadeethenc.com API terms), enforced by how we USE the output:
#   1. No modification, addition, or deletion of the content.
#   2. Clearly credit the publisher and source (HadeethEnc.com).
#   => Moot as of P178: their translations are not carried at all. We take the
#      Arabic matn, the grade, and the deep link, and translate in-house. The
#      credit obligation therefore does not attach to our text columns --
#      translation_source stays NULL on these rows and the HadeethEnc deep
#      link in source_urls is the attribution for what we did take.
#
# Split (mirrors source_sunnah.py):
#   parse_hadeeth(obj, ...)   -> PURE, offline-testable. Drops daif here.
#   fetch_hadeeth(...)        -> thin stdlib (urllib) network wrapper.
#   fetch_list(...)           -> thin stdlib wrapper for category browsing.
#
# Stdlib only: re, json, html, urllib.
# ============================================================
import re
import json
import html
import urllib.parse
import urllib.request
import urllib.error

API_BASE = "https://hadeethenc.com/api/v1"

# Languages this project ships. `tg` is Tajik, `uz` is Uzbek (Cyrillic).
WANTED_LANGS = ("en", "ru", "uz", "tg")

_TAG = re.compile(r"<[^>]+>")


def _clean_body(text) -> str:
    """Strip tags, unescape entities, collapse whitespace (incl. the \\r the
    API embeds in `hints`). Non-str input returns ''."""
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", text))).strip()


def present(value) -> bool:
    """
    A MISSING translation comes back as an empty string, not a 404 and not
    null. Verified on id 1751, which has no uz/tg: the endpoint returns 200
    with "" for every text field. A parser that trusts the response would
    write empty fields silently, so absence is checked explicitly everywhere.
    """
    return bool(_clean_body(value))


def classify_grade(grade_ar: str, grade_local: str = "") -> tuple:
    """
    Map HadeethEnc's grade to a canonical bucket.
    Returns (bucket, conflict) with bucket in {sahih, hasan, daif, unknown},
    matching source_sunnah.classify_grade's contract.

    grade_ar is preferred because it is language-independent: the localized
    `grade` string changes per language ("Достоверный хадис", "Sahih"), while
    grade_ar is always Arabic. `conflict` is always False here -- HadeethEnc
    publishes a single editorial grade, it does not report disagreeing
    graders the way Sunnah's `grades` array does. Dorar remains the authority.
    """
    s = f"{_clean_body(grade_ar)} {_clean_body(grade_local)}".lower()
    if not s.strip():
        return ("unknown", False)
    if any(k in s for k in ("ضعيف", "موضوع", "منكر", "daif", "da'if", "weak",
                            "munkar", "mawdu", "fabricat", "слаб", "недостовер")):
        return ("daif", False)
    if any(k in s for k in ("صحيح", "sahih", "достовер", "ishonarli", "саҳеҳ")):
        return ("sahih", False)
    if any(k in s for k in ("حسن", "hasan", "хорош")):
        return ("hasan", False)
    return ("unknown", False)


def build_source_url(hadeeth_id: str, language: str = "ar") -> str:
    """Canonical DEEP-LINK (not a homepage), per the project's citation rule."""
    return f"https://hadeethenc.com/{language}/browse/hadith/{hadeeth_id}"


def parse_hadeeth(obj: dict, translations: dict | None = None) -> dict:
    """
    Parse one HadeethEnc `hadeeths/one` object into a Stage-0 result.

    obj          -- the Arabic-or-any-language payload (must carry hadeeth_ar).
    translations -- optional {lang: payload}. P178: their translations are no
                    longer carried into the row; this is consulted only as a
                    fallback source for the Arabic matn (hadeeth_ar).

    Returns {status, reason, candidate} exactly like parse_sunnah_hadith.
    Daif / ungraded are DROPPED at the door (G: sahih/hasan only).
    """
    hadeeth_id = str(obj.get("id") or "").strip()
    if not hadeeth_id:
        return {"status": "dropped", "reason": "no hadeeth id", "candidate": None}

    # The Arabic lives in `hadeeth_ar` when the payload was fetched in another
    # language, and in `hadeeth` when fetched with language=ar -- the ar
    # response has no hadeeth_ar key at all. Accept either.
    ar = _clean_body(obj.get("hadeeth_ar"))
    if not present(ar) and (obj.get("_language") or "").lower() == "ar":
        ar = _clean_body(obj.get("hadeeth"))
    if not present(ar):
        for payload in (translations or {}).values():
            if isinstance(payload, dict) and present(payload.get("hadeeth_ar")):
                ar = _clean_body(payload["hadeeth_ar"])
                break
    if not present(ar):
        return {"status": "dropped", "reason": "no Arabic matn", "candidate": None}

    # P179: hadeeth_ar arrives as isnad-intro + matn, while the library holds
    # matn only. That is why the first five rows ran 300-450 characters against
    # a library average under 130, and why every translation opened with "From
    # Abu Bakrah, may Allah be pleased with him". The intro is its own field, so
    # strip it when it is literally the prefix -- and only then. A mismatch means
    # HadeethEnc changed shape and belongs in front of a human, not silently
    # trimmed to look right.
    intro = (_clean_body(obj.get("hadeeth_intro_ar"))
             or (_clean_body(obj.get("hadeeth_intro"))
                 if (obj.get("_language") or "").lower() == "ar" else ""))
    intro_stripped = None
    if present(intro):
        if ar.startswith(intro):
            ar = ar[len(intro):].strip()
            intro_stripped = True
        else:
            # id 66511: the intro carries «رضي الله عنه» and the body does not,
            # so a byte comparison misses. Never guess the boundary -- a wrong
            # cut damages the matn and a right-looking one is unverifiable.
            intro_stripped = False
    if not present(ar):
        return {"status": "dropped",
                "reason": "Arabic was intro only, no matn", "candidate": None}

    bucket, conflict = classify_grade(obj.get("grade_ar", ""), obj.get("grade", ""))
    if bucket not in ("sahih", "hasan"):
        return {"status": "dropped",
                "reason": f"grade={bucket} (sahih/hasan only)",
                "candidate": None}

    candidate = {
        "collection": "",          # HadeethEnc gives no collection id -- Dorar supplies
        "hadith_number": "",       # nor a number -- Dorar supplies
        "citation_pending": True,  # MUST be resolved before promotion
        # P179: HadeethEnc has no narrator-NAME field. hadeeth_intro_ar is the
        # isnad phrase, so filling narrator from it wrote a chain where the
        # library holds a name -- and buildRef() falls back to printing the
        # narrator verbatim (P150), so it would have reached the caption. There
        # is nothing in the payload to derive a name from, so it is left unset
        # and resolved with the citation, like collection/hadith_number above.
        "narrator": None,
        # None = no intro field at all, True = removed from the matn,
        # False = present and NOT removable, so the row must not promote.
        "matn_intro_raw": intro or None,
        "matn_intro_stripped": intro_stripped,
        "grade": bucket,
        "grading_source": "hadeethenc.com (preliminary — confirm via Dorar)",
        "grade_conflict": conflict,
        "raw_grades": [g for g in (_clean_body(obj.get("grade_ar")),
                                   _clean_body(obj.get("grade"))) if g],
        "attribution_raw": (_clean_body(obj.get("attribution_ar"))
                            or _clean_body(obj.get("attribution"))),
        # Free-text Arabic bibliography with volume/page pairs and commentary
        # works mixed in -- one entry can list two numbers for the same
        # collection. NOT parsed for the citation; kept raw as a cross-check
        # against whatever Dorar returns. A disagreement warrants a human look.
        "reference_raw": _clean_body(obj.get("reference")),
        "source_urls": {"hadeethenc": build_source_url(hadeeth_id)},
        "text_arabic": ar,
        # P178: HadeethEnc's own translations are not carried. Stage 3 measured
        # them at EN 3/5, RU 0/5, UZ 0/5, TJ 1/5 clean against 8/8 for in-house.
        # The defects are interpretive expansion; the worst added «бегуноҳ»
        # (innocent) to قتل النفس on #6871 in both UZ and TJ, which changes the
        # ruling. HadeethEnc is discovery + Arabic matn + citation only.
        "text_english": "",
        "text_russian": "",
        "text_uzbek_cyrillic": "",
        "text_tajik": "",
        # Set by whoever actually produces the text. A row carrying our own
        # translation must not credit them (P174 cuts both ways).
        "translation_source": None,
        "available_langs": [l for l in (obj.get("translations") or [])
                            if isinstance(l, str)],
        "hadeethenc_id": hadeeth_id,
    }
    return {"status": "candidate", "reason": "", "candidate": candidate}


# HadeethEnc 403s the default Python-urllib User-Agent while serving curl
# fine, so identify the client explicitly.
UA = "hadith-reels/1.0 (+https://hadithverifier.com)"


def _get_json(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_hadeeth(hadeeth_id: str, language: str = "ar", *,
                  base_url: str = API_BASE, timeout: int = 20) -> dict:
    """Thin network wrapper. No API key -- HadeethEnc is public."""
    q = urllib.parse.urlencode({"language": language, "id": str(hadeeth_id)})
    obj = _get_json(f"{base_url}/hadeeths/one/?{q}", timeout=timeout)
    if isinstance(obj, dict):
        obj["_language"] = language
    return obj


def fetch_langs(hadeeth_id: str, langs=WANTED_LANGS, *,
                base_url: str = API_BASE, timeout: int = 20) -> dict:
    """Fetch one hadeeth in several languages. Absent ones are omitted."""
    out = {}
    for lang in langs:
        try:
            payload = fetch_hadeeth(hadeeth_id, lang, base_url=base_url, timeout=timeout)
        except urllib.error.HTTPError as e:
            # 404 means this hadeeth has no such language; anything else is a
            # transport or blocking failure and must NOT look like absence.
            if e.code == 404:
                continue
            raise
        except (urllib.error.URLError, ValueError):
            raise
        if isinstance(payload, dict) and present(payload.get("hadeeth")):
            out[lang] = payload
    return out


def fetch_list(category_id: str, language: str = "en", page: int = 1,
               per_page: int = 20, *, base_url: str = API_BASE,
               timeout: int = 20) -> dict:
    """Paginated category listing. Returns the raw {data, meta} envelope."""
    q = urllib.parse.urlencode({"language": language, "category_id": str(category_id),
                                "page": page, "per_page": per_page})
    return _get_json(f"{base_url}/hadeeths/list/?{q}", timeout=timeout)
