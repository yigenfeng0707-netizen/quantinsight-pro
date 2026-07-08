import { chromium } from "playwright";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto("http://127.0.0.1:8501", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(3000);
await page.waitForSelector("text=用户登录", { timeout: 60000 });
try {
  await page.getByRole("textbox", { name: "用户名" }).fill("admin");
  console.log("role fill ok");
} catch (e) {
  console.log("role fill fail", e.message);
}
await browser.close();
