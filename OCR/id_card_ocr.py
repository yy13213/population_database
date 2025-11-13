# -*-coding:utf-8-*-
"""
身份证OCR识别和数据录入系统
使用GPT-4 Vision识别身份证信息，并存入数据库
"""
import io
import json
import base64
import pymysql
from datetime import datetime, date
from openai import OpenAI
from PIL import Image

# 数据库配置
MYSQL_CONFIG = {

}

# OpenAI配置
client = OpenAI(
    base_url="https://api.openai-proxy.org/v1",
    api_key="sk-nqxmOAEeIRkAYEs66tjqlvNCZ4Nl6uEK3XL554V1zFit2ojI"
)

def load_province_data():
    """加载省份地址码数据"""
    with open('../province_data.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_id_card_number(id_no):
    """
    从身份证号中解析信息
    :param id_no: 18位身份证号
    :return: (area_code, birth_date, gender)
    """
    # 地址码（前6位）
    area_code = id_no[0:6]
    
    # 出生日期（第7-14位）
    birth_str = id_no[6:14]
    birth_year = int(birth_str[0:4])
    birth_month = int(birth_str[4:6])
    birth_day = int(birth_str[6:8])
    birth_date = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
    
    # 性别（第17位，奇数=男，偶数=女）
    gender_code = int(id_no[16])
    gender = "男" if gender_code % 2 == 1 else "女"
    
    return area_code, birth_date, gender

def find_address_by_code(area_code, province_data):
    """
    根据地址码查找对应的省市区
    :param area_code: 6位地址码
    :param province_data: 省份数据
    :return: (province, city, district)
    """
    # 遍历所有省份
    for province_name, province_info in province_data.items():
        address_codes = province_info.get('地址码', {})
        
        # 查找匹配的地址码
        for code, address_str in address_codes.items():
            if code == area_code:
                # 解析地址字符串
                parts = address_str.split('-')
                if len(parts) >= 3:
                    return parts[0], parts[1], parts[2]
                elif len(parts) == 2:
                    return parts[0], parts[1], ''
                else:
                    return parts[0], '', ''
    
    # 如果找不到，返回空值
    return '', '', ''

def recognize_id_card(image_path):
    """
    使用GPT-4 Vision识别身份证信息
    :param image_path: 身份证图片路径
    :return: dict 包含身份证信息的字典
    """
    try:
        # 读取图片
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # 转换为base64
        image_base64 = base64.b64encode(image_bytes).decode()
        
        # 构建提示
        prompt = """
请识别这张身份证图片中的信息，并以JSON格式返回。

要求：
1. 仔细识别身份证上的所有文字信息
2. 身份证号码必须准确，18位数字
3. 地址要完整，包含省市区
4. 返回纯JSON格式，不要有其他文字

返回格式示例：
{
    "id_no": "110101199001011234",
    "name": "张三",
    "ethnicity": "汉族",
    "address": "北京市东城区某某街道某某号"
}

注意：
- id_no: 18位身份证号码
- name: 姓名
- ethnicity: 民族
- address: 住址（尽可能详细）
"""
        
        # 调用GPT-4 Vision
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        # 解析返回结果
        result_text = response.choices[0].message.content
        
        # 提取JSON（可能包含markdown代码块）
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        # 解析JSON
        id_card_info = json.loads(result_text)
        
        return id_card_info
    
    except Exception as e:
        raise Exception(f"身份证识别失败: {str(e)}")

def parse_address(address_str):
    """
    从地址字符串中提取省市区
    :param address_str: 地址字符串
    :return: (province, city, district)
    """
    # 常见的省市区关键词
    province_keywords = ['省', '市', '自治区', '特别行政区']
    city_keywords = ['市', '地区', '自治州', '盟']
    district_keywords = ['区', '县', '市', '旗']
    
    province = ''
    city = ''
    district = ''
    
    # 简单的规则提取
    parts = address_str.replace('省', '省|').replace('市', '市|').replace('区', '区|').replace('县', '县|').split('|')
    parts = [p.strip() for p in parts if p.strip()]
    
    if len(parts) >= 1:
        province = parts[0]
        if not any(kw in province for kw in province_keywords):
            province = province + ('省' if province else '')
    
    if len(parts) >= 2:
        city = parts[1]
        if not any(kw in city for kw in city_keywords):
            city = city + ('市' if city else '')
    
    if len(parts) >= 3:
        district = parts[2]
        if not any(kw in district for kw in district_keywords):
            district = district + ('区' if district else '')
    
    return province, city, district

def process_id_card_data(ocr_result, province_data, source_code='CLI'):
    """
    处理OCR识别结果，生成完整的人口数据
    :param ocr_result: OCR识别结果
    :param province_data: 省份数据
    :param source_code: 数据来源代号
    :return: dict 完整的人口数据
    """
    id_no = ocr_result.get('id_no', '')
    
    # 验证身份证号
    if not id_no or len(id_no) != 18:
        raise Exception("身份证号码格式错误")
    
    # 从身份证号中解析信息
    area_code, birth_date, gender = parse_id_card_number(id_no)
    
    # 根据地址码查找户籍所在地
    hukou_province, hukou_city, hukou_district = find_address_by_code(area_code, province_data)
    
    # 从OCR结果中提取现居住地
    address_str = ocr_result.get('address', '')
    cur_province, cur_city, cur_district = parse_address(address_str)
    
    # 组装完整数据
    person_data = {
        'id_no': id_no,
        'name': ocr_result.get('name', ''),
        'former_name': None,  # 留空
        'gender': gender,
        'birth_date': birth_date,
        'ethnicity': ocr_result.get('ethnicity', ''),
        'marital_status': None,  # 留空
        'education_level': None,  # 留空
        'hukou_province': hukou_province,
        'hukou_city': hukou_city,
        'hukou_district': hukou_district,
        'housing': None,  # 留空
        'cur_province': cur_province,
        'cur_city': cur_city,
        'cur_district': cur_district,
        'hukou_type': None,  # 留空
        'income': None,  # 留空
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source': source_code  # 使用传入的source代号
    }
    
    return person_data

def display_person_data(person_data):
    """
    显示人口数据
    :param person_data: 人口数据字典
    """
    print("\n" + "=" * 70)
    print("识别到的身份证信息")
    print("=" * 70)
    
    print(f"\n📋 基本信息")
    print(f"  身份证号码：{person_data['id_no']}")
    print(f"  姓名：{person_data['name']}")
    print(f"  性别：{person_data['gender']}")
    print(f"  出生日期：{person_data['birth_date']}")
    print(f"  民族：{person_data['ethnicity']}")
    
    print(f"\n🏠 户籍信息（从身份证号前6位解析）")
    print(f"  省份：{person_data['hukou_province']}")
    print(f"  城市：{person_data['hukou_city']}")
    print(f"  区县：{person_data['hukou_district']}")
    
    print(f"\n📍 现居住地（从身份证地址识别）")
    print(f"  省份：{person_data['cur_province']}")
    print(f"  城市：{person_data['cur_city']}")
    print(f"  区县：{person_data['cur_district']}")
    
    print(f"\n📅 其他信息")
    print(f"  处理时间：{person_data['processed_at']}")
    print(f"  数据来源：{person_data['source']}")
    
    print("\n" + "=" * 70)

def save_to_database(person_data):
    """
    保存数据到数据库
    :param person_data: 人口数据字典
    :return: bool 是否成功
    """
    try:
        connection = pymysql.connect(**MYSQL_CONFIG)
        cursor = connection.cursor()
        
        sql = """
        INSERT INTO population 
        (id_no, name, former_name, gender, birth_date, ethnicity, marital_status, 
         education_level, hukou_province, hukou_city, hukou_district, housing, 
         cur_province, cur_city, cur_district, hukou_type, income, processed_at, source)
        VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = (
            person_data['id_no'],
            person_data['name'],
            person_data['former_name'],
            person_data['gender'],
            person_data['birth_date'],
            person_data['ethnicity'],
            person_data['marital_status'],
            person_data['education_level'],
            person_data['hukou_province'],
            person_data['hukou_city'],
            person_data['hukou_district'],
            person_data['housing'],
            person_data['cur_province'],
            person_data['cur_city'],
            person_data['cur_district'],
            person_data['hukou_type'],
            person_data['income'],
            person_data['processed_at'],
            person_data['source']
        )
        
        cursor.execute(sql, data)
        connection.commit()
        
        print("\n✅ 数据已成功保存到数据库！")
        return True
    
    except pymysql.err.IntegrityError as e:
        if '1062' in str(e):
            print("\n❌ 保存失败：该身份证号已存在于数据库中")
        else:
            print(f"\n❌ 保存失败：{str(e)}")
        return False
    
    except Exception as e:
        print(f"\n❌ 保存失败：{str(e)}")
        return False
    
    finally:
        if connection:
            connection.close()

def main(image_path, source_code=None):
    """
    主函数
    :param image_path: 身份证图片路径
    :param source_code: 数据来源代号
    """
    print("\n🔍 正在识别身份证...")
    
    try:
        # 1. 如果没有提供source_code，询问用户
        if not source_code:
            print("\n❓ 请输入数据来源代号（例如：YY）：")
            source_code = input("数据来源代号：").strip()
            
            if not source_code:
                print("❌ 数据来源代号不能为空")
                return
        
        print(f"✅ 数据来源：{source_code}")
        
        # 2. 加载省份数据
        province_data = load_province_data()
        
        # 3. OCR识别身份证
        ocr_result = recognize_id_card(image_path)
        print("✅ 身份证识别成功")
        
        # 4. 处理数据
        person_data = process_id_card_data(ocr_result, province_data, source_code)
        
        # 5. 显示数据
        display_person_data(person_data)
        
        # 6. 征得用户同意
        print("\n❓ 是否将以上信息保存到数据库？")
        confirm = input("请输入 yes 确认，或 no 取消：").strip().lower()
        
        if confirm in ['yes', 'y']:
            # 7. 保存到数据库
            save_to_database(person_data)
        else:
            print("\n❌ 已取消保存")
    
    except Exception as e:
        print(f"\n❌ 处理失败：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法：")
        print("  python id_card_ocr.py <身份证图片路径> [数据来源代号]")
        print("\n示例：")
        print("  python id_card_ocr.py id_card.jpg YY")
        print("  python id_card_ocr.py id_card.jpg  # 会提示输入代号")
    else:
        image_path = sys.argv[1]
        source_code = sys.argv[2] if len(sys.argv) > 2 else None
        main(image_path, source_code)

