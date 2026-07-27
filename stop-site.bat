@echo off
chcp 65001 >nul
setlocal
rem ============================================================
rem  ESCH 双语镜像站 —— 停止本地预览服务器
rem  按端口 4173 查找并结束进程；PowerShell 不可用时回退 netstat+taskkill。
rem ============================================================
set PORT=4173

powershell -NoProfile -Command "$pids=(Get-NetTCPConnection -LocalPort %PORT% -ErrorAction SilentlyContinue).OwningProcess|Sort-Object -Unique; if($pids){$pids|ForEach-Object{Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue}; Write-Host '[escah] 已停止预览服务器（端口 %PORT%）'}else{Write-Host '[escah] 未检测到端口 %PORT% 上的服务，无需停止'}"

if errorlevel 1 (
    echo [escah] PowerShell 不可用，改用 netstat 回退...
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
        taskkill /pid %%a /f >nul 2>&1
        echo [escah] 已结束进程 PID %%a
    )
)

endlocal
