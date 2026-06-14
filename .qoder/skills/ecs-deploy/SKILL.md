---
name: ecs-deploy
description: Deploy code to Alibaba Cloud ECS via Cloud Assistant API. Supports full deploy (tar.gz + base64 chunked transfer), single-file hotfix, secrets update, and status check. Use when the user asks to deploy to ECS, update the server, push to production, check server status, or restart the Streamlit service.
---

# ECS Deploy via Cloud Assistant

Deploy code to Alibaba Cloud ECS without SSH — uses Cloud Assistant `RunCommand` API with v3 signature (ACS3-HMAC-SHA256).

## Server Context

- **Instance**: `i-bp1g3jpaz9v1xczizza8` in `cn-hangzhou`
- **Deploy path**: `/opt/quantinsight/` (flat structure, no git, no subdirectory)
- **Venv**: `/opt/quantinsight/venv/`
- **DB**: `/opt/quantinsight/data/users.db`
- **Service**: `quantinsight` (systemd, Streamlit with TLS on port 8443)
- **Secrets**: `/opt/quantinsight/.streamlit/secrets.toml`
- **Local source**: `d:\shFintech\streamlit_app\`

## Credentials

Stored in deploy scripts. RAM user `power-application-user`:
- AK_ID: `LTAI5t6UPpyN8gJ1znY2G88s`
- Region: `cn-hangzhou`, Endpoint: `ecs.cn-hangzhou.aliyuncs.com`

## Operations

### 1. Full Deploy (multi-file)

Use when multiple files changed (app.py + ui_themes.py + etc).

**Workflow**:
1. Create `tar.gz` of changed files from `streamlit_app/`
2. Base64-encode the archive
3. Split into 15KB chunks (Cloud Assistant ~18KB command limit)
4. Upload each chunk via `echo -n "..." >> /tmp/deploy_b64.txt`
5. On server: base64-decode → extract → backup originals → copy → restart

Run: `python d:\shFintech\_ecs_deploy_files.py`

**File list** is defined in `FILES_TO_TRANSFER` at the top of the script. Update it when adding new files.

### 2. Single-File Hotfix

Use for quick fixes to one file (typically `app.py`).

**Workflow**:
1. Read local file → base64 encode → split into 15KB chunks
2. Upload chunks → decode on server → backup → replace → restart

Run: `python d:\shFintech\_ecs_hotfix.py`

Edit the `app_path` variable at line 73 to target a different file.

### 3. Secrets Update

Use to add/modify `secrets.toml` entries (API keys, model configs).

Run: `python d:\shFintech\_ecs_update_secrets.py`

The script: backs up secrets → checks for existing keys → merges new entries → restarts service.

### 4. Status Check / Remote Command

Run any shell command on the server:

```python
# Inline in a deploy script or standalone:
run_command("systemctl is-active quantinsight")
run_command("curl -sk -o /dev/null -w '%{http_code}' https://localhost:8443/")
run_command("journalctl -u quantinsight --no-pager -n 20")
```

## API v3 Signature Reference

All API calls use **ACS3-HMAC-SHA256**:

```
CanonicalRequest = POST + / + sorted_query + sorted_headers + signed_headers + SHA256(empty_body)
StringToSign = "ACS3-HMAC-SHA256\n" + SHA256(CanonicalRequest)
Signature = HMAC-SHA256(AK_SECRET, StringToSign)
Authorization = "ACS3-HMAC-SHA256 Credential={AK_ID},SignedHeaders={...},Signature={sig}"
```

Required headers: `host`, `x-acs-action`, `x-acs-version` (2014-05-26), `x-acs-date`, `x-acs-signature-nonce`, `x-acs-content-sha256`, `x-acs-credentials-provider` (static_ak).

## Key API Actions

| Action | Purpose |
|--------|---------|
| `DescribeInstances` | Get instance status, IP |
| `RunCommand` | Execute shell script on instance |
| `DescribeInvocations` | Poll command status + get output |

## Verification Checklist

After every deploy, confirm:
1. **Syntax valid**: `python -c "import py_compile; py_compile.compile('/opt/quantinsight/app.py')"`
2. **Service active**: `systemctl is-active quantinsight` → `active`
3. **HTTP 200**: `curl -sk -o /dev/null -w '%{http_code}' https://localhost:8443/`
4. **File sizes match**: compare local vs server byte counts

## PowerShell Note

Set `$env:PYTHONIOENCODING="utf-8"` before running deploy scripts to avoid GBK encoding errors with Unicode output (checkmarks, etc.).

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `IncompleteSignature` | Wrong AK secret or clock skew | Verify credentials; sync system time |
| `InstanceNotFound` | Wrong instance ID or region | Check `INSTANCE_ID` and `REGION` |
| Command timeout (>5min) | Long-running script | Increase `timeout_secs` param |
| `CloudAssistantNotInstalled` | Agent not running on instance | `systemctl start aliyun` on instance |
| GBK encode error | PowerShell locale | `$env:PYTHONIOENCODING="utf-8"` |
