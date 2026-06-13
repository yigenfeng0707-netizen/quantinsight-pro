# Test Streamlit Demo
# Run for 20 seconds, check health, then stop

Set-Location "D:\shFintech\streamlit_app"
$env:PYTHONIOENCODING = 'utf-8'

Write-Host "Starting Streamlit..."
$proc = Start-Process -FilePath "C:\Users\52637\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Scripts\streamlit.exe" -ArgumentList "run", "app.py", "--server.port", "8501", "--server.headless", "true", "--server.runOnSave", "false", "--browser.gatherUsageStats", "false" -PassThru -WindowStyle Hidden -RedirectStandardOutput "D:\shFintech\_streamlit_test.log" -RedirectStandardError "D:\shFintech\_streamlit_test_err.log"

Start-Sleep -Seconds 20

Write-Host "=== Checking health ==="
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Body: $($response.Content)"
} catch {
    Write-Host "Error: $($_.Exception.Message)"
}

Write-Host "=== Checking logs ==="
if (Test-Path "D:\shFintech\_streamlit_test.log") {
    Get-Content "D:\shFintech\_streamlit_test.log" -Tail 20 -Encoding UTF8
}
if (Test-Path "D:\shFintech\_streamlit_test_err.log") {
    Write-Host "--- ERR ---"
    Get-Content "D:\shFintech\_streamlit_test_err.log" -Tail 20 -Encoding UTF8
}

# Stop the process
Get-Process -Name streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "=== Done ==="
