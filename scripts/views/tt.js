// scripts/views/tt.js - P436. Run with browser_evaluate on
// https://www.tiktok.com/tiktokstudio/content (filename: .playwright-mcp/views-tt.json).
// The list is virtualised: scroll until nothing new appears six times running.
async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  await sleep(6000);
  const DATE = /^[A-Z][a-z]{2}\s\d{1,2},\s(\d{4}\s)?\d{1,2}:\d{2}\s?[AP]M$/;
  const seen = {}; let stale = 0;
  for (let s = 0; s < 150 && stale < 6; s++) {
    const before = Object.keys(seen).length;
    const L = document.body.innerText.split('\n').map(x => x.trim());
    for (let i = 1; i < L.length; i++) {
      if (DATE.test(L[i]) && L[i + 1] === 'Everyone') {
        seen[L[i] + '|' + L[i - 1].slice(0, 60)] = { date: L[i], caption: L[i - 1].slice(0, 200),
          views: L[i + 2], likes: L[i + 3], comments: L[i + 4] };
      }
    }
    document.querySelectorAll('*').forEach(e => {
      if (e.scrollHeight > e.clientHeight + 50 && getComputedStyle(e).overflowY !== 'visible') e.scrollTop += 900;
    });
    window.scrollBy(0, 900); await sleep(1300);
    stale = Object.keys(seen).length === before ? stale + 1 : 0;
  }
  return { platform: 'tiktok', at: new Date().toISOString(), rows: Object.values(seen) };
}
