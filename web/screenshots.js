const { chromium } = require("playwright");
const path = require("path");
const root = path.resolve(__dirname, "..");
const pageUrl = `file://${root}/web/index.html`;
const out = `${root}/docs/images`;

async function open(browser, opts, lang) {
    const ctx = await browser.newContext(opts);
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    await page.goto(`${pageUrl}#${lang}`);
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(() => setTarget(10, 16, 4));
    return { page, errors };
}

(async () => {
    const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});

    const a = await open(browser, { viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2, colorScheme: "light" }, "en");
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
    await a.page.screenshot({ path: `${out}/play-en.png`, fullPage: true });

    const b = await open(browser, { viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2, colorScheme: "dark" }, "cs");
    await b.page.evaluate(() => solveAll());
    await b.page.click("#count");
    await b.page.waitForFunction(() => state.count && !state.count.pending);
    await b.page.screenshot({ path: `${out}/solved-cs-dark.png`, fullPage: true });

    const c = await open(browser, { viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, colorScheme: "light", isMobile: true, hasTouch: true }, "en");
    await c.page.evaluate(() => { solveAll(); });
    await c.page.screenshot({ path: `${out}/mobile-en.png` });

    const d = await open(browser, { viewport: { width: 1000, height: 700 }, deviceScaleFactor: 2, colorScheme: "light" }, "en");
    await d.page.evaluate(() => solveAll());
    await d.page.locator("#frame").screenshot({ path: `${out}/board-en.png` });

    const overflow = await c.page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    console.log("errors:", [...a.errors, ...b.errors, ...c.errors, ...d.errors], "mobile overflow:", overflow);
    await browser.close();
})();
