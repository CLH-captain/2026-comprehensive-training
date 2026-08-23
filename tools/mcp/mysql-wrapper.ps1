$ErrorActionPreference = 'Stop'

# Loads the existing project DATABASE_URL without copying credentials into Hermes config.
$envFile = Join-Path $PSScriptRoot '..\..\.env'
$line = Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
if (-not $line) { throw "DATABASE_URL was not found in $envFile" }
$connection = $line.Substring('DATABASE_URL='.Length)
$uri = [Uri]$connection
$parts = $uri.UserInfo.Split(':', 2)
$env:MYSQL_HOST = $uri.Host
$env:MYSQL_PORT = if ($uri.Port -gt 0) { [string]$uri.Port } else { '3306' }
$env:MYSQL_USER = [Uri]::UnescapeDataString($parts[0])
$env:MYSQL_PASS = if ($parts.Count -gt 1) { [Uri]::UnescapeDataString($parts[1]) } else { '' }
$env:MYSQL_DB = $uri.AbsolutePath.Trim('/')
$env:MCP_DB_NAME = $env:MYSQL_DB

# mcp-server-mysql exposes read-only query tools.
& npx --yes mcp-server-mysql@1.0.42
exit $LASTEXITCODE
