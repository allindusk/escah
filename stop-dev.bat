@echo off
chcp 65001 >nul
setlocal
rem ============================================================
rem  ESCH 双语镜像站 —— 停止开发模式
rem  关闭 start-dev.bat 拉起的 Dev 服务器与内容源监听窗口。
rem ============================================================
echo [escah] 正在停止开发模式（Dev 服务器 + 内容监听）...

taskkill /FI "WINDOWTITLE eq ESCAH-DEV-*" /T /F >nul 2>&1

echo [escah] 已停止。若浏览器仍显示旧内容，刷新一次即可。
echo.

endlocal
