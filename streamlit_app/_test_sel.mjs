import { chromium } from "playwright";

async function login(page) {
  await page.goto("http://127.0.0.1:8501", { waitUntil: "domcontentloaded" });
  await page.waitForSelector("text=用户登录", { timeout: 60000 });
  await page.getByRole("textbox", { name: "用户名" }).fill("admin");
  await page.getByRole("textbox", { name: "密码" }).fill(process.env.TEST_ADMIN_PASS);
  await page.getByRole("button", { name: "登录" }).click();
  await page.waitForTimeout(8000);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await login(page);
await page.getByTestId("stRadioGroup").getByText("📈 量化策略回测").click();
await page.waitForTimeout(5000);
const n = await page.locator('[data-testid="stSelectbox"]').count();
console.log("selectboxes", n);
for (let i = 0; i < n; i++) {
  const t = await page.locator('[data-testid="stSelectbox"]').nth(i).innerText();
  console.log(i, t.replace(/\n/g, " | "));
}
// try clicking strategy text directly
await page.getByText("双均线动量").click();
await page.waitForTimeout(1000);
const opts = await page.getByRole("option").allTextContents();
console.log("options", opts);
await browser.close();
