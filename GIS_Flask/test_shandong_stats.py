#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试山东省统计模块
"""
import sys
import time
from shandong_stats import ShandongStatistics

def test_statistics():
    """测试统计功能"""
    print("\n" + "="*60)
    print("🧪 测试山东省统计模块")
    print("="*60)
    
    stats = ShandongStatistics()
    
    # 测试总人口
    print("\n1️⃣ 测试总人口查询...")
    start = time.time()
    total = stats.get_total_population()
    duration = time.time() - start
    print(f"   ✅ 总人口: {total:,} (耗时: {duration:.2f}秒)")
    
    # 测试城市人口
    print("\n2️⃣ 测试城市人口查询...")
    start = time.time()
    cities = stats.get_city_population()
    duration = time.time() - start
    print(f"   ✅ 城市数: {len(cities)} (耗时: {duration:.2f}秒)")
    if cities:
        print(f"   📊 前5个城市:")
        for i, (city, count) in enumerate(list(cities.items())[:5]):
            print(f"      {i+1}. {city}: {count:,}")
    
    # 测试性别统计
    print("\n3️⃣ 测试性别统计查询...")
    start = time.time()
    gender = stats.get_gender_statistics()
    duration = time.time() - start
    print(f"   ✅ 性别统计: {gender} (耗时: {duration:.2f}秒)")
    
    # 测试年龄分布
    print("\n4️⃣ 测试年龄分布查询...")
    start = time.time()
    age = stats.get_age_distribution()
    duration = time.time() - start
    print(f"   ✅ 年龄分布: {age} (耗时: {duration:.2f}秒)")
    
    # 测试教育统计
    print("\n5️⃣ 测试教育统计查询...")
    start = time.time()
    education = stats.get_education_statistics()
    duration = time.time() - start
    print(f"   ✅ 教育统计: {len(education)} 种 (耗时: {duration:.2f}秒)")
    
    # 测试婚姻统计
    print("\n6️⃣ 测试婚姻统计查询...")
    start = time.time()
    marriage = stats.get_marriage_statistics()
    duration = time.time() - start
    print(f"   ✅ 婚姻统计: {marriage} (耗时: {duration:.2f}秒)")
    
    # 测试死亡统计
    print("\n7️⃣ 测试死亡统计查询...")
    start = time.time()
    death = stats.get_death_statistics()
    duration = time.time() - start
    print(f"   ✅ 死亡统计: {death} (耗时: {duration:.2f}秒)")
    
    # 测试收入统计
    print("\n8️⃣ 测试收入统计查询...")
    start = time.time()
    income = stats.get_income_statistics()
    duration = time.time() - start
    print(f"   ✅ 收入统计: {income} (耗时: {duration:.2f}秒)")
    
    # 测试民族统计
    print("\n9️⃣ 测试民族统计查询...")
    start = time.time()
    ethnicity = stats.get_ethnicity_statistics()
    duration = time.time() - start
    print(f"   ✅ 民族统计: {len(ethnicity)} 种 (耗时: {duration:.2f}秒)")
    
    # 测试迁移统计
    print("\n🔟 测试迁移统计查询...")
    start = time.time()
    migration = stats.get_migration_statistics()
    duration = time.time() - start
    print(f"   ✅ 迁移统计: {migration} (耗时: {duration:.2f}秒)")
    
    # 测试综合统计
    print("\n" + "="*60)
    print("📊 测试综合统计查询...")
    print("="*60)
    start = time.time()
    comprehensive = stats.get_comprehensive_statistics()
    duration = time.time() - start
    
    print(f"\n✅ 综合统计完成 (总耗时: {duration:.2f}秒)")
    print(f"   - 总人口: {comprehensive.get('total_population', 0):,}")
    print(f"   - 城市数: {len(comprehensive.get('city_population', {}))}")
    print(f"   - 婚姻记录: {comprehensive.get('marriage', {}).get('total', 0):,}")
    print(f"   - 死亡记录: {comprehensive.get('death', {}).get('total', 0):,}")
    
    stats.close()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60 + "\n")
    
    return comprehensive

if __name__ == '__main__':
    try:
        data = test_statistics()
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

