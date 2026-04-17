@echo off
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
echo 请打开浏览器访问: http://localhost:8443
echo 按 Ctrl+C 停止程序
echo.

python app.py

pause
