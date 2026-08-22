$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot "backend"
$frontendRoot = Join-Path $projectRoot "frontend"
$logsRoot = Join-Path $projectRoot "logs"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"
$pnpm = (Get-Command pnpm.cmd -ErrorAction Stop).Source

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot ".env"))) {
    throw "未找到项目 .env，请先完成本机配置。"
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "未找到后端虚拟环境，请先安装 backend/requirements.txt。"
}

$occupied = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in 8000, 5173 }
if ($occupied) {
    throw "端口 8000 或 5173 已被占用。若演示服务已启动，请直接访问 http://127.0.0.1:5173。"
}

New-Item -ItemType Directory -Path $logsRoot -Force | Out-Null
$backendProcess = Start-Process -FilePath $python `
    -ArgumentList "-m", "uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $logsRoot "backend-demo.out.log") `
    -RedirectStandardError (Join-Path $logsRoot "backend-demo.err.log")
$frontendProcess = Start-Process -FilePath $pnpm `
    -ArgumentList "dev", "--host", "127.0.0.1", "--port", "5173" `
    -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $logsRoot "frontend-demo.out.log") `
    -RedirectStandardError (Join-Path $logsRoot "frontend-demo.err.log")

@{
    backend = $backendProcess.Id
    frontend = $frontendProcess.Id
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logsRoot "demo-processes.json") -Encoding utf8

Start-Sleep -Seconds 2
Write-Host "演示系统已启动：" -ForegroundColor Green
Write-Host "  前端：http://127.0.0.1:5173"
Write-Host "  API：http://127.0.0.1:8000/docs"
Write-Host "结束演示时运行：.\scripts\stop-demo.ps1"
