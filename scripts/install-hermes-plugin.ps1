param(
    [string]$HermesHome = (Join-Path $env:APPDATA 'cn.org.hermesagent.desktop\runtime\hermes-home')
)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot '..\hermes_plugin\szut-club-statistics'
$targetRoot = Join-Path $HermesHome 'plugins'
$target = Join-Path $targetRoot 'szut-club-statistics'
$targetRootFull = [IO.Path]::GetFullPath($targetRoot)
$targetFull = [IO.Path]::GetFullPath($target)

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Project plugin source not found: $source"
}
New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
if (-not $targetFull.StartsWith($targetRootFull + [IO.Path]::DirectorySeparatorChar)) {
    throw "Unsafe Hermes plugin target: $targetFull"
}
if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
}
Copy-Item -LiteralPath $source -Destination $target -Recurse
Write-Host "Installed Hermes plugin: $target"
Write-Host "Enable with: hermes plugins enable szut-club-statistics"
