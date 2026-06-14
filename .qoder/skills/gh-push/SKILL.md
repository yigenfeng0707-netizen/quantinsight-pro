---
name: gh-push
description: Push local git commits to GitHub using gh CLI for authentication. Use when the user asks to push code, sync to GitHub, update the remote repository, or when git push fails with credential errors. Handles PowerShell encoding quirks automatically.
---

# GitHub Push via gh CLI

Push commits to GitHub reliably using `gh` CLI for HTTPS auth, with verification.

## Arguments

- **branch** (optional): Target branch name. Defaults to current branch.

## Workflow

### Step 1: Verify gh CLI auth

```powershell
gh auth status
```

Must show `Logged in to github.com`. If not authenticated, run `gh auth login` interactively.

### Step 2: Check unpushed commits

```powershell
$branch = git branch --show-current
git log --oneline "origin/$branch..HEAD"
```

If empty, nothing to push — tell the user.

### Step 3: Push

```powershell
$branch = git branch --show-current
git push origin $branch 2>&1
```

**PowerShell encoding note**: `git push` writes progress to stderr. PowerShell may display this as a `RemoteException` / `NativeCommandError` with garbled characters. This is **NOT a real error**. The actual result is in the output lines like:
- Success: `abc1234..def5678  main -> main`
- Already up to date: `Everything up-to-date`

Check the **text output**, not the exit code, to determine success.

### Step 4: Verify on GitHub

Confirm the remote HEAD matches local:

```powershell
$branch = git branch --show-current
$repo = gh repo view --json nameWithOwner --jq ".nameWithOwner"
$remote_sha = gh api "repos/$repo/commits?per_page=1" --jq ".[0].sha[0:7]"
$local_sha = git rev-parse --short HEAD
```

If `$remote_sha` equals `$local_sha[0:7]`, push is confirmed. Report the SHA to the user.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `gh: command not found` | gh CLI not installed | `winget install GitHub.cli` |
| `gh auth status` shows not logged in | Token expired | `gh auth login` |
| `Connection was reset` | Network/firewall issue | Retry; check proxy settings |
| `rejects non-fast-forward` | Remote has new commits | `git pull --rebase origin <branch>` first |
| PowerShell garbled stderr | Encoding mismatch | Ignore — check text output for `->` pattern |
