const path = require("path");
const { test, expect } = require("@playwright/test");

const PAGE_URL = `file://${path.resolve(__dirname, "..", "index.html")}`;
const ROWS = 6;
const COLS = 9;

const SOLUTION_COUNTS = [
    { month: 11, day: 16, weekday: 4, label: "NOV, 16, Fri", count: 168 },
    { month: 10, day: 16, weekday: 4, label: "OCT, 16, Fri", count: 502 },
    { month: 1, day: 1, weekday: 0, label: "JAN, 1, Mon", count: 527 },
    { month: 2, day: 29, weekday: 3, label: "FEB, 29, Thu", count: 222 },
    { month: 12, day: 31, weekday: 6, label: "DEC, 31, Sun", count: 623 },
];

async function openGame(page, date = { month: 11, day: 16, weekday: 4 }) {
    const errors = [];
    page.on("pageerror", (err) => errors.push(err.message));
    page.on("console", (msg) => {
        if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto(PAGE_URL);
    await setDate(page, date);
    return errors;
}

async function setDate(page, { month, day, weekday }) {
    await page.selectOption("#month", String(month));
    await page.selectOption("#day", String(day));
    await page.selectOption("#weekday", String(weekday));
}

async function clickCell(page, row, col) {
    const board = page.locator("#board");
    const box = await board.boundingBox();
    await board.click({ position: { x: ((col + 0.5) / COLS) * box.width, y: ((row + 0.5) / ROWS) * box.height } });
}

async function pickPiece(page, name) {
    await page.locator(`.tray-piece[data-name="${name}"]`).click();
}

const placedCount = (page) => page.locator("#placed-count");
const status = (page) => page.locator("#status");

test("loads with ten pieces, the chosen date and no console errors", async ({ page }) => {
    const errors = await openGame(page);
    await expect(page.locator(".tray-piece")).toHaveCount(10);
    await expect(page.locator("#chips .chip")).toHaveText(["NOV", "16", "Fri"]);
    await expect(placedCount(page)).toHaveText("0/10");
    await expect(status(page)).toContainText("Leave NOV, 16, Fri uncovered");
    expect(errors).toEqual([]);
});

test("opens on today's date", async ({ page }) => {
    await page.goto(PAGE_URL);
    const expected = await page.evaluate(() => {
        const now = new Date();
        return [String(now.getMonth() + 1), String(now.getDate()), String((now.getDay() + 6) % 7)];
    });
    await expect(page.locator("#month")).toHaveValue(expected[0]);
    await expect(page.locator("#day")).toHaveValue(expected[1]);
    await expect(page.locator("#weekday")).toHaveValue(expected[2]);
});

test("places a piece centred on the clicked cell", async ({ page }) => {
    await openGame(page);
    await pickPiece(page, "I");
    await clickCell(page, 0, 2);
    await expect(placedCount(page)).toHaveText("1/10");
    await expect(page.locator('.tray-piece[data-name="I"]')).toHaveClass(/on-board/);
});

test("rotate turns the selected piece before placing", async ({ page }) => {
    await openGame(page);
    await pickPiece(page, "I");
    await page.locator("#rotate").click();
    await clickCell(page, 2, 8);
    await expect(placedCount(page)).toHaveText("1/10");
});

test("rejects a piece that covers a date cell", async ({ page }) => {
    await openGame(page);
    await pickPiece(page, "I");
    await clickCell(page, 3, 3);
    await expect(placedCount(page)).toHaveText("0/10");
    await expect(status(page)).toHaveClass(/bad/);
    await expect(status(page)).toContainText("I doesn't fit there: it would cover 16");
});

test("rejects a piece that runs off the board", async ({ page }) => {
    await openGame(page);
    await pickPiece(page, "I");
    await clickCell(page, 5, 7);
    await expect(placedCount(page)).toHaveText("0/10");
    await expect(status(page)).toContainText("it runs off the board");
});

test("rejects a piece that overlaps another", async ({ page }) => {
    await openGame(page);
    await pickPiece(page, "I");
    await clickCell(page, 0, 2);
    await pickPiece(page, "L");
    await clickCell(page, 0, 3);
    await expect(placedCount(page)).toHaveText("1/10");
    await expect(status(page)).toContainText("it overlaps I");
});

test("clicking a placed piece picks it up again", async ({ page }) => {
    await openGame(page);
    await pickPiece(page, "I");
    await clickCell(page, 0, 2);
    await clickCell(page, 0, 4);
    await expect(placedCount(page)).toHaveText("0/10");
    await expect(page.locator('.tray-piece[data-name="I"]')).toHaveAttribute("aria-pressed", "true");
});

test("hint places one piece that belongs to a solution", async ({ page }) => {
    await openGame(page);
    await page.locator("#hint").click();
    await expect(placedCount(page)).toHaveText("1/10");
    await expect(status(page)).toContainText("Hint: placed");
    await page.locator("#solve").click();
    await expect(placedCount(page)).toHaveText("10/10");
});

test("solve completes the board and keeps placed pieces", async ({ page }) => {
    await openGame(page);
    await page.locator("#hint").click();
    const hinted = await page.locator(".tray-piece.on-board").getAttribute("data-name");
    await page.locator("#solve").click();
    await expect(placedCount(page)).toHaveText("10/10");
    await expect(page.locator("#frame")).toHaveClass(/solved/);
    await expect(status(page)).toContainText("Solved. Only NOV, 16, Fri are showing.");
    await expect(page.locator(`.tray-piece[data-name="${hinted}"]`)).toHaveClass(/on-board/);
    await expect(page.locator("#hint")).toBeDisabled();
});

test("a position that isolates a cell has no solution", async ({ page }) => {
    await openGame(page);
    await pickPiece(page, "U");
    await clickCell(page, 1, 1);
    await expect(placedCount(page)).toHaveText("1/10");
    await page.locator("#hint").click();
    await expect(status(page)).toContainText("No solution from this position");
    await expect(placedCount(page)).toHaveText("1/10");
});

test("clear empties the board", async ({ page }) => {
    await openGame(page);
    await page.locator("#solve").click();
    await page.locator("#clear").click();
    await expect(placedCount(page)).toHaveText("0/10");
});

test("changing the date picks up pieces that cover it", async ({ page }) => {
    await openGame(page);
    await pickPiece(page, "I");
    await clickCell(page, 0, 2);
    await page.selectOption("#month", "1");
    await expect(placedCount(page)).toHaveText("0/10");
    await expect(status(page)).toContainText("Picked up I because it covered the new date.");
});

test.describe("solution browser", () => {
    test.skip(({ isMobile }) => isMobile, "solver results do not depend on the viewport");

    for (const { month, day, weekday, label, count } of SOLUTION_COUNTS) {
        test(`finds all ${count} solutions for ${label}`, async ({ page }) => {
            await openGame(page, { month, day, weekday });
            await page.locator("#count").click();
            await expect(page.locator("#count-line")).toContainText(`${label} has ${count} solutions`);
            await expect(page.locator("#sol-label")).toHaveText(`Solution 1 / ${count}`);
            await expect(placedCount(page)).toHaveText("10/10");
        });
    }

    test("slider and arrows step through the solutions", async ({ page }) => {
        await openGame(page);
        await page.locator("#count").click();
        await expect(page.locator("#browser")).toBeVisible();
        const first = await page.locator("#board").innerHTML();

        await page.locator("#sol-next").click();
        await expect(page.locator("#sol-label")).toHaveText("Solution 2 / 168");
        expect(await page.locator("#board").innerHTML()).not.toEqual(first);

        await page.locator("#sol-range").focus();
        await page.keyboard.press("End");
        await expect(page.locator("#sol-label")).toHaveText("Solution 168 / 168");
        await expect(status(page)).toContainText("Showing solution 168 of 168.");

        await page.locator("#sol-next").click();
        await expect(page.locator("#sol-label")).toHaveText("Solution 1 / 168");
        await page.locator("#sol-prev").click();
        await expect(page.locator("#sol-label")).toHaveText("Solution 168 / 168");
    });

    test("changing the date hides the solution browser", async ({ page }) => {
        await openGame(page);
        await page.locator("#count").click();
        await expect(page.locator("#browser")).toBeVisible();
        await page.selectOption("#day", "17");
        await expect(page.locator("#browser")).toBeHidden();
    });
});

test("the page never scrolls sideways", async ({ page }) => {
    await openGame(page);
    await page.locator("#solve").click();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
});
