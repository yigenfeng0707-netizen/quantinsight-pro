# QuantInsight Demo 健康检查（F1）
# 每 30 分钟由计划任务 QIHealthCheck 调用一次；连续 N 次失败弹窗告警。
# 手动跑一次：powershell -NoProfile -ExecutionPolicy Bypass -File scripts\healthcheck_qi.ps1
param(
    [string]$Url = "http://121.196.102.54/_stcore/health",
    [int]$FailThreshold = 3,
    [int]$TimeoutSec = 15,
    [int]$PopupSeconds = 30
)

$ErrorActionPreference = "Continue"

$StateDir = Join-Path (Split-Path $PSScriptRoot -Parent) "_healthcheck"
if (-not (Test-Path $StateDir)) { New-Item -ItemType Directory -Force -Path $StateDir | Out-Null }

$LogFile   = Join-Path $StateDir "health.log"
$StateFile = Join-Path $StateDir "consecutive_failures.txt"
$AlertMark = Join-Path $StateDir "last_alert.txt"

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# 读取连续失败计数
$fails = 0
if (Test-Path $StateFile) {
    [void][int]::TryParse(((Get-Content $StateFile -Raw) -as [string]).Trim(), [ref]$fails)
}

# 探测
$ok = $false
$detail = ""
try {
    $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
    if ($r.StatusCode -eq 200 -and "$($r.Content)".Trim() -eq "ok") {
        $ok = $true
        $detail = "200 ok"
    } else {
        $detail = "HTTP $($r.StatusCode): $("$($r.Content)".Trim())"
    }
} catch {
    $detail = "ERR: $($_.Exception.Message)"
}

if ($ok) {
    $fails = 0
    Set-Content -Path $StateFile -Value "0" -Encoding ASCII
    Add-Content -Path $LogFile -Value "$ts OK $detail" -Encoding UTF8
} else {
    $fails++
    Set-Content -Path $StateFile -Value "$fails" -Encoding ASCII
    Add-Content -Path $LogFile -Value "$ts FAIL($fails) $detail" -Encoding UTF8

    if ($fails -ge $FailThreshold) {
        # 同一天只弹一次，避免每 30 分钟轰炸
        $today = $ts.Substring(0, 10)
        $lastAlert = ""
        if (Test-Path $AlertMark) { $lastAlert = ((Get-Content $AlertMark -Raw) -as [string]).Trim() }
        if ($lastAlert -ne $today) {
            $msg = "QuantInsight Demo 连续 $fails 次健康检查失败`n`n$Url`n$detail`n`n处理（见《部署速查》）：`n1) Workbench 登录服务器`n2) taskkill /F /IM python.exe`n3) schtasks /run /tn QuantInsight"
            try {
                (New-Object -ComObject WScript.Shell).Popup($msg, $PopupSeconds, "QuantInsight 告警", 48) | Out-Null
            } catch { }
            Set-Content -Path $AlertMark -Value $today -Encoding UTF8
        }
    }
}

# 日志轮转：超过 500KB 时保留一份 .1
if ((Test-Path $LogFile) -and ((Get-Item $LogFile).Length -gt 512000)) {
    Move-Item -Path $LogFile -Destination "$LogFile.1" -Force
}

# 只保留最近 2000 行
if (Test-Path $LogFile) {
    $lines = Get-Content $LogFile
    if ($lines.Count -gt 2000) {
        $lines | Select-Object -Last 2000 | Set-Content -Path $LogFile -Encoding UTF8
    }
}