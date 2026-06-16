"""Push local git commit to GitHub via Git Data API (works around network reset)."""
import subprocess
import json
import base64
import os
import sys
import time

REPO = "yigenfeng0707-netizen/quantinsight-pro"
BRANCH = "main"

# Files to push (relative to repo root)
FILES = [
    "streamlit_app/app.py",
    "streamlit_app/features/report_generator.py",
    "streamlit_app/features/performance_utils.py",
    "streamlit_app/ui_themes.py",
]

def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def gh_get(path):
    """gh api GET path"""
    r = run(["gh", "api", path])
    if r.returncode != 0:
        print(f"  [gh api error] {path}: {r.stderr[:200]}")
        return None
    return json.loads(r.stdout) if r.stdout else {}

def gh_post(path, body):
    """gh api POST path with JSON body via --input"""
    tmp = "_gh_payload.json"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False)
    try:
        r = run(["gh", "api", "-X", "POST", path, "--input", tmp])
        if r.returncode != 0:
            print(f"  [gh api error] POST {path}: {r.stderr[:300]}")
            return None
        return json.loads(r.stdout) if r.stdout else {}
    finally:
        try: os.remove(tmp)
        except: pass

def gh_patch(path, body):
    """gh api PATCH path with JSON body via --input"""
    tmp = "_gh_payload.json"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False)
    try:
        r = run(["gh", "api", "-X", "PATCH", path, "--input", tmp])
        if r.returncode != 0:
            print(f"  [gh api error] PATCH {path}: {r.stderr[:300]}")
            return None
        return json.loads(r.stdout) if r.stdout else {}
    finally:
        try: os.remove(tmp)
        except: pass

# 1. Get parent SHA (HEAD of branch)
print(f"==> Getting parent SHA for {BRANCH}")
parent = gh_get(f"repos/{REPO}/git/ref/heads/{BRANCH}")
if not parent:
    print("Failed to get parent SHA")
    sys.exit(1)
parent_sha = parent["object"]["sha"]
print(f"  Parent SHA: {parent_sha[:12]}")

# 2. Get parent commit's tree
print("==> Getting parent tree")
parent_commit = gh_get(f"repos/{REPO}/git/commits/{parent_sha}")
base_tree_sha = parent_commit["tree"]["sha"]
print(f"  Base tree SHA: {base_tree_sha[:12]}")

# 3. For each file: read local content, base64 encode, create blob
print("==> Creating blobs for changed files")
blobs = []
for f in FILES:
    if not os.path.exists(f):
        print(f"  [skip] {f} (not found)")
        continue
    with open(f, "rb") as fp:
        content = fp.read()
    b64 = base64.b64encode(content).decode()
    body = {"content": b64, "encoding": "base64"}
    blob = gh_post(f"repos/{REPO}/git/blobs", body)
    if blob and "sha" in blob:
        blobs.append({"path": f, "sha": blob["sha"]})
        print(f"  [OK] {f} -> {blob['sha'][:12]} ({len(content)} bytes)")
    else:
        print(f"  [FAIL] {f}")
        sys.exit(1)

# 4. Create new tree based on parent tree
print("==> Creating new tree")
tree_body = {
    "base_tree": base_tree_sha,
    "tree": [{"path": b["path"], "sha": b["sha"], "mode": "100644"} for b in blobs]
}
new_tree = gh_post(f"repos/{REPO}/git/trees", tree_body)
if not new_tree:
    print("Failed to create tree")
    sys.exit(1)
new_tree_sha = new_tree["sha"]
print(f"  New tree SHA: {new_tree_sha[:12]}")

# 5. Create new commit
print("==> Creating new commit")
commit_msg = "V2.0 升级: UI对比度/菜单性能/报告生成/北向资金/Qwen3-Max primary"
commit_body = {
    "message": commit_msg,
    "tree": new_tree_sha,
    "parents": [parent_sha],
}
new_commit = gh_post(f"repos/{REPO}/git/commits", commit_body)
if not new_commit:
    print("Failed to create commit")
    sys.exit(1)
new_commit_sha = new_commit["sha"]
print(f"  New commit SHA: {new_commit_sha[:12]}")

# 6. Update ref
print(f"==> Updating ref refs/heads/{BRANCH}")
update = gh_patch(f"repos/{REPO}/git/refs/heads/{BRANCH}", {"sha": new_commit_sha})
if not update:
    print("Failed to update ref")
    sys.exit(1)
print(f"  [OK] {BRANCH} -> {new_commit_sha[:12]}")

# 7. Verify
print("==> Verifying")
time.sleep(2)
verify = gh_get(f"repos/{REPO}/commits?per_page=1")
if verify and len(verify) > 0:
    print(f"  Latest remote commit: {verify[0]['sha'][:12]}")
    if verify[0]["sha"] == new_commit_sha:
        print("  [OK] PUSH VERIFIED")
    else:
        print("  [WARN] Remote HEAD doesn't match")
print("\nAll done.")

