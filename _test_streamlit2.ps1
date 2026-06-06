# Test Streamlit page loading
$env:PYTHONIOENCODING = 'utf-8'

Write-Host "Starting Streamlit..."
$proc = Start-Process -FilePath "C:\Users\52637\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\streamlit.exe" -ArgumentList "run", "D:\shFintech\streamlit_app\app.py", "--server.port", "8502", "--server.headless", "true", "--server.runOnSave", "false", "--browser.gatherUsageStats", "false" -PassThru -WindowStyle Hidden -RedirectStandardOutput "D:\shFintech\_streamlit2.log" -RedirectStandardError "D:\shFintech\_streamlit2_err.log"

Start-Sleep -Seconds 30

Write-Host "=== Testing endpoints ==="
$endpoints = @(
    "http://localhost:8502/_stcore/health",
    "http://localhost:8502/",
    "http://localhost:8502/static/index.html"
)
foreach ($ep in $endpoints) {
    try {
        $r = Invoke-WebRequest -Uri $ep -UseBasicParsing -TimeoutSec 10
        Write-Host "$ep : $($r.StatusCode) ($($r.Content.Length) bytes)"
    } catch {
        Write-Host "$ep : ERROR - $($_.Exception.Message)"
    }
}

Write-Host "=== Streamlit logs ==="
if (Test-Path "D:\shFintech\_streamlit2_err.log") {
    Get-Content "D:\shFintech\_streamlit2_err.log" -Tail 30 -Encoding UTF8
}

Get-Process -Name streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "=== Done ==="
