@echo off
chcp 65001 >nul
setlocal
rem ============================================================
rem  ESCH 双语镜像站 —— 本地一键启动（预览已构建站点）
rem  双击本文件即可：自动检测是否已构建，未构建则先构建，
rem  然后起本地预览服务器并打开浏览器。
rem  服务器在前台运行，关闭本窗口即停止服务。
rem  预览地址： http://localhost:4173/escah/
rem ============================================================
cd /d "%~dp0site"

rem 若未构建则先构建
if not exist ".vitepress\dist\index.html" (
    echo [escah] 未检测到构建产物，先执行构建（首次约需 30~60 秒）...
    node build.mjs build
    if errorlevel 1 (
        echo [escah] 构建失败，请确认本机已安装 Node.js 且 node 命令位于 PATH。
        pause
        exit /b 1
    )
)

echo [escah] 启动本地预览服务器，地址： http://localhost:4173/escah/
echo [escah] 按 Ctrl+C 停止服务；直接关闭本窗口也会停止。
start "" "http://localhost:4173/escah/"
node build.mjs preview
