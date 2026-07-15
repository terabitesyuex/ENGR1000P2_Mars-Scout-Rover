@echo off
setlocal

if "%~1"=="" (
    echo Usage: %~nx0 phase2.2 [-AllowDirty]
    exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "PHASE=%~1"
shift /1

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%verify_phase.ps1" -Phase "%PHASE%" %1 %2 %3 %4 %5 %6 %7 %8 %9
exit /b %ERRORLEVEL%
