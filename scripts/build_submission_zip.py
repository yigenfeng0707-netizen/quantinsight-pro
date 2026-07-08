"""
AFAC2026 提交包 ZIP 打包 V2 (QuantInsight Pro)
- 2026-07-08 V2 输出: submission/QuantInsight_Pro_AFAC2026_提交包_20260708_V2.zip
- 新增 V2 物料: 5 份答辩 Word、7 张 _assets/PNG、5min PPT、V3 PPT、3 份 P2 物料、录制脚本
- INCLUDE_DIRS 保持 03_正式文档_WORD + 02_Demo交付/POC实验数据
- 排除 .venv / __pycache__ / node_modules / .git / .pyc / .log
- ZIP 大小 ≤ 50MB
- stats: 文件数 / 原始 bytes / ZIP bytes
"""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUB = ROOT / "submission"
OUT = SUB / "QuantInsight_Pro_AFAC2026_提交包_20260708_V2.zip"
MAX_ZIP_BYTES = 50 * 1024 * 1024  # 50 MB

# ---- 目录: 03_正式文档_WORD（含 5 份答辩 Word + 7 张 _assets/PNG）+ POC实验数据 + delivery/ ----
INCLUDE_DIRS = [
    SUB / "03_正式文档_WORD",
    SUB / "02_Demo交付" / "POC实验数据",
    ROOT / "delivery",  # V2.1: 统一交付目录（手动上传用）
]

# ---- 单文件: V2 新增物料（与 INCLUDE_DIRS 重叠的会经去重跳过） ----
INCLUDE_FILES = [
    # 基础 README 与归档
    SUB / "README.md",
    SUB / "00_项目README_QuantInsight_Pro.docx",
    SUB / "00_项目README_QuantInsight_Pro.html",
    SUB / "06_文档归档说明.md",
    SUB / "05_团队信息一致性核查报告.md",
    SUB / "07_AFAC2026_自评打分报告.md",
    SUB / "07_AFAC2026_自评打分报告.docx",
    SUB / "01_商业计划书_QuantInsight_Pro.md",
    SUB / "01_商业计划书_QuantInsight_Pro.html",
    # 02_Demo交付
    SUB / "02_Demo交付" / "README_运行指南.md",
    SUB / "02_Demo交付" / "AFAC_Demo_录制脚本_V4.md",  # V2 新物料: 录制脚本
    SUB / "02_Demo交付" / "VIDEO_STATUS.md",
    SUB / "02_Demo交付" / "交互设计与流程图.html",
    SUB / "02_Demo交付" / "逻辑流程图.md",
    SUB / "02_Demo交付" / "QuantInsight_Pro_Demo_3min.mp4",
    # V2 新物料: 5min 路演 PPT (ROOT 级, 放 submission/ 根)
    ROOT / "QuantInsight_Pro_Pitch_Deck_5min_V1.pptx",
    # V2 新物料: V3 PPT (ROOT 级, 放 submission/ 根)
    ROOT / "QuantInsight_Pro_Pitch_Deck_V3.pptx",
    # V2 新物料: 3 份 P2 (05_锦上添花)
    SUB / "05_锦上添花" / "A1_海报_AFAC2026.png",
    SUB / "05_锦上添花" / "易拉宝_AFAC2026.png",
    SUB / "05_锦上添花" / "永字资管背书牌_V1.docx",
    # V2 新物料: 5 份答辩 Word (与 03_正式文档_WORD 目录重叠, 走去重)
    SUB / "03_正式文档_WORD" / "09_答辩话术_V3.docx",
    SUB / "03_正式文档_WORD" / "10_3轮模拟答辩_V1.docx",
    SUB / "03_正式文档_WORD" / "11_风险预案_V2.docx",
    SUB / "03_正式文档_WORD" / "12_5杀手锏提问_V1.docx",
    SUB / "03_正式文档_WORD" / "13_QA_Database_V2.docx",
    # V2 新物料: 7 张 _assets/PNG (与 03_正式文档_WORD 目录重叠, 走去重)
    SUB / "03_正式文档_WORD" / "_assets" / "01_business_model_canvas.png",
    SUB / "03_正式文档_WORD" / "_assets" / "02_ltv_cac_radar.png",
    SUB / "03_正式文档_WORD" / "_assets" / "03_nrr_funnel.png",
    SUB / "03_正式文档_WORD" / "_assets" / "04_backtest_curve.png",
    SUB / "03_正式文档_WORD" / "_assets" / "05_client_growth.png",
    SUB / "03_正式文档_WORD" / "_assets" / "06_customer_subscription_matrix.png",
    SUB / "03_正式文档_WORD" / "_assets" / "07_team_structure.png",
]

