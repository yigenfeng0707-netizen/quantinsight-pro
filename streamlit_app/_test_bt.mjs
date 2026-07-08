import { chromium } from "playwright";

async function login(page) {
  await page.goto("http://127.0.0.1:8501", { waitUntil: "domcontentloaded" });
  await page.waitForSelector("text=用户登录", { timeout: 60000 });
  await page.getByRole("textbox", { name: "用户名" }).fill("admin");
  await page.getByRole("textbox", { name: "密码" }).fill("18969081266*");
  await page.getByRole("button", { name: "登录" }).click();
  await page.waitForTimeout(8000);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await login(page);
await page.getByTestId("stRadioGroup").getByText("📈 量化策略回测").click();
await page.waitForTimeout(5000);

const box = page.locator('[data-testid="stSelectbox"]').nth(1);
await box.click();
await page.waitForTimeout(1000);
const opts = await page.getByRole("option").allTextContents();
console.log("options", opts);
await page.getByRole("option", { name: "多因子合成" }).click();
await page.waitForTimeout(2000);
await page.getByRole("button", { name: "🚀 运行回测" }).click();
await page.waitForTimeout(35000);
const body = await page.locator("body").innerText();
console.log("annual", body.match(/年化[^\n]+/g));
await page.screenshot({ path: "../demo-output/debug_bt.png" });
await browser.close();
