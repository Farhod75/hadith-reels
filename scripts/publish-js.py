"""publish-js.py - P439: the per-reel Playwright scripts for Meta, TikTok and YouTube.

Until P439 these came from out/{metajs,ytjs,ttjs}<N>.py, copied set to set (out/ is archived by
tidy-out, and the 90 s Checks wait + the exact "Create" button lived only in the latest copy).

  python scripts/publish-js.py --number 7536                 # all three platforms, all four languages
  python scripts/publish-js.py --number 7536 --platform yt --langs en

Reads out/set-<N>.json (slug) and out/texts-<N>.json (meta, tt, yt_title, yt_desc, yt_tags per
language). Writes <platform><N>-<lang>.js into the Playwright MCP folder of the newest
AnthropicClaude app-* (the folder moves on every desktop update - P-note 2026-11-17), or --dir.
Run each file with browser_run_code_unsafe (filename). Nothing is clicked here; publishing still
waits for the operator's "да".

P445 - Meta in four files per language, run in this order (clear the file chooser with
browser_file_upload and no paths after metaup and metacover):
  metaup<N>-<l>.js     opens the Reels composer and picks the reel (copied into <dir>/upload/)
  meta<N>-<l>.js       pastes the caption
  metacover<N>-<l>.js  uploads the language's cover
  metashare.js         refuses without a cover, waits for the copyright check, sets the
                       audience (radio 3, checkbox 4 off), checks both, shares, clicks Done
YouTube: a previous upload still running makes Studio ask "leave site?"; the script dismisses
it, waits and retries, and returns {blocked} instead of leaving the page.
"""
import argparse
import glob
import io
import json
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['en', 'ru', 'uz', 'tj']
YT_CHECKS_MS = 90000   # under the device bridge's ~140 s; a timeout leaves a Draft to finish by hand

META = '''async (page) => {
  const TXT=%s;
  const ed = page.locator('[contenteditable=true]').last();
  await ed.click(); await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
  await page.keyboard.insertText(TXT);
  await page.waitForTimeout(1500);
  return {len: (await ed.innerText()).length, want: TXT.length};
}'''

TT = '''async (page) => {
  const TXT=%s;
  const ed = page.locator('.public-DraftEditor-content').first();
  await ed.click(); await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
  await page.keyboard.insertText(TXT);
  await page.waitForTimeout(1500); await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  const want = {'Reuse of content': false, 'AI-generated content': true, 'Music copyright check': true};
  const res = await page.evaluate((want)=>{ const out={}; for (const s of document.querySelectorAll('input[type=checkbox],[role=switch]')) { let p=s; for(let i=0;i<6&&p;i++){ p=p.parentElement; if(p && p.innerText && p.innerText.trim().length>3) break; } const lab=(p?p.innerText.trim():''); for (const k in want) { if (lab.startsWith(k)) { const cur = s.checked ?? (s.getAttribute('aria-checked')==='true'); if (cur!==want[k]) s.click(); out[k]=true; } } } return out; }, want);
  await page.waitForTimeout(2500);
  const ai = page.getByRole('button', {name:/Turn on|Confirm/}); if (await ai.count()) await ai.first().evaluate(e=>e.click()).catch(()=>{});
  const len = await ed.evaluate(e=>e.innerText.length);
  return {len, want: TXT.length, res};
}'''

COMPOSER = ('https://business.facebook.com/latest/reels_composer'
            '?asset_id=1423366717525447&business_id=1985396645464439')

META_UP = '''async (page) => {
  const V=%s;
  await page.goto(%s); await page.waitForTimeout(6000);
  const [fc] = await Promise.all([page.waitForEvent('filechooser', {timeout:30000}),
    page.getByText(/Добавить видео|Загрузить видео/).first().click()]);
  await fc.setFiles(V);
  return 'reel picked - clear the chooser (browser_file_upload, no paths), then run meta<N>-<lang>.js';
}'''

META_COVER = '''async (page) => {
  const C=%s;
  await page.getByText('Загрузить изображение').first().waitFor({timeout:90000});
  await page.getByText('Загрузить изображение').first().click(); await page.waitForTimeout(1500);
  const [fc] = await Promise.all([page.waitForEvent('filechooser'), page.getByText('Загрузить изображение').last().click()]);
  await fc.setFiles(C);
  return 'cover picked - clear the chooser, then run metashare.js';
}'''

