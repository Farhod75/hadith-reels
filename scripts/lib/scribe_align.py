# -*- coding: utf-8 -*-
"""P422: subtitles for UZ/TJ from our own Cyrillic text + ElevenLabs Scribe word timings.

Scribe v3 hears Uzbek and writes LATIN, hears Tajik and writes PERSIAN script, so its text
can never be burned (P078). Its word TIMINGS are good. This module lines our text (the exact
text sent to TTS) up with Scribe's words on a shared consonant skeleton, takes the timings,
and builds the cues. The words on screen are always ours.
"""
import re

_CY = {'б': 'b', 'в': 'v', 'г': 'g', 'ғ': 'g', 'д': 'd', 'ж': 'j', 'з': 'z', 'й': 'y', 'к': 'k',
       'қ': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'ф': 'f',
       'х': 'h', 'ҳ': 'h', 'ц': 's', 'ч': 'c', 'ш': 'S', 'щ': 'S', 'ҷ': 'j', 'ю': 'y', 'я': 'y',
       'ё': 'y'}
_LA = {'b': 'b', 'v': 'v', 'g': 'g', 'd': 'd', 'j': 'j', 'z': 'z', 'y': 'y', 'k': 'k', 'q': 'k',
       'l': 'l', 'm': 'm', 'n': 'n', 'p': 'p', 'r': 'r', 's': 's', 't': 't', 'f': 'f', 'x': 'h',
       'h': 'h', 'c': 'c', 'w': 'v'}
_FA = {'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's', 'ج': 'j', 'چ': 'c', 'ح': 'h', 'خ': 'h', 'د': 'd',
       'ذ': 'z', 'ر': 'r', 'ز': 'z', 'ژ': 'j', 'س': 's', 'ش': 'S', 'ص': 's', 'ض': 'z', 'ط': 't',
       'ظ': 'z', 'غ': 'g', 'ف': 'f', 'ق': 'k', 'ک': 'k', 'ك': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm',
       'ن': 'n', 'و': 'v', 'ه': 'h', 'ی': 'y', 'ي': 'y', 'ة': 'h', 'ئ': 'y', 'ؤ': 'v'}


def skeleton(word):
    """Consonant skeleton shared by Cyrillic, Uzbek Latin and Persian spellings of one word.
    Vowels, v/y/h (written or dropped differently in each script) and doubled letters go."""
    w, out, i = word.lower(), '', 0
    while i < len(w):
        if w[i:i + 2] == 'sh':
            out += 'S'; i += 2; continue
        if w[i:i + 2] == 'ch':
            out += 'c'; i += 2; continue
        ch = w[i]
        out += _CY.get(ch) or _LA.get(ch) or _FA.get(ch) or ''
        i += 1
    out = re.sub(r'[vyh]', '', out)
    return re.sub(r'(.)\1+', r'\1', out)


def _dist(a, b):
    if not a and not b:
        return 0.0
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[:], i
        for j, cb in enumerate(b, 1):
            d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (ca != cb))
    return d[-1] / float(max(len(a), len(b)))


