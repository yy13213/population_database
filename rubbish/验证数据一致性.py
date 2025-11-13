# -*-coding:utf-8-*-
"""
验证数据一致性脚本
检查身份证号中的信息与数据库字段是否一致
"""
import pymysql
from datetime import date

MYSQL_CONFIG = {

}

def parse_id_card(id_no):
    """从身份证号解析信息"""
    # 地址码（前6位）
    area_code = id_no[0:6]
    
    # 出生日期（7-14位）
    birth_str = id_no[6:14]
    birth_year = int(birth_str[0:4])
    birth_month = int(birth_str[4:6])
    birth_day = int(birth_str[6:8])
    birth_date = date(birth_year, birth_month, birth_day)
    
    # 性别（第17位）
    gender_code = int(id_no[16])
    gender = "男" if gender_code % 2 == 1 else "女"
    
    return area_code, birth_date, gender

def verify_data_consistency():
    """验证数据一致性"""
    print("=" * 70)
    print("数据一致性验证")
    print("=" * 70)
    
    connection = pymysql.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # 获取样本数据
    print("\n正在检查数据...")
    cursor.execute("SELECT id_no, name, gender, birth_date FROM population LIMIT 100")
    samples = cursor.fetchall()
    
    if not samples:
        print("❌ 数据库中没有数据")
        return
    
    print(f"检查样本数：{len(samples)} 条\n")
    
    # 验证结果
    gender_match = 0
    gender_mismatch = 0
    birth_match = 0
    birth_mismatch = 0
    
    mismatch_examples = []
    
    for person in samples:
        id_no = person['id_no']
        db_gender = person['gender']
        db_birth = person['birth_date']
        
        try:
            # 从身份证解析
            area_code, id_birth, id_gender = parse_id_card(id_no)
            
            # 比较性别
            if db_gender == id_gender:
                gender_match += 1
            else:
                gender_mismatch += 1
                if len(mismatch_examples) < 5:
                    mismatch_examples.append({
                        'type': '性别不匹配',
                        'id_no': id_no,
                        'name': person['name'],
                        'db_value': db_gender,
                        'id_value': id_gender
                    })
            
            # 比较出生日期
            if db_birth == id_birth:
                birth_match += 1
            else:
                birth_mismatch += 1
                if len(mismatch_examples) < 5:
                    mismatch_examples.append({
                        'type': '出生日期不匹配',
                        'id_no': id_no,
                        'name': person['name'],
                        'db_value': str(db_birth),
                        'id_value': str(id_birth)
                    })
        
        except Exception as e:
            print(f"解析身份证号失败: {id_no} - {str(e)}")
    
    # 打印结果
    print("📊 验证结果")
    print("-" * 70)
    
    print(f"\n1. 性别一致性检查：")
    print(f"   ✅ 匹配：{gender_match} 条 ({gender_match*100/len(samples):.1f}%)")
    print(f"   ❌ 不匹配：{gender_mismatch} 条 ({gender_mismatch*100/len(samples):.1f}%)")
    
    print(f"\n2. 出生日期一致性检查：")
    print(f"   ✅ 匹配：{birth_match} 条 ({birth_match*100/len(samples):.1f}%)")
    print(f"   ❌ 不匹配：{birth_mismatch} 条 ({birth_mismatch*100/len(samples):.1f}%)")
    
    # 显示不匹配的示例
    if mismatch_examples:
        print(f"\n⚠️  发现不匹配的数据示例：")
        for i, example in enumerate(mismatch_examples[:5], 1):
            print(f"\n   示例 {i}:")
            print(f"   类型：{example['type']}")
            print(f"   姓名：{example['name']}")
            print(f"   身份证：{example['id_no']}")
            print(f"   数据库值：{example['db_value']}")
            print(f"   身份证值：{example['id_value']}")
    
    # 总体结论
    print("\n" + "=" * 70)
    if gender_mismatch == 0 and birth_mismatch == 0:
        print("✅ 所有数据一致性检查通过！")
        print("   身份证号中的信息与数据库字段完全匹配")
    else:
        print("⚠️  发现数据不一致")
        print(f"   建议：重新运行数据填充脚本生成新数据")
    print("=" * 70)
    
    # 详细示例展示
    print("\n📋 随机展示5条数据的完整信息：")
    cursor.execute("SELECT id_no, name, gender, birth_date FROM population ORDER BY RAND() LIMIT 5")
    examples = cursor.fetchall()
    
    for i, person in enumerate(examples, 1):
        print(f"\n{i}. {person['name']}")
        print(f"   身份证号：{person['id_no']}")
        
        try:
            area_code, id_birth, id_gender = parse_id_card(person['id_no'])
            print(f"   【从身份证解析】")
            print(f"     地址码：{area_code}")
            print(f"     出生日期：{id_birth}")
            print(f"     性别：{id_gender}")
            print(f"   【数据库字段】")
            print(f"     出生日期：{person['birth_date']}")
            print(f"     性别：{person['gender']}")
            
            # 一致性标记
            birth_ok = "✅" if person['birth_date'] == id_birth else "❌"
            gender_ok = "✅" if person['gender'] == id_gender else "❌"
            print(f"   【一致性】出生日期 {birth_ok}  性别 {gender_ok}")
        except Exception as e:
            print(f"   ❌ 解析失败：{str(e)}")
    
    connection.close()

if __name__ == '__main__':
    verify_data_consistency()

