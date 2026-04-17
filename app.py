#!/usr/bin/env python3
"""
网络设备巡检和配置备份软件 - 主程序
支持思科、华为、H3C、锐捷、DELL等厂商
"""

import os
import json
import time
import zipfile
import tempfile
import threading
import csv
import io
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, session, send_from_directory
from flask_cors import CORS
import netmiko
from netmiko import ConnectHandler
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import difflib
import hashlib

app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
app.secret_key = 'network-device-management-secret-key-2024'
CORS(app)

# 配置文件存储
CONFIG_DIR = Path("config_backups")
INSPECTION_DIR = Path("inspection_reports")
TEMPLATE_DIR = Path("templates")
CONFIG_DIR.mkdir(exist_ok=True)
INSPECTION_DIR.mkdir(exist_ok=True)
TEMPLATE_DIR.mkdir(exist_ok=True)

# 设备厂商映射
DEVICE_TYPES = {
    'cisco': 'cisco_ios',
    'huawei': 'huawei',
    'h3c': 'hp_comware',
    'ruijie': 'ruijie_os',
    'dell': 'dell_os10',
    'juniper': 'juniper_junos',
    'arista': 'arista_eos'
}

# 默认巡检命令
DEFAULT_INSPECTION_COMMANDS = {
    'cisco': [
        ('show version', '设备版本信息'),
        ('show running-config', '运行配置'),
        ('show interfaces status', '接口状态'),
        ('show ip interface brief', 'IP接口摘要'),
        ('show cdp neighbors', 'CDP邻居'),
        ('show logging', '系统日志'),
        ('show processes cpu', 'CPU使用率'),
        ('show memory statistics', '内存使用率'),
        ('show environment', '环境状态')
    ],
    'huawei': [
        ('display version', '设备版本信息'),
        ('display current-configuration', '当前配置'),
        ('display interface brief', '接口摘要'),
        ('display ip interface brief', 'IP接口摘要'),
        ('display lldp neighbor', 'LLDP邻居'),
        ('display logbuffer', '日志缓冲区'),
        ('display cpu-usage', 'CPU使用率'),
        ('display memory-usage', '内存使用率'),
        ('display device', '设备信息')
    ],
    'h3c': [
        ('display version', '设备版本信息'),
        ('display current-configuration', '当前配置'),
        ('display interface brief', '接口摘要'),
        ('display ip interface brief', 'IP接口摘要'),
        ('display lldp neighbor-information', 'LLDP邻居信息'),
        ('display logbuffer', '日志缓冲区'),
        ('display cpu-usage', 'CPU使用率'),
        ('display memory', '内存使用率'),
        ('display device', '设备信息')
    ],
    'ruijie': [
        ('show version', '设备版本信息'),
        ('show running-config', '运行配置'),
        ('show interfaces status', '接口状态'),
        ('show ip interface brief', 'IP接口摘要'),
        ('show lldp neighbors', 'LLDP邻居'),
        ('show logging', '系统日志'),
        ('show processes cpu', 'CPU使用率'),
        ('show memory', '内存使用率')
    ],
    'dell': [
        ('show version', '设备版本信息'),
        ('show running-config', '运行配置'),
        ('show interfaces status', '接口状态'),
        ('show ip interface brief', 'IP接口摘要'),
        ('show lldp neighbors', 'LLDP邻居'),
        ('show logging', '系统日志'),
        ('show processes cpu', 'CPU使用率'),
        ('show memory', '内存使用率')
    ]
}

class DeviceManager:
    """设备管理类"""
    
    def __init__(self):
        self.devices = {}
        self.load_devices()
    
    def load_devices(self):
        """加载设备列表"""
        try:
            if os.path.exists('devices.json'):
                with open('devices.json', 'r', encoding='utf-8') as f:
                    self.devices = json.load(f)
        except:
            self.devices = {}
    
    def save_devices(self):
        """保存设备列表"""
        with open('devices.json', 'w', encoding='utf-8') as f:
            json.dump(self.devices, f, ensure_ascii=False, indent=2)
    
    def add_device(self, name, ip, vendor, username, password, port=22):
        """添加设备"""
        device_id = hashlib.md5(f"{ip}:{port}".encode()).hexdigest()[:8]
        self.devices[device_id] = {
            'id': device_id,
            'name': name,
            'ip': ip,
            'vendor': vendor,
            'username': username,
            'password': password,
            'port': port,
            'created_at': datetime.now().isoformat()
        }
        self.save_devices()
        return device_id
    
    def batch_import_devices(self, devices_data):
        """批量导入设备"""
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for idx, device_data in enumerate(devices_data, 1):
            try:
                # 验证必要字段
                required_fields = ['name', 'ip', 'vendor', 'username', 'password']
                for field in required_fields:
                    if field not in device_data or not device_data[field]:
                        raise ValueError(f"缺少必要字段: {field}")
                
                # 添加设备
                device_id = self.add_device(
                    name=device_data['name'],
                    ip=device_data['ip'],
                    vendor=device_data['vendor'],
                    username=device_data['username'],
                    password=device_data['password'],
                    port=int(device_data.get('port', 22))
                )
                
                results['success'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"第{idx}行: {str(e)}")
        
        return results
    
    def remove_device(self, device_id):
        """删除设备"""
        if device_id in self.devices:
            del self.devices[device_id]
            self.save_devices()
            return True
        return False
    
    def get_device(self, device_id):
        """获取设备信息"""
        return self.devices.get(device_id)
    
    def get_all_devices(self):
        """获取所有设备"""
        return list(self.devices.values())

