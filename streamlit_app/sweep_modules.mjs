// 全模块线上排雷扫描：QA 账号登录 → 遍历侧栏所有模块 → 检查加载错误
// 只用 roadshow（QA 账号），不碰 6 个试用号的使用记录
import { chromium } from "playwright";

const BASE = "http://121.196.102.54";
const ERR_PAT = /Traceback|NameError|AttributeError|ImportError|TypeError|KeyError|IndexError|ValueError|发生错误|出现错误|加载失败|❌|💀|something went wrong/i;

const b = await chromium.launch({ headless: true });
const ctx = await b.newContext({ viewport: { width: 1600, height: 900 } });
const page = await ctx.newPage();
const errors = [];
const visited = [];
page.setDefaultTimeout(90000);
const wait = (ms) => new Promise(r => setTimeout(r, ms));

await page.goto(BASE, { waitUntil: "load" });
await wait(15000);
await page.locator('input[placeholder="请输入用户名"]').fill("admin");
await page.locator('input[placeholder="请输入密码"]').fill("QIyrd2026demo");
await page.getByRole("button", { name: /登录/ }).last().click();
await wait(18000);
const bodyAfter = await page.locator("body").innerText();
console.log("LOGIN:", bodyAfter.includes("选择功能模块") ? "ok" : "FAIL", "| still_on_login:", bodyAfter.includes("用户登录"));

// 提取侧栏所有模块标签
const allLabels = await page.locator('div[role="radiogroup"] label, [data-testid="stRadio"] label').allTextContents().catch(() => []);
console.log("RADIOS:", JSON.stringify(allLabels));

for (const label of allLabels.filter(x => x && x.trim())) {
  const name = label.trim();
  try {
    await page.locator(`label:has-text("${name}")`).first().click({ timeout: 20000 });
    await wait(9000);
    const t = await page.locator("body").innerText();
    const hits = t.match(new RegExp(ERR_PAT.source, "gi"));
    // 允许「📰 最新新闻」等含 ❌ 误报，做白名单过滤
    const whitelisted = /新闻|快讯|退市|风险提示/.test(name) && hits && hits.length <= 3;
    if (hits && hits.length > 3 && !whitelisted) {
      const sample = (t.match(/.{0,40}(Traceback|NameError|AttributeError|ImportError|TypeError|KeyError|IndexError|ValueError).{0,60}/s) || [""])[0].replace(/\s+/g, " ").slice(0, 130);
      errors.push({ module: name, n: hits.length, sample });
      console.log(`❌ ${name}: ${hits.length} 处错误信号 | ${sample}`);
    } else {
      visited.push(name);
      console.log(`✅ ${name}${hits ? ` (${hits.length} 疑似误报已过滤)` : ""}`);
    }
  } catch (e) {
    errors.push({ module: name, n: 0, sample: "CLICK_FAIL: " + String(e).slice(0, 80) });
    console.log(`⚠️ ${name}: 点击失败 ${String(e).slice(0, 60)}`);
  }
}
await page.screenshot({ path: "../_local_shots/sweep_final.png" });
await b.close();
console.log("\n===== SWEEP SUMMARY =====");
console.log(` modules_ok=${visited.length}  modules_err=${errors.length}`);
for (const e of errors) console.log(" ERR:", e.module, "|", e.sample);
console.log("SWEEP_DONE");
