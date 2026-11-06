# scripts/tidy-out.py - sort out/ by the P106 layout (operator 2026-11-03 21:43 and 22:08: "the folder order we agreed").
# P106: work/ holds the CURRENT set only, published/ is the archive in the same {style}/{slug}/ shape. It drifted:
# work/ held ~50 sets. Now: every published set's work/{style}/{slug} moves to published/{style}/{slug}, test folders
# go to _legacy/, and the loose files of a set go INTO that set's published folder (_files/), so one folder is one set.
# DRY RUN by default: writes out/_tidy_plan.csv (from,to,reason) and prints counts. --apply moves, and
# writes out/_tidy_undo.ps1 that moves every file back. Nothing is deleted. Subfolders are not touched.
#
# Stays at the top of out/ (tools read these paths): the files of the sets NOT yet published -
# a work/ folder, or (P373) a set-<n>.json for a number the tracker has not published
# (2734, 223), and the global working files the scripts name (candidate/candidates JSON, reports,
# source-queries/refs, translations JSON, probe reports).
# Everything else goes under out/_archive/:
#   sets/<number>/   loose files of a set whose slug folder cannot be identified (else published/{style}/{slug}/_files/)
#   scripts/         other one-off scripts (.py .ps1 .js .sh .sql .ts .bak)
#   logs/            .log .err .out
#   commit-msgs/     commit_msg_*.txt, msg_*.txt
#   misc/            the rest that is clearly ours (txt/json/md not read by any tool)
# and out/deliverables/ for files meant for the operator (FB cover and avatar, the Sol audit zip, loose mp4/jpg).
import csv, io, os, re, sys, shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, 'out')
UNPUBLISHED = set()   # filled in main(): numbers of work/ sets the tracker has not published yet
KEEP_EXACT = {'candidate-translations.json', 'candidate-translations.reviewed.json', 'candidate-verdicts.json',
              'candidates-dorar.json', 'candidates-dropped.json', 'candidates.json', 'matn-number-report.json',
              'matn-verify-report.json', 'diacritic-audit.json', 'he-refs.txt', 'source-queries.txt',
              'source-refs.txt', 'tajik-translations.json', 'uzbek-scripts.json', 'model-probe.json',
              'model-probe.txt', 'last-parse-failure.txt', '_tidy_plan.csv', '_tidy_undo.ps1'}
LIVE_SET_FILE = re.compile(r'^(caption-(\d+)(-[a-z]{2})?(-tg-video)?\.(txt|json)|draft-[a-z-]+?-(\d+)-[a-z]{2}\.txt|'
                           r'set-(\d+)\.json|tg-(\d+)\.(json|log)|clips-(\d+)\.json|render-[a-z-]+?-(\d+)\.(json|log))$')
SCRIPT = {'.py', '.ps1', '.js', '.sh', '.sql', '.ts', '.bak'}
LOG = {'.log', '.err', '.out'}


def published_numbers():
    t = io.open(os.path.join(REPO, 'reel-tracker.md'), encoding='utf-8-sig').read()
    return set(re.findall(r'^\| R\d+ \| [\d-]+ \| [^|#]*#(\d+) \|', t, re.M))


def in_preparation(top_names, known):
    """P373: numbers of sets being prepared - a set-<n>.json at the top of out/ for a
    number the tracker has not published. Such a set has drafts and a caption JSON
    but no work/ folder until its narration is recorded, and P373 archived exactly
    those files as 'not read by any tool'. Pure."""
    out = set()
    for name in top_names:
        m = re.match(r'^set-(\d+)\.json$', name)
        if m and m.group(1) not in known:
            out.add(m.group(1))
    return out


def set_number(name, known):
    stem = re.sub(r'^w\d+_', '', name)                     # w47_reg2749.py -> reg2749.py
    found = [n for n in re.findall(r'(?<!\d)(\d{2,5})(?!\d)', stem) if n in known]
    return found[0] if len(set(found)) == 1 else None


def classify(name, known):
    ext = os.path.splitext(name)[1].lower()
    if name in KEEP_EXACT or name.startswith('source-queries') or name.startswith('proposed-'):
        return None, 'tool input/output - stays'
    m = LIVE_SET_FILE.match(name)
    num = set_number(name, known | UNPUBLISHED)
    if num in UNPUBLISHED and m:
        return None, 'unpublished set %s - stays' % num
    if num and num not in UNPUBLISHED:
        return os.path.join('_archive', 'sets', num), 'published set %s' % num
    if num in UNPUBLISHED:
        return os.path.join('_archive', 'sets', num), 'unpublished set %s, one-off' % num
    if name.startswith('fb-') or ext in ('.zip', '.mp4', '.jpg', '.png'):
        return 'deliverables', 'for the operator'
    if name.startswith('commit_msg') or name.startswith('msg_') or re.match(r'^_?commit_?msg', name):
        return os.path.join('_archive', 'commit-msgs'), 'commit message'
    if ext in LOG:
        return os.path.join('_archive', 'logs'), 'log'
    if ext in SCRIPT:
        return os.path.join('_archive', 'scripts'), 'one-off script'
    if ext in ('.txt', '.json', '.md', '.csv'):
        return os.path.join('_archive', 'misc'), 'not read by any tool'
    return None, 'unrecognised - left in place'


