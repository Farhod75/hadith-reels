// scripts/views/yt.js - P436. Run with browser_evaluate on
// https://studio.youtube.com/channel/UCr4Y-G_66R1ju97R9eZbe3w/videos/short
// (filename: .playwright-mcp/views-yt.json). Walks every page of the Shorts list.
async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 40 && !document.querySelector('ytcp-video-row'); i++) await sleep(500);
  const out = {};
  for (let p = 0; p < 40; p++) {
    for (const r of document.querySelectorAll('ytcp-video-row')) {
      const a = r.querySelector('a[href*="/video/"]');
      const id = a ? a.getAttribute('href').split('/')[2] : null;
      const g = s => (r.querySelector(s)?.innerText || '').replace(/\s+/g, ' ').trim();
      if (id) out[id] = { id, title: g('#video-title'), vis: g('.tablecell-visibility'),
                          date: g('.tablecell-date'), views: g('.tablecell-views'),
                          comments: g('.tablecell-comments'), likes: g('.tablecell-likes') };
    }
    const nx = document.querySelector('#navigate-after');
    if (!nx || nx.hasAttribute('disabled') || nx.getAttribute('aria-disabled') === 'true') break;
    nx.click(); await sleep(2500);
  }
  return { platform: 'youtube', at: new Date().toISOString(), rows: Object.values(out) };
}
