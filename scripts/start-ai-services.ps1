param(
    [string]$OllamaExe = 'D:\ollama-windows-amd64\ollama.exe',
    [string]$OllamaModels = 'D:\ollama-windows-amd64\models',
    [string]$HermesDesktopExe = 'D:\Hermes\Hermes Agent CN Desktop\hermes-agent-cn-desktop.exe',
    [int]$WaitSeconds = 25
)

$ErrorActionPreference = 'Stop'

function Test-HttpEndpoint([string]$Uri) {
    try {
        $null = Invoke-RestMethod -Uri $Uri -TimeoutSec 2
        return $true
    } catch {
        return $false
    }
}

if (-not (Test-HttpEndpoint 'http://127.0.0.1:11434/api/tags')) {
    if (-not (Test-Path -LiteralPath $OllamaExe -PathType Leaf)) {
        throw "Ollama executable not found: $OllamaExe"
    }
    $env:OLLAMA_MODELS = $OllamaModels
    Start-Process -FilePath $OllamaExe -ArgumentList 'serve' -WorkingDirectory (Split-Path $OllamaExe) -WindowStyle Hidden
    Write-Host 'Started Ollama.'
} else {
    Write-Host 'Ollama is already running.'
}

if (-not (Test-HttpEndpoint 'http://127.0.0.1:9120/api/status')) {
    if (-not (Test-Path -LiteralPath $HermesDesktopExe -PathType Leaf)) {
        throw "Hermes Desktop executable not found: $HermesDesktopExe"
    }
    Start-Process -FilePath $HermesDesktopExe -WorkingDirectory (Split-Path $HermesDesktopExe) -WindowStyle Hidden
    Write-Host 'Started Hermes Desktop services.'
} else {
    Write-Host 'Hermes Dashboard is already running.'
}

$deadline = (Get-Date).AddSeconds($WaitSeconds)
do {
    $ollamaReady = Test-HttpEndpoint 'http://127.0.0.1:11434/api/tags'
    $hermesReady = Test-HttpEndpoint 'http://127.0.0.1:9120/api/status'
    if ($ollamaReady -and $hermesReady) { break }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $deadline)

if (-not $ollamaReady) { throw 'Ollama did not become ready in time.' }
if (-not $hermesReady) { throw 'Hermes Dashboard did not become ready in time.' }
Write-Host 'AI services are ready: Ollama :11434, Hermes Dashboard :9120.'