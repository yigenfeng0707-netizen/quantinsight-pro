// 修复验收 v2：智能指令 → 📊 报告生成 tab → 生成（输入框/按钮先探测）
import { chromium } from "playwright";
const BASE = "http://121.196.102.54";
const b = await chromium.launch({ headless: true });
const ctx = await b.newContext({ viewport: { width: 1600, height: 900 } });
const page = await ctx.newPage();
page.setDefaultTimeout(60000);
const wait = (ms) => new Promise(r => setTimeout(r, ms));

await page.goto(BASE, { waitUntil: "load" });
await wait(10000);
await page.locator('input[placeholder="请输入用户名"]').fill("admin");
await page.locator('input[placeholder="请输入密码"]').fill("QIyrd2026demo");
await page.getByRole("button", { name: /登录/ }).last().click();
await wait(12000);
console.log("LOGIN:", (await page.locator("body").innerText()).includes("选择功能模块") ? "ok" : "FAIL");

await page.locator('label:has-text("⚡ 智能指令")').first().click();
await wait(9000);
await page.getByRole("tab", { name: "📊 报告生成" }).click();
await wait(6000);

// 探测该 tab 下的按钮与输入
const btnLoc = page.getByRole("button");
const n = await btnLoc.count();
const btns = [];
for (let i = 0; i < Math.min(n, 40); i++) btns.push((await btnLoc.nth(i).innerText().catch(() => "")).trim());
console.log("TAB_BTNS:", JSON.stringify(btns.filter(x => x)));

const genBtn = page.getByRole("button", { name: /生成/ }).last();
await genBtn.scrollIntoViewIfNeeded().catch(() => {});
await genBtn.click();
console.log("CLICKED_GEN");
let result = "TIMEOUT";
for (let i = 0; i < 36; i++) {
  await wait(5000);
  const t = await page.locator("body").innerText();
  if (t.includes("报告生成成功")) { result = "SUCCESS"; break; }
  if (t.includes("生成失败") || t.includes("❌")) { result = "FAIL: " + (t.match(/❌[^\n]*|生成失败[^\n]*/)?.[0] || "").slice(0, 150); break; }
}
console.log("RESULT:", result);
await page.screenshot({ path: "../_local_shots/report_verify.png" });
await b.close();
console.log("VERIFY_DONE");
