const { defineConfig, devices } = require("@playwright/test");

const launchOptions = process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {};

module.exports = defineConfig({
    testDir: "web/tests",
    fullyParallel: true,
    reporter: process.env.CI ? [["github"], ["list"]] : "list",
    use: { launchOptions },
    projects: [
        { name: "desktop", use: { ...devices["Desktop Chrome"], launchOptions } },
        { name: "phone", use: { ...devices["Pixel 7"], launchOptions } },
    ],
});