def align(src_words, hyp):
    """src_words: our words. hyp: [{'text','start','end'}] from Scribe.
    Returns (times, mean_cost, src_unmatched, hyp_unmatched); times[i] = (start, end) for src word i.
    Allowed steps: 1:1, k:1 (Scribe merged our words, 'ва саллам' -> 'vasallam'),
    1:k (Scribe split one of ours, the Tajik honorific into five Persian words), skips."""
    n, m, INF = len(src_words), len(hyp), float('inf')
    S = [skeleton(w) for w in src_words]
    H = [skeleton(h['text']) for h in hyp]
    D = [[INF] * (m + 1) for _ in range(n + 1)]
    B = [[None] * (m + 1) for _ in range(n + 1)]
    D[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            c = D[i][j]
            if c == INF:
                continue
            if i < n and j < m:
                for k in (1, 2, 3):
                    if i + k <= n:
                        v = c + _dist(''.join(S[i:i + k]), H[j]) + 0.3 * (k - 1)
                        if v < D[i + k][j + 1]:
                            D[i + k][j + 1], B[i + k][j + 1] = v, ('m', k)
                for k in (2, 3, 4, 5):
                    if j + k <= m:
                        v = c + _dist(S[i], ''.join(H[j:j + k])) + 0.3 * (k - 1)
                        if v < D[i + 1][j + k]:
                            D[i + 1][j + k], B[i + 1][j + k] = v, ('s', k)
            if i < n and c + 1 < D[i + 1][j]:
                D[i + 1][j], B[i + 1][j] = c + 1, ('ds', 1)
            if j < m and c + 1 < D[i][j + 1]:
                D[i][j + 1], B[i][j + 1] = c + 1, ('dh', 1)
    times, ops, i, j = [None] * n, [], n, m
    while i or j:
        op, k = B[i][j]
        ops.append(op)
        if op == 'm':
            h = hyp[j - 1]
            span = (h['end'] - h['start']) / k
            for t in range(k):
                times[i - k + t] = (h['start'] + t * span, h['start'] + (t + 1) * span)
            i, j = i - k, j - 1
        elif op == 's':
            times[i - 1] = (hyp[j - k]['start'], hyp[j - 1]['end'])
            i, j = i - 1, j - k
        elif op == 'ds':
            i -= 1
        else:
            j -= 1
    for x in range(n):            # a word of ours Scribe did not return: between its neighbours
        if times[x] is None:
            a = next((times[y][1] for y in range(x - 1, -1, -1) if times[y]), 0.0)
            b = next((times[y][0] for y in range(x + 1, n) if times[y]), a + 0.3)
            times[x] = (a, max(a, b))
    return times, D[n][m] / max(n, 1), ops.count('ds'), ops.count('dh')


def cues(words, times, max_words=6, max_chars=38, hold=()):
    """Group words into cues: break after . : ! ? », after , ; once 3 words are in, or at the size
    limit; then fold a one-word cue into its neighbour when the pair still fits. hold: indices after
    which a size break is not allowed (the spoken honorific, P423)."""
    out, cur = [], []
    depth = 0
    for k, w in enumerate(words):
        cur.append(k)
        depth += w.count('(') - w.count(')')
        text = ' '.join(words[c] for c in cur)
        # never break a size limit inside parentheses - '(may Allah be pleased with him)' stays on one cue
        size_break = (len(cur) >= max_words or len(text) >= max_chars) and depth <= 0 and k not in hold
        if (re.search(r'[.:!?»)]["»]?$', w) and depth <= 0 or (re.search(r'[,;]$', w) and len(cur) >= 3 and depth <= 0)
                or size_break or len(text) >= max_chars + 30):
            out.append(cur); cur = []; depth = max(depth, 0)
    if cur:
        out.append(cur)
    # a one-word clause end left behind by a size break: rebalance with the cue before it
    for i in range(1, len(out)):
        prev, c = out[i - 1], out[i]
        if (len(c) == 1 and len(prev) >= 4 and re.search(r'[.:!?»,;]["»]?$', words[c[0]])
                and not re.search(r'[.:!?»,;]["»]?$', words[prev[-1]])):
            cuts = [j for j in range(1, len(prev)) if prev[j - 1] not in hold]
            if not cuts:
                continue
            cut = min(cuts, key=lambda j: abs(j - len(prev) / 2.0))
            out[i - 1], out[i] = prev[:cut], prev[cut:] + c
    merged = []
    for c in out:
        prev = merged[-1] if merged else None
        fits = prev is not None and len(' '.join(words[x] for x in prev + c)) <= max_chars + 8
        if fits and (len(c) == 1 and not re.search(r'[.!?»]$', words[prev[-1]]) or len(prev) == 1):
            merged[-1] = prev + c
        else:
            merged.append(c)
    return [(times[c[0]][0], times[c[-1]][1], ' '.join(words[x] for x in c)) for c in merged]


def srt_time(t):
    ms = int(round(t * 1000))
    return '%02d:%02d:%02d,%03d' % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def to_srt(cue_list):
    return '\n'.join('%d\n%s --> %s\n%s\n' % (i, srt_time(a), srt_time(b), t)
                     for i, (a, b, t) in enumerate(cue_list, 1))
