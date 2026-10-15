<#
  scripts\setup.ps1 —— 一次性环境初始化

  做三件事：
      1. 建 .venv 虚拟环境
      2. 装后端依赖
      3. 装前端依赖

  换电脑 / 新队友上手，只需要跑这一个脚本。
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host ''
Write-Host '=== 1/3 检查 Python ===' -ForegroundColor Cyan
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host '  没找到 python，请先安装 Python 3.10+' -ForegroundColor Red
    exit 1
}
python --version

Write-Host ''
Write-Host '=== 2/3 建虚拟环境 + 装后端依赖 ===' -ForegroundColor Cyan

# 外部命令（pip / npm）会往 stderr 写进度和提示，
# 在 $ErrorActionPreference='Stop' 下，PowerShell 会把任何 stderr 输出
# 升级成 NativeCommandError 直接中断脚本 —— 哪怕 pip 本身是成功的。
# 所以调用外部命令期间一律放开，改为看退出码。
$ErrorActionPreference = 'Continue'

if (-not (Test-Path '.venv')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host '  创建 .venv 失败' -ForegroundColor Red
        exit 1
    }
    Write-Host '  .venv 已创建'
} else {
    Write-Host '  .venv 已存在，跳过创建'
}

& '.\.venv\Scripts\pip.exe' install -r requirements.txt --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    Write-Host "  装后端依赖失败（退出码 $LASTEXITCODE）" -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host '=== 3/3 装前端依赖 ===' -ForegroundColor Cyan
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    Write-Host '  没找到 npm，跳过前端。装了 Node.js 之后重跑本脚本。' -ForegroundColor Yellow
} else {
    npm --version
    Push-Location 'frontend'
    npm install
    $npmCode = $LASTEXITCODE
    Pop-Location
    if ($npmCode -ne 0) {
        Write-Host "  装前端依赖失败（退出码 $npmCode）" -ForegroundColor Red
        exit 1
    }
}

Write-Host ''
Write-Host '完成。接下来：' -ForegroundColor Green
Write-Host '  .\scripts\start-all.ps1        一键起前后端' -ForegroundColor White
Write-Host '  .\scripts\start-backend.ps1   只起后端 (8000)' -ForegroundColor White
Write-Host '  .\scripts\start-frontend.ps1  只起前端 (5173)' -ForegroundColor White
Write-Host ''
