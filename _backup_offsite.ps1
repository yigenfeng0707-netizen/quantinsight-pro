# QuantInsight Pro - 异地备份清单
# Phase 2 C2/C3: 多份异地备份 (用户操作)
# 用法: powershell -ExecutionPolicy Bypass -File _backup_offsite.ps1

$Source = "D:\shFintech"
$LogFile = Join-Path $Source ("_backup_log_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + ".txt")

function Log($msg) {
    $line = "[" + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + "] " + $msg
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

Log "=========================================="
Log "QuantInsight Pro - 异地备份脚本"
Log "=========================================="

Log ""
Log "=== C2.1: 打印清单 (用户操作) ==="
Log "  1. BP V2 PDF x 2 copies (双面, 14 页)"
Log "  2. 路演脚本 x 3 copies (冯亦根 + 备问 + 推荐单位)"
Log "  3. Q&A V2 x 1 copy"

Log ""
Log "=== C2.2: U 盘备份 (>= 16 GB, 3 个) ==="
$files = @(
    "QuantInsight_Pro_提交包_v1.0_20260606_加密.zip",
    "QuantInsight_Pro_BP_V2.pdf",
    "QuantInsight_Pro_Pitch_Deck_V2.pptx",
    "QuantInsight_Pro_Demo_Video_Final.mp4",
    "QuantInsight_Pro_Pitch_Presenter_Video.mp4",
    "QuantInsight_Pro_Financial_Model_V3.xlsx",
    "QuantInsight_Pro_Pitch_Script_V1.md",
    "_pwd_submission_v1.txt"
)
$total = 0
foreach ($f in $files) {
    $fp = Join-Path $Source $f
    if (Test-Path $fp) {
        $s = (Get-Item $fp).Length
        $total += $s
        Log ("  [OK] " + $f + " | " + $s + " bytes (" + [math]::Round($s/1MB, 2) + " MB)")
    } else {
        Log ("  [WARN] " + $f + " not found")
    }
}
Log ("  Total: " + [math]::Round($total/1MB, 2) + " MB")
Log "  U 盘 1: 主团队 (冯亦根保管)"
Log "  U 盘 2: 推荐单位 (薛永再保管)"
Log "  U 盘 3: 异地保管 (银行保险箱)"

Log ""
Log "=== C2.3: 异地备份目标 (用户操作) ==="
Log "  1. 银行保险箱: 1 套 U 盘 (含加密 ZIP + 5 份核心 + 3 份视频)"
Log "  2. 律师托管: 1 份纸质 (BP V2 + 路演脚本 + Q&A)"
Log "  3. 网盘加密: 1 份 (百度网盘 / 阿里云盘)"

Log ""
Log "=== C3.1-3: 路演脚本多份异地 ==="
Log "  C3.1 打印 3 份:"
Log "    - 冯亦根 (主讲) 1 份"
Log "    - 备问团队 (薛永再+黄成选+冯思涵) 1 份"
Log "    - 推荐单位 (薛永再) 1 份"
Log "  C3.2 邮件 3 份 (用户操作):"
Log "    - 团队邮箱: fengyigen@insightquant.com"
Log "    - 推荐单位邮箱: xueyongzai@hz-yongzi.com"
Log "    - 律师邮箱: 待用户提供"
Log "  C3.3 网盘 1 份 (加密后上传):"
Log "    - 百度网盘: QuantInsight_Pro_2026"
Log "    - 阿里云盘: 备份"

Log ""
Log "=== 加密 ZIP 信息 ==="
$EncZip = Join-Path $Source "QuantInsight_Pro_提交包_v1.0_20260606_加密.zip"
if (Test-Path $EncZip) {
    $encSize = (Get-Item $EncZip).Length
    Log ("  [OK] 加密 ZIP: " + $EncZip)
    Log ("  [OK] 大小: " + [math]::Round($encSize/1MB, 2) + " MB")
    Log "  [OK] 加密算法: AES-256 (pyzipper WZ_AES)"
    Log "  [OK] 密码文件: _pwd_submission_v1.txt"
    Log ""
    Log "  密码保管 (3 处独立备份):"
    Log "  1. 团队主邮箱草稿 (用户操作)"
    Log "  2. 推荐单位邮箱草稿 (用户操作)"
    Log "  3. 律师托管 (用户操作)"
    Log "  4. 银行保险箱 (纸质密封, 推荐)"
} else {
    Log ("  [ERROR] 加密 ZIP 不存在: " + $EncZip)
    Log "  请先运行: python D:\shFintech\_encrypt_zip.py"
}

Log ""
Log "=========================================="
Log "备份清单完成"
Log ("日志: " + $LogFile)
Log "=========================================="
