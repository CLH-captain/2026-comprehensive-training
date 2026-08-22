[CmdletBinding()]
param()

$script:HasFailure = $false

function Write-Check {
    param(
        [ValidateSet('PASS', 'WARN', 'FAIL')]
        [string]$Level,
        [string]$Name,
        [string]$Detail
    )

    $color = switch ($Level) {
        'PASS' { 'Green' }
        'WARN' { 'Yellow' }
        'FAIL' { 'Red' }
    }
    Write-Host "[$Level] $Name - $Detail" -ForegroundColor $color
    if ($Level -eq 'FAIL') {
        $script:HasFailure = $true
    }
}

function Test-TcpPort {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutMilliseconds = 800
    )

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $task = $client.ConnectAsync($HostName, $Port)
        return $task.Wait($TimeoutMilliseconds) -and $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonCommand) {
    Write-Check FAIL 'Python' 'python was not found in PATH'
}
else {
    $pythonVersion = (& python --version 2>&1) -join ' '
    $match = [regex]::Match($pythonVersion, '(\d+)\.(\d+)')
    $pythonSupported = $match.Success -and (
        [int]$match.Groups[1].Value -gt 3 -or (
            [int]$match.Groups[1].Value -eq 3 -and
            [int]$match.Groups[2].Value -ge 11
        )
    )
    if ($pythonSupported) {
        Write-Check PASS 'Python' $pythonVersion
    }
    else {
        Write-Check FAIL 'Python' "Python 3.11 or newer is required; found $pythonVersion"
    }
}

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $nodeCommand) {
    Write-Check FAIL 'Node.js' 'node was not found in PATH'
}
else {
    $nodeVersion = (& node --version 2>&1) -join ' '
    $nodeMajor = [int]([regex]::Match($nodeVersion, '\d+').Value)
    if ($nodeMajor -ge 22) {
        Write-Check PASS 'Node.js' $nodeVersion
    }
    else {
        Write-Check FAIL 'Node.js' "Node.js 22 or newer is required; found $nodeVersion"
    }
}

$pnpmCommand = Get-Command pnpm.cmd -ErrorAction SilentlyContinue
$corepackCommand = Get-Command corepack.cmd -ErrorAction SilentlyContinue
if ($null -ne $pnpmCommand) {
    Write-Check PASS 'pnpm' ((& $pnpmCommand.Source --version 2>&1) -join ' ')
}
elseif ($null -ne $corepackCommand) {
    Write-Check PASS 'pnpm via Corepack' $corepackCommand.Source
}
else {
    Write-Check FAIL 'pnpm' 'neither pnpm.cmd nor corepack.cmd was found in PATH'
}

$mysqlService = Get-Service -Name MySQL80 -ErrorAction SilentlyContinue
if ($null -eq $mysqlService) {
    Write-Check FAIL 'MySQL80' 'Windows service was not found'
}
elseif ($mysqlService.Status -ne 'Running') {
    Write-Check FAIL 'MySQL80' "service state is $($mysqlService.Status)"
}
else {
    Write-Check PASS 'MySQL80' 'Windows service is running'
}

if (Test-TcpPort -HostName '127.0.0.1' -Port 3306) {
    Write-Check PASS 'MySQL port' '127.0.0.1:3306 is reachable'
}
else {
    Write-Check FAIL 'MySQL port' '127.0.0.1:3306 is not reachable'
}

$requiredFiles = @(
    @{ Name = 'Hermes Desktop'; Path = 'D:\Hermes\Hermes Agent CN Desktop\hermes-agent-cn-desktop.exe' },
    @{ Name = 'Ollama'; Path = 'D:\ollama-windows-amd64\ollama.exe' },
    @{ Name = 'Custom Modelfile'; Path = 'D:\ollama_custom\Modelfile' },
    @{ Name = '64K model manifest'; Path = 'D:\ollama-windows-amd64\models\manifests\registry.ollama.ai\library\qwen3.5-4b-64k\latest' }
)

foreach ($item in $requiredFiles) {
    if (Test-Path -LiteralPath $item.Path) {
        Write-Check PASS $item.Name $item.Path
    }
    else {
        Write-Check FAIL $item.Name "file does not exist: $($item.Path)"
    }
}

if (Test-TcpPort -HostName '127.0.0.1' -Port 8642) {
    Write-Check PASS 'Hermes API' '127.0.0.1:8642 is listening'
}
else {
    Write-Check WARN 'Hermes API' 'not running; this does not block work before Phase 7'
}

if (Test-TcpPort -HostName '127.0.0.1' -Port 11434) {
    Write-Check PASS 'Ollama API' '127.0.0.1:11434 is listening'
}
else {
    Write-Check WARN 'Ollama API' 'not running; this does not block work before Phase 7'
}

if ($script:HasFailure) {
    exit 1
}

exit 0
