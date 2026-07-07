#!/usr/bin/env node
/** Copy Playwright recordings + hyperframes assets into Remotion public/. */
import fs from "fs";
import path from "path";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const DEMO_OUT = path.join(ROOT, "demo-output");
const PUBLIC = path.join(ROOT, "demo-video-remotion", "public");
const FFMPEG = "C:\\ffmpeg\\ffmpeg-6.1.1-essentials_build\\bin\\ffmpeg.exe";

fs.mkdirSync(path.join(PUBLIC, "videos"), { recursive: true });
fs.mkdirSync(path.join(PUBLIC, "screenshots"), { recursive: true });

for (const id of ["h1", "h2", "h3", "h4"]) {
  const src = path.join(DEMO_OUT, `${id}.webm`);
  const dest = path.join(PUBLIC, "videos", `${id}.webm`);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
    console.log(`✓ videos/${id}.webm`);
  }
}

const shotMap = {
  h1_stock_pick: "debug_stock.png",
  h2_shap: "debug_shap.png",
  h4_backtest: "debug_bt.png",
};

for (const [dest, src] of Object.entries(shotMap)) {
  const s = path.join(DEMO_OUT, src);
  const d = path.join(PUBLIC, "screenshots", `${dest}.png`);
  if (fs.existsSync(s)) {
    fs.copyFileSync(s, d);
    console.log(`✓ screenshots/${dest}.png`);
  }
}

// Extract h3 thumbnail from webm
const h3webm = path.join(PUBLIC, "videos", "h3.webm");
const h3png = path.join(PUBLIC, "screenshots", "h3_ai_qa.png");
if (fs.existsSync(h3webm) && fs.existsSync(FFMPEG)) {
  spawnSync(
    FFMPEG,
    ["-y", "-sseof", "-3", "-i", h3webm, "-vframes", "1", "-update", "1", h3png],
    { stdio: "inherit" },
  );
  if (fs.existsSync(h3png)) console.log("✓ screenshots/h3_ai_qa.png (from webm)");
}

// h1 from capture if exists
const h1cap = path.join(ROOT, "demo-video-remotion", "public", "screenshots", "h1_stock_pick.png");
if (!fs.existsSync(h1cap)) {
  const alt = path.join(DEMO_OUT, "debug_stock.png");
  if (fs.existsSync(alt)) fs.copyFileSync(alt, h1cap);
}

console.log("\nAssets ready for Remotion render.");