def slug_dirs():
    out = {}
    for root in ('work', 'published'):
        for style in ('adults', 'kids'):
            d = os.path.join(OUT, root, style)
            if os.path.isdir(d):
                for s in os.listdir(d):
                    out.setdefault(s, set()).add(style)
    return out


def number_to_slugdir(num, slugs):
    hits = [(st, s) for s, styles in slugs.items() for st in styles if re.search(r'(?<!\d)%s$' % num, s)]
    return hits[0] if len(hits) == 1 else None


def plan_work_moves(known):
    moves = []
    for style in ('adults', 'kids'):
        d = os.path.join(OUT, 'work', style)
        if not os.path.isdir(d):
            continue
        for s in sorted(os.listdir(d)):
            src = os.path.join('work', style, s)
            m = re.search(r'(\d+)$', s)
            if s.startswith('nonexistent') or s.endswith('-9999'):
                moves.append((src, os.path.join('_legacy', 'work-tests', style, s), 'test folder'))
            elif m and m.group(1) in UNPUBLISHED:
                continue                                    # current, not yet published - stays in work/
            elif m and m.group(1) in known:
                moves.append((src, os.path.join('published', style, s), 'published set'))
    return moves


def main():
    apply = '--apply' in sys.argv
    known = published_numbers()
    slugs = slug_dirs()
    for style in ('adults', 'kids'):
        d = os.path.join(OUT, 'work', style)
        for s in (os.listdir(d) if os.path.isdir(d) else []):
            m = re.search(r'(\d+)$', s)
            if m and m.group(1) not in known and not s.endswith('-9999'):
                UNPUBLISHED.add(m.group(1))
    UNPUBLISHED.update(in_preparation(os.listdir(OUT), known))   # P373
    rows, counts = [], {}
    work_moves = plan_work_moves(known)
    for name in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, name)
        if not os.path.isfile(p):
            continue
        dest, why = classify(name, known)
        if dest and dest.startswith(os.path.join('_archive', 'sets')):
            num = dest.split(os.sep)[-1]
            sd = number_to_slugdir(num, slugs)
            if sd:
                dest = os.path.join('published' if num not in UNPUBLISHED else 'work', sd[0], sd[1], '_files')
                why += ' -> its set folder'
        key = dest or 'stays'
        if dest and dest.startswith(os.path.join('_archive', 'sets')):
            key = os.path.join('_archive', 'sets', '*')
        elif dest and dest.endswith('_files'):
            key = dest.split(os.sep)[0] + os.sep + '*' + os.sep + '_files'
        counts[key] = counts.get(key, 0) + 1
        rows.append((name, dest or '', why))
    with io.open(os.path.join(OUT, '_tidy_plan.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh); w.writerow(['file', 'to', 'why']); w.writerows(rows); w.writerows(work_moves)
    print('published sets known from the tracker: %d; in work, not yet published: %s' % (len(known), ', '.join(sorted(UNPUBLISHED)) or '-'))
    print('work/ set folders to move: %d (%s)' % (len(work_moves), ', '.join(sorted(set(m[2] for m in work_moves)))))
    for k in sorted(counts):
        print('  %-24s %d' % (k, counts[k]))
    left = [r for r in rows if not r[1]]
    print('stays at the top (%d):' % len(left))
    for r in left:
        print('   %s  (%s)' % (r[0], r[2]))
    if not apply:
        print('DRY RUN - plan in out/_tidy_plan.csv. --apply to move.')
        return 0
    undo = []
    for src, dst, _ in work_moves:
        s, d = os.path.join(OUT, src), os.path.join(OUT, dst)
        if os.path.exists(d):
            print('SKIP (exists): ' + d); continue
        os.makedirs(os.path.dirname(d), exist_ok=True)
        try:
            shutil.move(s, d)
        except OSError as e:
            print('COULD NOT MOVE %s: %s (a file is open? close it and re-run)' % (src, e)); continue
        undo.append("Move-Item -LiteralPath '%s' -Destination '%s'" % (d.replace("'", "''"), s.replace("'", "''")))
    for name, dest, _ in rows:
        if not dest:
            continue
        d = os.path.join(OUT, dest); os.makedirs(d, exist_ok=True)
        target = os.path.join(d, name)
        if os.path.exists(target):
            print('SKIP (exists): ' + target); continue
        try:
            shutil.move(os.path.join(OUT, name), target)
        except OSError as e:
            print('COULD NOT MOVE %s: %s' % (name, e)); continue
        undo.append("Move-Item -LiteralPath '%s' -Destination '%s'" % (target.replace("'", "''"), os.path.join(OUT, name).replace("'", "''")))
    io.open(os.path.join(OUT, '_tidy_undo.ps1'), 'w', encoding='utf-8-sig').write('\r\n'.join(reversed(undo)) + '\r\n')
    print('moved %d files; undo: out\\_tidy_undo.ps1' % len(undo))
    return 0


if __name__ == '__main__':
    sys.exit(main())
