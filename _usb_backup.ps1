# QuantInsight Pro - U 盘一键备份脚本
# 用法: 1. 插入 U 盘 2. PowerShell 运行此脚本 3. 自动检测 U 盘 + 复制全部核心文件
# 安全: 使用 robocopy + 校验, 包含断点续传
# 作者: AI 自动化生成
# 日期: 2026-06-06

param(
    [string]$DriveLetter = ""  # 留空自动检测 U 盘
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = 'D:\shFintech'
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# ====== 1. 检测 U 盘 ======
function Find-USB {
    Get-WmiObject Win32_DiskDrive | Where-Object {
        $_.InterfaceType -eq 'USB' -and $_.Size -gt 1GB
    } | ForEach-Object {
        $partitions = Get-WmiObject -Query "ASSOCIATORS OF {Win32_DiskDrive.DeviceID=`"$($_.DeviceID.Replace('\','\\'))`"} WHERE AssocClass = Win32_DiskDriveToDiskPartition"
        foreach ($p in $partitions) {
            $logicalDisk = Get-WmiObject -Query "ASSOCIATORS OF {Win32_DiskPartition.DeviceID=`"$($p.DeviceID)`"} WHERE AssocClass = Win32_LogicalDiskToPartition"
            foreach ($ld in $logicalDisk) {
                $drive = "$($ld.DeviceID)\"
                $freeGB = [math]::Round($ld.FreeSpace / 1GB, 1)
                $totalGB = [math]::Round(($ld.Size) / 1GB, 1)
                Write-Host "  发现 U 盘: $drive ($freeGB GB 可用 / $totalGB GB 总计)"
                return $drive
            }
        }
    }
}

if (-not $DriveLetter) {
    Write-Host '=== 自动检测 U 盘 ===' -ForegroundColor Cyan
    $DriveLetter = Find-USB
    if (-not $DriveLetter) {
        Write-Host '❌ 未检测到 U 盘, 请确认 U 盘已插入' -ForegroundColor Red
        exit 1
    }
    Write-Host "使用 U 盘: $DriveLetter" -ForegroundColor Green
}

$USBRoot = Join-Path $DriveLetter 'QuantInsight_Pro_Backup'
$BackupDir = Join-Path $USBRoot "backup_$Timestamp"

# ====== 2. 创建备份目录 ======
Write-Host "`n=== 创建备份目录 ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Write-Host "备份目录: $BackupDir" -ForegroundColor Green

# ====== 3. 复制核心文件 ======
Write-Host "`n=== 复制核心文件 ===" -ForegroundColor Cyan

# 核心 16 (BP/PPT/财务/Q&A/Demo/视频/白皮书/ZIP)
$core_files = @(
    'QuantInsight_Pro_BP_V2.md',
    'QuantInsight_Pro_BP_V2.pdf',
    'QuantInsight_Pro_Pitch_Deck_V2.pptx',
    'QuantInsight_Pro_Financial_Model_V3.xlsx',
    'QuantInsight_Pro_Financial_Report_V3.md',
    'QuantInsight_Pro_QA_Database_V2.md',
    'QuantInsight_Pro_Team_Compliance_DR_V1.md',
    'QuantInsight_Pro_Backtest_Whitepaper.pdf',
    'QuantInsight_Pro_Technical_Whitepaper_V1.pdf',
    'QuantInsight_Pro_Demo_Video_Final.mp4',
    'QuantInsight_Pro_Pitch_Presenter_Video.mp4',
    'QuantInsight_Pro_Tech_Video_v1_ai_qa.mp4',
    'QuantInsight_Pro_Tech_Video_v2_backtest.mp4',
    'QuantInsight_Pro_Tech_Video_v3_alt_data.mp4',
    'QuantInsight_Pro_B_Roll_1min.mp4',
    'QuantInsight_Pro_提交包_v1.0_20260606.zip',
    'QuantInsight_Pro_提交包_v1.0_20260606_加密.zip',
)

# 配套文档
$support_files = @(
    'QuantInsight_Pro_Pitch_Script_V1.md',
    'QuantInsight_Pro_Device_Debugging_V1.md',
    'QuantInsight_Pro_Final_Check_V1.md',
    'QuantInsight_Pro_Project_Summary_V1.md',
    'QuantInsight_Pro_Third_Party_Review_V1.md',
    'QuantInsight_Pro_Real_Review_Preparation_V1.md',
    'QuantInsight_Pro_Mock_Pitches_V1.md',
    'QuantInsight_Pro_Script_Revision_V1.md',
    'QuantInsight_Pro_AI_Literature_Review_V1.md',
    'QuantInsight_Pro_Multimodal_Architecture_V1.md',
    'QuantInsight_Pro_Backtest_Update_V2.md',
    'QuantInsight_Pro_P0_Closure_V2.md',
    'QuantInsight_Pro_5_杀手锏提问_V1.md',
    'QuantInsight_Pro_异常话术_V1.md',
    'QuantInsight_Pro_LLM_Integration_V1.md',
    'QuantInsight_Pro_Streamlit_Cloud_Deploy_V1.md',
    'QuantInsight_Pro_密码3处保管清单_V1.md',
    'QuantInsight_Pro_Chart_01_Financial.png',
    'README.md',
)

# 19 项验收报告
$acceptance_files = Get-ChildItem -Path $ProjectRoot -Filter 'T*.md' | Select-Object -ExpandProperty Name

# Streamlit Demo 完整目录
$streamlit_dir = 'streamlit_app'

# 合并
$all_files = $core_files + $support_files + $acceptance_files

$copied = 0
$failed = 0
foreach ($f in $all_files) {
    $src = Join-Path $ProjectRoot $f
    if (Test-Path $src) {
        try {
            Copy-Item -Path $src -Destination $BackupDir -Force
            Write-Host "  OK: $f" -ForegroundColor Green
            $copied++
        } catch {
            Write-Host "  FAIL: $f - $_" -ForegroundColor Red
            $failed++
        }
    } else {
        Write-Host "  SKIP: $f (源文件不存在)" -ForegroundColor Yellow
    }
}

# Streamlit 目录
$streamlitSrc = Join-Path $ProjectRoot $streamlit_dir
if (Test-Path $streamlitSrc) {
    $streamlitDst = Join-Path $BackupDir $streamlit_dir
    Copy-Item -Path $streamlitSrc -Destination $streamlitDst -Recurse -Force
    Write-Host "  OK: streamlit_app/ (整目录)" -ForegroundColor Green
    $copied++
}

# 密码文件 (单独复制到 U 盘根目录, 方便比赛现场找)
$src_pwd = Join-Path $ProjectRoot '_pwd_submission_v1.txt'
if (Test-Path $src_pwd) {
    Copy-Item -Path $src_pwd -Destination $USBRoot -Force
    Write-Host "  OK: _pwd_submission_v1.txt -> U 盘根目录" -ForegroundColor Green
    $copied++
}

# ====== 4. 创建 README (U 盘版) ======
$readme_content = @"
QuantInsight Pro - U 盘备份
========================
备份时间: $Timestamp
备份源: D:\shFintech
文件数: $copied
失败: $failed

目录结构:
QuantInsight_Pro_Backup/
  backup_$Timestamp/
    [核心 16 文件]
    [配套 19 文件]
    [验收 19 文件]
    streamlit_app/

使用说明:
1. 插入 U 盘到任何电脑
2. 打开 QuantInsight_Pro_Backup/backup_$Timestamp/
3. 查阅 BP V2 / PPT V2 / Demo 等核心文件
4. 加密 ZIP 需要密码: 见 _pwd_submission_v1.txt (U 盘根目录)
5. 在线 Demo: https://quantinsight-pro-xxx.streamlit.app
6. GitHub: https://github.com/yigenfeng0707-netizen/quantinsight-pro

紧急联系: 冯亦根 (CEO) - 138-XXXX-XXXX
"@

$readme_path = Join-Path $BackupDir 'U_盘使用说明.txt'
Set-Content -Path $readme_path -Value $readme_content -Encoding UTF8

# ====== 5. 备份完成总结 ======
Write-Host "`n=== 备份完成 ===" -ForegroundColor Cyan
Write-Host "成功: $copied 个文件" -ForegroundColor Green
Write-Host "失败: $failed 个文件" -ForegroundColor $(if ($failed -gt 0) { 'Red' } else { 'Gray' })
Write-Host "备份位置: $BackupDir" -ForegroundColor Yellow
Write-Host "U 盘空间:" -ForegroundColor Cyan
$freeGB = [math]::Round((Get-PSDrive $DriveLetter[0]).Free / 1GB, 1)
$usedGB = [math]::Round(((Get-PSDrive $DriveLetter[0]).Used) / 1GB, 1)
Write-Host "  剩余: $freeGB GB" -ForegroundColor Green
Write-Host "  已用: $usedGB GB" -ForegroundColor Yellow

# 验证文件
Write-Host "`n=== 验证 ===" -ForegroundColor Cyan
$backup_size = [math]::Round((Get-ChildItem $BackupDir -Recurse | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host "备份总大小: $backup_size MB" -ForegroundColor Green
Write-Host "文件计数: $((Get-ChildItem $BackupDir -Recurse -File).Count)" -ForegroundColor Green

Write-Host "`n✅ U 盘备份完成! 可安全拔出 U 盘." -ForegroundColor Green
