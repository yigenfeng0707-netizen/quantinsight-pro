"""
AFAC2026 提交包 ZIP 打包（QuantInsight Pro · 当前工作区版）
输出: submission/QuantInsight_Pro_AFAC2026_提交包.zip
"""
from __future__ import annotations

import os
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "submission"
OUT = SUB / f"QuantInsight_Pro_AFAC2026_提交包_{datetime.now():%Y%m%d}.zip"

INCLUDE_DIRS = [
    SUB / "03_正式文档_WORD",
    SUB / "02_Demo交付" / "POC实验数据",
]

INCLUDE_FILES = [
    SUB / "README.md",
    SUB / "01_商业计划书_QuantInsight_Pro.md",
    SUB / "01_商业计划书_QuantInsight_Pro.html",
    SUB / "02_Demo交付" / "README_运行指南.md",
    SUB / "02_Demo交付" / "Demo视频制作脚本_3min.md",
    SUB / "02_Demo交付" / "交互设计与流程图.html",
    SUB / "02_Demo交付" / "逻辑流程图.md",
    SUB / "02_Demo交付" / "QuantInsight_Pro_Demo_3min.mp4",
]

STREAMLIT = ROOT / "streamlit_app"
SKIP_IN_STREAMLIT = {".venv", "__pycache__", ".pytest_cache", "node_modules", ".git"}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_IN_STREAMLIT:
        return True
    if path.suffix in {".pyc", ".log"}:
        return True
    return False


def add_path(zf: zipfile.ZipFile, src: Path, arc: str, stats: dict):
    if not src.exists():
        stats["missing"].append(str(src.relative_to(ROOT)))
        return
    if src.is_file():
        zf.write(src, arc)
        stats["count"] += 1
        stats["bytes"] += src.stat().st_size
        return
    for p in src.rglob("*"):
        if p.is_file() and not should_skip(p):
            rel = p.relative_to(src)
            zf.write(p, f"{arc}/{rel.as_posix()}")
            stats["count"] += 1
            stats["bytes"] += p.stat().st_size


def main():
    stats = {"count": 0, "bytes": 0, "missing": []}
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for f in INCLUDE_FILES:
            add_path(zf, f, f"submission/{f.relative_to(SUB).as_posix()}", stats)
        for d in INCLUDE_DIRS:
            add_path(zf, d, f"submission/{d.relative_to(SUB).as_posix()}", stats)
        add_path(zf, STREAMLIT, "streamlit_app", stats)

    size = OUT.stat().st_size
    print(f"ZIP: {OUT}")
    print(f"Files: {stats['count']} | Raw: {stats['bytes']:,} | ZIP: {size:,} ({size/1024/1024:.2f} MB)")
    if stats["missing"]:
        print("Missing (optional):")
        for m in stats["missing"]:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
