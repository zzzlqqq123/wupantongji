@echo off
REM ========================================
REM Quick Build Script
REM ========================================

echo.
echo ========================================
echo    Building...
echo ========================================
echo.

REM Check and install dependencies
echo [Info] Checking dependencies...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [Info] Installing PyInstaller...
    python -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import ttkbootstrap" 2>nul
if errorlevel 1 (
    echo [Info] Installing ttkbootstrap...
    python -m pip install ttkbootstrap -i https://pypi.tuna.tsinghua.edu.cn/simple
)

python -c "import PIL" 2>nul
if errorlevel 1 (
    echo [Info] Installing Pillow...
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo [Info] Cleaning old files...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist" rmdir /s /q "dist" 2>nul

echo.
echo [Info] Starting build (20-60 seconds)...
echo.

REM Execute build - add hidden imports
python -m PyInstaller --onefile --windowed --name "MisjudgmentStats" --clean --noconfirm ^
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
if exist "dist\MisjudgmentStats.exe" (
    echo [Success] Build complete!
    echo ========================================
    echo.
    echo Output: dist\MisjudgmentStats.exe
    echo.
    start explorer dist
) else (
    echo [Failed] Build failed, check errors above
    echo ========================================
)

echo.
echo Press any key to close...
pause >nul
