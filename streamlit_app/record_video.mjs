// E4 复赛兜底录屏：一条完整演示视频（登录 → 问答 → 回测 → SHAP）
// 运行：node record_video.mjs   （本地 Streamlit 需已在 127.0.0.1:8501）
import { chromium } from "playwright";
import fs from "fs";

const BASE = "http://127.0.0.1:8501";
const OUT = "../_local_shots/video";
fs.mkdirSync(OUT, { recursive: true });

const b = await chromium.launch({ headless: true });
const ctx = await b.newContext({
  viewport: { width: 1600, height: 900 },
  deviceScaleFactor: 1.5,
  recordVideo: { dir: OUT, size: { width: 1600, height: 900 } },
});
const page = await ctx.newPage();
page.setDefaultTimeout(60000);
const t0 = Date.now();
const log = (m) => console.log(`[${Math.round((Date.now() - t0) / 1000)}s] ${m}`);
const pause = (ms, why) => { log(`PAUSE ${why} ${ms / 1000}s`); return page.waitForTimeout(ms); };

await page.goto(BASE, { waitUntil: "load" });
await pause(15000, "hero");
const body = await page.locator("body").innerText();
if (body.includes("登录") && !body.includes("选择功能模块")) {
  await page.locator('input[placeholder="请输入用户名"]').fill("roadshow");
  await page.locator('input[placeholder="请输入密码"]').fill("Roadshow2026!");
  await page.getByRole("button", { name: /登录/ }).last().click();
  await pause(12000, "login");
}
log("LOGIN:", (await page.locator("body").innerText()).includes("选择功能模块") ? "ok" : "FAIL");

const nav = async (label) => {
  await page.locator(`label:has-text("${label}")`).first().click({ timeout: 15000 });
  await pause(10000, `nav ${label}`);
};

// ── 模块 1：AI 投研问答（引用可溯源） ──
await nav("🤖 AI 投研问答");
await page.locator("textarea").first().fill("贵州茅台最近一年的营业收入和归母净利润是多少？请注明数据来源与统计口径。");
await page.getByRole("button", { name: /分析/ }).click();
log("QA_SUBMITTED");
let answered = false;
for (let i = 0; i < 36; i++) {
  await page.waitForTimeout(5000);
  const t = await page.locator("body").innerText();
  if ((t.includes("来源") || t.includes("亿元") || t.includes("净利润")) && t.length > 1500) { answered = true; break; }
}
log("QA_ANSWERED:", answered);
await pause(8000, "qa展示引用");
await page.screenshot({ path: "../_local_shots/video_qa.png" });

// ── 模块 2：量化策略回测（确定性计算） ──
await nav("📈 量化策略回测");
await page.getByLabel("📊 标的指数").click();
await page.waitForTimeout(900);
await page.getByRole("option", { name: "创业板指" }).click({ timeout: 8000 });
await page.waitForTimeout(800);
await page.getByLabel("🧠 策略类型").click();
await page.waitForTimeout(900);
await page.getByRole("option", { name: "多因子合成" }).click({ timeout: 8000 });
await page.waitForTimeout(1200);
await page.getByRole("button", { name: /运行回测/ }).click();
log("BT_RUNNING");
await page.waitForTimeout(120000);
await page.locator("text=回测结果").first().scrollIntoViewIfNeeded().catch(() => {});
await pause(4000, "回测结果展示");
await page.screenshot({ path: "../_local_shots/video_backtest.png" });

// ── 模块 3：个股分析 + SHAP 归因（可解释性） ──
await nav("🔍 个股分析");
await page.getByRole("button", { name: /贵州茅台/ }).first().click();
await pause(8000, "个股加载");
await page.locator('label:has-text("SHAP解释")').first().click();
await pause(5000, "SHAP展开");
await page.getByRole("button", { name: /开始 SHAP 分析/ }).click();
log("SHAP_RUNNING");
await page.waitForTimeout(60000);
await page.getByRole("tab", { name: /条形/ }).click({ timeout: 10000 }).catch(() => log("TAB_BAR_FAIL"));
await pause(8000, "条形图渲染");
await page.locator("text=模型性能指标").first().scrollIntoViewIfNeeded().catch(() => {});
await page.keyboard.press("PageDown");
await pause(6000, "指标展示");
await page.locator("text=SHAP").last().scrollIntoViewIfNeeded().catch(() => {});
await pause(8000, "SHAP图展示");
await page.screenshot({ path: "../_local_shots/video_shap.png" });

const video = await page.video();
await ctx.close();
const vp = await video.path();
const dest = `${OUT}/demo_full_${new Date().toISOString().slice(0, 10)}.webm`;
fs.renameSync(vp, dest);
log("VIDEO_SAVED:", dest, fs.statSync(dest).size);
await b.close();
console.log("RECORD_DONE");
