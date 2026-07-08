# -*- coding: utf-8 -*-
"""Batch convert 5 答辩 / 风险 / Q&A markdown files to rich Word DOCX.

All outputs go to ``submission/03_正式文档_WORD/`` and use the
``md_to_docx_rich.convert_markdown_file`` entry point so that the resulting
documents contain native Word formatting (headings, bold/italic runs, lists,
multi-column tables, block quotes) with no leftover markdown characters
(``#`` / ``**`` / ``|` `` etc.).
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from md_to_docx_rich import convert_markdown_file  # noqa: E402

OUT_DIR = ROOT / "submission" / "03_正式文档_WORD"
META = "AFAC2026 · 初创组 · 2026-07-08"

# (source_md, output_docx, doc_title, subtitle)
JOBS = [
    (
        ROOT / "QuantInsight_Pro_答辩话术_V3.md",
        OUT_DIR / "09_答辩话术_V3.docx",
        "QuantInsight Pro 答辩话术 V3",
        "AFAC2026 金融智能创新大赛 · 5分钟答辩",
    ),
    (
        ROOT / "QuantInsight_Pro_3轮模拟答辩脚本_V1.md",
        OUT_DIR / "10_3轮模拟答辩_V1.docx",
        "QuantInsight Pro 3轮模拟答辩脚本 V1",
        "AFAC2026 · 模拟答辩实战剧本",
    ),
    (
        ROOT / "QuantInsight_Pro_风险预案_V2.md",
        OUT_DIR / "11_风险预案_V2.docx",
        "QuantInsight Pro 风险预案 V2",
        "AFAC2026 · 路演风险与应急响应",
    ),
    (
        ROOT / "QuantInsight_Pro_5_杀手锏提问_V1.md",
        OUT_DIR / "12_5杀手锏提问_V1.docx",
        "QuantInsight Pro 5个杀手锏提问 V1",
        "AFAC2026 · 评委高难度提问拆解",
    ),
    (
        ROOT / "QuantInsight_Pro_QA_Database_V2.md",
        OUT_DIR / "13_QA_Database_V2.docx",
        "QuantInsight Pro Q&A Database V2",
        "AFAC2026 · 完整问答库",
    ),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    for md_path, out_path, title, subtitle in JOBS:
        record: dict = {"title": title, "out": out_path, "ok": False}
        if not md_path.exists():
            print(f"[SKIP] source missing: {md_path}")
            results.append(record)
            continue
        try:
            convert_markdown_file(
                md_path,
                out_path,
                doc_title=title,
                subtitle=subtitle,
                meta=META,
            )
            record["ok"] = True
            print(f"[OK]   {title}  ->  {out_path}")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[FAIL] {title}: {exc}")
            traceback.print_exc()
        results.append(record)

    failed = [r for r in results if not r["ok"]]
    print(f"\n=== Done · {len(results) - len(failed)}/{len(results)} succeeded ===")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
