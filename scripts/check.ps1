<#
  scripts\check.ps1 —— 一键自检

  检查环境是否就绪、后端是否在跑、接口是否通。
  队友上手第一件事就跑这个，比一个个排查快。
#>
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$ok = $true

Write-Host ''
Write-Host '=== 环境 ===' -ForegroundColor Cyan

$python = Join-Path $root '.venv\Scripts\python.exe'
if (Test-Path $python) {
    Write-Host '  [OK]   虚拟环境 .venv 存在' -ForegroundColor Green
} else {
    Write-Host '  [缺]   虚拟环境 .venv 不存在 -> 跑 .\scripts\setup.ps1' -ForegroundColor Red
    $ok = $false
}

$nodeOk = $null -ne (Get-Command npm -ErrorAction SilentlyContinue)
if ($nodeOk) {
    $nm = Test-Path 'frontend\node_modules'
    if ($nm) {
        Write-Host '  [OK]   前端依赖已安装' -ForegroundColor Green
    } else {
        Write-Host '  [缺]   前端依赖未装 -> 跑 .\scripts\setup.ps1' -ForegroundColor Red
        $ok = $false
    }
} else {
    Write-Host '  [缺]   没找到 npm（Node.js 未安装）' -ForegroundColor Red
    $ok = $false
}

Write-Host ''
Write-Host '=== 后端 ===' -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod 'http://localhost:8000/health' -TimeoutSec 3
    Write-Host ("  [OK]   后端在跑  数据 {0} 笔 / {1} 个导入批次" -f $health.transactions, $health.batches) -ForegroundColor Green
} catch {
    Write-Host '  [停]   后端没在跑 -> .\scripts\start-backend.ps1' -ForegroundColor Yellow
    $ok = $false
}

# 顺带打一个真实业务接口：/health 只能证明进程活着，打通业务才能证明库也好着
try {
    $q = 'type=expense&period=month&value=2026-09'
    $null = Invoke-RestMethod "http://localhost:8000/api/report/summary?$q" -TimeoutSec 5
    Write-Host '  [OK]   报告接口可用（summary 200）' -ForegroundColor Green
} catch {
    Write-Host "  [异常] 报告接口不通 -> $($_.Exception.Message)" -ForegroundColor Yellow
    $ok = $false
}

Write-Host ''
Write-Host '=== 前端 ===' -ForegroundColor Cyan
try {
    $null = Invoke-WebRequest 'http://localhost:5173' -TimeoutSec 3 -UseBasicParsing
    Write-Host '  [OK]   前端在跑：http://localhost:5173' -ForegroundColor Green
} catch {
    Write-Host '  [停]   前端没在跑 -> .\scripts\start-frontend.ps1' -ForegroundColor Yellow
    $ok = $false
}

Write-Host ''
if ($ok) {
    Write-Host '  全部就绪' -ForegroundColor Green
    Write-Host '  后端接口文档  http://localhost:8000/docs' -ForegroundColor Green
    Write-Host '  前端页面      http://localhost:5173' -ForegroundColor Green
} else {
    Write-Host '  有问题，按上面的提示处理' -ForegroundColor Yellow
}
Write-Host ''
