#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查数据库中山东省数据的实际格式
"""
import pymysql

MYSQL_CONFIG = {

}

try:
    connection = pymysql.connect(**MYSQL_CONFIG)
    cursor = connection.cursor()
    
    print("=" * 60)
    print("🔍 检查数据库中山东省数据的实际格式")
    print("=" * 60)
    
    # 检查户籍省份中包含"山东"的所有不同格式
    print("\n1. 检查户籍省份中包含'山东'的所有格式:")
    cursor.execute("""
        SELECT DISTINCT hukou_province, COUNT(*) as count
        FROM population
        WHERE hukou_province LIKE '%山东%'
        GROUP BY hukou_province
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"   '{row[0]}': {row[1]:,} 条")
    
    # 检查现居住省份中包含"山东"的所有不同格式
    print("\n2. 检查现居住省份中包含'山东'的所有格式:")
    cursor.execute("""
        SELECT DISTINCT cur_province, COUNT(*) as count
        FROM population
        WHERE cur_province LIKE '%山东%'
        GROUP BY cur_province
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"   '{row[0]}': {row[1]:,} 条")
    
    # 检查视图中的数据
    print("\n3. 检查视图中的数据:")
    try:
        cursor.execute("SELECT COUNT(*) FROM shandong_population")
        view_count = cursor.fetchone()[0]
        print(f"   shandong_population 视图: {view_count:,} 条")
    except Exception as e:
        print(f"   ❌ 视图不存在或查询失败: {e}")
    
    # 测试不同的查询条件
    print("\n4. 测试不同的查询条件:")
    
    conditions = [
        ("hukou_province = '山东'", "户籍 = '山东'"),
        ("hukou_province = '山东省'", "户籍 = '山东省'"),
        ("hukou_province LIKE '%山东%'", "户籍 LIKE '%山东%'"),
        ("cur_province = '山东'", "现居 = '山东'"),
        ("cur_province = '山东省'", "现居 = '山东省'"),
        ("cur_province LIKE '%山东%'", "现居 LIKE '%山东%'"),
    ]
    
    for condition, desc in conditions:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM population WHERE {condition}")
            count = cursor.fetchone()[0]
            print(f"   {desc}: {count:,} 条")
        except Exception as e:
            print(f"   {desc}: 查询失败 - {e}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()

