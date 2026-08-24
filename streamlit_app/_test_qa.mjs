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
await page.getByText("🤖 AI 投研问答").click();
await page.waitForTimeout(4000);
try {
  await page.getByRole("textbox", { name: "请输入您的投研问题" }).fill("贵州茅台最新财报的核心亮点和风险点是什么？");
  console.log("qa fill ok");
} catch (e) {
  console.log("qa fill fail", e.message);
  const areas = await page.locator("textarea").count();
  console.log("textarea count", areas);
}
await page.getByRole("button", { name: "🚀 分析" }).click();
await page.waitForTimeout(12000);
await page.screenshot({ path: "../demo-output/debug_qa.png" });
await browser.close();
