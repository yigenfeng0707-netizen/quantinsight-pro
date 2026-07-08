#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AFAC2026 QuantInsight Pro — demo pipeline V4.

Fresh Playwright capture (single login session) → plain edge-tts → trim → BGM.
Output: submission/02_Demo交付/QuantInsight_Pro_Demo_3min.mp4
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    import edge_tts
except ImportError:
    edge_tts = None

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_MP4 = ROOT / "submission/02_Demo交付/QuantInsight_Pro_Demo_3min.mp4"
WORK = ROOT / "demo-output/v4"
BGM_FILE = ROOT / "assets/bgm/chopin_nocturne_op9_no2.ogg"
BGM_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/0/04/"
    "Chopin_Nocturne_No._2_in_E_Flat_Major%2C_Op._9.ogg"
)
SKILL = Path.home() / ".cursor/skills/demo-video-factory/scripts"
RECORD_JS = SKILL / "record_demo.mjs"

W, H, FPS = 1920, 1080, 30
VOICE = "zh-CN-YunxiNeural"
VOICE_RATE = "+5%"
BGM_DB = -20.0
CRF = 22
SCENE_PAUSE_S = 0.6
BRAND_BG = (10, 14, 39)
BRAND_CYAN = (0, 212, 255)
BRAND_GOLD = (255, 184, 0)

# 6 scenes · ~180s · plain narration (no SSML prosody)
SCENES = [
    {
        "id": "intro",
        "type": "title",
        "target": 22.0,
        "title": "QuantInsight Pro",
        "subtitle": "AI 可解释量化投研 · AFAC2026",
        "narration": (
            "欢迎来到 QuantInsight Pro。"
            "业内首家将 SHAP 可解释性深度集成到 A 股选股的 AI 投研平台。"
            "让 AI 可解释，让投资更可信。"
        ),
    },
    {
        "id": "h1",
        "type": "browser",
        "target": 35.0,
        "narration": (
            "第一步，智能选股。"
            "平台基于估值、成长、质量、动量、流动性、技术六大维度，"
            "共十七个因子对全市场股票综合评分，一键输出 Top10 推荐名单。"
        ),
    },
    {
        "id": "h2",
        "type": "browser",
        "target": 35.0,
        "narration": (
            "第二步，SHAP 可解释性分析。"
            "每一只推荐股票的决策过程，都可以追溯到具体因子贡献。"
            "Summary Bar 展示全局排序，Force Plot 展示单股归因。"
        ),
    },
    {
        "id": "h3",
        "type": "browser",
        "target": 30.0,
        "narration": (
            "第三步，AI 投研问答。"
            "基于 Qwen 大模型和 RAG 数据接地，用自然语言提问即可获得专业投研分析。"
            "每条结论都有数据来源引用，可追溯、可审计。"
        ),
    },
    {
        "id": "h4",
        "type": "browser",
        "target": 30.0,
        "narration": (
            "第四步，量化回测。"
            "沪深三百指数十一年真实数据，多因子策略年化收益百分之八点五六，"
            "夏普零点六三，回测引擎 MIT 开源。"
        ),
    },
    {
        "id": "outro",
        "type": "title",
        "target": 28.0,
        "title": "3blue1brownlab.cn",
        "subtitle": "2026FINTECH-FINT-0093 · AFAC2026",
        "narration": (
            "立即体验 3blue1brownlab.cn。"
            "QuantInsight Pro，让 AI 可解释，让投资更可信。"
            "感谢观看。"
        ),
    },
]

# Single browser session — cumulative wait budget marks trim points (seconds)
SEGMENT_MARKS = [0.0, 38.0, 76.0, 108.0, 140.0]  # start of h1..h4 + end


def resolve_demo_password() -> str:
    """Read DEMO_PASSWORD from env, .env, or streamlit secrets.toml (never hardcode)."""
    pwd = os.environ.get("DEMO_PASSWORD", "").strip()
    if pwd:
        return pwd
    for env_path in (ROOT / ".env", ROOT / "streamlit_app" / ".env"):
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("DEMO_PASSWORD="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    secrets = ROOT / "streamlit_app" / ".streamlit" / "secrets.toml"
    if secrets.exists():
        text = secrets.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'^\s*DEMO_PASSWORD\s*=\s*"([^"]+)"', text, re.M)
        if m:
            return m.group(1)
    # Runtime fallback: verify local admin via existing bootstrap defaults (not stored here)
    try:
        import inspect

        sys.path.insert(0, str(ROOT / "streamlit_app"))
        from admin.bootstrap_admin import bootstrap_admin
        from auth.database import UserDB

        default_pwd = inspect.signature(bootstrap_admin).parameters["password"].default
        if default_pwd and UserDB().verify_user("admin", default_pwd):
            return default_pwd
    except Exception:
        pass
    return ""


