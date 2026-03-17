"""
打包脚本 - Python版本
用于将误判统计小程序打包成可执行文件
"""
import os
import sys
import subprocess
import io

# 设置标准输出编码为UTF-8，避免Windows GBK编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_and_install_package(package_name, import_name=None):
    """检查并安装包"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"[OK] {package_name} 已安装")
        return True
    except ImportError:
        print(f"[X] {package_name} 未安装，正在安装...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package_name,
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
            ])
            print(f"[OK] {package_name} 安装成功")
            return True
        except subprocess.CalledProcessError:
            print(f"[X] {package_name} 安装失败")
            return False

def clean_old_files():
    """清理旧的构建文件"""
    import shutil
    dirs_to_remove = ["build", "dist"]
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"[OK] 已清理 {dir_name} 目录")
            except Exception as e:
                print(f"[X] 清理 {dir_name} 失败: {e}")

def build_app():
    """执行打包"""
    print("\n" + "="*50)
    print("开始打包误判统计小程序")
    print("="*50 + "\n")
    
    # 1. 检查并安装依赖
    print("[1/3] 检查依赖包...")
    packages = [
        ("pyinstaller", "PyInstaller"),
        ("ttkbootstrap", "ttkbootstrap"),
        ("pillow", "PIL"),
        ("openpyxl", "openpyxl"),
    ]
    
    for package, import_name in packages:
        if not check_and_install_package(package, import_name):
            print(f"\n错误: 无法安装 {package}，请手动安装后重试")
            return False
    
    # 2. 清理旧文件
    print("\n[2/3] 清理旧文件...")
    clean_old_files()
    
    # 3. 执行打包
    print("\n[3/3] 开始打包 (需要 20-60 秒)...")
    print("-" * 50)
    
    # PyInstaller 命令参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "误判统计小程序",
        "--clean",
        "--noconfirm",
        "--hidden-import=ttkbootstrap",
        "--hidden-import=PIL",
        "--hidden-import=openpyxl",
        "--hidden-import=modules.barcode_searcher",
        "--hidden-import=modules.config_manager",
        "--hidden-import=modules.data_handler",
        "--hidden-import=modules.gui_manager",
        "--hidden-import=modules.image_loader",
        "--hidden-import=modules.statistics",
        "--hidden-import=utils.version_utils",
        "main.py"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "="*50)
        
        # 检查输出文件
        exe_path = os.path.join("dist", "误判统计小程序.exe")
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print("[OK] 打包成功！")
            print("="*50)
            print(f"\n输出文件: {exe_path}")
            print(f"文件大小: {file_size:.2f} MB")
            print("\n打包完成！")
            
            # 尝试打开文件夹
            try:
                import platform
                if platform.system() == "Windows":
                    os.startfile("dist")
            except:
                pass
            
            return True
        else:
            print("[X] 打包失败：未找到输出文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print("\n" + "="*50)
        print("[X] 打包失败")
        print("="*50)
        print(f"错误信息: {e}")
        return False

if __name__ == "__main__":
    try:
        success = build_app()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n打包已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
