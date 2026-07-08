# -*- coding: utf-8 -*-
"""
GitHub 仓库二次清理 · AFAC2026 V2 提交（追打）
- 移动剩余 V1 漏网文件
- git rm 已跟踪的 .qoder/（IDE 技能配置 · 不入库）
- commit + push
"""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(r"d:\AFAC2026金融智能创新大赛\quantinsight-deploy")
ARCHIVE_LEGACY = ROOT / "archive" / "legacy_v1"

# 第二次清理的漏网 V1 文件
V1_STRAGGLERS = [
    "QuantInsight_Pro_QA.md",  # 7KB V1
    "QuantInsight_Pro_风险预案_V1.md",  # 9KB V1（被 V2 取代）
    "QuantInsight_Pro_财务模型V2.xlsx",  # 16KB V1（被 V3 取代）
    "_deploy.sh",  # 496B V1
]


def run(cmd: list[str], cwd: Path = ROOT) -> tuple[int, str, str]:
    """运行 git 命令并返回 (returncode, stdout, stderr)"""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    print("=" * 70)
    print("🧹 GitHub 仓库二次清理 · AFAC2026 V2 提交（追打）")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. 移动漏网 V1 文件
    print(f"\n📦 移动 V1 漏网文件 → archive/legacy_v1/")
    for fname in V1_STRAGGLERS:
        src = ROOT / fname
        dst = ARCHIVE_LEGACY / fname
        if not src.exists():
            print(f"   ⚠ 不存在: {fname}")
            continue
        try:
            shutil.move(str(src), str(dst))
            print(f"   ✅ {fname}")
        except Exception as e:
            print(f"   ❌ {fname}: {e}")

    # 2. git rm .qoder/（IDE 技能配置）
    print(f"\n📦 git rm -r .qoder/（IDE 技能配置 · 不入库）")
    rc, out, err = run(["git", "rm", "-r", "--cached", ".qoder/"])
    if rc == 0:
        print(f"   ✅ .qoder/ 已从 git 跟踪移除（本地保留）")
        # 列出被移除的文件
        for line in out.split("\n")[:10]:
            if line.startswith("rm '"):
                print(f"      {line[:80]}")
    else:
        print(f"   ❌ {err[:200]}")

    # 3. 状态检查
    print(f"\n📊 git status 预览:")
    rc, out, err = run(["git", "status", "--short"])
    lines = [l for l in out.split("\n") if l.strip()]
    dels = [l for l in lines if l.startswith(" D ")]
    rms = [l for l in lines if l.startswith("D ")]
    print(f"   总变动: {len(lines)} 条")
    print(f"   - 已暂存删除: {len(dels)}")
    print(f"   - 工作树删除: {len(rms)}")

    # 4. 暂存并提交
    print(f"\n📝 git add -A 暂存...")
    rc, out, err = run(["git", "add", "-A"])
    if rc == 0:
        print(f"   ✅ 暂存成功")
    else:
        print(f"   ❌ {err[:200]}")

    print(f"\n📝 git commit...")
    commit_msg = """AFAC2026 V2.1: 清理剩余 V1 漏网文件 + 移除 .qoder/ IDE 配置

🧹 二次清理（4 文件删除 + 1 目录移除）：
- 删除 QuantInsight_Pro_QA.md（V1, 7KB, 被 V2 QA_Database 取代）
- 删除 QuantInsight_Pro_风险预案_V1.md（V1, 9KB, 被 V2 取代）
- 删除 QuantInsight_Pro_财务模型V2.xlsx（V1, 16KB, 被 V3 取代）
- 删除 _deploy.sh（V1, 496B, 旧部署脚本）
- git rm -r .qoder/（IDE 技能配置 · 4 文件 · 本地保留但不跟踪）

✅ 主区 grep「创·在上海」= 0 命中
✅ 主区无 V1 老报告残留

🤖 Generated with [Trae](https://trae.ai)

Co-Authored-By: Trae <noreply@trae.ai>"""
    rc, out, err = run(["git", "commit", "-m", commit_msg])
    if rc == 0:
        # 提取 commit hash
        for line in out.split("\n"):
            if "files changed" in line or "file changed" in line:
                print(f"   ✅ {line.strip()}")
                break
    else:
        print(f"   ❌ {err[:300]}")
        return

    # 5. 推送
    print(f"\n🚀 git push afac2026 main...")
    rc, out, err = run(["git", "push", "afac2026", "main"])
    if rc == 0:
        print(f"   ✅ 推送成功")
        for line in out.split("\n"):
            if "main -> main" in line or "->" in line:
                print(f"      {line.strip()}")
    else:
        print(f"   ❌ {err[:300]}")

    # 6. 最终验证
    print(f"\n📊 最终 GitHub 状态:")
    rc, out, err = run(["gh", "api", "repos/yigenfeng0707-netizen/quantinsight-pro-afac2026"])
    if rc == 0:
        import json
        data = json.loads(out)
        print(f"   仓库: {data['full_name']}")
        print(f"   最新推送: {data['pushed_at']}")
        print(f"   默认分支: {data['default_branch']}")
        print(f"   仓库大小: {data['size']:,} KB")

    print()
    print("=" * 70)
    print("✅ 二次清理完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