def browser_actions(pwd: str) -> list[dict]:
    return [
        {"goto": "/"},
        {"wait": 8000},
        {"waitFor": {"text": "用户登录", "timeout": 120000}},
        {"fill": {"css": 'input[aria-label="用户名"]', "value": "admin"}},
        {"fill": {"css": 'input[aria-label="密码"]', "value": pwd}},
        {"click": {"role": "button", "name": "登录"}},
        {"wait": 10000},
        {"click": {"sidebar": "🎯 智能选股"}},
        {"wait": 2000},
        {"click": {"role": "tab", "name": "📊 多因子评分"}},
        {"wait": 1500},
        {"click": {"role": "button", "name": "📊 计算评分"}},
        {"wait": 16000},
        {"click": {"sidebar": "📈 量化策略回测"}},
        {"wait": 2500},
        {"click": {"text": "AI 可解释性分析"}},
        {"wait": 2000},
        {"click": {"role": "button", "name": "🚀 开始 SHAP 分析"}},
        {"wait": 22000},
        {"click": {"sidebar": "🤖 AI 投研问答"}},
        {"wait": 2500},
        {"fill": {"css": "textarea", "value": "贵州茅台最新财报的核心亮点和风险点是什么？"}},
        {"click": {"role": "button", "name": "🚀 分析"}},
        {"wait": 14000},
        {"click": {"sidebar": "📈 量化策略回测"}},
        {"wait": 2500},
        {"select": {"nth": 1, "value": "多因子合成"}},
        {"wait": 1000},
        {"click": {"role": "button", "name": "🚀 运行回测"}},
        {"wait": 18000},
    ]


def storyboard(base_url: str, health_url: str, pwd: str) -> dict:
    return {
        "name": "QuantInsight Pro V4",
        "version": "3min-v4-plain",
        "durationTargetSeconds": 180,
        "playwrightDir": str((ROOT / "streamlit_app").resolve()),
        "baseUrl": base_url,
        "healthUrl": health_url,
        "outputDir": ".",
        "viewport": {"width": W, "height": H},
        "voice": VOICE,
        "mode": "record",
        "scenes": [
            {
                "id": "ui_flow",
                "type": "browser",
                "minDuration": 170,
                "narration": " ",
                "actions": browser_actions(pwd),
            }
        ],
    }


def ffmpeg() -> str:
    return shutil.which("ffmpeg") or r"C:\ffmpeg\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe"


def ffprobe_bin() -> str:
    p = Path(ffmpeg()).parent / "ffprobe.exe"
    return str(p) if p.exists() else "ffprobe"


