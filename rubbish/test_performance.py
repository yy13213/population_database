#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能对比测试：MEMORY vs InnoDB
测试不同存储引擎下的查询性能
"""
import sys
import os
import time

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GIS.data_statistics import PopulationStatistics


class PerformanceTest:
    """性能测试类"""
    
    def __init__(self):
        self.results = []
    
    def test_query(self, name, func, *args):
        """
        测试单个查询性能
        """
        start_time = time.time()
        result = func(*args)
        duration = time.time() - start_time
        
        # 获取结果大小
        if isinstance(result, dict):
            size = len(result)
        elif isinstance(result, list):
            size = len(result)
        else:
            size = 0
        
        return duration, size
    
    def run_tests(self, use_memory):
        """
        运行所有测试
        """
        engine_name = "MEMORY" if use_memory else "InnoDB"
        print(f"\n{'='*60}")
        print(f"🧪 测试 {engine_name} 引擎性能")
        print(f"{'='*60}")
        
        # 初始化统计类
        stats = PopulationStatistics(use_memory_tables=use_memory)
        
        if not stats.connect():
            print("❌ 数据库连接失败")
            return None
        
        test_cases = [
            ("人口统计", stats.get_province_population),
            ("人口密度", stats.get_province_density),
            ("婚姻统计", stats.get_marriage_statistics),
            ("人口迁移", stats.get_migration_statistics),
            ("性别统计", stats.get_gender_statistics),
            ("年龄分布", stats.get_age_distribution),
            ("民族统计", stats.get_ethnicity_statistics),
        ]
        
        results = []
        
        for name, func in test_cases:
            print(f"\n📊 测试: {name}")
            
            # 预热（第一次查询可能较慢）
            func()
            
            # 实际测试（执行3次取平均）
            times = []
            for i in range(3):
                duration, size = self.test_query(name, func)
                times.append(duration)
                print(f"   第{i+1}次: {duration*1000:.2f} ms")
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            results.append({
                'name': name,
                'avg': avg_time,
                'min': min_time,
                'max': max_time,
                'size': size
            })
            
            print(f"   ✅ 平均: {avg_time*1000:.2f} ms | 数据量: {size}")
        
        stats.close()
        
        return results
    
    def compare_results(self, innodb_results, memory_results):
        """
        对比两种引擎的结果
        """
        print(f"\n{'='*60}")
        print("📈 性能对比分析")
        print(f"{'='*60}")
        print(f"\n{'测试项':<12} | {'InnoDB':<12} | {'MEMORY':<12} | {'提升':<10}")
        print("-" * 60)
        
        total_speedup = 0
        
        for innodb, memory in zip(innodb_results, memory_results):
            speedup = innodb['avg'] / memory['avg'] if memory['avg'] > 0 else 0
            total_speedup += speedup
            
            print(f"{innodb['name']:<12} | "
                  f"{innodb['avg']*1000:>10.2f}ms | "
                  f"{memory['avg']*1000:>10.2f}ms | "
                  f"{speedup:>8.1f}x")
        
        avg_speedup = total_speedup / len(innodb_results)
        
        print("-" * 60)
        print(f"{'平均提升':<12} | {'':>12} | {'':>12} | {avg_speedup:>8.1f}x")
        print(f"{'='*60}\n")
        
        # 总结
        print("📊 测试总结:")
        print(f"   - 测试项目数: {len(innodb_results)}")
        print(f"   - 平均提升: {avg_speedup:.1f} 倍")
        print(f"   - 最大提升: {max(innodb['avg']/memory['avg'] for innodb, memory in zip(innodb_results, memory_results)):.1f} 倍")
        print(f"   - 最小提升: {min(innodb['avg']/memory['avg'] for innodb, memory in zip(innodb_results, memory_results)):.1f} 倍")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 内存数据库性能对比测试")
    print("="*60)
    print("\n⚠️  注意: 此测试需要已同步数据到内存表")
    print("   如未同步，请先运行: python sync_to_memory.py\n")
    
    input("按回车键开始测试...")
    
    tester = PerformanceTest()
    
    # 测试 InnoDB
    print("\n" + "="*60)
    print("第一阶段: 测试 InnoDB 引擎（磁盘表）")
    print("="*60)
    innodb_results = tester.run_tests(use_memory=False)
    
    if not innodb_results:
        print("❌ InnoDB 测试失败")
        return
    
    print("\n⏸️  暂停5秒...")
    time.sleep(5)
    
    # 测试 MEMORY
    print("\n" + "="*60)
    print("第二阶段: 测试 MEMORY 引擎（内存表）")
    print("="*60)
    memory_results = tester.run_tests(use_memory=True)
    
    if not memory_results:
        print("❌ MEMORY 测试失败")
        return
    
    # 对比结果
    tester.compare_results(innodb_results, memory_results)
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试已取消")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

