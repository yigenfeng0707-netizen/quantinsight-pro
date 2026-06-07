@echo off
echo ============================================
echo HyperFrames Installation Verification
echo ============================================
echo.
echo 1. Checking hyperframes version...
hyperframes --version
if %errorlevel% equ 0 (
    echo SUCCESS: hyperframes command is working!
) else (
    echo INFO: Command may require new terminal session
    echo Testing with full path...
    "%USERPROFILE%\AppData\Roaming\npm\hyperframes.cmd" --version
)
echo.
echo 2. Checking npm global path...
echo PATH contains npm: %PATH% | findstr /i "npm"
echo.
echo 3. Checking environment configuration...
echo User PATH: 
reg query "HKCU\Environment" /v PATH | findstr /i "npm"
echo.
echo ============================================
echo Verification Complete!
echo ============================================
echo.
echo Note: If hyperframes command is not found, 
echo please restart your terminal or log out and log back in.
pause