class NetworkDevice:
    """网络设备连接类"""
    
    def __init__(self, device_info):
        self.device_info = device_info
        self.connection = None
    
    def connect(self):
        """连接到设备"""
        try:
            device_params = {
                'device_type': DEVICE_TYPES.get(self.device_info['vendor'], 'cisco_ios'),
                'host': self.device_info['ip'],
                'username': self.device_info['username'],
                'password': self.device_info['password'],
                'port': self.device_info.get('port', 22),
                'timeout': 30,
                'secret': self.device_info.get('enable_password', ''),
                'verbose': False
            }
            
            self.connection = ConnectHandler(**device_params)
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def disconnect(self):
        """断开连接"""
        if self.connection:
            self.connection.disconnect()
            self.connection = None
    
    def execute_command(self, command):
        """执行命令"""
        try:
            if not self.connection:
                success, message = self.connect()
                if not success:
                    return False, message
            
            output = self.connection.send_command(command, delay_factor=2)
            return True, output
        except Exception as e:
            return False, f"执行命令失败: {str(e)}"
    
    def backup_config(self):
        """备份配置"""
        try:
            if not self.connection:
                success, message = self.connect()
                if not success:
                    return False, message
            
            # 获取配置
            if self.device_info['vendor'] in ['huawei', 'h3c']:
                config = self.connection.send_command('display current-configuration')
            else:
                config = self.connection.send_command('show running-config')
            
            # 保存配置
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.device_info['ip']}_{timestamp}.cfg"
            filepath = CONFIG_DIR / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(config)
            
            return True, {
                'filename': filename,
                'filepath': str(filepath),
                'config': config[:500] + "..." if len(config) > 500 else config
            }
        except Exception as e:
            return False, f"备份配置失败: {str(e)}"

