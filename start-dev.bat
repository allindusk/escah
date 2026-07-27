@echo off
chcp 65001 >nul
setlocal
rem ============================================================
rem  ESCH 双语镜像站 —— 开发模式一键启动（支持热部署 / HMR）
rem  双击本文件即可：先生成最新站点内容（sync-site），
rem  然后同时启动：
rem    1) VitePress Dev 服务器（端口 5173，支持前端代码/页面热更新）
rem    2) 内容源监听（tools/dev-watch.py）：改译文/_manual_zh.json/
rem       glossary/terms.yaml / data/parsed 后会自动 sync-site，
rem       浏览器随即热刷新，无需手动重建或重启。
rem
rem  开发地址： http://localhost:5173/escah/
rem  停止方式： 运行 stop-dev.bat，或关闭两个子窗口。
rem ============================================================
cd /d "%~dp0"

echo [escah] 生成最新站点内容（sync-site）...
python -m escah_pipeline.cli sync-site
if errorlevel 1 (
    echo [escah] sync-site 失败，请确认本机已安装 Python 且 python 命令位于 PATH。
    pause
    exit /b 1
)

echo [escah] 启动 Dev 服务器（http://localhost:5173/escah/）...
start "ESCAH-DEV-SERVER" /D "%~dp0site" node build.mjs dev

echo [escah] 启动内容源监听（改译文/源文件将自动 sync-site 并热刷新）...
start "ESCAH-DEV-WATCH" /D "%~dp0" python tools\dev-watch.py

echo.
echo [escah] 开发模式已启动：
echo   - 前端 Dev 服务器 : http://localhost:5173/escah/
echo   - 内容监听窗口     : ESCAH-DEV-WATCH（自动 sync-site）
echo   - 停止请运行 stop-dev.bat
echo.
start "" "http://localhost:5173/escah/"

endlocal
