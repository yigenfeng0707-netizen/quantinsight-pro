# 注册健康检查计划任务（F1）：每 30 分钟一次，当前用户、登录时运行（这样弹窗才看得见）
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File scripts\install_healthcheck_task.ps1
# 卸载：Unregister-ScheduledTask -TaskName QIHealthCheck -Confirm:$false
$ErrorActionPreference = "Stop"

$here   = $PSScriptRoot
$script = Join-Path $here "healthcheck_qi.ps1"
if (-not (Test-Path $script)) { throw "找不到 healthcheck_qi.ps1：$script" }

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`""

$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(2)) `
    -RepetitionInterval (New-TimeSpan -Minutes 30)

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName "QIHealthCheck" `
    -Action $action -Trigger $trigger -Settings $settings -Principal $principal `
    -Description "QuantInsight Demo 每 30 分钟健康检查；连续 3 次失败弹窗告警" -Force | Out-Null

Write-Host "已注册计划任务 QIHealthCheck（每 30 分钟，2 分钟后首跑）"
Get-ScheduledTask -TaskName "QIHealthCheck" | Select-Object TaskName, State | Format-Table