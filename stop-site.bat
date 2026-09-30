@echo off
chcp 65001 >nul
setlocal
rem ============================================================
rem  ESCH 双语镜像站 —— 停止本地预览服务器
rem  按端口 4173 查找并结束进程；PowerShell 不可用时回退 netstat+taskkill。
rem  ⚠️ 2026-09-27 修正：回退分支原用 `findstr ":%PORT% "`（未锚定），
rem     会连带匹配到"**远端**端口 4173 的连接"（如浏览器与它建立的 ESTABLISHED 连接），
rem     极端情况下可能误杀无关进程 ✗。改为锚定到 LISTENING 行。
rem ============================================================
set PORT=4173

powershell -NoProfile -Command "$pids=(Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue).OwningProcess|Sort-Object -Unique; if($pids){$pids|ForEach-Object{Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue}; Write-Host '[escah] 已停止预览服务器（端口 %PORT%）'}else{Write-Host '[escah] 未检测到端口 %PORT% 上正在监听的服务，无需停止'}"

if errorlevel 1 (
    echo [escah] PowerShell 不可用，改用 netstat 回退...
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /R /C:":%PORT% .*LISTENING"') do (
        taskkill /pid %%a /f >nul 2>&1
        echo [escah] 已结束进程 PID %%a
    )
)

endlocal