def create_inspection_report(device_info, inspection_results, output_path):
    """创建巡检报告Word文档"""
    doc = Document()
    
    # 标题
    title = doc.add_heading('网络设备巡检报告', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 基本信息
    doc.add_heading('设备基本信息', level=1)
    
    info_table = doc.add_table(rows=4, cols=2)
    info_table.style = 'Light Grid Accent 1'
    
    info_table.cell(0, 0).text = '设备名称'
    info_table.cell(0, 1).text = device_info.get('name', 'N/A')
    info_table.cell(1, 0).text = '设备IP'
    info_table.cell(1, 1).text = device_info.get('ip', 'N/A')
    info_table.cell(2, 0).text = '设备厂商'
    info_table.cell(2, 1).text = device_info.get('vendor', 'N/A')
    info_table.cell(3, 0).text = '巡检时间'
    info_table.cell(3, 1).text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 巡检结果
    doc.add_heading('巡检结果', level=1)
    
    for result in inspection_results:
        doc.add_heading(f"巡检项目: {result['description']}", level=2)
        doc.add_paragraph(f"执行命令: {result['command']}")
        
        if result['success']:
            status_para = doc.add_paragraph("状态: ")
            status_run = status_para.add_run("成功")
            status_run.font.color.rgb = RGBColor(0, 128, 0)  # 绿色
        else:
            status_para = doc.add_paragraph("状态: ")
            status_run = status_para.add_run("失败")
            status_run.font.color.rgb = RGBColor(255, 0, 0)  # 红色
        
        # 输出结果
        doc.add_heading('输出结果:', level=3)
        output_para = doc.add_paragraph(result['output'][:1000])
        output_para.style = 'Normal'
        
        doc.add_page_break()
    
    # 保存文档
    doc.save(output_path)
    return output_path

def compare_configs(config1, config2):
    """比较两个配置文件"""
    lines1 = config1.splitlines()
    lines2 = config2.splitlines()
    
    diff = difflib.unified_diff(
        lines1, lines2,
        fromfile='config1',
        tofile='config2',
        lineterm=''
    )
    
    diff_lines = list(diff)
    
    # 分析差异
    added = []
    removed = []
    
    for line in diff_lines:
        if line.startswith('+') and not line.startswith('+++'):
            added.append(line[1:])
        elif line.startswith('-') and not line.startswith('---'):
            removed.append(line[1:])
    
    return {
        'diff': '\n'.join(diff_lines),
        'added': added,
        'removed': removed,
        'total_changes': len(added) + len(removed)
    }

def create_import_template():
    """创建导入模板文件"""
    template_content = """设备名称,IP地址,设备厂商,用户名,密码,端口
核心交换机-1,192.168.1.1,cisco,admin,password,22
接入交换机-1,192.168.1.2,huawei,admin,password,22
防火墙-1,192.168.1.3,h3c,admin,password,22
路由器-1,192.168.1.4,ruijie,admin,password,22
服务器交换机,192.168.1.5,dell,admin,password,22

说明：
1. 设备厂商可选值：cisco, huawei, h3c, ruijie, dell, juniper, arista
2. 端口默认为22，如不填写则使用默认值
3. 所有字段均为必填（端口除外）
4. 请使用UTF-8编码保存文件
5. 支持.csv和.xlsx格式
"""
    
    # 创建CSV模板
    csv_data = [
        ['设备名称', 'IP地址', '设备厂商', '用户名', '密码', '端口'],
        ['核心交换机-1', '192.168.1.1', 'cisco', 'admin', 'password', '22'],
        ['接入交换机-1', '192.168.1.2', 'huawei', 'admin', 'password', '22'],
        ['防火墙-1', '192.168.1.3', 'h3c', 'admin', 'password', '22'],
        ['路由器-1', '192.168.1.4', 'ruijie', 'admin', 'password', '22'],
        ['服务器交换机', '192.168.1.5', 'dell', 'admin', 'password', '22']
    ]
    
    template_path = TEMPLATE_DIR / "device_import_template.csv"
    with open(template_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    
    return template_path

# API路由
@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/compare')
def compare_page():
    """配置对比页面"""
    return render_template('compare.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """获取所有设备"""
    manager = DeviceManager()
    return jsonify({
        'success': True,
        'devices': manager.get_all_devices()
    })

@app.route('/api/devices', methods=['POST'])
def add_device():
    """添加设备"""
    data = request.json
    manager = DeviceManager()
    
    device_id = manager.add_device(
        name=data['name'],
        ip=data['ip'],
        vendor=data['vendor'],
        username=data['username'],
        password=data['password'],
        port=data.get('port', 22)
    )
    
    return jsonify({
        'success': True,
        'device_id': device_id,
        'message': '设备添加成功'
    })

@app.route('/api/devices/batch-import', methods=['POST'])
def batch_import_devices():
    """批量导入设备"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有上传文件'
            })
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            })
        
        # 读取CSV文件
        content = file.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(content))
        
        devices_data = []
        for row in csv_reader:
            devices_data.append({
                'name': row.get('设备名称', '').strip(),
                'ip': row.get('IP地址', '').strip(),
                'vendor': row.get('设备厂商', '').strip().lower(),
                'username': row.get('用户名', '').strip(),
                'password': row.get('密码', '').strip(),
                'port': row.get('端口', '22').strip()
            })
        
        # 导入设备
        manager = DeviceManager()
        results = manager.batch_import_devices(devices_data)
        
        return jsonify({
            'success': True,
            'message': f'批量导入完成，成功: {results["success"]}, 失败: {results["failed"]}',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'导入失败: {str(e)}'
        })

@app.route('/api/template/download')
def download_template():
    """下载导入模板"""
    template_path = create_import_template()
    return send_file(template_path, as_attachment=True, download_name='device_import_template.csv')

@app.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    manager = DeviceManager()
    success = manager.remove_device(device_id)
    
    return jsonify({
        'success': success,
        'message': '设备删除成功' if success else '设备不存在'
    })

@app.route('/api/inspection/commands', methods=['GET'])
def get_inspection_commands():
    """获取巡检命令"""
    vendor = request.args.get('vendor', 'cisco')
    commands = DEFAULT_INSPECTION_COMMANDS.get(vendor, DEFAULT_INSPECTION_COMMANDS['cisco'])
    
    return jsonify({
        'success': True,
        'commands': commands
    })

@app.route('/api/inspection/execute', methods=['POST'])
def execute_inspection():
    """执行巡检"""
    data = request.json
    device_id = data['device_id']
    commands = data['commands']
    
    manager = DeviceManager()
    device_info = manager.get_device(device_id)
    
    if not device_info:
        return jsonify({
            'success': False,
            'message': '设备不存在'
        })
    
    device = NetworkDevice(device_info)
    results = []
    
    for cmd, desc in commands:
        success, output = device.execute_command(cmd)
        results.append({
            'command': cmd,
            'description': desc,
            'success': success,
            'output': output
        })
    
    device.disconnect()
    
    # 生成报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{device_info['name']}_{device_info['ip']}_{timestamp}.docx"
    report_path = INSPECTION_DIR / report_filename
    
    create_inspection_report(device_info, results, report_path)
    
    return jsonify({
        'success': True,
        'results': results,
        'report_url': f'/api/reports/download/{report_filename}'
    })

@app.route('/api/backup', methods=['POST'])
def backup_config():
    """备份配置"""
    data = request.json
    device_id = data['device_id']
    
    manager = DeviceManager()
    device_info = manager.get_device(device_id)
    
    if not device_info:
        return jsonify({
            'success': False,
            'message': '设备不存在'
        })
    
    device = NetworkDevice(device_info)
    success, result = device.backup_config()
    device.disconnect()
    
    if success:
        return jsonify({
            'success': True,
            'message': '配置备份成功',
            'data': result
        })
    else:
        return jsonify({
            'success': False,
            'message': result
        })

@app.route('/api/backup/list', methods=['GET'])
def list_backups():
    """列出所有备份"""
    backups = []
    
    for file in CONFIG_DIR.glob("*.cfg"):
        stats = file.stat()
        backups.append({
            'filename': file.name,
            'path': str(file),
            'size': stats.st_size,
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'device_ip': file.name.split('_')[0]
        })
    
    return jsonify({
        'success': True,
        'backups': sorted(backups, key=lambda x: x['modified'], reverse=True)
    })

@app.route('/api/backup/package', methods=['POST'])
def package_backups():
    """打包备份文件"""
    data = request.json
    selected_files = data.get('files', [])
    
    if not selected_files:
        # 打包当天所有备份
        today = datetime.now().strftime("%Y%m%d")
        selected_files = [f.name for f in CONFIG_DIR.glob(f"*_{today}*.cfg")]
    
    if not selected_files:
        return jsonify({
            'success': False,
            'message': '没有找到备份文件'
        })
    
    # 创建ZIP文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"config_backup_{timestamp}.zip"
    zip_path = CONFIG_DIR / zip_filename
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in selected_files:
            filepath = CONFIG_DIR / filename
            if filepath.exists():
                zipf.write(filepath, filename)
    
    return jsonify({
        'success': True,
        'message': '打包成功',
        'zip_url': f'/api/backup/download/{zip_filename}'
    })

@app.route('/api/compare', methods=['POST'])
def compare_config():
    """比较配置文件"""
    data = request.json
    
    config1 = data.get('config1', '')
    config2 = data.get('config2', '')
    
    if not config1 or not config2:
        return jsonify({
            'success': False,
            'message': '需要两个配置文件进行比较'
        })
    
    result = compare_configs(config1, config2)
    
    return jsonify({
        'success': True,
        'result': result
    })

@app.route('/api/reports/download/<filename>')
def download_report(filename):
    """下载巡检报告"""
    filepath = INSPECTION_DIR / filename
    if filepath.exists():
        return send_file(filepath, as_attachment=True)
    return jsonify({'success': False, 'message': '文件不存在'}), 404

@app.route('/api/backup/download/<filename>')
def download_backup(filename):
    """下载备份文件"""
    filepath = CONFIG_DIR / filename
    if filepath.exists():
        return send_file(filepath, as_attachment=True)
    return jsonify({'success': False, 'message': '文件不存在'}), 404

@app.route('/api/backup/read/<filename>')
def read_backup(filename):
    """读取备份文件内容"""
    filepath = CONFIG_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'success': True,
            'content': content
        })
    return jsonify({'success': False, 'message': '文件不存在'}), 404

if __name__ == '__main__':
    print("网络设备巡检和配置备份软件启动中...")
    print(f"访问地址: https://localhost:8443")
    print("配置对比页面: https://localhost:8443/compare")
    print("按 Ctrl+C 停止服务")
    
    # 使用waitress作为生产服务器
    from waitress import serve
    serve(app, host='0.0.0.0', port=8443)
