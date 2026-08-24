import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto("http://127.0.0.1:8501", { waitUntil: "load" });
await page.waitForTimeout(25000);

await page.locator('input[type="text"]').first().fill("admin");
await page.locator('input[type="password"]').first().fill(process.env.TEST_ADMIN_PASS);
await page.getByRole("button", { name: "登录" }).click();
await page.waitForTimeout(10000);
const text = await page.locator("body").innerText();
console.log("logged in:", text.includes("智能选股"));
await page.screenshot({ path: "../demo-output/debug_after_login.png" });
await browser.close();
