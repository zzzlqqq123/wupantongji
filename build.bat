@echo off
chcp 65001 >nul
REM ========================================
REM 快速打包脚本
REM ========================================

echo.
echo ========================================
echo    正在打包...
echo ========================================
echo.

REM 检查并安装依赖
echo [提示] 检查依赖包...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [提示] 正在安装 PyInstaller...
    python -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import ttkbootstrap" 2>nul
if errorlevel 1 (
    echo [提示] 正在安装 ttkbootstrap...
    python -m pip install ttkbootstrap -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import PIL" 2>nul
if errorlevel 1 (
    echo [提示] 正在安装 Pillow...
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo [提示] 清理旧文件...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

echo.
echo [提示] 开始打包 (需要 20-60 秒)...
echo.

REM 执行打包 - 添加隐藏导入以确保所有模块都被包含
python -m PyInstaller --onefile --windowed --name "误判统计小程序" --clean --noconfirm ^
    --hidden-import=ttkbootstrap ^
    --hidden-import=PIL ^
    --hidden-import=openpyxl ^
    --hidden-import=modules.barcode_searcher ^
    --hidden-import=modules.config_manager ^
    --hidden-import=modules.data_handler ^
    --hidden-import=modules.gui_manager ^
    --hidden-import=modules.image_loader ^
    --hidden-import=modules.statistics ^
    --hidden-import=utils.version_utils ^
    main.py 2>&1

echo.
echo ========================================
if exist "dist\误判统计小程序.exe" (
    echo [成功] 打包完成！
    echo ========================================
    echo.
    echo 输出文件: dist\误判统计小程序.exe
    echo.
    start explorer dist
) else (
    echo [失败] 打包失败，请检查上方错误信息
    echo ========================================
)

echo.
echo 按任意键关闭...
pause >nul
