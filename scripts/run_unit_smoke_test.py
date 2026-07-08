#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QuantInsight Pro 全量测试：单元测试 + 模块导入 + 生产健康检查"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
import urllib.request
import ssl
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "streamlit_app"
OUT = ROOT / "submission" / "04_测试报告"
OUT.mkdir(parents=True, exist_ok=True)

MODULES = [
    "backtest_engine",
    "data_cache",
    "eastmoney_source",
    "ui_themes",
    "features.stock_screener",
    "features.shap_explainer",
    "features.report_generator",
    "features.multi_source_data",
    "features.trade_simulator",
    "features.sqlite_data_layer",
    "features.dashboard_v2",
    "features.qlib_integration",
    "ai.rag_engine",
    "auth.database",
    "admin.bootstrap_admin",
]


def run_pytest() -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "test_backtest_engine.py", "test_data_pipeline.py", "-q", "--tb=no"],
        cwd=APP,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {"status": "PASS" if r.returncode == 0 else "FAIL", "output": r.stdout + r.stderr}


def import_smoke() -> list:
    sys.path.insert(0, str(APP))
    results = []
    for mod in MODULES:
        try:
            importlib.import_module(mod)
            results.append({"module": mod, "status": "PASS"})
        except Exception as e:
            results.append({"module": mod, "status": "FAIL", "error": str(e)[:200]})
    return results


def health_check(url: str) -> dict:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kw = {"timeout": 20}
        if url.startswith("https"):
            kw["context"] = ctx
        r = urllib.request.urlopen(url, **kw)
        body = r.read(200).decode("utf-8", "replace")
        return {"url": url, "status": "PASS" if r.status == 200 else "FAIL", "body": body}
    except Exception as e:
        return {"url": url, "status": "FAIL", "error": str(e)}


def main():
    report = {
        "timestamp": datetime.now().isoformat(),
        "pytest": run_pytest(),
        "imports": import_smoke(),
        "health": [
            health_check("https://3blue1brownlab.cn/_stcore/health"),
            health_check("http://47.76.46.88/_stcore/health"),
        ],
    }
    imp_fail = [x for x in report["imports"] if x["status"] == "FAIL"]
    report["summary"] = {
        "pytest": report["pytest"]["status"],
        "imports_pass": len(report["imports"]) - len(imp_fail),
        "imports_fail": len(imp_fail),
        "health_pass": sum(1 for h in report["health"] if h["status"] == "PASS"),
    }
    out = OUT / "unit_and_smoke_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    if report["pytest"]["status"] != "PASS" or imp_fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
