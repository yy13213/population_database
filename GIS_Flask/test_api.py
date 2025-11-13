"""
API测试脚本
快速测试所有API接口
"""

import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:5050"

def print_result(title, response):
    """打印测试结果"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")
    print(f"状态码: {response.status_code}")
    
    try:
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except:
        print(f"响应: {response.text}")
    
    print(f"耗时: {response.elapsed.total_seconds():.3f}秒")

def test_health():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL}/api/health")
    print_result("健康检查", response)
    return response.status_code == 200

def test_cache_info():
    """测试缓存信息"""
    response = requests.get(f"{BASE_URL}/api/cache/info")
    print_result("缓存信息", response)
    return response.status_code == 200

def test_population():
    """测试人口数据"""
    # 获取所有省份
    response = requests.get(f"{BASE_URL}/api/data/population")
    print_result("所有省份人口数据", response)
    
    # 获取特定省份
    response = requests.get(f"{BASE_URL}/api/data/population?province=广东")
    print_result("广东省人口数据", response)
    
    return response.status_code == 200

def test_density():
    """测试人口密度"""
    response = requests.get(f"{BASE_URL}/api/data/density")
    print_result("人口密度数据", response)
    return response.status_code == 200

def test_marriage():
    """测试婚姻数据"""
    response = requests.get(f"{BASE_URL}/api/data/marriage")
    print_result("婚姻数据", response)
    return response.status_code == 200

def test_migration():
    """测试迁移数据"""
    response = requests.get(f"{BASE_URL}/api/data/migration?limit=10")
    print_result("人口迁移数据（前10条）", response)
    return response.status_code == 200

def test_gender():
    """测试性别数据"""
    response = requests.get(f"{BASE_URL}/api/data/gender")
    print_result("性别统计数据", response)
    return response.status_code == 200

def test_age():
    """测试年龄数据"""
    response = requests.get(f"{BASE_URL}/api/data/age")
    print_result("年龄分布数据", response)
    return response.status_code == 200

def test_ethnicity():
    """测试民族数据"""
    response = requests.get(f"{BASE_URL}/api/data/ethnicity?province=广东")
    print_result("广东省民族数据", response)
    return response.status_code == 200

def test_summary():
    """测试汇总数据"""
    response = requests.get(f"{BASE_URL}/api/data/summary")
    print_result("汇总数据", response)
    return response.status_code == 200

def test_provinces():
    """测试省份列表"""
    response = requests.get(f"{BASE_URL}/api/provinces")
    print_result("省份列表", response)
    return response.status_code == 200

def test_all_data():
    """测试获取所有数据"""
    response = requests.get(f"{BASE_URL}/api/data/all")
    print_result("所有数据", response)
    return response.status_code == 200

def test_performance():
    """性能测试"""
    print(f"\n{'='*60}")
    print(f"⚡ 性能测试")
    print(f"{'='*60}")
    
    # 测试10次请求
    times = []
    for i in range(10):
        start = datetime.now()
        response = requests.get(f"{BASE_URL}/api/data/summary")
        elapsed = (datetime.now() - start).total_seconds()
        times.append(elapsed)
        print(f"第 {i+1} 次请求: {elapsed:.4f}秒")
    
    avg_time = sum(times) / len(times)
    print(f"\n平均响应时间: {avg_time:.4f}秒")
    print(f"最快: {min(times):.4f}秒")
    print(f"最慢: {max(times):.4f}秒")

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 Flask GIS API 测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {BASE_URL}")
    
    tests = [
        ("健康检查", test_health),
        ("缓存信息", test_cache_info),
        ("人口数据", test_population),
        ("人口密度", test_density),
        ("婚姻数据", test_marriage),
        ("迁移数据", test_migration),
        ("性别数据", test_gender),
        ("年龄数据", test_age),
        ("民族数据", test_ethnicity),
        ("汇总数据", test_summary),
        ("省份列表", test_provinces),
        ("所有数据", test_all_data)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} 测试失败: {str(e)}")
            results.append((name, False))
    
    # 性能测试
    try:
        test_performance()
    except Exception as e:
        print(f"\n❌ 性能测试失败: {str(e)}")
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    failed = total - passed
    
    print(f"\n总计: {total} 个测试")
    print(f"✅ 通过: {passed} 个")
    print(f"❌ 失败: {failed} 个")
    print(f"通过率: {passed/total*100:.1f}%")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 测试中断")
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器")
        print("💡 请确保Flask服务已启动：python app.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")


