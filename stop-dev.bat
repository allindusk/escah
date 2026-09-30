@echo off
chcp 65001 >nul
setlocal
rem ============================================================
rem  ESCH 双语镜像站 —— 停止开发模式
rem  按端口 5173 结束 Dev 服务器；PowerShell 不可用时回退 netstat+taskkill。
rem  内容源监听窗口没有监听端口，另按窗口标题关闭。
rem
rem  ⚠️ 2026-09-27 修正：原实现只按**窗口标题** taskkill /FI "WINDOWTITLE eq ESCAH-DEV-*"，
rem     对"用 npm run dev / 手动起的 dev server"根本杀不掉 ✗，却仍打印"已停止" ✗（误导）。
rem     改为**按端口**结束（与 stop-site.bat 同一套逻辑，最可靠），并如实报告结果。
rem ============================================================
set PORT=5173

echo [escah] 正在停止开发模式（Dev 服务器 + 内容监听）...
powershell -NoProfile -Command "$pids=(Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue).OwningProcess|Sort-Object -Unique; if($pids){$pids|ForEach-Object{Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue}; Write-Host '[escah] 已停止 Dev 服务器（端口 %PORT%）'}else{Write-Host '[escah] 端口 %PORT% 上没有正在监听的 Dev 服务器，无需停止'}"
if errorlevel 1 (
    echo [escah] PowerShell 不可用，改用 netstat 回退...
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr /R /C:":%PORT% .*LISTENING"') do (
        taskkill /pid %%a /f >nul 2>&1
        echo [escah] 已结束进程 PID %%a
    )
)

rem 监听/开浏览器两个辅助窗口没有监听端口，只能按窗口标题关（关不到也无妨）
taskkill /FI "WINDOWTITLE eq ESCAH-DEV-WATCH*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ESCAH-DEV-OPEN*" /T /F >nul 2>&1

echo [escah] 完成。若浏览器仍显示旧内容，刷新一次即可。
echo.

endlocal

