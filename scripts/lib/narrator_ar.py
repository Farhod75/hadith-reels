# -*- coding: utf-8 -*-
"""
narrator_ar.py - the English lib/refs.ts NARRATORS key for a narrator name as Dorar writes it.

P344: promote-candidates.py refuses a narrator that is not a NARRATORS key, and Dorar returns
the companion's name in Arabic, so every candidate needed a hand patch before promotion
(out/w46_narr<n>.py). upload-candidates.py now calls to_english() when it writes the row.

EXACT match after normalisation only - no fuzzy matching. A name not in the table is returned
unchanged (still Arabic), so promote's P344 refusal stays the safety net: a wrong companion in
the S block is an integrity defect, an unmapped one is a one-line addition here.
Every value must be a key of lib/refs.ts NARRATORS (scripts/lib/test_narrator_ar.py checks).
"""
import re

_TASHKEEL = re.compile(u'[ً-ْٰـ]')       # harakat, dagger alif, tatweel
_HONORIFIC = re.compile(u'\\s*(رضي الله عنه|رضي الله عنها|رضي الله عنهما|رضي الله عنهم)\\s*$')


def normalize(name):
    s = _TASHKEEL.sub('', name or '').strip()
    s = _HONORIFIC.sub('', s)
    s = re.sub(u'[أإآٱ]', u'ا', s).replace(u'ى', u'ي')
    s = re.sub(u'عبد\\s+الله', u'عبدالله', s)
    return re.sub(r'\s+', ' ', s).strip()


_RAW = {
    u'أبو هريرة': 'Abu Hurairah',
    u'أنس بن مالك': 'Anas ibn Malik',
    u'عبد الله بن عمرو': 'Abdullah ibn Amr',
    u'عبد الله بن عمرو بن العاص': 'Abdullah ibn Amr',
    u'عبد الله بن مسعود': 'Abdullah ibn Masud',
    u'ابن مسعود': 'Abdullah ibn Masud',
    u'أبو بكرة': 'Abu Bakra',
    u'أبو الدرداء': 'Abu Darda',
    u'أبو ذر': 'Abu Dharr',
    u'أبو ذر الغفاري': 'Abu Dharr',
    u'أبو مالك الأشعري': 'Abu Malik al-Ashari',
    u'أبو موسى الأشعري': 'Abu Musa al-Ashari',
    u'أبو سعيد الخدري': 'Abu Said al-Khudri',
    u'أبو شريح العدوي': 'Abu Shuraih al-Adawi',
    u'عدي بن حاتم': 'Adiy ibn Hatim',
    u'عائشة': 'Aisha',
    u'عائشة أم المؤمنين': 'Aisha',
    u'حذيفة بن اليمان': 'Hudhayfah ibn al-Yaman',
    u'عبد الله بن عباس': 'Ibn Abbas',
    u'ابن عباس': 'Ibn Abbas',
    u'عبد الله بن عمر': 'Ibn Umar',
    u'ابن عمر': 'Ibn Umar',
    u'جابر بن عبد الله': 'Jabir ibn Abdullah',
    u'جبير بن مطعم': 'Jubayr ibn Mutim',
    u'معاوية بن جاهمة': "Mu'awiyah ibn Jahimah",
    u'معاذ بن جبل': 'Muadh ibn Jabal',
    u'النعمان بن بشير': "Nu'man ibn Bashir",
    u'سلمان الفارسي': 'Salman al-Farisi',
    u'صهيب': 'Suhaib',
    u'صهيب الرومي': 'Suhaib',
    u'عمر بن الخطاب': 'Umar ibn al-Khattab',
    u'أم سلمة': 'Umm Salamah',
    u'أم سلمة أم المؤمنين': 'Umm Salamah',
    u'عثمان بن عفان': 'Uthman ibn Affan',
}
TABLE = {normalize(k): v for k, v in _RAW.items()}


def to_english(name):
    """The NARRATORS key for an Arabic name, or the name unchanged (English keys pass through)."""
    if not name:
        return name
    return TABLE.get(normalize(name), name)
