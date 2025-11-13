"""
安全启动脚本 - 带完整错误处理
"""

import sys
import os

print("="*60)
print("🚀 正在启动Flask GIS应用...")
print("="*60)

# 步骤1: 检查依赖
print("\n1️⃣ 检查依赖包...")
try:
    import flask
    import pymysql
    import pandas
    print("   ✅ 所有依赖包已安装")
except ImportError as e:
    print(f"   ❌ 缺少依赖包: {e}")
    print("   请运行: pip install -r requirements.txt")
    sys.exit(1)

# 步骤2: 检查端口
print("\n2️⃣ 检查端口...")
import socket
def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except OSError:
        return False

if not check_port(6667):
    print("   ⚠️ 端口6667被占用，尝试使用其他端口...")
    # 可以在这里添加逻辑使用其他端口
else:
    print("   ✅ 端口6667可用")

# 步骤3: 检查province_data.json
print("\n3️⃣ 检查数据文件...")
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
province_data_path = os.path.join(project_root, 'province_data.json')

if os.path.exists(province_data_path):
    print(f"   ✅ 找到province_data.json: {province_data_path}")
else:
    print(f"   ❌ 找不到province_data.json")
    print(f"   期望路径: {province_data_path}")
    sys.exit(1)

# 步骤4: 测试数据库连接
print("\n4️⃣ 测试数据库连接...")
try:
    MYSQL_CONFIG = {

    }
    
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM population")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"   ✅ 数据库连接成功 (人口: {count:,})")
except Exception as e:
    print(f"   ❌ 数据库连接失败: {e}")
    print("   应用可能无法正常工作，但仍会尝试启动...")

# 步骤5: 启动Flask应用
print("\n5️⃣ 启动Flask应用...")
print("="*60)

try:
    # 导入并启动app
    from app import app
    
    print("\n✅ 应用启动成功！")
    print(f"📍 访问地址: http://127.0.0.1:6667")
    print(f"💡 按 Ctrl+C 停止服务\n")
    print("="*60 + "\n")
    
    app.run(
        host='127.0.0.1',
        port=6667,
        debug=True,
        threaded=True
    )
except Exception as e:
    print(f"\n❌ 应用启动失败!")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    print("\n完整错误堆栈:")
    import traceback
    traceback.print_exc()
    print("\n" + "="*60)
    print("💡 建议:")
    print("   1. 运行诊断脚本: python diagnose.py")
    print("   2. 检查数据库连接")
    print("   3. 确认所有依赖已安装")
    print("="*60)
    sys.exit(1)

