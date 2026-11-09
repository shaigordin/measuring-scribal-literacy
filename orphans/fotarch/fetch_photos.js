// Polite Fotoarchiv photo fetcher: one browser session, full page loads, pauses between pages.
// For each publication: Konkordanz row -> photo selection -> viewer; the viewer's own image
// request (pixl3.php) is saved as the browser receives it. First photo per fragment only.
// Usage: node fetch_photos.js <outdir> "KBo 41.22" "KUB 35.146" ...
const { chromium } = require('playwright');
const fs = require('fs');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const PAUSE = 6000;
(async () => {
  const [out, ...pubs] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1600, height: 1200 } })).newPage();
  const log = [];
  for (const pub of pubs) {
    const rec = { pub };
    try {
      await p.goto('https://hethport.net/hetkonk/hetkonk_abfrage.php?p=' + encodeURIComponent(pub), { waitUntil: 'networkidle', timeout: 180000 });
      await sleep(PAUSE);
      const hit = await p.$$eval('tr', (trs, pub) => {
        for (const t of trs) {
          const tds = [...t.querySelectorAll('td')];
          const y3 = tds.filter(d => d.id === 'y3');
          if (y3.length && y3[0].textContent.trim().replace(/\s+/g, ' ').replace(/\+$/, '') === pub) {
            const a = t.querySelector('a[href*="bildpraep"]');
            return { fundnr: tds[0].textContent.trim(), cth: y3[1] ? y3[1].textContent.trim() : '', href: a ? a.href : null };
          }
        }
        return null;
      }, pub);
      Object.assign(rec, hit || {});
      if (!hit || !hit.href) { rec.status = 'no photo link'; log.push(rec); console.log(JSON.stringify(rec)); continue; }
      await p.goto(hit.href, { waitUntil: 'networkidle', timeout: 180000 });
      await sleep(PAUSE);
      const touch = await p.$$eval('a', as => as.map(a => a.href).filter(h => /touchpic/.test(h)));
      rec.photos_available = touch.length;
      if (!touch.length) { rec.status = 'no photos'; log.push(rec); console.log(JSON.stringify(rec)); continue; }
      rec.bildnr = new URL(touch[0]).searchParams.get('bildnr');
      const imgP = p.waitForResponse(r => /pixl3\.php/.test(r.url()), { timeout: 180000 });
      await p.goto(touch[0], { waitUntil: 'networkidle', timeout: 180000 });
      const img = await imgP;
      const buf = await img.body();
      const fn = `${out}/${pub.replace(/[ .+]/g, '_')}_${rec.bildnr}.jpg`;
      fs.writeFileSync(fn, buf);
      rec.file = fn; rec.bytes = buf.length; rec.status = 'ok';
      rec.citation = `hethiter.net/: fotarch ${rec.bildnr}`;
    } catch (e) { rec.status = 'error: ' + e.message.split('\n')[0]; }
    log.push(rec); console.log(JSON.stringify(rec));
    await sleep(PAUSE);
  }
  fs.writeFileSync(`${out}/photos.json`, JSON.stringify(log, null, 1));
  await b.close();
})();
