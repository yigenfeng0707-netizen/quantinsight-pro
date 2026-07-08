#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QuantInsight Demo 视频后处理：生成 SRT 字幕并烧录至 MP4（与旁白同步）"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


def ffmpeg() -> str:
    return shutil.which("ffmpeg") or r"C:\ffmpeg\ffmpeg-6.1.1-essentials_build\bin\ffmpeg.exe"


def ffprobe() -> str:
    p = Path(ffmpeg()).parent / "ffprobe.exe"
    return str(p) if p.exists() else "ffprobe"


def duration(path: Path) -> float:
    r = subprocess.run(
        [ffprobe(), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def fmt_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap_text(text: str, width: int = 36) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    lines, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= width and ch in "，。！？、； ":
            lines.append(cur.strip())
            cur = ""
    if cur.strip():
        lines.append(cur.strip())
    return "\n".join(lines)


def build_srt(work_dir: Path, manifest: dict, scene_cfg: dict, out_srt: Path) -> None:
    entries = []
    t = 0.0
    idx = 1
    for i, scene in enumerate(manifest["scenes"]):
        seg = work_dir / f"{i:02d}_{scene['id']}.mp4"
        if not seg.exists():
            continue
        d = duration(seg)
        narration = (scene.get("narration") or scene_cfg.get(scene["id"], {}).get("narration") or "").strip()
        if narration:
            entries.append((idx, t, t + d, wrap_text(narration)))
            idx += 1
        t += d
    lines = []
    for n, start, end, text in entries:
        lines += [str(n), f"{fmt_ts(start)} --> {fmt_ts(end)}", text, ""]
    out_srt.write_text("\n".join(lines), encoding="utf-8")
    print(f"SRT: {out_srt} ({len(entries)} cues, total {t:.1f}s)")


def burn_subtitles(video: Path, srt: Path, out: Path) -> None:
    style = (
        "FontName=Microsoft YaHei,FontSize=28,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,"
        "Alignment=2,MarginV=48"
    )
    srt_esc = str(srt.resolve()).replace("\\", "/").replace(":", "\\:")
    vf = f"subtitles='{srt_esc}':force_style='{style}'"
    cmd = [
        ffmpeg(), "-y", "-i", str(video),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    print(f"Burned: {out} ({out.stat().st_size/1024/1024:.1f} MB, {duration(out):.1f}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--storyboard", "-s", required=True)
    args = ap.parse_args()
    sb_path = Path(args.storyboard).resolve()
    sb = json.loads(sb_path.read_text(encoding="utf-8"))
    out_dir = (sb_path.parent / sb.get("outputDir", "demo-output")).resolve()
    work = out_dir / "compose_work"
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scene_cfg = {s["id"]: s for s in sb.get("scenes", [])}

    merged = work / "merged.mp4"
    if not merged.exists():
        raise FileNotFoundError(f"缺少合成视频 {merged}，请先运行 compose_demo_video.py")

    srt_path = out_dir / "QuantInsight_Pro_Demo_3min.srt"
    build_srt(work, manifest, scene_cfg, srt_path)

    final_base = (sb_path.parent / sb.get("finalMp4", "demo-output/final.mp4")).resolve()
    final_sub = final_base.with_name(final_base.stem + "_字幕版.mp4")
    burn_subtitles(merged, srt_path, final_sub)
    shutil.copy(final_sub, final_base)
    shutil.copy(srt_path, final_base.with_suffix(".srt"))
    print(f"Final: {final_base}")


if __name__ == "__main__":
    main()
