/**
 * QuantInsight Pro — 生产环境全模块 E2E 测试
 * 用法: node scripts/full_e2e_production.mjs [baseUrl]
 */
import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.argv[2] || "https://3blue1brownlab.cn";
const USER = "admin";
const PASS = process.env.TEST_ADMIN_PASS;
const OUT = path.join(__dirname, "..", "submission", "04_测试报告");
fs.mkdirSync(OUT, { recursive: true });

const PAGES = [
  "🏠 首页",
  "🤖 AI 投研问答",
  "🎯 智能选股",
  "🔍 个股分析",
  "📊 实时数据看板",
  "📡 智能盯盘",
  "💼 我的组合",
  "📈 模拟交易",
  "⚡ 智能指令",
  "📡 另类数据仪表盘",
  "📈 量化策略回测",
  "🔬 因子挖掘与IC测试",
  "🔄 宏观因子融合",
  "📡 信号验证中心",
  "🔍 语义检索",
  "📊 行业分析",
  "👤 个人中心",
  "⚙️ 管理后台",
];

const ERROR_PATTERNS = [
  /Traceback \(most recent call last\)/,
  /TypeError:/,
  /ModuleNotFoundError:/,
  /页面加载出错/,
  /AttributeError:/,
  /ValueError:.*unexpected keyword/,
  /Script execution error/,
];

function hasError(text) {
  for (const p of ERROR_PATTERNS) {
    if (p.test(text)) return p.source;
  }
  return null;
}

async function login(page) {
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 90000 });
  await page.waitForTimeout(8000);
  const body = await page.locator("body").innerText();
  if (body.includes("用户登录") || body.includes("登录")) {
    const userBox = page.getByRole("textbox", { name: "用户名" });
    if (await userBox.count()) {
      await userBox.fill(USER);
      await page.getByRole("textbox", { name: "密码" }).fill(PASS);
      await page.getByRole("button", { name: "登录" }).click();
    } else {
      await page.locator('input[type="text"]').first().fill(USER);
      await page.locator('input[type="password"]').first().fill(PASS);
      await page.getByRole("button", { name: "登录" }).click();
    }
    await page.waitForTimeout(10000);
  }
  const after = await page.locator("body").innerText();
  if (!after.includes("选择功能模块") && !after.includes("智能选股")) {
    throw new Error("登录失败");
  }
}

async function gotoPage(page, label) {
  const radio = page.locator(`label`).filter({ hasText: label });
  if (await radio.count()) {
    await radio.first().click();
  } else {
    await page.getByText(label, { exact: true }).click();
  }
  await page.waitForTimeout(6000);
}

async function testPage(page, label) {
  const result = { page: label, status: "PASS", error: null, notes: "" };
  try {
    await gotoPage(page, label);
    const text = await page.locator("body").innerText();
    const err = hasError(text);
    if (err) {
      result.status = "FAIL";
      result.error = err;
      return result;
    }
    if (!text.trim()) {
      result.status = "FAIL";
      result.error = "empty page";
      return result;
    }
    result.notes = `chars=${text.length}`;
  } catch (e) {
    result.status = "FAIL";
    result.error = e.message;
  }
  return result;
}

async function testSmartSelect(page) {
  await gotoPage(page, "🎯 智能选股");
  await page.getByRole("tab", { name: "📊 多因子评分" }).click().catch(() => {});
  await page.waitForTimeout(2000);
  const btn = page.getByRole("button", { name: /计算评分/ });
  if (await btn.count()) {
    await btn.first().click();
    await page.waitForTimeout(12000);
  }
  const text = await page.locator("body").innerText();
  const err = hasError(text);
  return {
    action: "智能选股-多因子评分",
    status: err ? "FAIL" : text.includes("评分") || text.includes("Top") ? "PASS" : "WARN",
    error: err,
  };
}

async function testBacktest(page) {
  await gotoPage(page, "📈 量化策略回测");
  const btn = page.getByRole("button", { name: /运行回测/ });
  if (await btn.count()) {
    await btn.first().click();
    await page.waitForTimeout(15000);
  }
  const text = await page.locator("body").innerText();
  const err = hasError(text);
  return {
    action: "量化回测-运行",
    status: err ? "FAIL" : "PASS",
    error: err,
  };
}

async function testAIQA(page) {
  await gotoPage(page, "🤖 AI 投研问答");
  const ta = page.locator("textarea").first();
  if (await ta.count()) {
    await ta.fill("简要分析当前A股市场趋势");
    const analyze = page.getByRole("button", { name: /分析/ });
    if (await analyze.count()) {
      await analyze.first().click();
      await page.waitForTimeout(45000);
    }
  }
  const text = await page.locator("body").innerText();
  const err = hasError(text);
  const hasReply =
    text.includes("建议") || text.includes("summary") || text.includes("摘要") || text.includes("Mock");
  return {
    action: "AI投研问答",
    status: err ? "FAIL" : hasReply ? "PASS" : "WARN",
    error: err,
    notes: hasReply ? "有回复内容" : "无明确回复",
  };
}

async function testStockAnalysis(page) {
  await gotoPage(page, "🔍 个股分析");
  await page.waitForTimeout(3000);
  const text = await page.locator("body").innerText();
  const err = hasError(text);
  return {
    action: "个股分析",
    status: err ? "FAIL" : text.includes("SHAP") || text.includes("分析") ? "PASS" : "WARN",
    error: err,
  };
}

async function main() {
  const report = {
    baseUrl: BASE,
    timestamp: new Date().toISOString(),
    pageTests: [],
    actionTests: [],
    summary: {},
  };

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
    ignoreHTTPSErrors: true,
  });

  try {
    await login(page);
    report.login = "PASS";

    for (const p of PAGES) {
      const r = await testPage(page, p);
      report.pageTests.push(r);
      console.log(`${r.status} ${p}${r.error ? " — " + r.error : ""}`);
    }

    for (const fn of [testSmartSelect, testBacktest, testAIQA, testStockAnalysis]) {
      const r = await fn(page);
      report.actionTests.push(r);
      console.log(`${r.status} ${r.action}${r.error ? " — " + r.error : ""}`);
    }

    await page.screenshot({ path: path.join(OUT, "e2e_final.png"), fullPage: false });
  } catch (e) {
    report.login = "FAIL";
    report.fatal = e.message;
    console.error("FATAL:", e.message);
  } finally {
    await browser.close();
  }

  const fails = [
    ...report.pageTests.filter((x) => x.status === "FAIL"),
    ...report.actionTests.filter((x) => x.status === "FAIL"),
  ];
  const warns = report.actionTests.filter((x) => x.status === "WARN");
  report.summary = {
    pages: report.pageTests.length,
    pagePass: report.pageTests.filter((x) => x.status === "PASS").length,
    actions: report.actionTests.length,
    actionPass: report.actionTests.filter((x) => x.status === "PASS").length,
    fail: fails.length,
    warn: warns.length,
    overall: fails.length === 0 && report.login === "PASS" ? "PASS" : "FAIL",
  };

  const jsonPath = path.join(OUT, "e2e_production_report.json");
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2), "utf-8");
  console.log("\nReport:", jsonPath);
  console.log("Summary:", JSON.stringify(report.summary));
  process.exit(report.summary.overall === "PASS" ? 0 : 1);
}

main();
