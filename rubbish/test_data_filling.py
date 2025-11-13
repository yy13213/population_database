# -*-coding:utf-8-*-
"""
测试版数据填充脚本 - 仅生成少量数据用于测试
"""
import json
import random
import pymysql
from datetime import datetime, date, timedelta
import sys
import os

# 数据库配置
MYSQL_CONFIG = {

}

# 测试模式：每个省只生成指定数量的数据
TEST_COUNT_PER_PROVINCE = 10

# 加载民族列表
def load_ethnicities():
    with open('ethnicity.md', 'r', encoding='utf-8') as f:
        content = f.read()
        ethnicities = eval(content)
    return ethnicities

# 加载省份数据
def load_province_data():
    with open('province_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 生成随机中文姓氏
def first_name():
    first_name_list = ['赵', '钱', '孙', '李', '周', '吴', '郑', '王', '冯', '陈']
    return random.choice(first_name_list)

# 生成随机中文字符
def GBK2312():
    head = random.randint(0xb0, 0xba)
    body = random.randint(0xa1, 0xf9)
    val = '%s%s' % (hex(head).replace('0x',''), hex(body).replace('0x',''))
    st = bytes.fromhex(val).decode('gb2312')
    return st

# 生成姓名
def genName():
    return first_name() + GBK2312() + (GBK2312() if random.randint(0, 1) else '')

# 生成身份证（指定前6位地址码）
def genIdCard(area_code, age, gender):
    # 验证并清理地址码
    area_code_str = str(area_code).strip()
    # 只保留数字
    area_code_str = ''.join(filter(str.isdigit, area_code_str))
    
    # 如果地址码不是6位，填充或截取
    if len(area_code_str) < 6:
        area_code_str = area_code_str.ljust(6, '0')
    elif len(area_code_str) > 6:
        area_code_str = area_code_str[:6]
    
    id_code_list = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_code_list = [1, 0, 'X', 9, 8, 7, 6, 5, 4, 3, 2]
    
    birth_year = date.today().year - age
    if birth_year < 1900:
        birth_year = 1900
    datestring = str(date(birth_year, 1, 1) + timedelta(days=random.randint(0, 364))).replace("-", "")
    
    rd = random.randint(1, 999)
    if gender == 0:
        gender_num = rd if rd % 2 == 0 else (rd + 1 if rd < 999 else rd - 1)
    else:
        gender_num = rd if rd % 2 == 1 else (rd - 1 if rd > 1 else rd + 1)
    
    result = area_code_str + datestring + str(gender_num).zfill(3)
    check_sum = sum([a * b for a, b in zip(id_code_list, [int(a) for a in result])]) % 11
    check_code = check_code_list[check_sum]
    
    return result + str(check_code)

# 解析地址
def parse_address(address_str):
    parts = address_str.split('-')
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1], ''
    else:
        return parts[0], '', ''

# 生成单个人口记录
def generate_person_data(area_code, address_str, ethnicities):
    age = random.randint(0, 100)
    gender = random.randint(0, 1)
    
    id_no = genIdCard(area_code, age, gender)
    name = genName()
    sex = "男" if gender == 1 else "女"
    
    birth_date = date.today() - timedelta(days=age*365 + random.randint(0, 364))
    
    # 随机民族 - 91%汉族，9%其他民族
    rand = random.random()
    if rand < 0.91:
        ethnicity = '汉族'
    else:
        # 从其他民族中随机选择（排除汉族）
        other_ethnicities = [e for e in ethnicities if e != '汉族']
        ethnicity = random.choice(other_ethnicities) if other_ethnicities else '汉族'
    
    education_levels = ['未上过学', '小学', '初中', '高中', '大专', '本科', '硕士及以上']
    education_level = random.choice(education_levels)
    
    province, city, district = parse_address(address_str)
    hukou_type = random.choice(['家庭户', '集体户'])
    processed_at = datetime.now()
    source = 'YY'
    
    return {
        'id_no': id_no,
        'name': name,
        'former_name': None,
        'gender': sex,
        'birth_date': birth_date,
        'ethnicity': ethnicity,
        'marital_status': None,
        'education_level': education_level,
        'hukou_province': province,
        'hukou_city': city,
        'hukou_district': district,
        'housing': None,
        'cur_province': None,
        'cur_city': None,
        'cur_district': None,
        'hukou_type': hukou_type,
        'income': None,
        'processed_at': processed_at,
        'source': source
    }

# 主函数
def main():
    print("=" * 60)
    print("人口数据填充脚本 - 测试版")
    print("=" * 60)
    print(f"每个省份生成: {TEST_COUNT_PER_PROVINCE} 条测试数据")
    print("=" * 60)
    
    # 加载数据
    print("正在加载配置数据...")
    ethnicities = load_ethnicities()
    province_data = load_province_data()
    print(f"加载完成：{len(ethnicities)} 个民族，{len(province_data)} 个省份")
    
    # 测试数据库连接
    print("正在测试数据库连接...")
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        print("数据库连接成功！")
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        return
    
    # 选择前3个省份进行测试
    test_provinces = list(province_data.items())[:3]
    
    print(f"\n将为以下省份生成测试数据：")
    for prov_name, prov_info in test_provinces:
        print(f"  - {prov_name} (原始人口: {prov_info['人口数']:,})")
    print()
    
    total_inserted = 0
    
    for prov_name, prov_info in test_provinces:
        print(f"正在处理 {prov_name}...")
        area_codes = prov_info['地址码']
        area_code_list = list(area_codes.items())
        
        batch = []
        for i in range(TEST_COUNT_PER_PROVINCE):
            area_code, address_str = random.choice(area_code_list)
            try:
                person = generate_person_data(area_code, address_str, ethnicities)
                batch.append(person)
            except Exception as e:
                print(f"  生成数据时出错: {str(e)}")
                continue
        
        # 插入数据
        try:
            cursor = conn.cursor()
            sql = """
            INSERT INTO population 
            (id_no, name, former_name, gender, birth_date, ethnicity, marital_status, 
             education_level, hukou_province, hukou_city, hukou_district, housing, 
             cur_province, cur_city, cur_district, hukou_type, income, processed_at, source)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            data = [
                (r['id_no'], r['name'], r['former_name'], r['gender'], r['birth_date'],
                 r['ethnicity'], r['marital_status'], r['education_level'],
                 r['hukou_province'], r['hukou_city'], r['hukou_district'], r['housing'],
                 r['cur_province'], r['cur_city'], r['cur_district'], r['hukou_type'],
                 r['income'], r['processed_at'], r['source'])
                for r in batch
            ]
            
            cursor.executemany(sql, data)
            conn.commit()
            total_inserted += len(batch)
            print(f"  {prov_name} 完成，成功插入 {len(batch)} 条记录")
            
            # 显示前2条示例数据
            print(f"  示例数据：")
            for j, person in enumerate(batch[:2], 1):
                print(f"    {j}. {person['name']} | {person['id_no']} | {person['gender']} | "
                      f"{person['ethnicity']} | {person['education_level']}")
            print()
            
        except Exception as e:
            print(f"  插入失败: {str(e)}\n")
    
    conn.close()
    
    print("=" * 60)
    print("测试完成！")
    print(f"总共成功插入: {total_inserted} 条测试数据")
    print("=" * 60)

if __name__ == '__main__':
    main()

