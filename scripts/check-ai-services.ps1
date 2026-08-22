param(
    [string]$Model = 'qwen3.5-4b-64k:latest',
    [string]$HermesRuntime = ''
)

$ErrorActionPreference = 'Stop'

if (-not $HermesRuntime) {
    $versions = Join-Path $env:APPDATA 'cn.org.hermesagent.desktop\runtime\versions'
    $runtime = Get-ChildItem -LiteralPath $versions -Filter 'hermes-agent-cn-runtime-win32-x64.exe' -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($runtime) { $HermesRuntime = $runtime.FullName }
}

$result = [ordered]@{
    ollama = 'unavailable'
    model = 'unavailable'
    context_length = $null
    hermes_runtime = 'unavailable'
    hermes_dashboard = 'unavailable'
}

try {
    $tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3
    $result.ollama = 'ready'
    if ($tags.models.name -contains $Model) {
        $result.model = $Model
        $body = @{ model = $Model } | ConvertTo-Json
        $show = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/show' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 10
        if ($show.parameters -match 'num_ctx\s+(\d+)') {
            $result.context_length = [int]$Matches[1]
        }
    }
} catch {}

if ($HermesRuntime -and (Test-Path -LiteralPath $HermesRuntime -PathType Leaf)) {
    $result.hermes_runtime = (& $HermesRuntime --version 2>$null | Select-Object -First 1)
}
try {
    $status = Invoke-RestMethod -Uri 'http://127.0.0.1:9120/api/status' -TimeoutSec 3
    $result.hermes_dashboard = "ready ($($status.version))"
} catch {}

[pscustomobject]$result | Format-List
if ($result.ollama -ne 'ready' -or $result.model -eq 'unavailable' -or $result.hermes_runtime -eq 'unavailable') {
    exit 1
}