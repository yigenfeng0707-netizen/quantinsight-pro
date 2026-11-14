// 复赛路演本地录屏 v2：node record_shots.mjs <chat|backtest|stock>
import { chromium } from "playwright";
import fs from "fs";

const BASE = "http://127.0.0.1:8501";
const stage = process.argv[2] || "chat";
const OUT = "../_local_shots";
fs.mkdirSync(OUT, { recursive: true });

const b = await chromium.launch({ headless: true });
const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1.5 });
const page = await ctx.newPage();
page.setDefaultTimeout(60000);

await page.goto(BASE, { waitUntil: "load" });
await page.waitForTimeout(20000);

// 登录（gate 内直接登录；roadshow 已注册）
const body = await page.locator("body").innerText();
if (body.includes("登录") && !body.includes("选择功能模块")) {
  await page.locator('input[placeholder="请输入用户名"]').fill("roadshow");
  await page.locator('input[placeholder="请输入密码"]').fill("Roadshow2026!");
  await page.getByRole("button", { name: /登录/ }).last().click();
  await page.waitForTimeout(12000);
}
console.log("LOGIN:", (await page.locator("body").innerText()).includes("选择功能模块") ? "ok" : "FAIL");

const nav = async (label) => {
  await page.locator(`label:has-text("${label}")`).first().click({ timeout: 15000 });
  await page.waitForTimeout(12000);
};

if (stage === "chat") {
  await nav("🤖 AI 投研问答");
  const q = "贵州茅台最近一年的营业收入和归母净利润是多少？请注明数据来源与统计口径。";
  await page.locator("textarea").first().fill(q);
  await page.getByRole("button", { name: /分析/ }).click();
  console.log("SUBMITTED: waiting LLM...");
  // 等回答：正文出现"来源/口径/数据"类字样或超时
  let answered = false;
  for (let i = 0; i < 24; i++) {
    await page.waitForTimeout(5000);
    const t = await page.locator("body").innerText();
    if ((t.includes("来源") || t.includes("亿元") || t.includes("净利润")) && t.length > 1200) {
      answered = true; break;
    }
  }
  console.log("ANSWERED:", answered);
  await page.waitForTimeout(4000);
  await page.screenshot({ path: `${OUT}/chat_answer.png` });
  console.log("SHOT: chat_answer.png");
}

if (stage === "backtest") {
  await nav("📈 量化策略回测");
  // 参数：中证500 + 多因子合成（react-aria ComboBox，aria-label 定位）
  await page.getByLabel("📊 标的指数").click();
  await page.waitForTimeout(900);
  await page.getByRole("option", { name: "创业板指" }).click({ timeout: 8000 });
  await page.waitForTimeout(800);
  await page.getByLabel("🧠 策略类型").click();
  await page.waitForTimeout(900);
  await page.getByRole("option", { name: "多因子合成" }).click({ timeout: 8000 });
  await page.waitForTimeout(1200);
  try {
    await page.getByLabel("📅 起始日期").click();
    await page.keyboard.type("2014", { delay: 60 });
    await page.keyboard.type("01", { delay: 60 });
    await page.keyboard.type("01", { delay: 60 });
    await page.keyboard.press("Enter");
    await page.waitForTimeout(2500);
    console.log("DATE_SET: 2014-01-01");
  } catch (e) { console.log("DATE_SET_FAIL:", String(e).slice(0, 100)); }
  await page.getByRole("button", { name: /运行回测/ }).click();
  console.log("BT_RUNNING: waiting...");
  await page.waitForTimeout(120000);
  await page.locator("text=回测结果").first().scrollIntoViewIfNeeded().catch(() => {});
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/backtest.png` });
  console.log("SHOT: backtest.png");
}

if (stage === "stock") {
  await nav("🔍 个股分析");
  await page.getByRole("button", { name: /贵州茅台/ }).first().click();
  await page.waitForTimeout(8000);
  await page.locator('label:has-text("SHAP解释")').first().click();
  await page.waitForTimeout(5000);
  await page.getByRole("button", { name: /开始 SHAP 分析/ }).click();
  console.log("SHAP_RUNNING: waiting 10-30s train...");
  await page.waitForTimeout(60000);
  // 切「条形」视图（st.tabs → role=tab）
  await page.getByRole("tab", { name: /条形/ }).click({ timeout: 10000 }).catch(() => {
    console.log("TAB_BAR_FAIL");
  });
  await page.waitForTimeout(8000);
  await page.locator("text=模型性能指标").first().scrollIntoViewIfNeeded().catch(() => {});
  await page.waitForTimeout(2500);
  await page.keyboard.press("PageDown");
  await page.waitForTimeout(6000);
  await page.locator("text=SHAP").last().scrollIntoViewIfNeeded().catch(() => {});
  await page.waitForTimeout(4000);
  await page.screenshot({ path: `${OUT}/stock_shap.png` });
  console.log("SHOT: stock_shap.png");
}

await b.close();
console.log("STAGE_DONE:", stage);
