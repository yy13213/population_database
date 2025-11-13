# -*-coding:utf-8-*-
"""
快速测试死亡和婚姻脚本的功能
查看当前数据库状态
"""
import pymysql

MYSQL_CONFIG = {

}

def main():
    print("=" * 60)
    print("数据库状态检查")
    print("=" * 60)
    
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 检查population表
        cursor.execute("SELECT COUNT(*) as count FROM population")
        pop_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM population WHERE gender='男'")
        male_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM population WHERE gender='女'")
        female_count = cursor.fetchone()['count']
        
        print(f"\n📊 人口表 (population)")
        print(f"  总人口: {pop_count:,}")
        print(f"  男性: {male_count:,} ({male_count*100/pop_count if pop_count > 0 else 0:.1f}%)")
        print(f"  女性: {female_count:,} ({female_count*100/pop_count if pop_count > 0 else 0:.1f}%)")
        
        # 检查民族分布
        cursor.execute("""
            SELECT 
                CASE WHEN ethnicity = '汉族' THEN '汉族' ELSE '其他' END as ethnic_group,
                COUNT(*) as count
            FROM population
            GROUP BY ethnic_group
        """)
        for row in cursor.fetchall():
            percentage = row['count'] * 100 / pop_count if pop_count > 0 else 0
            print(f"  {row['ethnic_group']}: {row['count']:,} ({percentage:.1f}%)")
        
        # 检查population_deceased表
        cursor.execute("SELECT COUNT(*) as count FROM population_deceased")
        deceased_count = cursor.fetchone()['count']
        
        print(f"\n⚰️  死亡人口表 (population_deceased)")
        print(f"  死亡人口: {deceased_count:,}")
        
        if deceased_count > 0:
            cursor.execute("""
                SELECT name, gender, birth_date, death_date,
                       TIMESTAMPDIFF(YEAR, birth_date, death_date) as age
                FROM population_deceased
                ORDER BY death_date DESC
                LIMIT 3
            """)
            print(f"  最近死亡记录：")
            for row in cursor.fetchall():
                print(f"    {row['name']} | {row['gender']} | 享年{row['age']}岁 | 卒于{row['death_date']}")
        
        # 检查marriage_info表
        cursor.execute("SELECT COUNT(*) as count FROM marriage_info")
        marriage_count = cursor.fetchone()['count']
        
        print(f"\n💑 婚姻信息表 (marriage_info)")
        print(f"  婚姻登记: {marriage_count:,} 对")
        
        if marriage_count > 0:
            cursor.execute("""
                SELECT male_name, female_name, marriage_date
                FROM marriage_info
                ORDER BY marriage_date DESC
                LIMIT 3
            """)
            print(f"  最近婚姻记录：")
            for row in cursor.fetchall():
                print(f"    {row['male_name']} ❤️  {row['female_name']} | {row['marriage_date']}")
        
        # 总结
        total_all = pop_count + deceased_count
        print(f"\n📈 总结")
        print(f"  总人口（存活+死亡）: {total_all:,}")
        if total_all > 0:
            print(f"  存活率: {pop_count*100/total_all:.2f}%")
            print(f"  死亡率: {deceased_count*100/total_all:.2f}%")
            if pop_count > 0:
                print(f"  结婚率: {marriage_count*2*100/pop_count:.2f}% (基于存活人口)")
        
        print("=" * 60)
        
        connection.close()
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == '__main__':
    main()

