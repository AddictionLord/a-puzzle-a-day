const { chromium } = require("playwright");
const path = require("path");
const root = path.resolve(__dirname, "..");
const pageUrl = `file://${root}/web/index.html`;
const out = `${root}/docs/images`;

async function open(browser, opts) {
    const ctx = await browser.newContext(opts);
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    await page.goto(pageUrl);
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() => setTarget(10, 16, 4));
    return { page, errors };
}

(async () => {
    const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});

    const a = await open(browser, { viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2, colorScheme: "light" });
    await a.page.evaluate(() => {
        solveAll();
        const keep = ["I", "F", "T", "Y", "P", "N"];
        for (const name of [...state.placed.keys()]) if (!keep.includes(name)) state.placed.delete(name);
        state.message = null; state.tone = "";
        render();
    });
    const sol = await a.page.evaluate(() => {
        const blocked = targets().map(([r, c]) => idxOf[r * COLS + c]);
        state.placed.forEach((cells) => cells.forEach(([r, c]) => blocked.push(idxOf[r * COLS + c])));
        return runSolver(blocked, [...state.placed.keys()], 1).first;
    });
    await a.page.evaluate((piece) => {
        select(piece.name);
        state.selected = piece.name;
        state.pose = transformFor(piece.name, piece.cells);
        const shape = transform(piece.name, state.pose.rot, state.pose.flip);
        const anchor = anchorOf(shape);
        const minR = Math.min(...piece.cells.map((p) => p[0]));
        const minC = Math.min(...piece.cells.map((p) => p[1]));
        state.hover = [anchor[0] + minR, anchor[1] + minC];
        render();
    }, sol.find((p) => p.name === "L") || sol[0]);
    await a.page.screenshot({ path: `${out}/play.png`, fullPage: true });

    const b = await open(browser, { viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2, colorScheme: "dark" });
    await b.page.evaluate(() => solveAll());
    await b.page.click("#count");
    await b.page.waitForFunction(() => state.count && !state.count.pending);
    await b.page.evaluate(() => showSolution(41));
    await b.page.screenshot({ path: `${out}/solved-dark.png`, fullPage: true });

    const c = await open(browser, { viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, colorScheme: "light", isMobile: true, hasTouch: true });
    await c.page.evaluate(() => { solveAll(); });
    await c.page.screenshot({ path: `${out}/mobile.png` });

    const d = await open(browser, { viewport: { width: 1000, height: 700 }, deviceScaleFactor: 2, colorScheme: "light" });
    await d.page.evaluate(() => solveAll());
    const board = (await d.page.locator("#frame").screenshot()).toString("base64");
    const card = await browser.newPage({ viewport: { width: 1280, height: 640 } });
    await card.setContent(socialCard(board), { waitUntil: "networkidle" });
    await card.evaluate(() => document.fonts.ready);
    await card.screenshot({ path: `${root}/web/og.png` });

    const overflow = await c.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    console.log("errors:", [...a.errors, ...b.errors, ...c.errors, ...d.errors], "mobile overflow:", overflow);
    await browser.close();
})();

function socialCard(boardPng) {
    return `<!doctype html><html><head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost:wght@600;700&family=Atkinson+Hyperlegible:wght@400;700&display=swap">
<style>
body { margin: 0; width: 1280px; height: 640px; display: grid; grid-template-columns: 500px 1fr; align-items: center;
    gap: 40px; padding: 0 64px; box-sizing: border-box; background: #e7ebe6; color: #1f2420;
    font-family: "Atkinson Hyperlegible", system-ui, sans-serif; }
h1 { font-family: "Jost", system-ui, sans-serif; font-size: 104px; line-height: 1; margin: 0 0 24px; letter-spacing: -0.02em; }
p { font-size: 32px; line-height: 1.35; margin: 0 0 32px; color: #3c443d; }
.url { font-size: 24px; font-weight: 700; color: #2c6b5e; }
img { width: 100%; filter: drop-shadow(0 18px 24px rgba(40, 28, 12, 0.25)); }
</style></head><body>
<div><h1>Pentaday</h1><p>Ten pentominoes. Leave only today's date showing. Every day has a solution.</p>
<div class="url">addictionlord.github.io/pentaday</div></div>
<img src="data:image/png;base64,${boardPng}" alt="">
</body></html>`;
}
