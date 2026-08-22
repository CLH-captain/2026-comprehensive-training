$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$processFile = Join-Path $projectRoot "logs\demo-processes.json"
if (-not (Test-Path -LiteralPath $processFile)) {
    Write-Host "未找到由启动脚本记录的演示进程。"
    exit 0
}

$processIds = Get-Content -LiteralPath $processFile -Raw -Encoding utf8 | ConvertFrom-Json
$allProcesses = Get-CimInstance Win32_Process
$targetIds = [System.Collections.Generic.HashSet[int]]::new()

function Add-ProcessTree([int]$parentId) {
    foreach ($child in $allProcesses | Where-Object { $_.ParentProcessId -eq $parentId }) {
        Add-ProcessTree $child.ProcessId
    }
    [void]$targetIds.Add($parentId)
}

foreach ($rootId in @($processIds.backend, $processIds.frontend)) {
    Add-ProcessTree $rootId
}
foreach ($processId in $targetIds) {
    $process = $allProcesses | Where-Object { $_.ProcessId -eq $processId }
    if ($process -and $process.CommandLine -like "*$projectRoot*") {
        Stop-Process -Id $processId -ErrorAction SilentlyContinue
    }
}
Remove-Item -LiteralPath $processFile -Force
Write-Host "演示服务已停止。" -ForegroundColor Green
