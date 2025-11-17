@echo off
REM Simple batch file to run the PowerShell build script
REM Usage: build.bat [clean]

echo ========================================
echo   AiDupeRanger Build Script (Batch)
echo ========================================
echo.

if "%1"=="clean" (
    echo Running with -Clean flag...
    powershell -ExecutionPolicy Bypass -File build_windows.ps1 -Clean
) else (
    echo Running normal build...
    powershell -ExecutionPolicy Bypass -File build_windows.ps1
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo.
) else (
    echo.
    echo Build failed! Check errors above.
    echo.
)

pause
