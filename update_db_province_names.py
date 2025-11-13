#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新数据库中的省份名称
将 "广西壮族"、"宁夏回族"、"新疆维吾尔" 改为简化名称
"""
import pymysql

# 数据库配置
MYSQL_CONFIG = {

}

# 名称映射
name_mapping = {
    '广西壮族自治区': '广西',
    '广西壮族': '广西',
    '宁夏回族自治区': '宁夏',
    '宁夏回族': '宁夏',
    '新疆维吾尔自治区': '新疆',
    '新疆维吾尔': '新疆'
}

def update_province_names():
    """更新数据库中的省份名称"""
    connection = None
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        print("连接数据库成功！")
        print("=" * 60)
        
        # 检查需要更新的记录数
        print("\n检查需要更新的记录...")
        for old_name, new_name in name_mapping.items():
            cursor.execute(
                "SELECT COUNT(*) FROM population WHERE hukou_province = %s",
                (old_name,)
            )
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  {old_name}: {count:,} 条记录")
        
        print("\n" + "=" * 60)
        print("开始更新省份名称...")
        print("=" * 60)
        
        total_updated = 0
        
        # 更新每个省份名称
        for old_name, new_name in name_mapping.items():
            cursor.execute(
                "UPDATE population SET hukou_province = %s WHERE hukou_province = %s",
                (new_name, old_name)
            )
            affected = cursor.rowcount
            if affected > 0:
                print(f"✓ {old_name} -> {new_name}: 更新 {affected:,} 条记录")
                total_updated += affected
        
        # 提交更改
        connection.commit()
        
        print("=" * 60)
        print(f"\n✅ 更新完成！共更新 {total_updated:,} 条记录")
        
        # 验证更新结果
        print("\n验证更新结果:")
        print("-" * 60)
        for new_name in ['广西', '宁夏', '新疆']:
            cursor.execute(
                "SELECT COUNT(*) FROM population WHERE hukou_province = %s",
                (new_name,)
            )
            count = cursor.fetchone()[0]
            print(f"{new_name}: {count:,} 条记录")
        
        # 检查是否还有旧名称
        print("\n检查旧名称残留:")
        print("-" * 60)
        has_old = False
        for old_name in name_mapping.keys():
            cursor.execute(
                "SELECT COUNT(*) FROM population WHERE hukou_province = %s",
                (old_name,)
            )
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"⚠️ {old_name}: 仍有 {count:,} 条记录")
                has_old = True
        
        if not has_old:
            print("✓ 无旧名称残留")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        if connection:
            connection.rollback()
    
    finally:
        if connection:
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == '__main__':
    print("数据库省份名称更新脚本")
    print("=" * 60)
    print("将更新以下省份名称:")
    for old_name, new_name in name_mapping.items():
        print(f"  {old_name} -> {new_name}")
    print("=" * 60)
    
    input("\n按 Enter 键开始更新，或 Ctrl+C 取消...")
    
    update_province_names()

