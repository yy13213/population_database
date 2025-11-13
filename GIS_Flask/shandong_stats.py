#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
山东省数据统计模块
直接从总表（population、population_deceased、marriage_info）查询统计数据
查询条件：hukou_province = '山东省' OR cur_province = '山东省'
"""
import pymysql
from typing import Dict, List
from datetime import datetime

# 数据库配置（使用磁盘表，不连接内存表）
MYSQL_CONFIG = {

}


class ShandongStatistics:
    """山东省统计分析类"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """连接数据库"""
        try:
            if self.connection and self.connection.open:
                self.connection.ping(reconnect=True)
                return True
            self.connection = pymysql.connect(**MYSQL_CONFIG)
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
    
    def execute_query(self, query: str, params=None, max_retries=3):
        """执行查询（带重试机制）"""
        cursor = None
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if not self.connect():
                    return []
                
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                return results
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ 查询失败（尝试{max_retries}次）: {e}")
                    return []
                print(f"⚠️ 查询失败 ({e}), 重试 {retry_count}/{max_retries}...")
                # 重新连接
                self.connection = None
                import time
                time.sleep(2)
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                    cursor = None
        
        return []
    
    def get_total_population(self) -> int:
        """获取山东省总人口"""
        query = """
            SELECT COUNT(DISTINCT id_no) 
            FROM population
            WHERE hukou_province = '山东省' OR cur_province = '山东省'
        """
        results = self.execute_query(query)
        count = results[0][0] if results else 0
        print(f"   📊 山东省总人口: {count:,}")
        return count
    
    def get_city_population(self) -> Dict[str, int]:
        """获取各地市人口"""
        query = """
            SELECT hukou_city, COUNT(DISTINCT id_no) as count
            FROM population
            WHERE (hukou_province = '山东省' OR cur_province = '山东省')
              AND hukou_city IS NOT NULL
            GROUP BY hukou_city
            ORDER BY count DESC
        """
        results = self.execute_query(query)
        return {row[0]: row[1] for row in results}
    
    def get_gender_statistics(self) -> Dict[str, int]:
        """获取性别统计"""
        query = """
            SELECT gender, COUNT(DISTINCT id_no) as count
            FROM population
            WHERE (hukou_province = '山东省' OR cur_province = '山东省')
              AND gender IS NOT NULL
            GROUP BY gender
        """
        results = self.execute_query(query)
        stats = {'male': 0, 'female': 0}
        for row in results:
            if row[0] == '男':
                stats['male'] = row[1]
            elif row[0] == '女':
                stats['female'] = row[1]
        
        # 计算性别比
        if stats['female'] > 0:
            stats['ratio'] = round((stats['male'] / stats['female']) * 100, 2)
        else:
            stats['ratio'] = 0
        
        return stats
    
    def get_age_distribution(self) -> Dict[str, int]:
        """获取年龄分布"""
        query = """
            SELECT 
                CASE
                    WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) < 18 THEN '0-18'
                    WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) BETWEEN 18 AND 34 THEN '18-35'
                    WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) BETWEEN 35 AND 59 THEN '35-60'
                    ELSE '60+'
                END as age_group,
                COUNT(DISTINCT id_no) as count
            FROM population
            WHERE (hukou_province = '山东省' OR cur_province = '山东省')
              AND birth_date IS NOT NULL
            GROUP BY age_group
        """
        results = self.execute_query(query)
        age_stats = {'0-18': 0, '18-35': 0, '35-60': 0, '60+': 0}
        for row in results:
            age_stats[row[0]] = row[1]
        return age_stats
    
    def get_education_statistics(self) -> Dict[str, int]:
        """获取受教育程度统计"""
        query = """
            SELECT education_level, COUNT(DISTINCT id_no) as count
            FROM population
            WHERE (hukou_province = '山东省' OR cur_province = '山东省')
              AND education_level IS NOT NULL
            GROUP BY education_level
            ORDER BY count DESC
        """
        results = self.execute_query(query)
        return {row[0]: row[1] for row in results}
    
    def get_marriage_statistics(self) -> Dict:
        """获取婚姻统计（使用JOIN优化，避免EXISTS子查询）"""
        # 总婚姻数 - 使用LEFT JOIN替代EXISTS，性能更好
        # 通过LEFT JOIN检查男方和女方，只要有一方是山东省的即可
        query1 = """
            SELECT COUNT(DISTINCT CONCAT(m.male_id_no, '-', m.female_id_no)) as total
            FROM marriage_info m
            LEFT JOIN population p1 ON p1.id_no = m.male_id_no 
                AND (p1.hukou_province = '山东省' OR p1.cur_province = '山东省')
            LEFT JOIN population p2 ON p2.id_no = m.female_id_no 
                AND (p2.hukou_province = '山东省' OR p2.cur_province = '山东省')
            WHERE p1.id_no IS NOT NULL OR p2.id_no IS NOT NULL
        """
        results1 = self.execute_query(query1)
        total_marriages = results1[0][0] if results1 else 0
        
        # 按年份统计 - 使用LEFT JOIN替代EXISTS
        query2 = """
            SELECT YEAR(m.marriage_date) as year, COUNT(DISTINCT CONCAT(m.male_id_no, '-', m.female_id_no)) as count
            FROM marriage_info m
            LEFT JOIN population p1 ON p1.id_no = m.male_id_no 
                AND (p1.hukou_province = '山东省' OR p1.cur_province = '山东省')
            LEFT JOIN population p2 ON p2.id_no = m.female_id_no 
                AND (p2.hukou_province = '山东省' OR p2.cur_province = '山东省')
            WHERE (p1.id_no IS NOT NULL OR p2.id_no IS NOT NULL)
              AND m.marriage_date IS NOT NULL
            GROUP BY YEAR(m.marriage_date)
            ORDER BY year DESC
            LIMIT 10
        """
        results2 = self.execute_query(query2)
        by_year = {str(row[0]): row[1] for row in results2} if results2 else {}
        
        return {
            'total': total_marriages,
            'by_year': by_year
        }
    
    def get_death_statistics(self) -> Dict:
        """获取死亡统计"""
        # 总死亡人数
        query1 = """
            SELECT COUNT(DISTINCT id_no) 
            FROM population_deceased
            WHERE hukou_province = '山东省' OR cur_province = '山东省'
        """
        results1 = self.execute_query(query1)
        total_deaths = results1[0][0] if results1 else 0
        
        # 按年份统计
        query2 = """
            SELECT YEAR(death_date) as year, COUNT(DISTINCT id_no) as count
            FROM population_deceased
            WHERE (hukou_province = '山东省' OR cur_province = '山东省')
              AND death_date IS NOT NULL
            GROUP BY YEAR(death_date)
            ORDER BY year DESC
            LIMIT 10
        """
        results2 = self.execute_query(query2)
        by_year = {str(row[0]): row[1] for row in results2} if results2 else {}
        
        return {
            'total': total_deaths,
            'by_year': by_year
        }
    
    def get_income_statistics(self) -> Dict:
        """获取收入统计"""
        query = """
            SELECT 
                COUNT(DISTINCT id_no) as count,
                AVG(income) as avg_income,
                MAX(income) as max_income,
                MIN(income) as min_income
            FROM population
            WHERE (hukou_province = '山东省' OR cur_province = '山东省')
              AND income IS NOT NULL AND income > 0
        """
        results = self.execute_query(query)
        if results and results[0][0] > 0:
            return {
                'count': results[0][0],
                'avg': round(float(results[0][1]), 2) if results[0][1] else 0,
                'max': float(results[0][2]) if results[0][2] else 0,
                'min': float(results[0][3]) if results[0][3] else 0
            }
        return {'count': 0, 'avg': 0, 'max': 0, 'min': 0}
    
    def get_ethnicity_statistics(self) -> Dict[str, int]:
        """获取民族统计"""
        query = """
            SELECT ethnicity, COUNT(DISTINCT id_no) as count
            FROM population
            WHERE (hukou_province = '山东省' OR cur_province = '山东省')
              AND ethnicity IS NOT NULL
            GROUP BY ethnicity
            ORDER BY count DESC
        """
        results = self.execute_query(query)
        return {row[0]: row[1] for row in results}
    
    def get_migration_statistics(self) -> Dict:
        """获取迁移统计"""
        # 流入人口（户籍非山东省，现居山东省）
        query1 = """
            SELECT COUNT(DISTINCT id_no)
            FROM population
            WHERE hukou_province != '山东省' 
              AND cur_province = '山东省'
        """
        results1 = self.execute_query(query1)
        inflow = results1[0][0] if results1 else 0
        
        # 流出人口（户籍山东省，现居非山东省）
        query2 = """
            SELECT COUNT(DISTINCT id_no)
            FROM population
            WHERE hukou_province = '山东省'
              AND cur_province != '山东省'
        """
        results2 = self.execute_query(query2)
        outflow = results2[0][0] if results2 else 0
        
        # 流入来源地
        query3 = """
            SELECT hukou_province, COUNT(DISTINCT id_no) as count
            FROM population
            WHERE hukou_province != '山东省'
              AND cur_province = '山东省'
            GROUP BY hukou_province
            ORDER BY count DESC
            LIMIT 10
        """
        results3 = self.execute_query(query3)
        inflow_from = {row[0]: row[1] for row in results3} if results3 else {}
        
        # 流出目的地
        query4 = """
            SELECT cur_province, COUNT(DISTINCT id_no) as count
            FROM population
            WHERE hukou_province = '山东省'
              AND cur_province != '山东省'
            GROUP BY cur_province
            ORDER BY count DESC
            LIMIT 10
        """
        results4 = self.execute_query(query4)
        outflow_to = {row[0]: row[1] for row in results4} if results4 else {}
        
        return {
            'inflow': inflow,
            'outflow': outflow,
            'net': inflow - outflow,
            'inflow_from': inflow_from,
            'outflow_to': outflow_to
        }
    
    def get_comprehensive_statistics(self) -> Dict:
        """获取综合统计数据（带错误处理和默认值）"""
        print("\n📊 开始获取山东省综合统计数据...")
        
        # 使用try-except确保每个方法都有默认值
        try:
            total_population = self.get_total_population()
        except Exception as e:
            print(f"⚠️ 获取总人口失败: {e}")
            total_population = 0
        
        try:
            city_population = self.get_city_population()
        except Exception as e:
            print(f"⚠️ 获取城市人口失败: {e}")
            city_population = {}
        
        try:
            gender = self.get_gender_statistics()
        except Exception as e:
            print(f"⚠️ 获取性别统计失败: {e}")
            gender = {'male': 0, 'female': 0, 'ratio': 0}
        
        try:
            age = self.get_age_distribution()
        except Exception as e:
            print(f"⚠️ 获取年龄分布失败: {e}")
            age = {'0-18': 0, '18-35': 0, '35-60': 0, '60+': 0}
        
        try:
            education = self.get_education_statistics()
        except Exception as e:
            print(f"⚠️ 获取教育统计失败: {e}")
            education = {}
        
        try:
            marriage = self.get_marriage_statistics()
        except Exception as e:
            print(f"⚠️ 获取婚姻统计失败: {e}")
            marriage = {'total': 0, 'by_year': {}}
        
        try:
            death = self.get_death_statistics()
        except Exception as e:
            print(f"⚠️ 获取死亡统计失败: {e}")
            death = {'total': 0, 'by_year': {}}
        
        try:
            income = self.get_income_statistics()
        except Exception as e:
            print(f"⚠️ 获取收入统计失败: {e}")
            income = {'count': 0, 'avg': 0, 'max': 0, 'min': 0}
        
        try:
            ethnicity = self.get_ethnicity_statistics()
        except Exception as e:
            print(f"⚠️ 获取民族统计失败: {e}")
            ethnicity = {}
        
        try:
            migration = self.get_migration_statistics()
        except Exception as e:
            print(f"⚠️ 获取迁移统计失败: {e}")
            migration = {'inflow': 0, 'outflow': 0, 'net': 0, 'inflow_from': {}, 'outflow_to': {}}
        
        data = {
            'total_population': total_population,
            'city_population': city_population,
            'gender': gender,
            'age': age,
            'education': education,
            'marriage': marriage,
            'death': death,
            'income': income,
            'ethnicity': ethnicity,
            'migration': migration,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"✅ 山东省数据获取完成")
        print(f"   - 总人口: {data['total_population']:,}")
        print(f"   - 城市数: {len(data['city_population'])}")
        print(f"   - 婚姻记录: {data['marriage']['total']:,}")
        print(f"   - 死亡记录: {data['death']['total']:,}")
        
        self.close()
        return data


# 测试代码
if __name__ == '__main__':
    stats = ShandongStatistics()
    data = stats.get_comprehensive_statistics()
    
    import json
    print("\n" + "="*60)
    print("山东省统计数据:")
    print("="*60)
    print(json.dumps(data, ensure_ascii=False, indent=2))

