# -*-coding:utf-8-*-
"""
婚姻登记脚本
- 从population表中随机选择0.4%的人口进行结婚配对
- 男女随机配对
- 插入marriage_info表
"""
import pymysql
from datetime import datetime, date, timedelta
import random
import sys

# 数据库配置
MYSQL_CONFIG = {

}

# 结婚比例
MARRIAGE_RATIO = 0.004  # 0.4%

def get_total_population(connection):
    """获取总人口数"""
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM population")
    result = cursor.fetchone()
    return result[0]

def get_population_by_gender(connection, gender):
    """按性别获取所有人口的身份证号、姓名和出生日期"""
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute(
        "SELECT id_no, name, birth_date FROM population WHERE gender = %s",
        (gender,)
    )
    return cursor.fetchall()

def generate_marriage_date(birth_date1, birth_date2):
    """
    生成合理的结婚日期
    - 必须在两人都满18岁之后
    - 不能晚于今天
    """
    # 转换出生日期
    if isinstance(birth_date1, str):
        birth_date1 = datetime.strptime(birth_date1, '%Y-%m-%d').date()
    if isinstance(birth_date2, str):
        birth_date2 = datetime.strptime(birth_date2, '%Y-%m-%d').date()
    
    # 找出较晚的出生日期（年轻的那个）
    younger_birth = max(birth_date1, birth_date2)
    
    # 计算满18岁的日期
    legal_marriage_date = younger_birth + timedelta(days=365 * 18)
    
    today = date.today()
    
    # 如果还未满18岁，返回None（不能结婚）
    if legal_marriage_date > today:
        return None
    
    # 在满18岁和今天之间随机选择一个日期
    days_range = (today - legal_marriage_date).days
    if days_range <= 0:
        return legal_marriage_date
    
    random_days = random.randint(0, days_range)
    marriage_date = legal_marriage_date + timedelta(days=random_days)
    
    return marriage_date

def insert_marriage(connection, male, female, marriage_date):
    """插入婚姻记录"""
    cursor = connection.cursor()
    
    sql = """
    INSERT INTO marriage_info 
    (male_name, female_name, male_id_no, female_id_no, marriage_date)
    VALUES 
    (%s, %s, %s, %s, %s)
    """
    
    data = (
        male['name'],
        female['name'],
        male['id_no'],
        female['id_no'],
        marriage_date
    )
    
    try:
        cursor.execute(sql, data)
        return True
    except Exception as e:
        # 可能因为外键约束或重复键失败
        if '1062' in str(e):  # 重复键
            return False
        print(f"插入婚姻记录失败: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("婚姻登记脚本")
    print("=" * 60)
    print(f"结婚比例: {MARRIAGE_RATIO * 100}%")
    print("=" * 60)
    
    # 连接数据库
    print("正在连接数据库...")
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        print("数据库连接成功！")
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        return
    
    try:
        # 获取总人口数
        total_pop = get_total_population(connection)
        marriage_count = int(total_pop * MARRIAGE_RATIO)
        
        # 结婚是成对的，所以需要的人数应该是偶数
        if marriage_count % 2 != 0:
            marriage_count += 1
        
        couples_count = marriage_count // 2
        
        print(f"总人口数: {total_pop:,}")
        print(f"需要结婚的人数: {marriage_count:,}")
        print(f"需要登记的夫妇数: {couples_count:,}")
        print()
        
        if couples_count == 0:
            print("没有需要处理的数据")
            return
        
        # 获取所有男性和女性
        print("正在加载人口数据...")
        males = get_population_by_gender(connection, '男')
        females = get_population_by_gender(connection, '女')
        
        print(f"男性人口: {len(males):,}")
        print(f"女性人口: {len(females):,}")
        print()
        
        if len(males) == 0 or len(females) == 0:
            print("没有足够的男性或女性人口进行配对")
            return
        
        # 随机选择男性和女性
        print("正在随机选择配对对象...")
        selected_males = random.sample(males, min(couples_count, len(males)))
        selected_females = random.sample(females, min(couples_count, len(females)))
        
        # 确保配对数量一致
        actual_couples = min(len(selected_males), len(selected_females))
        selected_males = selected_males[:actual_couples]
        selected_females = selected_females[:actual_couples]
        
        print(f"实际配对夫妇数: {actual_couples:,}")
        print()
        
        # 开始登记婚姻
        print("开始登记婚姻...")
        success_count = 0
        failed_count = 0
        skipped_count = 0  # 因年龄不够而跳过
        
        for i, (male, female) in enumerate(zip(selected_males, selected_females), 1):
            # 生成结婚日期
            marriage_date = generate_marriage_date(male['birth_date'], female['birth_date'])
            
            if marriage_date is None:
                # 年龄不够，跳过
                skipped_count += 1
                continue
            
            # 插入婚姻记录
            if insert_marriage(connection, male, female, marriage_date):
                success_count += 1
            else:
                failed_count += 1
            
            # 每100对提交一次
            if i % 100 == 0:
                connection.commit()
                print(f"进度: {i}/{actual_couples} ({i*100/actual_couples:.1f}%)")
        
        # 最终提交
        connection.commit()
        
        # 打印结果
        print()
        print("=" * 60)
        print("婚姻登记完成！")
        print("=" * 60)
        print(f"成功登记: {success_count:,} 对")
        print(f"失败: {failed_count:,} 对")
        print(f"因年龄不够跳过: {skipped_count:,} 对")
        print("=" * 60)
        
        # 显示几个示例
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT male_name, female_name, male_id_no, female_id_no, marriage_date 
            FROM marriage_info 
            ORDER BY marriage_date DESC
            LIMIT 5
        """)
        print("\n示例婚姻记录：")
        for row in cursor.fetchall():
            print(f"  {row['male_name']}({row['male_id_no']}) ❤️  {row['female_name']}({row['female_id_no']}) | 结婚日期: {row['marriage_date']}")
        
        # 统计信息
        cursor.execute("SELECT COUNT(*) as count FROM marriage_info")
        total_marriages = cursor.fetchone()['count']
        print(f"\n数据库中共有 {total_marriages:,} 对夫妇")
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    # 确认操作
    print("📝 此操作将在marriage_info表中插入随机婚姻记录")
    confirm = input("确认继续？(yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        main()
    else:
        print("操作已取消")

