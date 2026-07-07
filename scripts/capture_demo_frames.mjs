#!/usr/bin/env node
/**
 * Capture demo screenshots via Playwright + hyperframes site capture.
 * Reuses demo.storyboard.json actions for reliable Streamlit navigation.
 */
import { createRequire } from "module";
import { spawnSync } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const require = createRequire(path.join(ROOT, "streamlit_app", "package.json"));
const { chromium } = require("playwright");

const OUT_DIR = path.join(ROOT, "demo-video-remotion", "public", "screenshots");
const STORYBOARD = path.join(ROOT, "demo.storyboard.json");
const HF_CAPTURE_DIR = path.join(ROOT, "demo-output", "hyperframes-capture");

const SHOT_MAP = {
  h1: "h1_stock_pick.png",
  h2: "h2_shap.png",
  h3: "h3_ai_qa.png",
  h4: "h4_backtest.png",
};

fs.mkdirSync(OUT_DIR, { recursive: true });

function loadStoryboard() {
  return JSON.parse(fs.readFileSync(STORYBOARD, "utf-8"));
}

async function runAction(page, action, baseUrl) {
  if (typeof action === "number") return page.waitForTimeout(action);
  if (action.goto != null) {
    const u = action.goto.startsWith("http")
      ? action.goto
      : baseUrl.replace(/\/$/, "") + action.goto;
    await page.goto(u, { waitUntil: "domcontentloaded", timeout: 120000 });
    await page.waitForTimeout(3000);
    return;
  }
  if (action.wait != null) return page.waitForTimeout(action.wait);
  if (action.press != null) return page.keyboard.press(action.press);
  if (action.scroll?.y != null) return page.mouse.wheel(0, action.scroll.y);
  if (action.select) {
    const s = action.select;
    const box = page.locator('[data-testid="stSelectbox"]').nth(s.nth ?? 0);
    await box.click();
    await page.waitForTimeout(500);
    await page.getByRole("option", { name: s.value }).click();
    return;
  }
  if (action.waitFor?.text) {
    const t = action.waitFor.timeout ?? 30000;
    await page
      .waitForSelector(`text=${action.waitFor.text}`, { timeout: t })
      .catch(() => page.waitForTimeout(2000));
    return;
  }
  if (action.click) {
    const c = action.click;
    if (c.sidebar)
      return page.getByTestId("stRadioGroup").getByText(c.sidebar).click();
    if (c.testId) return page.getByTestId(c.testId).click();
    if (c.role) {
      const opts = {};
      if (c.namePattern) opts.name = new RegExp(c.namePattern);
      else if (c.name) opts.name = c.name;
      return page.getByRole(c.role, opts).click();
    }
    if (c.text) return page.getByText(c.text).click();
  }
  if (action.fill) {
    const f = action.fill;
    if (f.css) {
      await page.locator(f.css).fill(f.value);
      return;
    }
    const loc = f.testId
      ? page.getByTestId(f.testId)
      : page.getByRole(f.role, { name: f.name });
    await loc.fill(f.value);
  }
}

async function captureScene(browser, scene, sb) {
  const vp = sb.viewport || { width: 1920, height: 1080 };
  const page = await browser.newPage({ viewport: vp });
  page.setDefaultTimeout(90000);
  try {
    for (const action of scene.actions || []) {
      await runAction(page, action, sb.baseUrl);
    }
    await page.waitForTimeout(1000);
    const outName = SHOT_MAP[scene.id];
    if (!outName) return;
    const out = path.join(OUT_DIR, outName);
    await page.screenshot({ path: out, fullPage: false });
    console.log(`✓ ${outName} (${scene.id})`);
  } finally {
    await page.close();
  }
}

async function main() {
  const sb = loadStoryboard();
  console.log("=== QuantInsight Demo Frame Capture ===");
  console.log(`Base URL: ${sb.baseUrl}`);
  console.log(`Output: ${OUT_DIR}`);

  try {
    fs.mkdirSync(path.dirname(HF_CAPTURE_DIR), { recursive: true });
    console.log("\n[hyperframes] capture site visual identity...");
    const r = spawnSync(
      "hyperframes",
      ["capture", sb.baseUrl, "-o", HF_CAPTURE_DIR, "--json"],
      { encoding: "utf-8", timeout: 180000 },
    );
    if (r.status === 0) console.log("✓ hyperframes capture:", HF_CAPTURE_DIR);
    else console.warn("⚠ hyperframes capture skipped");
  } catch (e) {
    console.warn("⚠ hyperframes capture failed:", e.message);
  }

  const browser = await chromium.launch({ headless: true });
  try {
    const browserScenes = sb.scenes.filter(
      (s) => s.type === "browser" && SHOT_MAP[s.id],
    );
    for (const scene of browserScenes) {
      console.log(`\nCapturing ${scene.id}...`);
      await captureScene(browser, scene, sb);
    }
  } finally {
    await browser.close();
  }

  // Fallback: use hyperframes viewport screenshots if any shot missing
  for (const [, name] of Object.entries(SHOT_MAP)) {
    const dest = path.join(OUT_DIR, name);
    if (!fs.existsSync(dest)) {
      const hfShots = path.join(HF_CAPTURE_DIR, "assets", "screenshots");
      if (fs.existsSync(hfShots)) {
        const pngs = fs.readdirSync(hfShots).filter((f) => f.endsWith(".png"));
        if (pngs.length) {
          fs.copyFileSync(path.join(hfShots, pngs[0]), dest);
          console.log(`⚠ fallback screenshot for ${name} from hyperframes`);
        }
      }
    }
  }

  const missing = Object.values(SHOT_MAP).filter(
    (n) => !fs.existsSync(path.join(OUT_DIR, n)),
  );
  if (missing.length) {
    console.error("Missing screenshots:", missing.join(", "));
    process.exit(1);
  }
  console.log("\n=== Capture complete ===");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
