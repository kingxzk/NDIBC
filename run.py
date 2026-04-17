#!/usr/bin/env python3
"""
网络设备巡检和配置备份软件 - 启动脚本
"""

import os
import sys
import time
import webbrowser
import threading
from datetime import datetime

def print_logo():
    """打印程序Logo"""
    logo = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     网络设备巡检和配置备份软件 v0.4                           ║
    ║     Network Device Inspection & Backup & Compare Tools       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    支持厂商: Cisco, 华为, H3C, 锐捷, DELL, Juniper, Arista
    功能模块: 设备管理, 设备巡检, 配置备份, 配置对比
    """
    print(logo)

def open_browser_delayed():
    """延迟打开浏览器"""
    time.sleep(3)  # 等待服务器启动
    url = "https://localhost:8443"
    
    try:
        webbrowser.open(url)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 已自动打开浏览器")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   访问地址: {url}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 无法自动打开浏览器: {e}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   请手动访问: {url}")

def main():
    """主函数"""
    # 设置控制台编码
    if sys.platform == 'win32':
        import ctypes
        # 设置控制台为UTF-8编码
        os.system('chcp 65001 > nul')
    
    # 打印Logo
    print_logo()
    
    print("=" * 70)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 程序启动中...")
    print("-" * 70)
    
    # 检查Python版本
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Python版本: {sys.version}")
    
    # 检查必要模块
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查依赖模块...")
    required_modules = ['flask', 'netmiko', 'docx', 'pandas', 'waitress']
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ✓ {module}")
        except ImportError as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}]   ✗ {module}: {e}")
            print(f            print(f"[{datetime.now().strftime('%H:%M:%S')}]   请安装: pip install {module}")
    
    print("-" * 70)
    
    # 启动浏览器线程
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 启动浏览器线程...")
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    # 导入并启动主程序
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 导入主程序模块...")
        from app import main as app_main
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 启动Web服务器...")
        print("-" * 70)
        
        # 运行主程序
        app_main()
        
    except ImportError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 导入主程序失败: {e}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 请确保所有依赖已安装")
        print("按任意键退出...")
        input()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 收到停止信号")
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✗ 程序运行错误: {e}")
        print("按任意键退出...")
        input()

if __name__ == '__main__':
    main()
