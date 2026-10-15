<#
  scripts\start-frontend.ps1 —— 只启动前端

  用法（在项目根目录）：
      .\scripts\start-frontend.ps1

  首次运行会自动 npm install。

  启动后打开 http://localhost:5173
  前端调后端走 vite proxy：/api -> http://localhost:8000
  所以【后端必须也在跑】，否则页面能开但所有接口 502。
#>
param(
    [int]$Port = 5173
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root 'frontend')

if (-not (Test-Path 'node_modules')) {
    Write-Host ''
    Write-Host '  首次运行，正在安装前端依赖（可能几分钟）...' -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'npm install 失败，检查 Node 是否已安装。' -ForegroundColor Red
        exit 1
    }
    Write-Host ''
}

Write-Host '  前端启动中...' -ForegroundColor Cyan
Write-Host "  打开 http://localhost:$Port" -ForegroundColor Green
Write-Host "  接口转发到 http://localhost:8000/api" -ForegroundColor DarkGray
Write-Host '  按 Ctrl+C 停止' -ForegroundColor DarkGray
Write-Host ''

# vite 会往 stderr 写 banner 和报错，ErrorActionPreference=Stop 会把它当失败中断，
# 所以这里临时放开，靠 Ctrl+C 结束。
$ErrorActionPreference = 'Continue'
npm run dev -- --port $Port
