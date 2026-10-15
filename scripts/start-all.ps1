<#
  scripts\start-all.ps1 —— 一键起前后端（各开一个窗口）

  用法（在项目根目录）：
      .\scripts\start-all.ps1

  会开两个新窗口：
      后端 http://localhost:8000/docs
      前端 http://localhost:5173

  关掉这两个窗口就等于停了服务。
  单开一个也行：start-backend.ps1 / start-frontend.ps1
#>
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$s = $PSScriptRoot

if (-not (Test-Path (Join-Path $root '.venv\Scripts\python.exe'))) {
    Write-Host '还没初始化，先跑 .\scripts\setup.ps1' -ForegroundColor Yellow
    Read-Host '按回车退出'
    exit 1
}

Write-Host ''
Write-Host '  正在启动后端窗口...' -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "cd '$root'; & '$s\start-backend.ps1' -Port $BackendPort"
)

# 等后端起来再起前端，否则前端一打开就报 502，看着像坏了
Start-Sleep -Seconds 3

Write-Host '  正在启动前端窗口...' -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "cd '$root'; & '$s\start-frontend.ps1' -Port $FrontendPort"
)

Write-Host ''
Write-Host '  后端  http://localhost:8000/docs' -ForegroundColor Green
Write-Host "  前端  http://localhost:$FrontendPort" -ForegroundColor Green
Write-Host ''
Write-Host '  关掉那两个窗口就是停止服务。' -ForegroundColor DarkGray
Write-Host ''