META_SHARE = '''async (page) => {
  const cov = await page.getByText('Изменить изображение').count();
  if (!cov) return {stop: 'no cover - never publish without one'};
  await page.getByText('Нарушений авторских прав не обнаружено').first().waitFor({timeout:180000});
  const next = () => page.getByRole('button', {name:'Далее'}).last().click();
  await next(); await page.waitForTimeout(2500);
  await next(); await page.waitForTimeout(2500);
  const radios = page.locator('input[type=radio]');
  await radios.nth(2).check({force:true}); await page.waitForTimeout(800);
  const cbs = page.locator('input[type=checkbox]');
  if (await cbs.nth(3).isChecked()) await cbs.nth(3).uncheck({force:true});
  await page.waitForTimeout(800);
  const r = []; for (let i=0;i<await radios.count();i++) r.push(await radios.nth(i).isChecked());
  const c = []; for (let i=0;i<await cbs.count();i++) c.push(await cbs.nth(i).isChecked());
  if (JSON.stringify(r)!==%s || JSON.stringify(c)!==%s) return {stop:'audience not as expected - nothing shared', r, c};
  await page.getByRole('button', {name:'Поделиться'}).last().click();
  await page.getByRole('button', {name:'Готово'}).first().waitFor({timeout:240000});
  await page.getByRole('button', {name:'Готово'}).first().click();
  await page.waitForTimeout(3000);
  return {cov, shared: page.url()};
}'''
RADIOS = [False, False, True, True, False]
CHECKS = [False, True, False, False, False]

YT = '''async (page) => {
  const V=%s, C=%s, TITLE=%s, DESC=%s, TAGS=%s;
  // P445: an upload still running makes Studio ask "leave site?" - dismiss, wait, retry; never leave it
  let blocked = false, ok = false;
  const onDialog = d => { blocked = true; d.dismiss().catch(()=>{}); };
  page.on('dialog', onDialog);
  for (let i = 0; i < 4 && !ok; i++) {
    blocked = false;
    await page.goto('https://studio.youtube.com', {timeout: 20000}).catch(()=>{});
    if (!blocked) ok = true; else await page.waitForTimeout(10000);
  }
  page.off('dialog', onDialog);
  if (!ok) return {blocked: 'the previous upload is still running - run this file again in a minute'};
  await page.getByRole('button', {name:'Create', exact:true}).first().click();
  await page.getByText('Upload videos').first().click();
  await page.locator('input[name=Filedata]').setInputFiles(V);
  const tb = page.locator('#textbox');
  await tb.first().waitFor({timeout:120000});
  await page.waitForTimeout(3000);
  await tb.nth(0).click(); await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
  await page.keyboard.insertText(TITLE);
  await tb.nth(1).click(); await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
  await page.keyboard.insertText(DESC);
  await page.locator('#file-loader').setInputFiles(C);
  await page.waitForTimeout(4000);
  await page.locator('[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]').click();
  await page.locator('#toggle-button').click();
  const tags = page.getByRole('textbox', {name: /Tags/i});
  await tags.click(); await page.keyboard.insertText(TAGS + ',');
  for (let i=0;i<3;i++){ await page.locator('#next-button').click(); await page.waitForTimeout(1500); }
  await page.locator('[name=PUBLIC]').click();
  await page.getByText(/Checks complete/i).first().waitFor({timeout:%d}).catch(()=>{});
  const link = await page.locator('ytcp-video-info a').first().innerText().catch(()=>null);
  await page.locator('#done-button').click();
  await page.waitForTimeout(4000);
  const close = page.locator('#close-button');
  if (await close.count()) await close.first().click().catch(()=>{});
  return link;
}'''


def j(x):
    return json.dumps(x, ensure_ascii=False)


def need(texts, lang, *keys):
    t = texts.get(lang) or {}
    missing = [k for k in keys if not (t.get(k) or '').strip()]
    if missing:
        raise SystemExit('texts: %s has no %s' % (lang, ', '.join(missing)))
    return t


def meta_up_js(video, url=COMPOSER):
    return META_UP % (j(video), j(url))