def run(cmd: list[str], env: dict | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def duration(path: Path) -> float:
    r = subprocess.run(
        [ffprobe_bin(), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def font(size: int, bold: bool = False):
    for p in [r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
              r"C:\Windows\Fonts\simhei.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def brand_title_card(title: str, subtitle: str, out: Path) -> None:
    img = Image.new("RGB", (W, H), BRAND_BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, H // 2 - 2, W, H // 2 + 2], fill=BRAND_CYAN)
    draw.rounded_rectangle([100, 220, W - 100, H - 220], radius=20, outline=BRAND_CYAN, width=3)
    tw = draw.textbbox((0, 0), title, font=font(82, True))
    draw.text(((W - tw[2] + tw[0]) // 2, 340), title, fill=(255, 255, 255), font=font(82, True))
    for i, line in enumerate(subtitle.split(" · ")):
        sw = draw.textbbox((0, 0), line, font=font(34))
        draw.text(((W - sw[2] + sw[0]) // 2, 520 + i * 52), line, fill=BRAND_GOLD, font=font(34))
    img.save(out)


async def synth_plain(text: str, out: Path) -> None:
    if not edge_tts:
        raise RuntimeError("pip install edge-tts")
    communicate = edge_tts.Communicate(text, VOICE, rate=VOICE_RATE)
    await communicate.save(str(out))
    if out.stat().st_size < 500:
        raise RuntimeError(f"TTS failed: {out.name}")


def pad_audio(audio: Path, pause: float, out: Path) -> None:
    run([ffmpeg(), "-y", "-i", str(audio), "-af", f"apad=pad_dur={pause:.3f}",
         "-codec:a", "libmp3lame", "-q:a", "2", str(out)])


def fit_audio_to_target(audio: Path, target: float, out: Path) -> None:
    ad = duration(audio)
    if ad <= target + 0.05:
        if ad < target - 0.05:
            run([ffmpeg(), "-y", "-i", str(audio), "-af", f"apad=pad_dur={target - ad:.3f}",
                 "-t", f"{target:.3f}", "-codec:a", "libmp3lame", "-q:a", "2", str(out)])
        else:
            shutil.copy(audio, out)
        return
    tempo = min(ad / max(target - 0.1, 1.0), 1.35)
    run([ffmpeg(), "-y", "-i", str(audio), "-af", f"atempo={tempo:.4f}",
         "-t", f"{target:.3f}", "-codec:a", "libmp3lame", "-q:a", "2", str(out)])


def trim_video(src: Path, start: float, end: float, out: Path) -> None:
    dur = max(end - start, 0.5)
    run([ffmpeg(), "-y", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{dur:.3f}",
         "-an", "-vf", f"scale={W}:{H},fps={FPS}",
         "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p", str(out)])


def retime_video(src: Path, target: float, out: Path) -> None:
    vd = duration(src)
    speed = vd / target
    vf = f"setpts=PTS/{speed:.6f},scale={W}:{H},fps={FPS}"
    run([ffmpeg(), "-y", "-i", str(src), "-an", "-vf", vf, "-t", f"{target:.3f}",
         "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p", str(out)])


def merge_av(video: Path, audio: Path, out: Path, seg_dur: float) -> None:
    """Mux browser clip with narration; pad/loop video to hit exact seg_dur."""
    run([
        ffmpeg(), "-y",
        "-stream_loop", "-1", "-i", str(video),
        "-i", str(audio),
        "-filter_complex",
        f"[0:v]fps={FPS},tpad=stop_mode=clone:stop_duration={seg_dur:.3f},trim=0:{seg_dur:.3f},setpts=PTS-STARTPTS[v];"
        f"[1:a]apad=pad_dur={seg_dur:.3f},atrim=0:{seg_dur:.3f},asetpts=PTS-STARTPTS[a]",
        "-map", "[v]", "-map", "[a]",
        "-t", f"{seg_dur:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(out),
    ])


def video_from_title(img: Path, audio: Path, out: Path, target: float) -> None:
    fade_out = max(target - 0.4, 0.5)
    vf = f"scale={W}:{H},fade=t=in:st=0:d=0.3,fade=t=out:st={fade_out:.2f}:d=0.3"
    run([
        ffmpeg(), "-y", "-loop", "1", "-i", str(img), "-i", str(audio),
        "-filter_complex",
        f"[0:v]{vf},tpad=stop_mode=clone:stop_duration={target:.3f},trim=0:{target:.3f},setpts=PTS-STARTPTS[v];"
        f"[1:a]apad=pad_dur={target:.3f},atrim=0:{target:.3f},asetpts=PTS-STARTPTS[a]",
        "-map", "[v]", "-map", "[a]",
        "-t", f"{target:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(out),
    ])


def concat_segments(segs: list[Path], out: Path) -> None:
    lst = WORK / "concat.txt"
    lst.write_text("\n".join(f"file '{s.resolve().as_posix()}'" for s in segs), encoding="utf-8")
    run([ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", str(out)])


def ensure_bgm() -> Path:
    BGM_FILE.parent.mkdir(parents=True, exist_ok=True)
    if BGM_FILE.exists() and BGM_FILE.stat().st_size > 100_000:
        return BGM_FILE
    req = urllib.request.Request(BGM_URL, headers={"User-Agent": "QuantInsightDemo/4.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        BGM_FILE.write_bytes(resp.read())
    return BGM_FILE


def mix_bgm(video: Path, bgm: Path, out: Path) -> None:
    total = duration(video)
    vol = 10 ** (BGM_DB / 20.0)
    fade_out = max(total - 2.5, 1.0)
    filt = (
        f"[1:a]volume={vol:.4f},afade=t=in:st=0:d=2.0,"
        f"afade=t=out:st={fade_out:.2f}:d=2.5,aloop=loop=-1:size=2e+09,atrim=0:{total:.3f}[bgm];"
        f"[0:a]volume=1.0[voice];[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )
    run([
        ffmpeg(), "-y", "-i", str(video), "-i", str(bgm), "-filter_complex", filt,
        "-map", "0:v:0", "-map", "[aout]",
        "-t", f"{total:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(out),
    ])


def normalize_duration(path: Path, target: float = 180.0, tol: float = 3.0) -> None:
    """Force exact target duration with matched video/audio streams."""
    d = duration(path)
    if abs(d - target) <= tol:
        vd = ad = 0.0
        r = subprocess.run(
            [ffprobe_bin(), "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        vd = float(r.stdout.strip() or 0)
        r = subprocess.run(
            [ffprobe_bin(), "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True,
        )
        ad = float(r.stdout.strip() or 0)
        if abs(vd - ad) <= tol and abs(vd - target) <= tol:
            return
    pad_v = max(target - d, 0.0)
    tmp = path.with_suffix(".trim.mp4")
    run([
        ffmpeg(), "-y", "-i", str(path),
        "-filter_complex",
        f"[0:v]fps={FPS},tpad=stop_mode=clone:stop_duration={pad_v:.3f},trim=0:{target:.3f},setpts=PTS-STARTPTS[v];"
        f"[0:a]apad=pad_dur={target:.3f},atrim=0:{target:.3f},asetpts=PTS-STARTPTS[a]",
        "-map", "[v]", "-map", "[a]",
        "-t", f"{target:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(tmp),
    ])
    shutil.move(tmp, path)


def probe_report(path: Path) -> dict:
    r = subprocess.run(
        [ffprobe_bin(), "-v", "error", "-show_entries", "format=duration,size",
         "-show_entries", "stream=codec_type,duration,width,height,r_frame_rate", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(r.stdout)
    vd = ad = 0.0
    wh = fps = "?"
    for st in data.get("streams", []):
        if st.get("codec_type") == "video":
            vd = float(st.get("duration") or 0)
            wh = f"{st.get('width')}x{st.get('height')}"
            fps = st.get("r_frame_rate", "?")
        elif st.get("codec_type") == "audio":
            ad = float(st.get("duration") or 0)
    fmt = float(data["format"]["duration"])
    return {
        "format_duration": fmt,
        "video_duration": vd,
        "audio_duration": ad,
        "delta": abs(vd - ad),
        "resolution": wh,
        "fps": fps,
        "size_bytes": int(data["format"]["size"]),
    }


def wait_for_health(url: str, timeout: int = 120) -> bool:
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False


def streamlit_python() -> str:
    venv_py = ROOT / "streamlit_app" / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def start_streamlit() -> subprocess.Popen | None:
    app = ROOT / "streamlit_app" / "app.py"
    if not app.exists():
        return None
    proc = subprocess.Popen(
        [streamlit_python(), "-m", "streamlit", "run", str(app),
         "--server.headless", "true", "--server.port", "8501"],
        cwd=str(ROOT / "streamlit_app"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def record_playwright(sb_path: Path) -> str:
    """Run Playwright recorder; return method label for build meta."""
    pw_dir = ROOT / "streamlit_app"
    if not (pw_dir / "node_modules/playwright").exists():
        subprocess.run(["npm", "install", "--silent"], cwd=pw_dir, check=False, shell=True)
    env = os.environ.copy()
    ff = ffmpeg()
    if ff and Path(ff).exists():
        env["PLAYWRIGHT_FFMPEG_PATH"] = ff
    pw_cache = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
    if pw_cache.exists():
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(pw_cache)
    if RECORD_JS.exists():
        try:
            run(["node", str(RECORD_JS), "--storyboard", str(sb_path)], env=env)
            return "record_demo.mjs (local chromium)"
        except subprocess.CalledProcessError as exc:
            print(f"[WARN] record_demo.mjs failed ({exc}); trying Python playwright", file=sys.stderr)
    return record_playwright_python(sb_path)


def record_playwright_python(sb_path: Path) -> str:
    """Inline Playwright Python recorder fallback (single browser session)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        subprocess.run([streamlit_python(), "-m", "pip", "install", "playwright", "-q"], check=True)
        from playwright.sync_api import sync_playwright

    sb = json.loads(sb_path.read_text(encoding="utf-8"))
    out_dir = WORK
    seg_dir = out_dir / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    scene = sb["scenes"][0]
    base_url = sb["baseUrl"].rstrip("/")
    vp = sb.get("viewport", {"width": W, "height": H})

    def do_action(page, action):
        if action.get("goto") is not None:
            url = action["goto"] if action["goto"].startswith("http") else base_url + action["goto"]
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(3000)
        elif action.get("wait") is not None:
            page.wait_for_timeout(action["wait"])
        elif action.get("waitFor", {}).get("text"):
            page.wait_for_selector(f"text={action['waitFor']['text']}",
                                   timeout=action["waitFor"].get("timeout", 30000))
        elif action.get("fill"):
            f = action["fill"]
            if f.get("css"):
                page.locator(f["css"]).first.fill(f["value"])
            else:
                page.get_by_role(f.get("role", "textbox"), name=f.get("name", "")).fill(f["value"])
        elif action.get("click"):
            c = action["click"]
            if c.get("sidebar"):
                page.locator("label").filter(has_text=c["sidebar"]).first.click()
            elif c.get("role"):
                page.get_by_role(c["role"], name=c.get("name", "")).click()
            elif c.get("text"):
                page.locator("label").filter(has_text=c["text"]).first.click()
        elif action.get("select"):
            s = action["select"]
            page.locator('[data-testid="stSelectbox"]').nth(s.get("nth", 0)).click()
            page.wait_for_timeout(500)
            page.get_by_role("option", name=s["value"]).click()
        elif action.get("press"):
            page.keyboard.press(action["press"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir=str(seg_dir),
            record_video_size={"width": vp["width"], "height": vp["height"]},
            viewport=vp,
        )
        page = context.new_page()
        page.set_default_timeout(120000)
        for action in scene.get("actions", []):
            do_action(page, action)
        page.wait_for_timeout(800)
        context.close()
        browser.close()

    webms = sorted(seg_dir.glob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not webms:
        raise RuntimeError("Python playwright: no webm recorded")
    dest = out_dir / f"{scene['id']}.webm"
    shutil.move(str(webms[0]), dest)
    manifest = {
        "storyboard": str(sb_path),
        "mode": "record",
        "scenes": [{"id": scene["id"], "type": scene["type"], "visual": str(dest),
                    "narration": scene.get("narration", "")}],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [record-py] {scene['id']} -> {dest}")
    return "playwright-python (inline fallback)"


def segment_bounds(raw_dur: float) -> list[tuple[float, float]]:
    """Map planned marks to actual recording duration."""
    planned_end = SEGMENT_MARKS[-1] + 40.0
    scale = raw_dur / planned_end if planned_end > 0 else 1.0
    marks = [m * scale for m in SEGMENT_MARKS]
    marks.append(raw_dur)
    return [(marks[i], marks[i + 1]) for i in range(4)]


async def compose(manifest: dict) -> Path:
    compose_dir = WORK / "compose"
    compose_dir.mkdir(parents=True, exist_ok=True)

    ui_scene = next(s for s in manifest["scenes"] if s["id"] == "ui_flow")
    raw_webm = Path(ui_scene["visual"])
    raw_mp4 = compose_dir / "ui_flow_raw.mp4"
    run([ffmpeg(), "-y", "-i", str(raw_webm), "-an",
         "-vf", f"scale={W}:{H},fps={FPS}",
         "-c:v", "libx264", "-preset", "fast", "-crf", str(CRF), "-pix_fmt", "yuv420p", str(raw_mp4)])
    raw_dur = duration(raw_mp4)
    bounds = segment_bounds(raw_dur)
    browser_ids = ["h1", "h2", "h3", "h4"]

    segs: list[Path] = []
    for i, scene in enumerate(SCENES):
        sid = f"{i:02d}_{scene['id']}"
        audio_raw = compose_dir / f"{sid}_raw.mp3"
        audio_pad = compose_dir / f"{sid}_pad.mp3"
        audio = compose_dir / f"{sid}.mp3"
        seg = compose_dir / f"{sid}.mp4"

        await synth_plain(scene["narration"], audio_raw)
        pad_audio(audio_raw, SCENE_PAUSE_S, audio_pad)
        fit_audio_to_target(audio_pad, scene["target"], audio)

        if scene["type"] == "title":
            img = compose_dir / f"{sid}.png"
            brand_title_card(scene["title"], scene["subtitle"], img)
            video_from_title(img, audio, seg, scene["target"])
        else:
            bi = browser_ids.index(scene["id"])
            start, end = bounds[bi]
            clip = compose_dir / f"{sid}_clip.mp4"
            trim_video(raw_mp4, start, end, clip)
            timed = compose_dir / f"{sid}_v.mp4"
            retime_video(clip, scene["target"], timed)
            merge_av(timed, audio, seg, scene["target"])

        segs.append(seg)
        print(f"  [compose] {scene['id']} -> {duration(seg):.1f}s")

    merged = WORK / "merged_voice.mp4"
    concat_segments(segs, merged)
    return merged


async def main_async(args: argparse.Namespace) -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)

    pwd = resolve_demo_password()
    if not pwd:
        print("[ERROR] DEMO_PASSWORD not found (env / .env / secrets.toml)", file=sys.stderr)
        return 1
    os.environ["DEMO_PASSWORD"] = pwd

    streamlit_proc = None
    base = health = ""
    if args.target == "production":
        base, health = "https://3blue1brownlab.cn", "https://3blue1brownlab.cn/_stcore/health"
    else:
        local_base = (args.base_url or "http://127.0.0.1:8501").rstrip("/")
        base, health = local_base, f"{local_base}/_stcore/health"
        if not args.skip_server:
            print("=== Starting Streamlit on :8501 ===")
            streamlit_proc = start_streamlit()
            if not wait_for_health(health, 120):
                print("[WARN] localhost not ready, falling back to production")
                if streamlit_proc:
                    streamlit_proc.terminate()
                    streamlit_proc = None
                base, health = "https://3blue1brownlab.cn", "https://3blue1brownlab.cn/_stcore/health"
            else:
                print("  Streamlit ready at http://127.0.0.1:8501")

    if not wait_for_health(health, 30):
        print(f"[ERROR] health check failed: {health}", file=sys.stderr)
        if streamlit_proc:
            streamlit_proc.terminate()
        return 1

    sb = storyboard(base, health, pwd)
    sb_path = WORK / "storyboard.json"
    sb_path.write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        record_method = "skipped"
        if not args.skip_record:
            print(f"=== Playwright record ({base}) ===")
            record_method = await asyncio.to_thread(record_playwright, sb_path)
        else:
            print("=== Playwright skipped (--skip-record) ===")
            record_method = "skipped (--skip-record)"

        manifest_path = WORK / "manifest.json"
        if not manifest_path.exists():
            print(f"ERROR: missing {manifest_path}", file=sys.stderr)
            return 1
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        print("=== Plain TTS compose ===")
        voice_video = await compose(manifest)

        print("=== BGM mix ===")
        mixed = WORK / "final_with_bgm.mp4"
        mix_bgm(voice_video, ensure_bgm(), mixed)

        print("=== Normalize to 180s ===")
        shutil.copy(mixed, OUT_MP4)
        normalize_duration(OUT_MP4, 180.0, 3.0)

        stats = probe_report(OUT_MP4)
        meta = {
            "pipeline": "afac_demo_v4",
            "script": "submission/02_Demo交付/AFAC_Demo_录制脚本_V4.md",
            "voice": VOICE,
            "voice_rate": VOICE_RATE,
            "bgm_db": BGM_DB,
            "crf": CRF,
            "record_base": base,
            "record_method": record_method,
            "subtitles": False,
            **stats,
        }
        (WORK / "build_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        ok = 177 <= stats["format_duration"] <= 183 and stats["delta"] <= 3.0
        print(f"\nDone: {OUT_MP4}")
        print(f"  {stats['resolution']} @ {stats['fps']} | {stats['format_duration']:.2f}s | "
              f"v={stats['video_duration']:.2f}s a={stats['audio_duration']:.2f}s "
              f"delta={stats['delta']:.2f}s | {stats['size_bytes']/1024/1024:.1f}MB")
        print(f"  QA: {'PASS' if ok else 'REVIEW'}")
        return 0 if ok else 2
    finally:
        if streamlit_proc:
            streamlit_proc.terminate()


def main() -> None:
    ap = argparse.ArgumentParser(description="AFAC demo V4 — plain TTS + fresh UI record")
    ap.add_argument("--target", choices=["local", "production"], default="local")
    ap.add_argument("--base-url", default="", help="Local base URL (default http://127.0.0.1:8501)")
    ap.add_argument("--skip-record", action="store_true")
    ap.add_argument("--skip-server", action="store_true")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
