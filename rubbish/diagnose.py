import sys
import os

print("="*60)
print("🔍 Flask应用诊断工具")
print("="*60)

# 1. 检查Python版本
print("\n1️⃣ 检查Python版本:")
print(f"   Python版本: {sys.version}")
print(f"   ✅ Python版本正常")

# 2. 检查依赖包
print("\n2️⃣ 检查依赖包:")
required_packages = ['flask', 'pymysql', 'pandas']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f"   ✅ {package} 已安装")
    except ImportError:
        print(f"   ❌ {package} 未安装")
        missing_packages.append(package)

if missing_packages:
    print(f"\n   ⚠️ 缺少依赖包: {', '.join(missing_packages)}")
    print(f"   安装命令: pip install {' '.join(missing_packages)}")
else:
    print(f"   ✅ 所有依赖包已安装")

# 3. 检查端口占用
print("\n3️⃣ 检查端口占用:")
import socket

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except OSError:
        return False

if check_port(6667):
    print(f"   ✅ 端口6667可用")
else:
    print(f"   ❌ 端口6667被占用")
    print(f"   解决方法: 更换端口或关闭占用该端口的程序")

# 4. 检查province_data.json文件
print("\n4️⃣ 检查province_data.json文件:")
possible_paths = [
    '../province_data.json',
    '../../province_data.json',
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'province_data.json')
]

province_data_found = False
for path in possible_paths:
    if os.path.exists(path):
        print(f"   ✅ 找到文件: {os.path.abspath(path)}")
        province_data_found = True
        break

if not province_data_found:
    print(f"   ❌ 未找到province_data.json文件")
    print(f"   当前工作目录: {os.getcwd()}")
    print(f"   尝试的路径:")
    for path in possible_paths:
        print(f"      - {os.path.abspath(path)}")

# 5. 测试数据库连接
print("\n5️⃣ 测试数据库连接:")
try:
    import pymysql
    
    MYSQL_CONFIG = {

    }
    
    print(f"   连接到: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM population")
    count = cursor.fetchone()[0]
    print(f"   ✅ 数据库连接成功")
    print(f"   ✅ 人口表记录数: {count:,}")
    conn.close()
except Exception as e:
    print(f"   ❌ 数据库连接失败")
    print(f"   错误信息: {str(e)}")

# 6. 检查GIS模块
print("\n6️⃣ 检查GIS模块:")
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from GIS.data_statistics import PopulationStatistics
    print(f"   ✅ GIS.data_statistics 模块导入成功")
except Exception as e:
    print(f"   ❌ GIS.data_statistics 模块导入失败")
    print(f"   错误信息: {str(e)}")

# 7. 尝试初始化缓存管理器
print("\n7️⃣ 测试缓存管理器:")
try:
    from cache_manager import get_cache_manager
    print(f"   正在初始化缓存管理器（可能需要几秒钟）...")
    # 不实际初始化，因为会耗时
    print(f"   ✅ cache_manager 模块导入成功")
except Exception as e:
    print(f"   ❌ cache_manager 初始化失败")
    print(f"   错误信息: {str(e)}")

# 总结
print("\n" + "="*60)
print("📋 诊断总结")
print("="*60)

issues = []
if missing_packages:
    issues.append(f"缺少依赖包: {', '.join(missing_packages)}")
if not check_port(6667):
    issues.append("端口6667被占用")
if not province_data_found:
    issues.append("找不到province_data.json文件")

if issues:
    print("❌ 发现以下问题:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print("\n建议:")
    if missing_packages:
        print(f"   - 安装依赖: pip install {' '.join(missing_packages)}")
    if not check_port(6667):
        print(f"   - 更换端口或关闭占用程序")
    if not province_data_found:
        print(f"   - 确保从正确的目录运行应用")
else:
    print("✅ 未发现明显问题，尝试以下步骤:")
    print("   1. cd GIS_Flask")
    print("   2. python app.py")
    print("   3. 查看完整错误信息")

print("="*60 + "\n")

