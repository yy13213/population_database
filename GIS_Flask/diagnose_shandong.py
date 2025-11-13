#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
山东省数据诊断工具
检查数据库中山东省数据的实际格式，并修复视图
"""
import pymysql

MYSQL_CONFIG = {

}

def diagnose():
    """诊断山东省数据问题"""
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        print("\n" + "="*60)
        print("🔍 山东省数据诊断工具")
        print("="*60)
        
        # 1. 检查户籍省份中包含"山东"的所有不同格式
        print("\n1️⃣ 检查户籍省份中包含'山东'的所有格式:")
        cursor.execute("""
            SELECT DISTINCT hukou_province, COUNT(*) as count
            FROM population
            WHERE hukou_province LIKE '%山东%'
            GROUP BY hukou_province
            ORDER BY count DESC
        """)
        
        hukou_formats = {}
        results = cursor.fetchall()
        for row in results:
            hukou_formats[row[0]] = row[1]
            print(f"   '{row[0]}': {row[1]:,} 条")
        
        # 2. 检查现居住省份中包含"山东"的所有不同格式
        print("\n2️⃣ 检查现居住省份中包含'山东'的所有格式:")
        cursor.execute("""
            SELECT DISTINCT cur_province, COUNT(*) as count
            FROM population
            WHERE cur_province LIKE '%山东%'
            GROUP BY cur_province
            ORDER BY count DESC
        """)
        
        cur_formats = {}
        results = cursor.fetchall()
        for row in results:
            cur_formats[row[0]] = row[1]
            print(f"   '{row[0]}': {row[1]:,} 条")
        
        # 3. 检查视图是否存在
        print("\n3️⃣ 检查视图是否存在:")
        cursor.execute("SHOW FULL TABLES WHERE table_type = 'VIEW'")
        views = [row[0] for row in cursor.fetchall()]
        
        if 'shandong_population' in views:
            print("   ✅ shandong_population 视图存在")
            cursor.execute("SELECT COUNT(*) FROM shandong_population")
            view_count = cursor.fetchone()[0]
            print(f"   📊 视图记录数: {view_count:,}")
        else:
            print("   ❌ shandong_population 视图不存在")
        
        # 4. 测试不同的查询条件
        print("\n4️⃣ 测试不同的查询条件:")
        
        conditions = [
            ("hukou_province = '山东'", "户籍 = '山东'"),
            ("hukou_province = '山东省'", "户籍 = '山东省'"),
            ("hukou_province LIKE '%山东%'", "户籍 LIKE '%山东%'"),
            ("cur_province = '山东'", "现居 = '山东'"),
            ("cur_province = '山东省'", "现居 = '山东省'"),
            ("cur_province LIKE '%山东%'", "现居 LIKE '%山东%'"),
        ]
        
        best_condition = None
        max_count = 0
        
        for condition, desc in conditions:
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT id_no) FROM population WHERE {condition}")
                count = cursor.fetchone()[0]
                print(f"   {desc}: {count:,} 条")
                if count > max_count:
                    max_count = count
                    best_condition = condition
            except Exception as e:
                print(f"   {desc}: 查询失败 - {e}")
        
        # 5. 生成修复建议
        print("\n" + "="*60)
        print("💡 诊断结果和建议")
        print("="*60)
        
        if max_count > 0:
            print(f"\n✅ 找到山东省数据: {max_count:,} 条")
            print(f"📌 最佳查询条件: {best_condition}")
            
            # 确定实际的省份名称格式
            actual_formats = set(list(hukou_formats.keys()) + list(cur_formats.keys()))
            if actual_formats:
                print(f"\n📋 数据库中实际的省份名称格式:")
                for fmt in actual_formats:
                    print(f"   - '{fmt}'")
            
            print(f"\n🔧 建议:")
            print(f"   1. 重新创建视图，使用以下条件:")
            print(f"      WHERE hukou_province LIKE '%山东%' OR cur_province LIKE '%山东%'")
            print(f"   2. 或者使用精确匹配（如果确定格式）:")
            if '山东省' in actual_formats:
                print(f"      WHERE hukou_province = '山东省' OR cur_province = '山东省'")
            elif '山东' in actual_formats:
                print(f"      WHERE hukou_province = '山东' OR cur_province = '山东'")
        else:
            print("\n❌ 未找到山东省数据")
            print("   可能原因:")
            print("   1. 数据库中确实没有山东省数据")
            print("   2. 省份名称格式不同（如'山东省'、'山东'等）")
            print("   3. 数据在其他字段中")
        
        cursor.close()
        connection.close()
        
        return best_condition, max_count
        
    except Exception as e:
        print(f"\n❌ 诊断失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, 0


def fix_views(best_condition=None):
    """修复视图"""
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        print("\n" + "="*60)
        print("🔧 修复山东省视图")
        print("="*60)
        
        # 使用LIKE '%山东%'作为最通用的条件
        condition = "hukou_province LIKE '%山东%' OR cur_province LIKE '%山东%'"
        
        # 1. 重新创建人口视图
        print("\n1️⃣ 重新创建 shandong_population 视图...")
        cursor.execute("DROP VIEW IF EXISTS shandong_population")
        cursor.execute(f"""
            CREATE VIEW shandong_population AS
            SELECT * FROM population
            WHERE {condition}
        """)
        cursor.execute("SELECT COUNT(*) FROM shandong_population")
        count = cursor.fetchone()[0]
        print(f"   ✅ 创建成功，记录数: {count:,}")
        
        # 2. 重新创建死亡人口视图
        print("\n2️⃣ 重新创建 shandong_deceased 视图...")
        cursor.execute("DROP VIEW IF EXISTS shandong_deceased")
        cursor.execute(f"""
            CREATE VIEW shandong_deceased AS
            SELECT * FROM population_deceased
            WHERE {condition}
        """)
        cursor.execute("SELECT COUNT(*) FROM shandong_deceased")
        count = cursor.fetchone()[0]
        print(f"   ✅ 创建成功，记录数: {count:,}")
        
        # 3. 重新创建婚姻视图
        print("\n3️⃣ 重新创建 shandong_marriage 视图...")
        cursor.execute("DROP VIEW IF EXISTS shandong_marriage")
        cursor.execute(f"""
            CREATE VIEW shandong_marriage AS
            SELECT m.* FROM marriage_info m
            WHERE EXISTS (
                SELECT 1 FROM population p 
                WHERE (p.id_no = m.male_id_no OR p.id_no = m.female_id_no)
                AND ({condition})
            )
        """)
        cursor.execute("SELECT COUNT(*) FROM shandong_marriage")
        count = cursor.fetchone()[0]
        print(f"   ✅ 创建成功，记录数: {count:,}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("\n✅ 所有视图修复完成！")
        
    except Exception as e:
        print(f"\n❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔍 山东省数据诊断和修复工具")
    print("="*60)
    
    # 先诊断
    best_condition, max_count = diagnose()
    
    # 如果找到数据，询问是否修复
    if max_count > 0:
        print("\n" + "="*60)
        print("是否要修复视图？(y/n): ", end='')
        # 自动修复
        print("y (自动修复)")
        fix_views(best_condition)
    else:
        print("\n⚠️ 未找到山东省数据，无法修复视图")
        print("   请先检查数据库中是否有山东省相关数据")

