$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$processFile = Join-Path $projectRoot "logs\demo-processes.json"
if (-not (Test-Path -LiteralPath $processFile)) {
    Write-Host "未找到由启动脚本记录的演示进程。"
    exit 0
}

$processIds = Get-Content -LiteralPath $processFile -Raw -Encoding utf8 | ConvertFrom-Json
foreach ($processId in @($processIds.backend, $processIds.frontend)) {
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $processId
    }
}
Remove-Item -LiteralPath $processFile -Force
Write-Host "演示服务已停止。" -ForegroundColor Green
