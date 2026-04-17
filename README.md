# NDIBC
Network Device Inspection-Backup-Compare Tools (网络设备巡检、配置备份、配置对比工具)
基于Python Flask和Netmiko开发的网络设备管理平台，支持多厂商设备巡检、配置备份和配置对比功能。

## 功能特性

### 1. 设备管理
- 支持添加、删除网络设备
- 支持思科、华为、H3C、锐捷、DELL、Juniper、Arista等厂商

### 2. 设备巡检
- 预置各厂商常用巡检命令
- 支持自定义巡检命令
- 实时显示巡检过程
- 自动生成Word格式巡检报告
- 报告包含设备信息、巡检项目和结果

### 3. 配置备份
- 自动备份设备配置
- 支持批量打包备份文件

### 4. 配置对比
- 支持选择历史备份文件对比
- 支持手动输入配置对比
- 差异高亮显示（新增绿色，删除红色）

## 系统要求

- Python 3.8+
- 网络设备支持SSH访问
- 现代浏览器（Chrome、Firefox、Edge等）

## 安装和运行

### 1. 安装运行

windows系统直接运行 install&run.bat 即可自动安装程序所需要得组件，自动运行程序弹出web页面

### 2. 程序打包

为了方便日后使用，运行 build_exe.py，按照选项即可将程序打包成exe程序，放到其他windows上直接运行即可 

### 3. 访问系统

（一般情况下无需手动输入，自动弹出）http://localhost:8443

## 软件界面

<img width="830" height="874" alt="002" src="https://github.com/user-attachments/assets/b8102ac1-72db-4c96-ba09-f282f3eb3464" />
<img width="826" height="865" alt="001" src="https://github.com/user-attachments/assets/a7ddc222-9b9d-42e5-9d8d-0c19cc75cb2f" />
<img width="816" height="869" alt="004" src="https://github.com/user-attachments/assets/ce371f16-6e83-4b56-ade9-80414b837ede" />
<img width="865" height="563" alt="003" src="https://github.com/user-attachments/assets/b8301615-b323-4e22-be91-f835ef06d5cd" />

