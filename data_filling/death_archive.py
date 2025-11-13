# -*-coding:utf-8-*-
"""
死亡人口归档脚本
- 从population表中随机选择10%的人口
- 为他们生成随机死亡日期
- 将数据移至population_deceased表
- 从population表中删除
"""
import pymysql
from datetime import datetime, date, timedelta
import random
import sys

# 数据库配置
MYSQL_CONFIG = {

}

# 死亡比例
DEATH_RATIO = 0.10  # 10%

def generate_death_date(birth_date_str):
    """
    生成合理的死亡日期
    - 死亡日期必须在出生日期之后
    - 死亡日期不能晚于今天
    """
    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    today = date.today()
    
    # 计算年龄
    age = (today - birth_date).days // 365
    total_days = (today - birth_date).days
    
    # 确保至少有1天
    if total_days < 1:
        total_days = 1
    
    # 根据年龄生成合理的死亡日期
    if age < 1:
        # 婴儿，出生后1天到1年内死亡
        days_after_birth = random.randint(1, min(365, total_days))
        death_date = birth_date + timedelta(days=days_after_birth)
    elif age < 18:
        # 青少年，出生后到现在之间随机
        days_after_birth = random.randint(1, total_days)
        death_date = birth_date + timedelta(days=days_after_birth)
    else:
        # 成年人，更可能在最近几年死亡（符合现实）
        # 70%在最近10年内，30%在更早
        if random.random() < 0.7:
            # 最近10年
            max_days = min(total_days, 365 * 10)
            days_before_today = random.randint(0, max_days)
            death_date = today - timedelta(days=days_before_today)
        else:
            # 更早（成年后到10年前之间）
            min_age_days = 365 * 18  # 至少18岁
            max_age_days = max(min_age_days + 1, total_days - 365 * 10)
            if max_age_days > min_age_days:
                days_after_birth = random.randint(min_age_days, max_age_days)
            else:
                days_after_birth = min_age_days
            death_date = birth_date + timedelta(days=days_after_birth)
    
    # 确保死亡日期在合理范围内
    if death_date > today:
        death_date = today
    if death_date < birth_date:
        death_date = birth_date + timedelta(days=1)
    
    return death_date

def get_total_population(connection):
    """获取总人口数"""
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM population")
    result = cursor.fetchone()
    return result[0]

def select_random_people(connection, count):
    """随机选择指定数量的人口"""
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # 使用ORDER BY RAND()随机选择，但对于大数据量可能较慢
    # 这里使用更高效的方法：先获取所有ID，然后随机选择
    cursor.execute("SELECT id_no FROM population")
    all_ids = [row['id_no'] for row in cursor.fetchall()]
    
    # 随机选择
    selected_ids = random.sample(all_ids, min(count, len(all_ids)))
    
    # 获取完整数据
    if not selected_ids:
        return []
    
    # 分批查询，避免SQL太长
    batch_size = 1000
    all_people = []
    
    for i in range(0, len(selected_ids), batch_size):
        batch_ids = selected_ids[i:i+batch_size]
        placeholders = ','.join(['%s'] * len(batch_ids))
        sql = f"SELECT * FROM population WHERE id_no IN ({placeholders})"
        cursor.execute(sql, batch_ids)
        all_people.extend(cursor.fetchall())
    
    return all_people

def archive_to_deceased(connection, person, death_date):
    """
    将人口数据归档到死亡表
    """
    cursor = connection.cursor()
    
    sql = """
    INSERT INTO population_deceased 
    (id_no, name, former_name, gender, birth_date, ethnicity, marital_status, 
     education_level, hukou_province, hukou_city, hukou_district, housing, 
     cur_province, cur_city, cur_district, hukou_type, income, processed_at, source, death_date)
    VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    data = (
        person['id_no'], person['name'], person['former_name'], person['gender'],
        person['birth_date'], person['ethnicity'], person['marital_status'],
        person['education_level'], person['hukou_province'], person['hukou_city'],
        person['hukou_district'], person['housing'], person['cur_province'],
        person['cur_city'], person['cur_district'], person['hukou_type'],
        person['income'], person['processed_at'], person['source'], death_date
    )
    
    try:
        cursor.execute(sql, data)
        return True
    except Exception as e:
        print(f"归档失败 {person['id_no']}: {str(e)}")
        return False

def delete_from_marriage(connection, id_no):
    """从婚姻表中删除相关记录（如果有）"""
    cursor = connection.cursor()
    # 删除作为男方的婚姻记录
    cursor.execute("DELETE FROM marriage_info WHERE male_id_no = %s", (id_no,))
    # 删除作为女方的婚姻记录
    cursor.execute("DELETE FROM marriage_info WHERE female_id_no = %s", (id_no,))

def delete_from_population(connection, id_no):
    """从人口表中删除（先删除婚姻记录）"""
    # 先删除婚姻记录（如果有外键约束）
    delete_from_marriage(connection, id_no)
    # 再删除人口记录
    cursor = connection.cursor()
    cursor.execute("DELETE FROM population WHERE id_no = %s", (id_no,))

def main():
    print("=" * 60)
    print("死亡人口归档脚本")
    print("=" * 60)
    print(f"死亡比例: {DEATH_RATIO * 100}%")
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
        death_count = int(total_pop * DEATH_RATIO)
        
        print(f"总人口数: {total_pop:,}")
        print(f"需要归档的死亡人口: {death_count:,}")
        print()
        
        if death_count == 0:
            print("没有需要处理的数据")
            return
        
        # 随机选择人口
        print("正在随机选择人口...")
        selected_people = select_random_people(connection, death_count)
        print(f"已选择 {len(selected_people):,} 人")
        print()
        
        # 开始归档
        print("开始归档死亡人口...")
        success_count = 0
        failed_count = 0
        marriage_deleted = 0
        
        for i, person in enumerate(selected_people, 1):
            # 生成死亡日期
            death_date = generate_death_date(str(person['birth_date']))
            
            # 归档到死亡表
            if archive_to_deceased(connection, person, death_date):
                # 检查并统计婚姻记录
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM marriage_info WHERE male_id_no = %s OR female_id_no = %s",
                    (person['id_no'], person['id_no'])
                )
                marriage_count = cursor.fetchone()[0]
                marriage_deleted += marriage_count
                
                # 从人口表删除（会先删除婚姻记录）
                delete_from_population(connection, person['id_no'])
                success_count += 1
            else:
                failed_count += 1
            
            # 每100条提交一次
            if i % 100 == 0:
                connection.commit()
                print(f"进度: {i}/{len(selected_people)} ({i*100/len(selected_people):.1f}%)")
        
        # 最终提交
        connection.commit()
        
        # 打印结果
        print()
        print("=" * 60)
        print("归档完成！")
        print("=" * 60)
        print(f"成功归档: {success_count:,} 条")
        print(f"失败: {failed_count:,} 条")
        print(f"删除的婚姻记录: {marriage_deleted:,} 条")
        print(f"原人口表剩余: {get_total_population(connection):,} 条")
        print("=" * 60)
        
        # 显示几个示例
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id_no, name, gender, birth_date, death_date FROM population_deceased LIMIT 5")
        print("\n示例死亡记录：")
        for row in cursor.fetchall():
            age = (row['death_date'] - row['birth_date']).days // 365
            print(f"  {row['name']} | {row['gender']} | 生于{row['birth_date']} | 卒于{row['death_date']} | 享年{age}岁")
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == '__main__':
    # 确认操作
    print("⚠️  警告：此操作将从population表中删除10%的数据并移至population_deceased表！")
    confirm = input("确认继续？(yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        main()
    else:
        print("操作已取消")