STREAMLIT = ROOT / "streamlit_app"
SKIP_IN_STREAMLIT = {".venv", "__pycache__", ".pytest_cache", "node_modules", ".git"}
SKIP_SUFFIX = {".pyc", ".log"}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_IN_STREAMLIT:
        return True
    if path.suffix in SKIP_SUFFIX:
        return True
    return False


def arcname_for_sub_file(src: Path) -> str:
    """SUB 内单文件 → submission/<rel>/<filename>"""
    rel = src.relative_to(SUB)
    return f"submission/{rel.as_posix()}"


def arcname_for_root_file(src: Path) -> str:
    """ROOT 内单文件 (不在 SUB) → submission/<filename>"""
    return f"submission/{src.name}"


def add_file(zf: zipfile.ZipFile, src: Path, arc: str, stats: dict, seen: set):
    if not src.exists():
        stats["missing"].append(str(src.relative_to(ROOT)))
        return
    if not src.is_file():
        stats["missing"].append(f"NOT_A_FILE: {src.relative_to(ROOT)}")
        return
    if arc in seen:
        stats["dup"] += 1
        return
    seen.add(arc)
    zf.write(src, arc)
    stats["count"] += 1
    stats["bytes"] += src.stat().st_size


def add_dir(zf: zipfile.ZipFile, src: Path, arc_prefix: str, stats: dict, seen: set):
    if not src.exists():
        stats["missing"].append(str(src.relative_to(ROOT)))
        return
    for p in src.rglob("*"):
        if p.is_file() and not should_skip(p):
            rel = p.relative_to(src)
            arc = f"{arc_prefix}/{rel.as_posix()}"
            if arc in seen:
                stats["dup"] += 1
                continue
            seen.add(arc)
            zf.write(p, arc)
            stats["count"] += 1
            stats["bytes"] += p.stat().st_size


def main():
    stats = {"count": 0, "bytes": 0, "missing": [], "dup": 0}
    seen: set[str] = set()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # 1) INCLUDE_FILES 单文件
        for f in INCLUDE_FILES:
            if f.is_relative_to(SUB):
                add_file(zf, f, arcname_for_sub_file(f), stats, seen)
            else:
                add_file(zf, f, arcname_for_root_file(f), stats, seen)

        # 2) INCLUDE_DIRS 目录
        for d in INCLUDE_DIRS:
            if d.is_relative_to(SUB):
                arc = f"submission/{d.relative_to(SUB).as_posix()}"
            else:
                # ROOT 级目录（如 delivery/）→ 直接放 ROOT 名下
                arc = d.relative_to(ROOT).as_posix()
            add_dir(zf, d, arc, stats, seen)

        # 3) streamlit_app 整目录
        add_dir(zf, STREAMLIT, "streamlit_app", stats, seen)

    size = OUT.stat().st_size
    over_limit = size > MAX_ZIP_BYTES
    print(f"ZIP: {OUT}")
    print(f"Files: {stats['count']} | Raw: {stats['bytes']:,} bytes "
          f"({stats['bytes']/1024/1024:.2f} MB) | "
          f"ZIP: {size:,} bytes ({size/1024/1024:.2f} MB)")
    print(f"Duplicates skipped: {stats['dup']} | Missing: {len(stats['missing'])}")
    if over_limit:
        print(f"WARNING: ZIP > 50MB ({size/1024/1024:.2f} MB > 50 MB)")
    if stats["missing"]:
        print("Missing (optional):")
        for m in stats["missing"]:
            print(f"  - {m}")


if __name__ == "__main__":
    main()
