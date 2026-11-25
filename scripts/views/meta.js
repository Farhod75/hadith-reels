// scripts/views/meta.js - P436. Run with browser_evaluate on
// https://business.facebook.com/latest/insights/content?asset_id=1423366717525447&business_id=1985396645464439
// AFTER the Filter is set to exactly one of "Лента Instagram" / "Лента Facebook"
// (filename: .playwright-mcp/views-ig.json or views-fb.json). Last 30 days only.
async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  await sleep(3000);
  const out = {}; let stale = 0;
  const head = [...document.querySelectorAll('[role=row]')][0];
  const cols = head ? [...head.querySelectorAll('[role=columnheader],[role=cell],[role=gridcell]')]
    .map(c => c.innerText.replace(/[\s\u200b]+/g, ' ').trim()) : [];
  for (let s = 0; s < 120 && stale < 5; s++) {
    const before = Object.keys(out).length;
    for (const r of [...document.querySelectorAll('[role=row]')].slice(1)) {
      const c = [...r.querySelectorAll('[role=cell],[role=gridcell]')].map(x => x.innerText.replace(/\s+/g, ' ').trim());
      if (c.length < 4 || !c[1] || /^Ваша история/.test(c[0])) continue;
      const row = {}; cols.forEach((k, i) => { row[k] = c[i]; });
      row.caption = c[0].slice(0, 200); row.date = c[1];
      out[c[1] + '|' + c[0].slice(0, 60)] = row;
    }
    document.querySelectorAll('*').forEach(e => {
      if (e.scrollHeight > e.clientHeight + 50 && getComputedStyle(e).overflowY !== 'visible') e.scrollTop += 700;
    });
    await sleep(1500);
    stale = Object.keys(out).length === before ? stale + 1 : 0;
  }
  return { at: new Date().toISOString(), cols, rows: Object.values(out) };
}
