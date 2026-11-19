#!/usr/bin/env python3
"""Upload content/books/** to the PRIVATE Supabase Storage bucket 'books'.

The texts stay out of the public git repo; production reads them from this
bucket with the service-role key (lib/books.ts), behind canRead().

  python scripts/upload-books.py              # dry run: counts only
  python scripts/upload-books.py --commit     # create bucket if missing, upload (upsert)
"""
import argparse, json, mimetypes, os, sys, urllib.request, urllib.error

def env():
    e = {}
    for line in open('.env.local', encoding='utf-8'):
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.strip().split('=', 1); e[k] = v.strip().strip('"')
    return e

def req(method, url, key, body=None, ctype='application/json', extra=None):
    h = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': ctype}
    h.update(extra or {})
    r = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')

def req_retry(*a, tries=4, **k):
    import time
    for i in range(tries):
        try:
            return req(*a, **k)
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
            if i == tries - 1:
                return 0, f'network: {e}'
            time.sleep(2 * (i + 1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true')
    ap.add_argument('--root', default=os.path.join('content', 'books'))
    a = ap.parse_args()
    files = []
    for d, _, fs in os.walk(a.root):
        for f in fs:
            full = os.path.join(d, f)
            files.append((full, os.path.relpath(full, a.root).replace(os.sep, '/')))
    total = sum(os.path.getsize(f) for f, _ in files)
    print(f'{len(files)} files, {total/1048576:.1f} MB under {a.root}')
    if not a.commit:
        print('DRY RUN - nothing uploaded. Re-run with --commit.'); return 0
    e = env(); url, key = e['NEXT_PUBLIC_SUPABASE_URL'], e['SUPABASE_SERVICE_ROLE_KEY']
    st, body = req('GET', f'{url}/storage/v1/bucket/books', key)
    if st != 200:
        st, body = req('POST', f'{url}/storage/v1/bucket', key,
                       json.dumps({'id': 'books', 'name': 'books', 'public': False}).encode())
        print('create bucket:', st, body[:120])
        if st not in (200, 201): return 1
    else:
        if json.loads(body).get('public'):
            print('REFUSING: bucket books is public'); return 2
    ok = bad = 0
    for full, rel in files:
        ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        with open(full, 'rb') as fh:
            st, body = req_retry('POST', f'{url}/storage/v1/object/books/{rel}', key, fh.read(), ctype, {'x-upsert': 'true'})
        if st in (200, 201): ok += 1
        else:
            bad += 1; print('FAIL', st, rel, body[:120])
    print(f'uploaded {ok}, failed {bad}')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
