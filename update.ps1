<#
.SYNOPSIS
    手动增量更新镜像站点（轮询观察列表、sha256 比对、仅重处理变更页面）。
.DESCRIPTION
    封装 escah-pipeline update 子命令。优先使用已 pip 安装的 `escah-pipeline`，
    否则回退到仓库内 `python -m escah_pipeline.cli`。以 UTF-8 启动 Python 子进程，
    捕获退出码。可配合计划任务/双击手动运行。
.PARAMETER NoTranslate
    仅抓取与重解析，跳过翻译（用于无 API Key 时先备料）。
.PARAMETER Mock
    使用占位翻译（不调用 LLM），用于验证整条链路而不消耗额度。
.EXAMPLE
    .\update.ps1                 # 正常增量更新并翻译
    .\update.ps1 -Mock           # 用占位翻译验证链路
    .\update.ps1 -NoTranslate    # 只重抓/重解析，不翻译
#>
[CmdletBinding()]
param(
    [switch]$NoTranslate,
    [switch]$Mock
)

$ErrorActionPreference = "Stop"
# 强制控制台与子进程输出 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pushd = Push-Location -PassThru
try {
    Set-Location $repoRoot

    $argsList = @("update")
    if ($NoTranslate) { $argsList += "--no-translate" }
    if ($Mock)        { $argsList += "--mock" }

    # 优先使用已安装的 console 脚本，否则回退到仓库内模块
    $cmd = Get-Command escah-pipeline -ErrorAction SilentlyContinue
    if ($cmd) {
        & escah-pipeline @argsList
        $exitCode = $LASTEXITCODE
    } else {
        $pipelineDir = Join-Path $repoRoot "pipeline"
        if (-not (Test-Path $pipelineDir)) {
            throw "未找到 pipeline 目录：$pipelineDir"
        }
        Push-Location $pipelineDir
        try {
            & python -X utf8 -m escah_pipeline.cli @argsList
            $exitCode = $LASTEXITCODE
        } finally {
            Pop-Location
        }
    }

    if ($exitCode -ne 0) {
        Write-Error "更新脚本以非零退出码结束：$exitCode"
        exit $exitCode
    }
    Write-Host "增量更新完成。" -ForegroundColor Green
} finally {
    $pushd | Set-Location
}
