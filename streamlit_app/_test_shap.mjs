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
await page.waitForTimeout(4000);
await page.getByText("AI 可解释性分析").click();
await page.waitForTimeout(30000);
const tabs = await page.getByRole("tab").allTextContents();
console.log("tabs", tabs);
const body = await page.locator("body").innerText();
console.log("has SHAP", body.includes("SHAP"));
console.log("has error", body.includes("失败") || body.includes("加载失败"));
await page.screenshot({ path: "../demo-output/debug_shap.png", fullPage: true });
await browser.close();
