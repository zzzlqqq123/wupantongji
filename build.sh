#!/bin/bash
# ========================================
# 误判统计小程序 - 打包脚本 (Linux/Mac)
# ========================================

echo ""
echo "========================================"
echo "   误判统计小程序 - 打包工具"
echo "========================================"
echo ""

# 检查PyInstaller是否安装
python -c "import PyInstaller" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[错误] 未安装PyInstaller，正在安装..."
    python -m pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "[错误] PyInstaller安装失败！"
        exit 1
    fi
fi

echo "[信息] 清理旧的打包文件..."
rm -rf build dist

echo ""
echo "[信息] 开始打包程序..."
echo ""

# 使用PyInstaller打包
python -m PyInstaller \
    --onefile \
    --windowed \
    --name "误判统计小程序" \
    --clean \
    --noconfirm \
    main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 打包失败！"
    exit 1
fi

echo ""
echo "========================================"
echo "[成功] 打包完成！"
echo "========================================"
echo ""
echo "可执行文件位置: dist/误判统计小程序"
echo ""
