# ==========================================================
#  一键推送到 GitHub（从本脚本所在仓库的根目录操作）
#  用法：powershell -ExecutionPolicy Bypass -File .\push_to_github.ps1
#  默认目标：https://github.com/GaoYangHeng/XiaoYuanKouSuan-1s-Cheat.git
# ==========================================================
param(
    [string]$RepoUrl = "https://github.com/GaoYangHeng/XiaoYuanKouSuan-1s-Cheat.git"
)

$ErrorActionPreference = "Stop"

# 脚本位于 opensource/ 下，实际操作的是外层整个仓库
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

Write-Host "=========================================="
Write-Host " 推送到 GitHub"
Write-Host "=========================================="
Write-Host "仓库根: $RepoRoot"
Write-Host "目标: $RepoUrl"
Write-Host "注意: 将提交整个外层仓库（约 100+ MB，含 release APK）" -ForegroundColor Yellow

$confirm = Read-Host "确认推送？公开后不可撤回。(y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "已取消。"
    exit 0
}

# 1. 远端
Write-Host "[1/4] 配置远端 origin ..."
git remote remove origin 2>$null
git remote add origin $RepoUrl

# 2. 暂存 + 提交
Write-Host "[2/4] git add -A + commit ..."
git add -A
git commit -m "XiaoYuanKouSuan 1s auto-answer cheat: reverse engineering research notes, snippets and patched APK"

# 3. 分支
Write-Host "[3/4] 确保分支为 main ..."
git branch -M main

# 4. 推送（弹出凭据窗口时完成 GitHub 授权）
Write-Host "[4/4] 推送中 ..."
git push -u origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "推送失败。常见原因：仓库未创建 / 凭据被拒（需 Token 或浏览器授权）/ 网络问题。" -ForegroundColor Red
    exit 1
}

Write-Host "完成！访问: $($RepoUrl -replace '\.git$', '')"
