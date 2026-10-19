<#
.SYNOPSIS
    本地离线重建（拉取 CI 抓好的原站镜像后跑这个）。
.DESCRIPTION
    封装 escah-pipeline local-sync 子命令，全程不联网：
    解析 data/raw、i18n build（只重建 raw 变过的页，按 ja 文本回贴旧译文）、
    角色 JSON 回填、生成待译清单、生成站点内容（ja/zh）。
    前提：先 git pull 取回 CI 抓的 data/raw 与图片。
    若 pull 时 data/manifest.json 冲突，解决冲突后再跑
    python -m escah_pipeline.cli manifest merge 合并两侧状态。
.PARAMETER Pages
    只处理指定页（页名或 slug 均可），缺省为全部页。
.PARAMETER NoSite
    跳过站点内容生成。
.EXAMPLE
    .\local-sync.ps1
#>
[CmdletBinding()]
param(
    [string[]]$Pages,
    [switch]$NoSite,
    [switch]$NoExtract
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pushd = Push-Location -PassThru
try {
    Set-Location $repoRoot

    $argsList = @("local-sync")
    if ($Pages) { $argsList += "--pages"; $argsList += $Pages }
    if ($NoSite) { $argsList += "--no-site" }
    if ($NoExtract) { $argsList += "--no-extract" }

    $cmd = Get-Command escah-pipeline -ErrorAction SilentlyContinue
    if ($cmd) {
        & escah-pipeline @argsList
        $exitCode = $LASTEXITCODE
    } else {
        $pipelineDir = Join-Path $repoRoot "pipeline"
        if (-not (Test-Path $pipelineDir)) {
            throw "pipeline dir not found: $pipelineDir"
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
        Write-Error "local-sync failed: exitCode"
        exit $exitCode
    }
    Write-Host "local-sync done. New todos in tools/_todo_translate/" -ForegroundColor Green
} finally {
    $pushd | Set-Location
}
