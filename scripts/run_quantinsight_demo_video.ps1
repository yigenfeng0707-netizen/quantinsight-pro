# QuantInsight Pro - 3min demo video pipeline
param(
    [string]$ProjectRoot = "",
    [ValidateSet("local", "production")]
    [string]$Target = "local",
    [ValidateSet("record", "screenshot")]
    [string]$Mode = "record"
)

if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent $PSScriptRoot
}

$SkillScript = Join-Path $env:USERPROFILE ".cursor\skills\demo-video-factory\scripts\run_demo_video.ps1"
$Storyboard = Join-Path $ProjectRoot "demo.storyboard.json"
$StreamlitDir = Join-Path $ProjectRoot "streamlit_app"

if (-not (Test-Path $SkillScript)) {
    Write-Host "demo-video-factory skill not found: $SkillScript" -ForegroundColor Red
    exit 1
}

if ($Target -eq "production") {
    Write-Host "Using production URL in demo.storyboard.json" -ForegroundColor Yellow
}

$health = if ($Target -eq "production") { "https://3blue1brownlab.cn/_stcore/health" } else { "http://127.0.0.1:8501/_stcore/health" }
$needStart = $true
try {
    $r = Invoke-WebRequest -Uri $health -UseBasicParsing -TimeoutSec 8
    if ($r.StatusCode -eq 200) { $needStart = $false; Write-Host "App running: $health" -ForegroundColor Green }
} catch {}

$streamlitJob = $null
if ($needStart -and $Target -eq "local") {
    Write-Host "Starting Streamlit on :8501 ..." -ForegroundColor Cyan
    $streamlitJob = Start-Job -ScriptBlock {
        param($dir)
        Set-Location $dir
        $env:PYTHONIOENCODING = "utf-8"
        python -m streamlit run app.py --server.port 8501 --server.headless true 2>&1
    } -ArgumentList $StreamlitDir
    $deadline = (Get-Date).AddMinutes(3)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 4
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:8501/_stcore/health" -UseBasicParsing -TimeoutSec 5
            if ($r.Content -match "ok") { Write-Host "Streamlit ready." -ForegroundColor Green; break }
        } catch {}
    }
}

Push-Location $ProjectRoot
try {
    if (-not (Test-Path (Join-Path $StreamlitDir "node_modules\playwright"))) {
        Write-Host "Installing Playwright ..." -ForegroundColor Cyan
        Push-Location $StreamlitDir
        npm install --silent 2>$null
        npx playwright install chromium 2>$null
        Pop-Location
    }

    pip install -q edge-tts Pillow 2>$null

    Write-Host ""
    Write-Host "=== Phase 1: Record + Compose ===" -ForegroundColor Cyan
    & powershell -NoProfile -File $SkillScript -Storyboard $Storyboard -Mode $Mode
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host ""
    Write-Host "=== Phase 2: Subtitles ===" -ForegroundColor Cyan
    python (Join-Path $ProjectRoot "scripts\burn_demo_subtitles.py") --storyboard $Storyboard
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $mp4 = Join-Path $ProjectRoot "submission\02_Demo交付\QuantInsight_Pro_Demo_3min.mp4"
    if (Test-Path $mp4) {
        Write-Host ""
        Write-Host "[OK] Demo video: $mp4" -ForegroundColor Green
        & ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 $mp4 2>$null
    }
} finally {
    Pop-Location
    if ($streamlitJob) {
        Stop-Job $streamlitJob -ErrorAction SilentlyContinue
        Remove-Job $streamlitJob -Force -ErrorAction SilentlyContinue
    }
}
