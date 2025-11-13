# -*-coding:utf-8-*-
"""
外键约束演示脚本 - 帮助初学者理解外键的工作原理
"""
import pymysql

MYSQL_CONFIG = {


def demo_check_foreign_key():
    """演示1：检查某个人是否有婚姻记录"""
    print("=" * 60)
    print("演示1：检查外键引用")
    print("=" * 60)
    
    connection = pymysql.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # 随机找一个有婚姻记录的人
    cursor.execute("""
        SELECT p.id_no, p.name, p.gender,
               COUNT(m.male_id_no) + COUNT(m2.female_id_no) as marriage_count
        FROM population p
        LEFT JOIN marriage_info m ON p.id_no = m.male_id_no
        LEFT JOIN marriage_info m2 ON p.id_no = m2.female_id_no
        GROUP BY p.id_no, p.name, p.gender
        HAVING marriage_count > 0
        LIMIT 1
    """)
    
    person = cursor.fetchone()
    
    if person:
        print(f"\n找到一个有婚姻记录的人：")
        print(f"  身份证：{person['id_no']}")
        print(f"  姓名：{person['name']}")
        print(f"  性别：{person['gender']}")
        print(f"  婚姻记录数：{person['marriage_count']}")
        
        # 查看具体的婚姻记录
        cursor.execute("""
            SELECT male_name, female_name, marriage_date
            FROM marriage_info
            WHERE male_id_no = %s OR female_id_no = %s
        """, (person['id_no'], person['id_no']))
        
        marriages = cursor.fetchall()
        print(f"\n  婚姻详情：")
        for m in marriages:
            print(f"    {m['male_name']} ❤️  {m['female_name']} | {m['marriage_date']}")
        
        # 尝试直接删除（会失败）
        print(f"\n尝试直接删除这个人...")
        try:
            cursor.execute("DELETE FROM population WHERE id_no = %s", (person['id_no'],))
            connection.commit()
            print("  ✅ 删除成功！")
        except Exception as e:
            print(f"  ❌ 删除失败！")
            print(f"  错误信息：{str(e)}")
            print(f"\n  📚 解释：因为marriage_info表中还有引用，")
            print(f"          外键约束 ON DELETE RESTRICT 禁止删除")
            connection.rollback()
        
        # 正确的删除方法
        print(f"\n正确的删除方法：")
        print(f"  第1步：先删除婚姻记录")
        cursor.execute("""
            DELETE FROM marriage_info 
            WHERE male_id_no = %s OR female_id_no = %s
        """, (person['id_no'], person['id_no']))
        print(f"  ✅ 删除了 {cursor.rowcount} 条婚姻记录")
        
        print(f"  第2步：再删除人口记录")
        cursor.execute("DELETE FROM population WHERE id_no = %s", (person['id_no'],))
        print(f"  ✅ 删除了人口记录")
        
        # 回滚（不实际删除）
        connection.rollback()
        print(f"\n  ℹ️  注意：以上操作已回滚，数据未实际删除")
    else:
        print("没有找到有婚姻记录的人")
    
    connection.close()

def demo_delete_statistics():
    """演示2：统计需要删除的关联数据"""
    print("\n" + "=" * 60)
    print("演示2：统计需要删除的关联数据")
    print("=" * 60)
    
    connection = pymysql.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # 统计有多少人有婚姻记录
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT p.id_no) as people_with_marriage,
            COUNT(DISTINCT m.male_id_no) + COUNT(DISTINCT m.female_id_no) as total_married_people,
            COUNT(*) as total_marriages
        FROM population p
        LEFT JOIN marriage_info m ON p.id_no = m.male_id_no OR p.id_no = m.female_id_no
        WHERE m.male_id_no IS NOT NULL OR m.female_id_no IS NOT NULL
    """)
    
    stats = cursor.fetchone()
    
    print(f"\n当前数据库状态：")
    cursor.execute("SELECT COUNT(*) as count FROM population")
    pop_count = cursor.fetchone()['count']
    print(f"  总人口：{pop_count:,}")
    
    cursor.execute("SELECT COUNT(*) as count FROM marriage_info")
    marriage_count = cursor.fetchone()['count']
    print(f"  婚姻记录：{marriage_count:,} 对")
    
    if stats['people_with_marriage']:
        print(f"  有婚姻记录的人：{stats['total_married_people']:,}")
        print(f"  占比：{stats['total_married_people']*100/pop_count:.2f}%")
    
    print(f"\n如果要删除10%的人口：")
    delete_count = int(pop_count * 0.1)
    expected_marriage_delete = int(marriage_count * 0.1)  # 粗略估计
    print(f"  需要删除：{delete_count:,} 人")
    print(f"  预计影响：约 {expected_marriage_delete:,} 条婚姻记录")
    print(f"  ⚠️  如果不先删除婚姻记录，操作会失败！")
    
    connection.close()

def demo_foreign_key_types():
    """演示3：不同外键行为的对比"""
    print("\n" + "=" * 60)
    print("演示3：外键约束类型对比")
    print("=" * 60)
    
    print("""
外键约束有4种删除行为：

1. ON DELETE RESTRICT（当前使用的）
   ┌─────────────┐       ┌──────────────┐
   │ population  │       │ marriage_info│
   ├─────────────┤       ├──────────────┤
   │ 张三 [删除]  │ ---X-→│ 张三&李四    │
   └─────────────┘       └──────────────┘
   ❌ 删除失败！必须先删除婚姻记录
   
2. ON DELETE CASCADE（级联删除）
   ┌─────────────┐       ┌──────────────┐
   │ population  │       │ marriage_info│
   ├─────────────┤       ├──────────────┤
   │ 张三 [删除]  │ ---→  │ 张三&李四 [自动删除]│
   └─────────────┘       └──────────────┘
   ✅ 自动删除，像多米诺骨牌
   
3. ON DELETE SET NULL（设置为空）
   ┌─────────────┐       ┌──────────────┐
   │ population  │       │ marriage_info│
   ├─────────────┤       ├──────────────┤
   │ 张三 [删除]  │ ---→  │ NULL&李四    │
   └─────────────┘       └──────────────┘
   ⚠️  变成NULL，保留记录但失去引用
   
4. ON DELETE NO ACTION（与RESTRICT类似）
   ❌ 禁止删除

📚 推荐：
   - 学习阶段：使用 RESTRICT（当前）+ 手动删除
   - 生产环境：根据业务需求选择
   - 重要关系：使用 RESTRICT 防止误删
   - 日志记录：可以使用 CASCADE
    """)

def main():
    print("\n🎓 外键约束学习演示")
    print("本演示将帮助您理解外键的工作原理\n")
    
    try:
        # 演示1：实际操作演示
        demo_check_foreign_key()
        
        # 演示2：统计信息
        demo_delete_statistics()
        
        # 演示3：理论对比
        demo_foreign_key_types()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)
        print("\n💡 总结：")
        print("   1. 外键保护数据完整性，防止出现孤儿数据")
        print("   2. RESTRICT：删除前必须先删除引用")
        print("   3. CASCADE：自动级联删除（谨慎使用）")
        print("   4. 我的脚本使用方法1（手动删除），最安全")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示过程出错：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

