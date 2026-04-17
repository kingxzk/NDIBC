#!/usr/bin/env python3
"""
打包为EXE可执行文件的脚本
注意：由于WebContainer限制，此脚本仅供参考
在实际环境中需要使用PyInstaller等工具打包
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    try:
        import PyInstaller
        return True
    except ImportError:
        print("未安装PyInstaller，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            return True
        except:
            print("安装PyInstaller失败，请手动安装：")
            print("pip install pyinstaller")
            return False

def create_spec_file():
    """创建PyInstaller spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('requirements.txt', '.'),
        ('README.md', '.')
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'netmiko',
        'docx',
        'paramiko',
        'cryptography',
        'waitress',
        'jinja2'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NetworkDeviceManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

# 如果需要单文件，取消注释下面的配置
# exe = EXE(
#     pyz,
#     a.scripts,
#     [],
#     exclude_binaries=True,
#     name='NetworkDeviceManager',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     console=False,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     icon='icon.ico' if os.path.exists('icon.ico') else None,
# )
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='NetworkDeviceManager',
# )
'''
    
    with open('network_device_manager.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("已创建 spec 文件")

def build_exe():
    """构建EXE文件"""
    print("开始构建EXE可执行文件...")
    
    # 创建必要的目录
    Path("dist").mkdir(exist_ok=True)
    Path("build").mkdir(exist_ok=True)
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=NetworkDeviceManager",
        "--onefile",
        "--windowed",
        "--add-data=templates;templates",
        "--add-data=static;static",
        "--hidden-import=flask",
        "--hidden-import=flask_cors",
        "--hidden-import=netmiko",
        "--hidden-import=docx",
        "--hidden-import=paramiko",
        "--hidden-import=cryptography",
        "--hidden-import=waitress",
        "--hidden-import=jinja2",
        "app.py"
    ]
    
    # 如果有图标文件，添加图标参数
    if os.path.exists("icon.ico"):
        cmd.append("--icon=icon.ico")
    
    try:
        print("执行构建命令...")
        subprocess.run(cmd, check=True)
        print("构建成功！")
        
        # 复制必要的文件到dist目录
        dist_dir = Path("dist")
        if dist_dir.exists():
            # 创建配置文件目录
            (dist_dir / "config_backups").mkdir(exist_ok=True)
            (dist_dir / "inspection_reports").mkdir(exist_ok=True)
            
            # 复制说明文件
            shutil.copy("README.md", dist_dir / "README.md")
            shutil.copy("requirements.txt", dist_dir / "requirements.txt")
            
            print(f"\nEXE文件已生成在: {dist_dir / 'NetworkDeviceManager.exe'}")
            print("\n使用说明:")
            print("1. 双击 NetworkDeviceManager.exe 运行程序")
            print("2. 打开浏览器访问: https://localhost:8443")
            print("3. 按 Ctrl+C 停止程序")
            
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

def create_installer_script():
    """创建安装脚本"""
    install_script = '''@echo off
echo 网络设备巡检和配置备份软件安装程序
echo ====================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 未检测到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo 未检测到pip，请确保Python安装正确
    pause
    exit /b 1
)

echo 正在安装依赖...
pip install -r requirements.txt

if errorlevel 1 (
    echo 依赖安装失败，请手动安装:
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

echo 依赖安装完成!
echo.
echo 启动程序...
echo 请打开浏览器访问: https://localhost:8443
echo 按 Ctrl+C 停止程序
echo.

python app.py

pause
'''
    
    with open('install.bat', 'w', encoding='gbk') as f:
        f.write(install_script)
    
    print("已创建Windows安装脚本: install.bat")

def main():
    """主函数"""
    print("网络设备巡检和配置备份软件 - EXE打包工具")
    print("=" * 50)
    
    # 检查当前目录结构
    required_files = ['app.py', 'templates/index.html', 'requirements.txt']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("缺少必要文件:")
        for file in missing_files:
            print(f"  - {file}")
        print("\n请确保所有文件都存在后再打包。")
        return
    
    print("1. 创建Windows安装脚本")
    print("2. 打包为EXE可执行文件")
    print("3. 退出")
    
    choice = input("\n请选择操作 (1-3): ").strip()
    
    if choice == '1':
        create_installer_script()
        print("\n安装脚本已创建: install.bat")
        print("使用方法:")
        print("1. 双击 install.bat 运行安装程序")
        print("2. 程序将自动安装依赖并启动")
        
    elif choice == '2':
        if check_dependencies():
            create_spec_file()
            build_exe()
        else:
            print("无法继续打包，请先安装PyInstaller")
            
    elif choice == '3':
        print("退出")
    else:
        print("无效选择")

if __name__ == "__main__":
    main()
