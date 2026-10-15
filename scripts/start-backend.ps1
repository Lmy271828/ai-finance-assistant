<#
  scripts\start-backend.ps1 —— 只启动后端

  用法（在项目根目录）：
      .\scripts\start-backend.ps1
      .\scripts\start-backend.ps1 -Port 8080

  启动后：
      接口文档  http://localhost:8000/docs
      静态首页  http://localhost:8000/
#>
param(
    [int]$Port = 8000,
    [switch]$NoReload
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# ── 强制用项目自己的虚拟环境 ─────────────────────────────────
# 不这么做的话，pip 会把你全局 anaconda 环境里的 starlette 降级，
# 连带弄坏别的项目（sse-starlette 就不兼容了）。
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Host ''
    Write-Host '没有找到虚拟环境 .venv\ 先创建：' -ForegroundColor Yellow
    Write-Host '    .\scripts\setup.ps1' -ForegroundColor Yellow
    Write-Host ''
    exit 1
}

Write-Host ''
Write-Host '  后端启动中...' -ForegroundColor Cyan
Write-Host "  接口文档  http://localhost:$Port/docs" -ForegroundColor Green
Write-Host '  按 Ctrl+C 停止' -ForegroundColor DarkGray
Write-Host ''

$argList = @('-m', 'uvicorn', 'backend.main:app', '--port', "$Port")
if (-not $NoReload) { $argList += '--reload' }

# uvicorn 会持续往 stderr 写访问日志和热重载信息。
# 在 $ErrorActionPreference='Stop' 下，任何一行 stderr 都会把脚本打断。
$ErrorActionPreference = 'Continue'
& $python @argList
