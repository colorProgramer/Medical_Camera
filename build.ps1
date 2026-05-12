# Medical Camera 打包脚本 (PowerShell)
# 确保已安装 pyinstaller: pip install pyinstaller

Write-Host "正在开始打包流程..." -ForegroundColor Cyan

# 1. 清理旧的构建文件
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# 2. 执行打包指令
# --onefile: 打包成单个 EXE
# --noconsole: 运行时不显示黑窗口
# --add-data: 包含资源文件 (格式: "源目录;目标目录")
# --icon: 程序图标
pyinstaller --onefile --noconsole `
    --name "MedicalCamera" `
    --icon "assets/branding/icon.ico" `
    --add-data "assets;assets" `
    --add-data "native/bin;native/bin" `
    --clean `
    main.py

Write-Host "`n打包完成！" -ForegroundColor Green
Write-Host "EXE 文件位于: dist/MedicalCamera.exe" -ForegroundColor Yellow
Write-Host "您可以将此文件发送到其他电脑直接运行。" -ForegroundColor White
