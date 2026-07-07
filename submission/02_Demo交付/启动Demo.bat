@echo off
chcp 65001 >nul
title QuantInsight Pro Demo 启动器
echo ========================================
echo   QuantInsight Pro - AFAC2026 Demo
echo   项目编号: 2026FINTECH-FINT-0093
echo   在线地址: https://3blue1brownlab.cn
echo ========================================
echo.

set "APP_DIR=%~dp0..\..\streamlit_app"
cd /d "%APP_DIR%"
echo [INFO] 工作目录: %CD%

:: 优先使用 conda deei 环境（若存在）
where conda >nul 2>&1
if %ERRORLEVEL%==0 (
    call conda activate deei 2>nul
    if %ERRORLEVEL%==0 (
        echo [INFO] 已激活 conda 环境: deei
        goto :run
    )
)

:: 否则使用本地虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO] 首次运行，创建虚拟环境...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] 创建虚拟环境失败，请确认已安装 Python 3.10+
        pause
        exit /b 1
    )
)
call .venv\Scripts\activate.bat
echo [INFO] 已激活虚拟环境: .venv

:run
echo [INFO] 检查依赖...
pip install -r requirements.txt -q -i https://pypi.tuna.tsinghua.edu.cn/simple
if %ERRORLEVEL% neq 0 (
    echo [WARN] 依赖安装部分失败，尝试继续启动...
)

echo.
echo [INFO] 启动 Streamlit Demo...
echo [INFO] 浏览器将打开 http://localhost:8501
echo [INFO] 按 Ctrl+C 停止服务
echo.
streamlit run app.py --server.headless false
pause
