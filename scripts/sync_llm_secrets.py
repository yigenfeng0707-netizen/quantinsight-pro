#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 D:\\自定义大模型配置.txt 生成 Streamlit secrets.toml"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DEFAULT_CONFIG = Path(r"D:\自定义大模型配置.txt")
OUT_PATHS = [
    Path(__file__).resolve().parents[1] / "streamlit_app" / ".streamlit" / "secrets.toml",
    Path(__file__).resolve().parents[1] / "deploy" / "secrets.toml.local",
]


def _norm_chat_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1") or url.endswith("/compatible-mode/v1"):
        return url + "/chat/completions"
    return url


def parse_config(text: str) -> dict[str, str]:
    """解析 primary / fallback1 / fallback2 块"""
    data: dict[str, str] = {}

    # primary QWEN (Token Plan)
    m = re.search(r"API Key:\s*(\S+)", text)
    if m:
        data["QWEN_API_KEY"] = m.group(1).strip()
    m = re.search(
        r"https://token-plan[^\s)]+",
        text,
    )
    if m:
        data["QWEN_BASE_URL"] = _norm_chat_url(m.group(0))
    data.setdefault("QWEN_MODEL", "qwen3.6-plus")

    # fallback1 SenseNova
    fb1 = re.search(r"fallback1：([\s\S]*?)(?=fallback2：|$)", text)
    if fb1:
        block = fb1.group(1)
        m = re.search(r"ApiKey:\s*(\S+)", block, re.I)
        if m:
            data["SENSENOVA_API_KEY"] = m.group(1).strip()
        m = re.search(r"Baseurl:\s*(\S+)", block, re.I)
        if m:
            data["SENSENOVA_BASE_URL"] = _norm_chat_url(m.group(1))
        m = re.search(r"modelid:\s*(\S+)", block, re.I)
        if m:
            data["SENSENOVA_MODEL"] = m.group(1).strip()

    # fallback2 StepFun
    fb2 = re.search(r"fallback2：([\s\S]*)", text)
    if fb2:
        block = fb2.group(1)
        m = re.search(r"APIkey[：:]\s*(\S+)", block, re.I)
        if m:
            data["STEPFUN_API_KEY"] = m.group(1).strip()
        m = re.search(r"BaseUrl[：:]\s*(\S+)", block, re.I)
        if m:
            data["STEPFUN_BASE_URL"] = _norm_chat_url(m.group(1))
        m = re.search(r"Modelid[：:]\s*(\S+)", block, re.I)
        if m:
            data["STEPFUN_MODEL"] = m.group(1).strip()

    required = ["QWEN_API_KEY", "SENSENOVA_API_KEY", "STEPFUN_API_KEY"]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"配置不完整，缺少: {missing}")
    return data


def to_toml(data: dict[str, str]) -> str:
    lines = [
        "# Auto-generated from 自定义大模型配置.txt — do not commit",
        "# Priority: QWEN (Token Plan) > SenseNova > StepFun",
        "",
    ]
    order = [
        "QWEN_API_KEY", "QWEN_MODEL", "QWEN_BASE_URL",
        "SENSENOVA_API_KEY", "SENSENOVA_MODEL", "SENSENOVA_BASE_URL",
        "STEPFUN_API_KEY", "STEPFUN_MODEL", "STEPFUN_BASE_URL",
    ]
    for key in order:
        if key in data:
            lines.append(f'{key} = "{data[key]}"')
    lines.append("")
    return "\n".join(lines)


def main():
    cfg_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CONFIG
    if not cfg_path.exists():
        print(f"配置文件不存在: {cfg_path}", file=sys.stderr)
        sys.exit(1)
    data = parse_config(cfg_path.read_text(encoding="utf-8"))
    content = to_toml(data)
    for out in OUT_PATHS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"OK {out}")
    print("\nProviders:")
    print(f"  1. QWEN / {data.get('QWEN_MODEL')}")
    print(f"  2. SENSENOVA / {data.get('SENSENOVA_MODEL')}")
    print(f"  3. STEPFUN / {data.get('STEPFUN_MODEL')}")


if __name__ == "__main__":
    main()
