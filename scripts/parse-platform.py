#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse-platform.py - out/platform-<n>.md -> out/texts-<n>.json, the per-field texts the publishing
runs paste (Meta caption and tags, YouTube title/description/tags, TikTok description).

    python scripts/parse-platform.py 2592

platform-texts.py writes the .md with six fenced blocks per language, in this order:
meta, meta_tags, yt_title, yt_desc, yt_tags, tt. A language with any other count stops the run.

Moved from out/parse_platform.py (2026-11-21): tidy-out.py archives every script it finds in
out/ as a one-off, and this one is used on every set.
"""
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ['meta', 'meta_tags', 'yt_title', 'yt_desc', 'yt_tags', 'tt']


def parse(md):
    """{lang: {field: text}} from a platform-<n>.md. Pure."""
    out = {}
    for m in re.finditer(r'^## (EN|RU|UZ|TJ)\s*$(.*?)(?=^## |\Z)', md, re.S | re.M):
        blocks = re.findall(r'```\n(.*?)\n```', m.group(2), re.S)
        if len(blocks) != len(FIELDS):
            raise ValueError('%s has %d text blocks, expected %d' % (m.group(1), len(blocks), len(FIELDS)))
        out[m.group(1).lower()] = dict(zip(FIELDS, blocks))
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        raise SystemExit('usage: python scripts/parse-platform.py <number>')
    n = argv[0]
    md = io.open(os.path.join(REPO, 'out', 'platform-%s.md' % n), encoding='utf-8').read()
    out = parse(md)
    io.open(os.path.join(REPO, 'out', 'texts-%s.json' % n), 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print({k: [len(v[x]) for x in FIELDS] for k, v in out.items()})
    return 0


if __name__ == '__main__':
    sys.exit(main())