def meta_cover_js(cover):
    return META_COVER % j(cover)


def meta_share_js():
    js = lambda b: j(json.dumps([bool(x) for x in b]).replace(' ', ''))
    return META_SHARE % (js(RADIOS), js(CHECKS))


def meta_js(texts, lang):
    return META % j(need(texts, lang, 'meta')['meta'])


def tt_js(texts, lang):
    return TT % j(need(texts, lang, 'tt')['tt'])


def yt_js(texts, lang, number, slug, repo=REPO):
    t = need(texts, lang, 'yt_title', 'yt_desc', 'yt_tags')
    w = os.path.join(repo, 'out', 'work', 'adults', slug, lang)
    v = os.path.join(w, 'adults-%s-%s-reel.mp4' % (lang, slug))
    c = os.path.join(w, 'cover-%s-%s.jpg' % (number, lang))
    return YT % (j(v), j(c), j(t['yt_title']), j(t['yt_desc']), j(t['yt_tags']), YT_CHECKS_MS)


def playwright_dir(base=None):
    base = base or os.path.join(os.environ.get('LOCALAPPDATA', ''), 'AnthropicClaude')
    dirs = [d for d in glob.glob(os.path.join(base, 'app-*', '.playwright-mcp')) if os.path.isdir(d)]
    if not dirs:
        raise SystemExit('no AnthropicClaude app-*\\.playwright-mcp folder - pass --dir')
    return max(dirs, key=os.path.getmtime)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--number', required=True)
    ap.add_argument('--platform', default='meta,tt,yt')
    ap.add_argument('--langs', default=','.join(LANGS))
    ap.add_argument('--dir')
    a = ap.parse_args(argv)
    sp = os.path.join(REPO, 'out', 'set-%s.json' % a.number)
    slug = json.load(io.open(sp, encoding='utf-8'))['slug']
    texts = json.load(io.open(os.path.join(REPO, 'out', 'texts-%s.json' % a.number), encoding='utf-8'))
    d = a.dir or playwright_dir()
    up = os.path.join(d, 'upload')
    for p in a.platform.split(','):
        for l in a.langs.split(','):
            if p == 'meta':
                js = meta_js(texts, l)
                w = os.path.join(REPO, 'out', 'work', 'adults', slug, l)
                os.makedirs(up, exist_ok=True)
                for f in ('adults-%s-%s-reel.mp4' % (l, slug), 'cover-%s-%s.jpg' % (a.number, l)):
                    if os.path.exists(os.path.join(w, f)):
                        shutil.copy2(os.path.join(w, f), os.path.join(up, f))
                    else:
                        print('WARNING: %s missing - Meta needs it in %s' % (f, up))
                for name, code in (('metaup', meta_up_js(os.path.join(up, 'adults-%s-%s-reel.mp4' % (l, slug)))),
                                   ('metacover', meta_cover_js(os.path.join(up, 'cover-%s-%s.jpg' % (a.number, l))))):
                    o = os.path.join(d, '%s%s-%s.js' % (name, a.number, l))
                    io.open(o, 'w', encoding='utf-8', newline='\n').write(code)
                    print(o)
            elif p == 'tt':
                js = tt_js(texts, l)
            elif p == 'yt':
                js = yt_js(texts, l, a.number, slug)
            else:
                raise SystemExit('platform: meta, tt or yt')
            out = os.path.join(d, '%s%s-%s.js' % (p, a.number, l))
            io.open(out, 'w', encoding='utf-8', newline='\n').write(js)
            print(out)
    if 'meta' in a.platform:
        o = os.path.join(d, 'metashare.js')
        io.open(o, 'w', encoding='utf-8', newline='\n').write(meta_share_js())
        print(o)
    if 'yt' in a.platform:
        for l in a.langs.split(','):
            w = os.path.join(REPO, 'out', 'work', 'adults', slug, l)
            for f in ('adults-%s-%s-reel.mp4' % (l, slug), 'cover-%s-%s.jpg' % (a.number, l)):
                if not os.path.exists(os.path.join(w, f)):
                    print('WARNING: %s missing - the YouTube script will fail' % f)


if __name__ == '__main__':
    sys.exit(main())