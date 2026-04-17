@echo off
REM AI Employee Startup Script (Windows)
REM Run this to start your AI Employee

echo Starting AI Employee...
echo Vault: C:\Users\samee\AI_Employee_Vault

REM Set environment (copy .env.example to .env and fill values first)
if exist "C:\Users\samee\AI_Employee_Vault\.env" (
    for /f "tokens=1,2 delims==" %%A in ("C:\Users\samee\AI_Employee_Vault\.env") do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" set %%A=%%B
    )
) else (
    echo WARNING: .env file not found. Using defaults (DRY_RUN=true)
    set DRY_RUN=true
)

set VAULT_PATH=C:\Users\samee\AI_Employee_Vault

echo Mode: DRY_RUN=%DRY_RUN%
echo.

REM Start watchdog (manages orchestrator + filesystem_watcher)
echo Starting Watchdog Process Manager...
start "AI-Employee-Watchdog" python "C:\Users\samee\AI_Employee_Vault\scripts\watchdog_process.py" --vault "%VAULT_PATH%"

echo.
echo AI Employee is running!
echo - Watchdog will keep orchestrator and filesystem_watcher alive
echo - Drop files into: %VAULT_PATH%\Drop\
echo - Check status at: %VAULT_PATH%\Dashboard.md
echo - Approvals queue: %VAULT_PATH%\Pending_Approval\
echo.
echo Press any key to stop all processes...
pause

taskkill /FI "WINDOWTITLE eq AI-Employee-*" /F
echo AI Employee stopped.
