// QA: open index.html at 1280 px and 390 px, record console errors, take screenshots of key states into qa/.
// Usage: LEAFLET_DIR=/path/to/node_modules/leaflet node code/qa.js
// Serves the repo root on a local port; web tiles and fonts are blocked offline and ignored; Leaflet is served from a
// local npm copy of the same version (1.9.4).
const { chromium } = require("playwright");
const http = require("http"), fs = require("fs"), path = require("path");
const PORT = +(process.env.QAPORT || 8793);
const ROOT = path.resolve(__dirname, ".."), OUT = path.join(ROOT, "qa");
const LEAF = process.env.LEAFLET_DIR || path.join(process.env.SCRATCH || "", "node_modules/leaflet");
const TYPES = { ".html": "text/html", ".json": "application/json", ".png": "image/png", ".js": "text/javascript" };
const srv = http.createServer((q, s) => { let p = decodeURIComponent(q.url.split("?")[0]); if (p.endsWith("/")) p += "index.html"; const f = path.join(ROOT, p);
  fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { "Content-Type": TYPES[path.extname(f)] || "application/octet-stream" }); s.end(d); }); });
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  await new Promise(r => srv.listen(PORT, r));
  const b = await chromium.launch();
  const errs = [];
  for (const [w, h, tag] of [[1280, 900, "desk"], [390, 844, "phone"]]) {
    const pg = await b.newPage({ viewport: { width: w, height: h } });
    pg.on("console", m => { if (m.type() === "error" && !/Failed to load resource|ERR_|net::/.test(m.text())) errs.push(`${tag}: ${m.text()}`); });
    pg.on("pageerror", e => errs.push(`${tag} pageerror: ${e.message}`));
    await pg.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await pg.route(/leaflet.min.js/, r => r.fulfill({ path: path.join(LEAF, "dist/leaflet.js") }));
    await pg.route(/leaflet.min.css/, r => r.fulfill({ path: path.join(LEAF, "dist/leaflet.css") }));
    await pg.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
    await pg.goto(`http://localhost:${PORT}/index.html`, { waitUntil: "networkidle" });
    await pg.waitForTimeout(800);
    const ov = await pg.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    if (ov > 0) errs.push(`${tag}: horizontal overflow ${ov}px`);
    if (!(await pg.$(".mfs-btn"))) errs.push(`${tag}: no full-screen button`);
    await pg.screenshot({ path: `${OUT}/${tag}_top.png` });
    const atlas = await pg.$("#atlas"); await atlas.scrollIntoViewIfNeeded(); await pg.waitForTimeout(300);
    await atlas.screenshot({ path: `${OUT}/${tag}_map.png` });
    await pg.evaluate(() => { const p = PTS.find(x => x.n.includes("Kilkenny Union Workhouse Paupers")); pickItem(p, true); }); await pg.waitForTimeout(500);
    await atlas.screenshot({ path: `${OUT}/${tag}_map_kilkenny.png` });
    await pg.click('#colRow .btn[data-c="reuse"]'); await pg.evaluate(() => focus("England")); await pg.waitForTimeout(500);
    await atlas.screenshot({ path: `${OUT}/${tag}_map_reuse.png` });
    await pg.click('#kindTabs .btn[data-k="name"]'); await pg.evaluate(() => { const c = CTY.features.find(f => f.properties.c === "Norfolk"); pickCounty(c.properties, true); }); await pg.waitForTimeout(500);
    await atlas.screenshot({ path: `${OUT}/${tag}_map_norfolk_names.png` });
    await pg.fill("#q", "Southw"); await pg.waitForTimeout(300); await atlas.screenshot({ path: `${OUT}/${tag}_search.png` }); await pg.keyboard.press("Enter"); await pg.waitForTimeout(500);
    await atlas.screenshot({ path: `${OUT}/${tag}_search_pick.png` });
    await pg.click(".lyrBtn"); await pg.waitForTimeout(200); await atlas.screenshot({ path: `${OUT}/${tag}_layers.png` }); await pg.click(".lyrBtn");
    for (const id of ["natChart", "reuseChart", "nameChart", "ieChart", "cards"]) {
      const e = await pg.$("#" + id); await e.scrollIntoViewIfNeeded(); await pg.waitForTimeout(150); await e.screenshot({ path: `${OUT}/${tag}_chart_${id}.png` });
    }
    const tl = await pg.$(".tl"); await tl.screenshot({ path: `${OUT}/${tag}_timeline.png` });
    await pg.click(".mfs-btn"); await pg.waitForTimeout(500); await pg.screenshot({ path: `${OUT}/${tag}_fullscreen.png` }); await pg.click(".mfs-btn"); await pg.waitForTimeout(400);
    await pg.click("#theme"); await pg.waitForTimeout(400); await pg.evaluate(() => window.scrollTo(0, 0)); await pg.screenshot({ path: `${OUT}/${tag}_dark_top.png` });
    await atlas.scrollIntoViewIfNeeded(); await atlas.screenshot({ path: `${OUT}/${tag}_dark_map.png` });
    await pg.close();
  }
  await b.close(); srv.close();
  console.log(errs.length ? "ERRORS:\n" + errs.join("\n") : "no console errors");
})();
