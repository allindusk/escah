@echo off
setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUNBUFFERED=1
set ROOT=D:\D11_DeveloperProject\150_HTML_Project\escalation_heroines\escah
set LOG=%ROOT%\tools\_rebuild.log
set LOCK=%ROOT%\tools\_rebuild.lock

REM ============================================================
REM key 化 i18n 重建（2026-07-27 起，旧 zh_patch/char_zh 正则流程已废弃）
REM 并发护栏：锁存在 且 确有重建相关进程在跑 -> 拒绝；进程已死 -> 清僵尸锁继续
REM ============================================================
if exist "%LOCK%" (
  powershell -NoProfile -Command "$r=(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='node.exe'\" | Where-Object { $_.CommandLine -match 'escah_pipeline|build.mjs' } | Measure-Object).Count -gt 0; if($r){exit 0}else{exit 1}"
  if %ERRORLEVEL%==0 (
    echo [%time%] ABORT: 检测到重建相关进程仍在运行（锁=%LOCK%），先等它结束。>> "%LOG%"
    echo [ABORT] 已有重建在跑，先结束再启动（详见 %LOG%）。
    exit /b 3
  ) else (
    echo [%time%] 发现僵尸锁（无重建进程），清理后继续。>> "%LOG%"
    del "%LOCK%"
  )
)
echo running > "%LOCK%"

echo [%time%] START > "%LOG%"
cd /d "%ROOT%"

echo [%time%] [1/3] i18n 翻译应用开始（build→fill→char-fill，全站约 1 分钟）>> "%LOG%"
python -u -m escah_pipeline.cli translate >> "%LOG%" 2>&1
echo [%time%] [1/3] i18n done>> "%LOG%"

echo [%time%] [2/3] sync-site 开始>> "%LOG%"
python -u -m escah_pipeline.cli sync-site >> "%LOG%" 2>&1
echo [%time%] [2/3] sync-site done>> "%LOG%"

echo [%time%] [3/3] node build.mjs build 开始>> "%LOG%"
cd /d "%ROOT%\site"
node build.mjs build >> "%LOG%" 2>&1
echo [%time%] [3/3] DONE>> "%LOG%"

del "%LOCK%"
