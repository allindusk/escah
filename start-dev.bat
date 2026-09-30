@echo off
chcp 65001 >nul
setlocal
rem ============================================================
rem  ESCH 双语镜像站 —— 开发模式一键启动（支持热部署 / HMR）
rem  双击本文件即可：先生成最新站点内容（sync-site），
rem  然后同时启动：
rem    1) VitePress Dev 服务器（端口 5173，支持前端代码/页面热更新）
rem    2) 内容源监听（tools/dev-watch.py）：改**译文**（data/parsed/i18n 与
rem       glossary/*.yaml）、正文/角色数据或 data/registry 后会自动 sync-site，
rem       浏览器随即热刷新，无需手动重建或重启。
rem       ⚠️ 2026-09-27 修正：监听列表原先含已不存在的 data/parsed/zh 与
rem       tools/_manual_zh.json → 改译文根本不会触发 ✗，现已改为上面的真实路径。
rem
rem  开发地址： http://localhost:5173/escah/
rem  停止方式： 运行 stop-dev.bat（按端口结束），或关闭两个子窗口。
rem ============================================================
cd /d "%~dp0"

rem Python 检查：本脚本依赖 python（sync-site、内容监听、等端口就绪后开浏览器）。
where python >nul 2>&1
if errorlevel 1 (
    echo [escah] 未找到 python 命令，请先安装 Python 并确保它在 PATH 中。
    pause
    exit /b 1
)

rem 依赖检查：没装过 npm 依赖时，报错会出现在子窗口里、提示很误导 —— 提前拦住。
if not exist "site\node_modules\vitepress" (
    echo [escah] 未检测到 site\node_modules\vitepress，请先安装依赖：
    echo         cd site ^&^& npm ci
    pause
    exit /b 1
)

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

rem 后台等端口就绪再开浏览器：原先"先开浏览器、后起服务"会先看到"无法访问" ✗
echo [escah] 等端口 5173 就绪后自动打开浏览器...
start "ESCAH-DEV-OPEN" /D "%~dp0" python tools\open-when-ready.py 5173 "http://localhost:5173/escah/"

echo.
echo [escah] 开发模式已启动：
echo   - 前端 Dev 服务器 : http://localhost:5173/escah/（就绪后自动打开浏览器）
echo   - 内容监听窗口     : ESCAH-DEV-WATCH（自动 sync-site）
echo   - 停止请运行 stop-dev.bat
echo.

endlocal

