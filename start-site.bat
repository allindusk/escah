@echo off
chcp 65001 >nul
setlocal
rem ============================================================
rem  ESCH 双语镜像站 —— 本地一键启动（预览已构建站点）
rem  双击本文件即可：自动判断是否需要构建（产物缺失、或内容源比产物新），
rem  然后起本地预览服务器，并在**端口就绪后**自动打开浏览器。
rem  服务器在前台运行，关闭本窗口即停止服务。
rem  预览地址： http://localhost:4173/escah/
rem  停止方式： 运行 stop-site.bat（按端口结束，最可靠），或关闭本窗口。
rem ============================================================
cd /d "%~dp0"

rem Python 检查：本脚本依赖 python（判定是否需要构建、等端口就绪后开浏览器）。
rem 缺 python 时上面两步会静默失效（跳过构建、浏览器不打开）✗，所以提前拦住。
where python >nul 2>&1
if errorlevel 1 (
    echo [escah] 未找到 python 命令，请先安装 Python 并确保它在 PATH 中。
    pause
    exit /b 1
)

rem 依赖检查：没装过 npm 依赖时，报错会出现在子窗口里、且原提示语只说"确认已装 Node.js"，
rem 很误导 —— 这里提前拦住并给出正确命令。
if not exist "site\node_modules\vitepress" (
    echo [escah] 未检测到 site\node_modules\vitepress，请先安装依赖：
    echo         cd site ^&^& npm ci
    pause
    exit /b 1
)

rem 判断是否需要构建：产物缺失，或**内容源比产物更新**时都要重建。
rem ⚠️ 原实现只看 .vitepress\dist\index.html 是否存在 → 内容更新后不会重建，
rem    预览到旧站点 ✗（2026-09-27 实测：旧 dist 里还留着已删除的两页）。
rem 判定逻辑放在 tools/site-needs-build.py（可单测）：exit 0=需要构建，1=无需构建。
python tools\site-needs-build.py
if errorlevel 1 goto run_preview

echo [escah] 产物缺失或已过期，开始构建（首次约 30~60 秒）...
pushd site
node build.mjs build
if errorlevel 1 (
    popd
    echo [escah] 构建失败：请确认已安装 Node.js 且在 PATH 中（依赖需先 npm ci）。
    pause
    exit /b 1
)
popd

:run_preview
echo [escah] 启动本地预览服务器（端口 4173）...
echo [escah] 浏览器将在端口就绪后自动打开；按 Ctrl+C 停止服务。
rem 后台等端口就绪再开浏览器：原先"先开浏览器、后起服务"必现"无法访问" ✗
start "ESCAH-PREVIEW-OPEN" /D "%~dp0" python tools\open-when-ready.py 4173 "http://localhost:4173/escah/"
cd /d "%~dp0site"
node build.mjs preview

