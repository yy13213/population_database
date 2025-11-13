"""
人口数据统计分析模块
从数据库读取数据并进行统计分析
"""

import pymysql
from typing import Dict, List, Tuple
from datetime import datetime
import json
import os

# 数据库配置
MYSQL_CONFIG = {

}

class PopulationStatistics:
    """人口统计分析类"""
    
    def __init__(self, use_memory_tables=True):
        """
        初始化统计类
        :param use_memory_tables: 是否使用内存表（MEMORY引擎）
        """
        self.connection = None
        self.use_memory_tables = use_memory_tables
        self.province_data = self.load_province_data()
        
        # 表名映射
        if use_memory_tables:
            self.population_table = 'population_memory'
            self.deceased_table = 'population_deceased_memory'
            self.marriage_table = 'marriage_info_memory'
            print("🚀 使用内存表模式（MEMORY引擎）- 极速查询")
        else:
            self.population_table = 'population'
            self.deceased_table = 'population_deceased'
            self.marriage_table = 'marriage_info'
            print("💾 使用磁盘表模式（InnoDB引擎）")
    
    def load_province_data(self):
        """加载省份数据"""
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        province_data_path = os.path.join(project_root, 'province_data.json')
        
        # 尝试多个可能的路径
        possible_paths = [
            province_data_path,
            '../province_data.json',
            '../../province_data.json',
            os.path.join(project_root, 'GIS', 'province_data.json')
        ]
        
        for path in possible_paths:
            try:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except:
                continue
        
        # 如果都找不到，抛出错误
        raise FileNotFoundError(
            f"找不到province_data.json文件。\n"
            f"当前目录: {os.getcwd()}\n"
            f"尝试的路径: {possible_paths}"
        )
    
    def connect(self):
        """连接数据库，带重试机制"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 检查现有连接是否可用
                if self.connection and self.connection.open:
                    try:
                        self.connection.ping(reconnect=True)
                        return True
                    except:
                        self.connection = None
                
                # 创建新连接
                self.connection = pymysql.connect(**MYSQL_CONFIG)
                return True
                
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ 数据库连接失败（尝试{max_retries}次）: {str(e)}")
                    return False
                print(f"⚠️ 连接失败，{retry_count}/{max_retries}次重试中...")
                import time
                time.sleep(2)
        
        return False
    
    def close(self):
        """关闭数据库连接"""
        try:
            if self.connection and self.connection.open:
                self.connection.close()
        except:
            pass
        finally:
            self.connection = None
    
    def execute_query(self, query, params=None):
        """
        执行查询，带重试和错误处理
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.connect()
                cursor = self.connection.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                cursor.close()
                return results
                
            except pymysql.err.OperationalError as e:
                retry_count += 1
                print(f"⚠️ 查询失败 ({e}), 重试 {retry_count}/{max_retries}...")
                self.connection = None  # 强制重新连接
                
                if retry_count >= max_retries:
                    raise Exception(f"查询失败（尝试{max_retries}次）: {str(e)}")
                
                import time
                time.sleep(2)
            except Exception as e:
                raise Exception(f"查询执行错误: {str(e)}")
    
    def get_province_population(self) -> Dict[str, int]:
        """
        统计各省人口数量
        :return: {省名: 人口数}
        """
        query = f"""
            SELECT hukou_province, COUNT(*) as count
            FROM {self.population_table}
            WHERE hukou_province IS NOT NULL
            GROUP BY hukou_province
            ORDER BY count DESC
        """
        
        try:
            results = self.execute_query(query)
            
            # 转换为字典
            province_stats = {}
            for row in results:
                province_name = row[0]
                count = row[1]
                # 去掉"省"、"市"、"自治区"等后缀
                short_name = self._normalize_province_name(province_name)
                province_stats[short_name] = count
            
            print(f"✅ 获取省份人口数据成功，共 {len(province_stats)} 个省份")
            return province_stats
        except Exception as e:
            print(f"❌ 获取省份人口数据失败: {e}")
            return {}
    
    def get_province_density(self) -> Dict[str, float]:
        """
        计算各省人口密度（人/平方公里）
        注：需要省份面积数据
        :return: {省名: 密度}
        """
        # 中国各省面积（平方公里）
        province_areas = {
            '新疆': 1664900,
            '西藏': 1228400,
            '内蒙古': 1183000,
            '青海': 722300,
            '四川': 486000,
            '黑龙江': 473000,
            '甘肃': 425800,
            '云南': 394000,
            '广西': 237600,
            '湖南': 211800,
            '陕西': 205600,
            '河北': 188800,
            '吉林': 187400,
            '湖北': 185900,
            '广东': 179800,
            '贵州': 176200,
            '江西': 166900,
            '河南': 167000,
            '山西': 156300,
            '山东': 155800,
            '辽宁': 145900,
            '安徽': 139600,
            '福建': 121400,
            '江苏': 102600,
            '浙江': 101800,
            '重庆': 82400,
            '宁夏': 66400,
            '台湾': 36000,
            '海南': 35400,
            '北京': 16410,
            '天津': 11760,
            '上海': 6340,
            '香港': 1106,
            '澳门': 32.9
        }
        
        population_stats = self.get_province_population()
        
        density_stats = {}
        for province, count in population_stats.items():
            if province in province_areas:
                density = count / province_areas[province]
                density_stats[province] = round(density, 2)
            else:
                density_stats[province] = 0
        
        return density_stats
    
    def get_marriage_statistics(self) -> Dict[str, Dict]:
        """
        统计各省结婚人口
        :return: {省名: {'married_count': 数量, 'marriage_rate': 比例}}
        """
        # 优化后的查询：使用 UNION 代替 OR，大幅提升性能
        query = f"""
            SELECT hukou_province, COUNT(DISTINCT id_no) as married_count
            FROM (
                SELECT p.hukou_province, p.id_no
                FROM {self.population_table} p
                INNER JOIN {self.marriage_table} m ON p.id_no = m.male_id_no
                WHERE p.hukou_province IS NOT NULL
                UNION
                SELECT p.hukou_province, p.id_no
                FROM {self.population_table} p
                INNER JOIN {self.marriage_table} m ON p.id_no = m.female_id_no
                WHERE p.hukou_province IS NOT NULL
            ) AS married_people
            GROUP BY hukou_province
        """
        
        try:
            results = self.execute_query(query)
            
            # 获取总人口数
            total_population = self.get_province_population()
            
            marriage_stats = {}
            for row in results:
                province_name = row[0]
                married_count = row[1]
                short_name = self._normalize_province_name(province_name)
                
                total = total_population.get(short_name, 1)
                marriage_rate = round((married_count / total) * 100, 2) if total > 0 else 0
                
                marriage_stats[short_name] = {
                    'married_count': married_count,
                    'marriage_rate': marriage_rate,
                    'total': total
                }
            
            print(f"✅ 获取省份婚姻数据成功，共 {len(marriage_stats)} 个省份")
            return marriage_stats
        except Exception as e:
            print(f"❌ 获取省份婚姻数据失败: {e}")
            return {}
    
    def get_migration_statistics(self) -> List[Dict]:
        """
        统计人口迁移情况（户籍地 vs 现居住地）
        :return: [{'from': 省名, 'to': 省名, 'count': 数量}]
        """
        query = f"""
            SELECT 
                hukou_province,
                cur_province,
                COUNT(*) as count
            FROM {self.population_table}
            WHERE hukou_province IS NOT NULL 
            AND cur_province IS NOT NULL
            AND hukou_province != cur_province
            GROUP BY hukou_province, cur_province
            HAVING count >= 5
            ORDER BY count DESC
        """
        
        try:
            results = self.execute_query(query)
            
            migration_data = []
            for row in results:
                from_province = self._normalize_province_name(row[0])
                to_province = self._normalize_province_name(row[1])
                count = row[2]
                
                migration_data.append({
                    'from': from_province,
                    'to': to_province,
                    'count': count
                })
            
            print(f"✅ 获取人口迁移数据成功，共 {len(migration_data)} 条记录")
            return migration_data
        except Exception as e:
            print(f"❌ 获取人口迁移数据失败: {e}")
            return []
    
    def get_gender_statistics(self) -> Dict[str, Dict]:
        """
        统计各省性别比例
        :return: {省名: {'male': 数量, 'female': 数量, 'ratio': 性别比}}
        """
        query = f"""
            SELECT 
                hukou_province,
                gender,
                COUNT(*) as count
            FROM {self.population_table}
            WHERE hukou_province IS NOT NULL AND gender IS NOT NULL
            GROUP BY hukou_province, gender
        """
        
        try:
            results = self.execute_query(query)
            
            gender_stats = {}
            for row in results:
                province_name = self._normalize_province_name(row[0])
                gender = row[1]
                count = row[2]
                
                if province_name not in gender_stats:
                    gender_stats[province_name] = {'male': 0, 'female': 0}
                
                if gender == '男':
                    gender_stats[province_name]['male'] = count
                elif gender == '女':
                    gender_stats[province_name]['female'] = count
            
            # 计算性别比（每100个女性对应的男性数量）
            for province, stats in gender_stats.items():
                if stats['female'] > 0:
                    ratio = round((stats['male'] / stats['female']) * 100, 2)
                    stats['ratio'] = ratio
                else:
                    stats['ratio'] = 0
            
            print(f"✅ 获取性别统计数据成功，共 {len(gender_stats)} 个省份")
            return gender_stats
        except Exception as e:
            print(f"❌ 获取性别统计数据失败: {e}")
            return {}
    
    def get_age_distribution(self) -> Dict[str, Dict]:
        """
        统计各省年龄分布
        :return: {省名: {'0-18': 数量, '18-35': 数量, '35-60': 数量, '60+': 数量}}
        """
        query = f"""
            SELECT 
                hukou_province,
                CASE
                    WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) < 18 THEN '0-18'
                    WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) BETWEEN 18 AND 34 THEN '18-35'
                    WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) BETWEEN 35 AND 59 THEN '35-60'
                    ELSE '60+'
                END as age_group,
                COUNT(*) as count
            FROM {self.population_table}
            WHERE hukou_province IS NOT NULL AND birth_date IS NOT NULL
            GROUP BY hukou_province, age_group
        """
        
        try:
            results = self.execute_query(query)
            
            age_stats = {}
            for row in results:
                province_name = self._normalize_province_name(row[0])
                age_group = row[1]
                count = row[2]
                
                if province_name not in age_stats:
                    age_stats[province_name] = {'0-18': 0, '18-35': 0, '35-60': 0, '60+': 0}
                
                age_stats[province_name][age_group] = count
            
            print(f"✅ 获取年龄分布数据成功，共 {len(age_stats)} 个省份")
            return age_stats
        except Exception as e:
            print(f"❌ 获取年龄分布数据失败: {e}")
            return {}
    
    def get_ethnicity_statistics(self) -> Dict[str, Dict]:
        """
        统计各省民族分布
        :return: {省名: {'汉族': 数量, '其他': 数量}}
        """
        query = f"""
            SELECT 
                hukou_province,
                ethnicity,
                COUNT(*) as count
            FROM {self.population_table}
            WHERE hukou_province IS NOT NULL AND ethnicity IS NOT NULL
            GROUP BY hukou_province, ethnicity
        """
        
        try:
            results = self.execute_query(query)
            
            ethnicity_stats = {}
            for row in results:
                province_name = self._normalize_province_name(row[0])
                ethnicity = row[1]
                count = row[2]
                
                if province_name not in ethnicity_stats:
                    ethnicity_stats[province_name] = {}
                
                ethnicity_stats[province_name][ethnicity] = count
            
            print(f"✅ 获取民族统计数据成功，共 {len(ethnicity_stats)} 个省份")
            return ethnicity_stats
        except Exception as e:
            print(f"❌ 获取民族统计数据失败: {e}")
            return {}
    
    def get_comprehensive_statistics(self) -> Dict:
        """
        获取综合统计数据
        :return: 所有统计数据的字典
        """
        return {
            'population': self.get_province_population(),
            'density': self.get_province_density(),
            'marriage': self.get_marriage_statistics(),
            'migration': self.get_migration_statistics(),
            'gender': self.get_gender_statistics(),
            'age': self.get_age_distribution(),
            'ethnicity': self.get_ethnicity_statistics(),
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _normalize_province_name(self, name: str) -> str:
        """
        规范化省份名称（去掉省、市、自治区等后缀）
        """
        if not name:
            return ''
        
        suffixes = ['省', '市', '自治区', '特别行政区', '维吾尔自治区', '壮族自治区', '回族自治区']
        for suffix in suffixes:
            name = name.replace(suffix, '')
        
        # 特殊处理
        name_mapping = {
            '内蒙古': '内蒙古',
            '广西壮族': '广西',
            '西藏': '西藏',
            '宁夏回族': '宁夏',
            '新疆维吾尔': '新疆'
        }
        
        return name_mapping.get(name, name)


if __name__ == '__main__':
    # 测试
    stats = PopulationStatistics()
    
    print("=" * 60)
    print("📊 人口统计数据测试")
    print("=" * 60)
    
    # 1. 人口数量
    print("\n1️⃣ 各省人口数量（前10）:")
    population = stats.get_province_population()
    for i, (province, count) in enumerate(list(population.items())[:10], 1):
        print(f"   {i}. {province:8s}: {count:>8,} 人")
    
    # 2. 人口密度
    print("\n2️⃣ 各省人口密度（前10）:")
    density = stats.get_province_density()
    sorted_density = sorted(density.items(), key=lambda x: x[1], reverse=True)
    for i, (province, dens) in enumerate(sorted_density[:10], 1):
        print(f"   {i}. {province:8s}: {dens:>8.2f} 人/km²")
    
    # 3. 结婚统计
    print("\n3️⃣ 结婚人口统计（前5）:")
    marriage = stats.get_marriage_statistics()
    sorted_marriage = sorted(marriage.items(), key=lambda x: x[1]['married_count'], reverse=True)
    for i, (province, data) in enumerate(sorted_marriage[:5], 1):
        print(f"   {i}. {province:8s}: {data['married_count']:>6,} 人 ({data['marriage_rate']}%)")
    
    # 4. 人口迁移
    print("\n4️⃣ 人口迁移流向（前5）:")
    migration = stats.get_migration_statistics()
    for i, flow in enumerate(migration[:5], 1):
        print(f"   {i}. {flow['from']} → {flow['to']}: {flow['count']:>6,} 人")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)
    
    stats.close()

